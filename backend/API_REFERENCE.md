# ThinkAloud.ai — API Reference

**Base URL**: `http://134.199.198.184:8080/api/v1`  
**Swagger Docs**: `http://134.199.198.184:8080/docs`  
**Auth**: Bearer token in `Authorization` header

---

## Quick Start

```javascript
const API = "http://134.199.198.184:8080/api/v1";

// 1. Sign up
await fetch(`${API}/signup`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ username: "vishal", email: "vis@example.com", password: "pass123" }),
});

// 2. Verify OTP (check email)
const { access_token } = await fetch(`${API}/verify-signup`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email: "vis@example.com", otp: "123456" }),
}).then(r => r.json());

// 3. Use the token for all subsequent requests
const headers = {
  "Authorization": `Bearer ${access_token}`,
  "Content-Type": "application/json",
};
```

---

## 🔐 Authentication

### `POST /signup`
Register a new account. Sends OTP to email.

```json
// Request
{ "username": "vishal", "email": "vis@example.com", "password": "securepass123" }

// Response 200
{ "message": "OTP sent to your email" }

// Error 409
{ "detail": "Email already registered" }
```

---

### `POST /verify-signup`
Verify OTP and activate account. Returns auth tokens.

```json
// Request
{ "email": "vis@example.com", "otp": "123456" }

// Response 200
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci..."
}
```

---

### `POST /resend-signup-otp`
Resend OTP (60s cooldown).

```json
// Request
{ "email": "vis@example.com" }

// Response 200
{ "message": "OTP resent to your email" }

// Error 429
{ "detail": "Wait 60 seconds before resending" }
```

---

### `POST /login`
Login with email + password. 5 failed attempts = 15 min lockout.

```json
// Request
{ "email": "vis@example.com", "password": "securepass123" }

// Response 200
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci..."
}

// Error 401
{ "detail": "Invalid credentials" }
```

---

### `POST /refresh`
Exchange refresh token for new tokens.

```json
// Request
{ "refresh_token": "eyJhbGci..." }

// Response 200
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci..."
}
```

---

### `POST /forgot-password`
Request password reset OTP.

```json
// Request
{ "email": "vis@example.com" }

// Response 200 (always, for security)
{ "message": "If email exists, OTP sent" }
```

---

### `POST /reset-password`
Reset password with OTP.

```json
// Request
{ "email": "vis@example.com", "otp": "123456", "new_password": "newpass123" }

// Response 200
{ "message": "Password reset successful" }
```

---

## 👤 User Profile

> All endpoints require `Authorization: Bearer <token>`

### `GET /users/me`
Get current user's profile.

```json
// Response 200
{
  "id": 1,
  "username": "vishal",
  "email": "vis@example.com",
  "full_name": "Vishal Saini",
  "avatar_url": "/uploads/avatars/1_abc123.png",
  "bio": "Building cool stuff",
  "is_admin": false,
  "created_at": "2026-02-15T10:00:00Z",
  "last_login_at": "2026-02-22T08:30:00Z"
}
```

---

### `PATCH /users/me`
Update profile fields. Only send fields you want to change.

```json
// Request
{ "username": "vishal_dev", "full_name": "Vishal Saini", "bio": "Full-stack developer" }

// Response 200 → updated UserProfile
```

---

### `POST /users/me/avatar`
Upload avatar (multipart form). Max 2MB. PNG/JPG/WEBP only.

```javascript
const form = new FormData();
form.append("file", fileInput.files[0]);

const res = await fetch(`${API}/users/me/avatar`, {
  method: "POST",
  headers: { "Authorization": `Bearer ${token}` },
  body: form,
});
```

```json
// Response 200 → updated UserProfile with avatar_url
```

---

### `GET /users/me/practice-time`
Get total practice time.

```json
// Response 200
{
  "total_seconds": 9900,
  "total_hours": 2,
  "total_minutes": 45,
  "display": "2h 45m"
}
```

---

## 📋 Problems

### `GET /problems/`
List all published problems. Supports filtering and pagination.

```
GET /problems/?difficulty=easy&category=arrays&page=1&limit=20
```

```json
// Response 200
[
  {
    "id": 1,
    "title": "Two Sum",
    "slug": "two-sum",
    "difficulty": "easy",
    "category": "arrays",
    "tags": ["arrays", "hash-table"]
  }
]
```

---

### `GET /problems/{slug}`
Get problem detail by slug. Hidden test cases are filtered out.

```json
// Response 200
{
  "id": 1,
  "title": "Two Sum",
  "slug": "two-sum",
  "description": "Given an array of integers nums and an integer target...",
  "difficulty": "easy",
  "category": "arrays",
  "constraints": "2 <= nums.length <= 10^4",
  "tags": ["arrays", "hash-table"],
  "hints": ["Try using a hash map", "Think about complement"],
  "starter_code": {
    "python": "def two_sum(nums, target):\n    pass",
    "javascript": "function twoSum(nums, target) {\n}"
  },
  "test_cases": [
    { "input": "nums = [2,7,11,15], target = 9", "expected_output": "[0, 1]" }
  ]
}
```

---

## 🎯 Sessions

> All endpoints require `Authorization: Bearer <token>`

### `POST /sessions/`
Start a new practice session.

```json
// Request
{ "problem_id": 1, "session_type": "practice", "language": "python" }

// Response 200
{
  "id": 1,
  "user_id": 6,
  "problem_id": 1,
  "session_type": "practice",
  "language": "python",
  "status": "active",
  "started_at": "2026-02-22T08:00:00Z"
}
```

---

### `GET /sessions/`
List all sessions for current user (most recent first, limit 50).

```json
// Response 200
[
  {
    "id": 1,
    "problem_id": 1,
    "session_type": "practice",
    "status": "completed",
    "language": "python",
    "duration_seconds": 1200,
    "started_at": "2026-02-22T08:00:00Z",
    "completed_at": "2026-02-22T08:20:00Z"
  }
]
```

---

### `GET /sessions/{session_id}`
Get session detail with all submissions and feedback.

```json
// Response 200
{
  "id": 1,
  "status": "active",
  "submissions": [
    {
      "id": 1,
      "code": "def two_sum...",
      "language": "python",
      "tests_passed": 3,
      "tests_total": 3,
      "submitted_at": "2026-02-22T08:10:00Z"
    }
  ],
  "feedback": [
    {
      "id": 1,
      "overall_score": 8,
      "summary": "Great solution using a hash map..."
    }
  ]
}
```

---

### `POST /sessions/{session_id}/submit`
Submit code. Runs in Docker sandbox, executes against test cases.

```json
// Request
{
  "code": "def two_sum(nums, target):\n    seen = {}\n    for i, num in enumerate(nums):\n        comp = target - num\n        if comp in seen:\n            return [seen[comp], i]\n        seen[num] = i",
  "language": "python"
}

// Response 200
{
  "id": 1,
  "session_id": 1,
  "code": "def two_sum...",
  "language": "python",
  "tests_passed": 3,
  "tests_total": 3,
  "execution_result": {
    "stdout": "[0, 1]\n",
    "stderr": "",
    "exit_code": 0,
    "execution_time_ms": 106,
    "timed_out": false
  },
  "test_results": [
    {
      "input": "nums = [2,7,11,15], target = 9",
      "expected": "[0, 1]",
      "actual": "[0, 1]",
      "passed": true
    }
  ],
  "submitted_at": "2026-02-22T08:10:00Z"
}
```

---

### `POST /sessions/{session_id}/complete`
Mark session as completed. Updates duration, user progress, and streak.

```json
// Response 200
{
  "id": 1,
  "status": "completed",
  "duration_seconds": 1200,
  "completed_at": "2026-02-22T08:20:00Z"
}
```

---

## 📊 Stats & Progress

> All endpoints require `Authorization: Bearer <token>`

### `GET /stats/dashboard`
Aggregated dashboard stats.

```json
// Response 200
{
  "total_sessions": 15,
  "total_problems_attempted": 8,
  "total_problems_solved": 5,
  "easy_solved": 3,
  "medium_solved": 2,
  "hard_solved": 0,
  "current_streak": 3,
  "longest_streak": 7,
  "avg_score": 7.5
}
```

---

### `GET /stats/streaks`
Last 365 days activity data (for heatmap visualization).

```json
// Response 200
[
  { "date": "2026-02-20", "activity_count": 3 },
  { "date": "2026-02-21", "activity_count": 1 },
  { "date": "2026-02-22", "activity_count": 2 }
]
```

---

### `GET /stats/progress`
Per-problem progress.

```json
// Response 200
[
  {
    "problem_id": 1,
    "problem_title": "Two Sum",
    "difficulty": "easy",
    "attempts": 3,
    "best_score": 8.5,
    "is_solved": true
  }
]
```

---

## 🤖 AI (Powered by vLLM on MI300X)

> All endpoints require `Authorization: Bearer <token>`

### `POST /ai/sessions/{session_id}/feedback`
Generate AI code analysis for the latest submission. Saves to DB.

```json
// Response 200
{
  "feedback_id": 1,
  "session_id": 1,
  "overall_score": 8,
  "time_complexity": "O(n)",
  "space_complexity": "O(n)",
  "strengths": [
    "Clean, readable code",
    "Optimal O(n) time complexity with hash map"
  ],
  "weaknesses": [
    "No input validation",
    "Missing docstring"
  ],
  "suggestions": [
    "Add type hints for better readability",
    "Consider edge case: empty array input"
  ],
  "summary": "Strong solution using a hash map for O(n) lookup. Code is clean and efficient."
}
```

---

### `POST /ai/problems/{problem_id}/hint`
Get an AI hint. Never reveals the solution.

```json
// Request
{ "code": "def two_sum(nums, target):\n    pass", "language": "python" }

// Response 200
{
  "hint": "What if you stored each number you've seen so far? What data structure gives O(1) lookups?",
  "problem_id": 1
}
```

---

## 🎤 Voice Interview (LiveKit)

> All endpoints require `Authorization: Bearer <token>`

### `POST /voice/start/{session_id}`
Start a voice interview. Returns LiveKit connection details.

```json
// Response 200
{
  "livekit_url": "ws://134.199.198.184:7880",
  "token": "eyJhbGci...",
  "room_name": "interview-1",
  "session_id": 1
}
```

**Frontend integration:**
```jsx
import { LiveKitRoom, AudioTrack, RoomAudioRenderer } from "@livekit/components-react";

function VoiceInterview({ livekitUrl, token }) {
  return (
    <LiveKitRoom serverUrl={livekitUrl} token={token} connect={true}>
      <RoomAudioRenderer />
      {/* User's mic is automatically streamed */}
      {/* AI agent joins and speaks back */}
    </LiveKitRoom>
  );
}
```

---

### `POST /voice/end/{session_id}`
End a voice interview. Deletes the LiveKit room.

```json
// Request (optional)
{ "transcript": "Full conversation transcript..." }

// Response 200
{ "message": "Voice session ended", "session_id": 1 }
```

---

## 🔑 Frontend Auth Pattern

```javascript
// utils/api.js
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8080/api/v1";

class ApiClient {
  constructor() {
    this.accessToken = localStorage.getItem("access_token");
    this.refreshToken = localStorage.getItem("refresh_token");
  }

  setTokens(access, refresh) {
    this.accessToken = access;
    this.refreshToken = refresh;
    localStorage.setItem("access_token", access);
    localStorage.setItem("refresh_token", refresh);
  }

  clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  }

  async request(path, options = {}) {
    const headers = { "Content-Type": "application/json", ...options.headers };
    if (this.accessToken) {
      headers["Authorization"] = `Bearer ${this.accessToken}`;
    }

    let res = await fetch(`${API_URL}${path}`, { ...options, headers });

    // Auto-refresh on 401
    if (res.status === 401 && this.refreshToken) {
      const refreshRes = await fetch(`${API_URL}/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: this.refreshToken }),
      });

      if (refreshRes.ok) {
        const { access_token, refresh_token } = await refreshRes.json();
        this.setTokens(access_token, refresh_token);
        headers["Authorization"] = `Bearer ${access_token}`;
        res = await fetch(`${API_URL}${path}`, { ...options, headers });
      } else {
        this.clearTokens();
        window.location.href = "/login";
      }
    }

    return res;
  }

  // --- Auth ---
  signup(data) { return this.request("/signup", { method: "POST", body: JSON.stringify(data) }); }
  verifyOtp(data) { return this.request("/verify-signup", { method: "POST", body: JSON.stringify(data) }); }
  login(data) { return this.request("/login", { method: "POST", body: JSON.stringify(data) }); }

  // --- Profile ---
  getProfile() { return this.request("/users/me"); }
  updateProfile(data) { return this.request("/users/me", { method: "PATCH", body: JSON.stringify(data) }); }
  getPracticeTime() { return this.request("/users/me/practice-time"); }

  // --- Problems ---
  getProblems(params = "") { return this.request(`/problems/${params}`); }
  getProblem(slug) { return this.request(`/problems/${slug}`); }

  // --- Sessions ---
  startSession(data) { return this.request("/sessions/", { method: "POST", body: JSON.stringify(data) }); }
  getSessions() { return this.request("/sessions/"); }
  getSession(id) { return this.request(`/sessions/${id}`); }
  submitCode(sessionId, data) { return this.request(`/sessions/${sessionId}/submit`, { method: "POST", body: JSON.stringify(data) }); }
  completeSession(id) { return this.request(`/sessions/${id}/complete`, { method: "POST" }); }

  // --- Stats ---
  getDashboard() { return this.request("/stats/dashboard"); }
  getStreaks() { return this.request("/stats/streaks"); }
  getProgress() { return this.request("/stats/progress"); }

  // --- AI ---
  getFeedback(sessionId) { return this.request(`/ai/sessions/${sessionId}/feedback`, { method: "POST" }); }
  getHint(problemId, data) { return this.request(`/ai/problems/${problemId}/hint`, { method: "POST", body: JSON.stringify(data) }); }

  // --- Voice ---
  startVoice(sessionId) { return this.request(`/voice/start/${sessionId}`, { method: "POST" }); }
  endVoice(sessionId) { return this.request(`/voice/end/${sessionId}`, { method: "POST" }); }
}

export const api = new ApiClient();
```

---

## ❌ Error Responses

All errors follow this format:

```json
{ "detail": "Error message here" }
```

| Status | Meaning |
|--------|---------|
| 400 | Bad request / validation error |
| 401 | Not authenticated or invalid token |
| 403 | Account not verified |
| 404 | Resource not found |
| 409 | Conflict (duplicate email/username) |
| 429 | Rate limited / too many attempts |
| 500 | Server error |
