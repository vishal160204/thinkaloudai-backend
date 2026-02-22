"""
ThinkAloud.ai — Test Runner Service
Runs ALL test cases in a SINGLE container execution (like LeetCode).
"""
import json
import logging
import re

from app.services.code_runner import run_code

logger = logging.getLogger(__name__)


def build_batch_wrapper(code: str, test_cases: list[dict], language: str) -> str:
    """
    Wraps user code to run ALL test cases in one execution.
    Outputs JSON array of results — one per test case.
    
    This is how LeetCode does it: 1 container, all tests in a loop.
    """
    if language == "python":
        func_match = re.search(r'def\s+(\w+)\s*\(([^)]*)\)', code)
        if not func_match:
            return code

        func_name = func_match.group(1)
        params = [p.strip().split(':')[0].split('=')[0].strip()
                  for p in func_match.group(2).split(',') if p.strip()]

        # Build test runner that calls the function for each test case
        wrapper = f"{code}\n\n"
        wrapper += "# --- Test Runner (batch) ---\n"
        wrapper += "import json as _json\n"
        wrapper += "_results = []\n"

        for i, tc in enumerate(test_cases):
            test_input = tc.get("input", "")
            assignments = _parse_assignments(test_input, params)

            wrapper += f"\n# Test {i + 1}\n"
            wrapper += "try:\n"
            for param, value in assignments.items():
                wrapper += f"    _{param} = {value}\n"
            call_args = ', '.join(f'_{p}' for p in params)
            wrapper += f"    _out = {func_name}({call_args})\n"
            wrapper += f"    _results.append(str(_out))\n"
            wrapper += "except Exception as _e:\n"
            wrapper += f"    _results.append('ERROR: ' + str(_e))\n"

        wrapper += "\nfor _r in _results:\n"
        wrapper += "    print(_r)\n"

        return wrapper

    elif language == "javascript":
        func_match = re.search(r'function\s+(\w+)\s*\(([^)]*)\)', code)
        if not func_match:
            return code

        func_name = func_match.group(1)
        params = [p.strip() for p in func_match.group(2).split(',') if p.strip()]

        wrapper = f"{code}\n\n"
        wrapper += "// --- Test Runner (batch) ---\n"
        wrapper += "const _results = [];\n"

        for i, tc in enumerate(test_cases):
            test_input = tc.get("input", "")
            assignments = _parse_assignments(test_input, params)

            wrapper += "try {\n"
            for param, value in assignments.items():
                wrapper += f"    let _{param} = {value};\n"
            call_args = ', '.join(f'_{p}' for p in params)
            wrapper += f"    let _out = {func_name}({call_args});\n"
            wrapper += f"    _results.push(JSON.stringify(_out));\n"
            wrapper += "} catch(_e) {\n"
            wrapper += f"    _results.push('ERROR: ' + _e.message);\n"
            wrapper += "}\n"

        wrapper += "_results.forEach(r => console.log(r));\n"
        return wrapper

    elif language == "cpp":
        # For C++, we parse the function name and generate a main() that calls it
        func_match = re.search(r'(?:int|void|bool|string|vector\s*<[^>]+>|long\s*long|double|float|ListNode\*?|TreeNode\*?)\s+(\w+)\s*\(([^)]*)\)', code)
        if not func_match:
            return code

        func_name = func_match.group(1)
        raw_params = func_match.group(2)
        
        # Parse C++ params like "vector<int>& nums, int target"
        params = []
        for p in raw_params.split(','):
            p = p.strip()
            if not p:
                continue
            # Get the variable name (last word, strip & *)
            parts = p.replace('&', '').replace('*', '').split()
            if parts:
                params.append(parts[-1].strip())

        wrapper = f"#include <bits/stdc++.h>\nusing namespace std;\n\n{code}\n\n"
        wrapper += "int main() {\n"

        for i, tc in enumerate(test_cases):
            test_input = tc.get("input", "")
            assignments = _parse_assignments(test_input, params)

            wrapper += f"    // Test {i + 1}\n"
            wrapper += "    try {\n"
            
            # Declare variables with auto type deduction from values
            for param, value in assignments.items():
                cpp_value = _python_to_cpp_value(value)
                cpp_type = _infer_cpp_type(value)
                wrapper += f"        {cpp_type} _{param} = {cpp_value};\n"
            
            call_args = ', '.join(f'_{p}' for p in params if p in assignments)
            wrapper += f"        auto _result = {func_name}({call_args});\n"
            wrapper += f"        _print_result(_result);\n"
            wrapper += "    } catch (...) {\n"
            wrapper += f'        cout << "ERROR" << endl;\n'
            wrapper += "    }\n"

        wrapper += "    return 0;\n}\n"

        # Add a generic print helper before main
        print_helper = """
// --- Output helpers ---
template<typename T>
void _print_result(const vector<T>& v) {
    cout << "[";
    for (int i = 0; i < v.size(); i++) {
        if (i > 0) cout << ", ";
        cout << v[i];
    }
    cout << "]" << endl;
}
void _print_result(int v) { cout << v << endl; }
void _print_result(long long v) { cout << v << endl; }
void _print_result(double v) { cout << v << endl; }
void _print_result(bool v) { cout << (v ? "true" : "false") << endl; }
void _print_result(const string& v) { cout << '"' << v << '"' << endl; }

"""
        # Insert print helper between code and main
        parts = wrapper.split("int main() {")
        wrapper = parts[0] + print_helper + "int main() {" + parts[1]

        return wrapper

    return code


def _python_to_cpp_value(value: str) -> str:
    """Convert Python-style values to C++ syntax."""
    value = value.strip()
    # [1, 2, 3] → {1, 2, 3}
    if value.startswith('[') and value.endswith(']'):
        inner = value[1:-1]
        return '{' + inner + '}'
    # "string" → "string" (already valid C++)
    # true/false → true/false (already valid)
    # None → 0
    if value.lower() == 'none' or value.lower() == 'null':
        return '0'
    return value


def _infer_cpp_type(value: str) -> str:
    """Infer a C++ type from a Python-style value."""
    value = value.strip()
    if value.startswith('['):
        # Check if it's a 2D array
        inner = value[1:-1].strip()
        if inner.startswith('['):
            return "vector<vector<int>>"
        # Check if values are strings
        if '"' in inner or "'" in inner:
            return "vector<string>"
        return "vector<int>"
    if value.startswith('"') or value.startswith("'"):
        return "string"
    if value.lower() in ('true', 'false'):
        return "bool"
    if '.' in value:
        return "double"
    return "int"


def _parse_assignments(test_input: str, params: list[str]) -> dict:
    """
    Parse test input like 'nums = [2,7,11,15], target = 9'
    into {'nums': '[2,7,11,15]', 'target': '9'} using known param names.
    """
    assignments = {}

    for i, param in enumerate(params):
        pattern = rf'{param}\s*=\s*'
        match = re.search(pattern, test_input)
        if not match:
            continue

        value_start = match.end()

        if i < len(params) - 1:
            next_param = params[i + 1]
            next_pattern = rf',\s*{next_param}\s*='
            next_match = re.search(next_pattern, test_input[value_start:])
            if next_match:
                value = test_input[value_start:value_start + next_match.start()].strip()
            else:
                value = test_input[value_start:].strip()
        else:
            value = test_input[value_start:].strip()

        assignments[param] = value

    return assignments


async def run_tests(
    code: str,
    language: str,
    test_cases: list[dict],
) -> dict:
    """
    Run ALL test cases in a SINGLE container execution.
    
    Returns:
        {
            "test_results": [{"input", "expected", "actual", "passed"}],
            "tests_passed": int,
            "tests_total": int,
            "execution_result": dict,
        }
    """
    # Build one big script that runs all tests
    wrapped_code = build_batch_wrapper(code, test_cases, language)

    # Single execution for ALL test cases
    execution = await run_code(wrapped_code, language)

    # Parse output — one line per test case
    output_lines = execution["stdout"].strip().split("\n") if execution["stdout"].strip() else []

    results = []
    for i, tc in enumerate(test_cases):
        expected = tc.get("expected_output", "").strip()
        actual = output_lines[i].strip() if i < len(output_lines) else "NO OUTPUT"
        passed = actual == expected

        results.append({
            "input": tc.get("input", ""),
            "expected": expected,
            "actual": actual,
            "passed": passed,
        })

    tests_passed = sum(1 for r in results if r["passed"])

    return {
        "test_results": results,
        "tests_passed": tests_passed,
        "tests_total": len(results),
        "execution_result": execution,
    }
