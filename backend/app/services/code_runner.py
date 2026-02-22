"""
ThinkAloud.ai — Code Runner Service
Executes user code in isolated Docker containers.
Falls back to subprocess if Docker is unavailable.
Supports: Python, JavaScript, C++
"""
import asyncio
import logging
import os
import tempfile
import time

logger = logging.getLogger(__name__)

# Limits
MAX_EXECUTION_TIME = 10  # seconds
MAX_OUTPUT_SIZE = 10_000  # characters
SANDBOX_IMAGE = "thinkaloud-sandbox"
MEMORY_LIMIT = "128m"
CPU_PERIOD = 100_000
CPU_QUOTA = 50_000  # 50% of one core

# Language configs
LANGUAGE_CONFIG = {
    "python": {
        "ext": ".py",
        "cmd": "python3 /code/solution.py",
        "compile": None,
    },
    "javascript": {
        "ext": ".js",
        "cmd": "node /code/solution.js",
        "compile": None,
    },
    "cpp": {
        "ext": ".cpp",
        "cmd": "/code/solution",
        "compile": "g++ -O2 -std=c++17 -o /code/solution /code/solution.cpp",
    },
}


def _docker_available() -> bool:
    """Check if Docker is available."""
    try:
        import docker
        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False


# Concurrency limit — max 5 Docker containers at once
_execution_semaphore = asyncio.Semaphore(5)


async def run_code(code: str, language: str, stdin: str = "") -> dict:
    """Execute code with concurrency limit."""
    async with _execution_semaphore:
        if _docker_available():
            return await _run_in_docker(code, language, stdin)
        else:
            logger.warning("Docker unavailable — using subprocess fallback (NOT SAFE FOR PROD)")
            return await _run_in_subprocess(code, language, stdin)


async def _run_in_docker(code: str, language: str, stdin: str = "") -> dict:
    """Run code inside an isolated Docker container."""
    if language not in LANGUAGE_CONFIG:
        return _error_result(f"Unsupported language: {language}")

    config = LANGUAGE_CONFIG[language]
    ext = config["ext"]
    run_cmd = config["cmd"]
    compile_cmd = config["compile"]

    # Build the full command: compile (if needed) then run
    if compile_cmd:
        full_cmd = f"{compile_cmd} && {run_cmd}"
    else:
        full_cmd = run_cmd

    # Write code to temp file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=ext, delete=False, prefix="solution"
    ) as f:
        f.write(code)
        filepath = f.name

    try:
        import docker
        client = docker.from_env()

        start_time = time.perf_counter()

        container = client.containers.run(
            SANDBOX_IMAGE,
            command=f"sh -c '{full_cmd}'",
            volumes={filepath: {"bind": f"/code/solution{ext}", "mode": "ro"}},
            mem_limit=MEMORY_LIMIT,
            cpu_period=CPU_PERIOD,
            cpu_quota=CPU_QUOTA,
            network_disabled=True,       # No internet
            read_only=True,              # Read-only filesystem
            tmpfs={"/tmp": "size=10m"},   # Small writable /tmp
            user="sandbox",
            detach=True,
            stdin_open=bool(stdin),
        )

        try:
            result = container.wait(timeout=MAX_EXECUTION_TIME)
            stdout = container.logs(stdout=True, stderr=False).decode(errors="replace")
            stderr = container.logs(stdout=False, stderr=True).decode(errors="replace")
            exit_code = result.get("StatusCode", -1)
            timed_out = False
        except Exception:
            container.kill()
            stdout, stderr = "", f"Time Limit Exceeded ({MAX_EXECUTION_TIME}s)"
            exit_code, timed_out = -1, True

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        container.remove(force=True)

        return {
            "stdout": stdout[:MAX_OUTPUT_SIZE],
            "stderr": stderr[:MAX_OUTPUT_SIZE],
            "exit_code": exit_code,
            "execution_time_ms": elapsed_ms,
            "timed_out": timed_out,
        }

    except Exception as e:
        logger.error(f"Docker execution error: {e}", exc_info=True)
        return _error_result(f"Execution error: {str(e)}")

    finally:
        try:
            os.unlink(filepath)
        except OSError:
            pass


async def _run_in_subprocess(code: str, language: str, stdin: str = "") -> dict:
    """Fallback: run code in subprocess (dev only)."""
    if language not in LANGUAGE_CONFIG:
        return _error_result(f"Unsupported language: {language}")

    config = LANGUAGE_CONFIG[language]
    ext = config["ext"]

    with tempfile.NamedTemporaryFile(mode="w", suffix=ext, delete=False) as f:
        f.write(code)
        filepath = f.name

    try:
        if language == "python":
            cmd = ["python3", filepath]
        elif language == "javascript":
            cmd = ["node", filepath]
        elif language == "cpp":
            # Compile first, then run
            binary = filepath.replace(ext, "")
            compile_proc = await asyncio.create_subprocess_exec(
                "g++", "-O2", "-std=c++17", "-o", binary, filepath,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, compile_err = await asyncio.wait_for(
                compile_proc.communicate(), timeout=MAX_EXECUTION_TIME
            )
            if compile_proc.returncode != 0:
                return {
                    "stdout": "",
                    "stderr": f"Compilation Error:\n{compile_err.decode(errors='replace')[:MAX_OUTPUT_SIZE]}",
                    "exit_code": compile_proc.returncode,
                    "execution_time_ms": 0,
                    "timed_out": False,
                }
            cmd = [binary]
        else:
            return _error_result(f"Unsupported language: {language}")

        start_time = time.perf_counter()
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={"PATH": os.environ.get("PATH", ""), "HOME": "/tmp", "LANG": "en_US.UTF-8"},
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=stdin.encode() if stdin else None),
                timeout=MAX_EXECUTION_TIME,
            )
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)

            return {
                "stdout": stdout.decode(errors="replace")[:MAX_OUTPUT_SIZE],
                "stderr": stderr.decode(errors="replace")[:MAX_OUTPUT_SIZE],
                "exit_code": process.returncode,
                "execution_time_ms": elapsed_ms,
                "timed_out": False,
            }

        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            return {
                "stdout": "",
                "stderr": f"Time Limit Exceeded ({MAX_EXECUTION_TIME}s)",
                "exit_code": -1,
                "execution_time_ms": elapsed_ms,
                "timed_out": True,
            }

    except Exception as e:
        logger.error(f"Subprocess error: {e}", exc_info=True)
        return _error_result(f"Execution error: {str(e)}")
    finally:
        try:
            os.unlink(filepath)
            # Also clean up binary for C++
            if language == "cpp":
                binary = filepath.replace(ext, "")
                os.unlink(binary)
        except OSError:
            pass


def _error_result(msg: str) -> dict:
    return {
        "stdout": "",
        "stderr": msg,
        "exit_code": -1,
        "execution_time_ms": 0,
        "timed_out": False,
    }
