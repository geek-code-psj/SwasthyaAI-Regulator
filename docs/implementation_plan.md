# Fix: Frontend + API Wiring

Fix all UI/API wiring bugs. **DO NOT touch**: AI logic, extraction, validation modules.

---

## User Review Required

> [!IMPORTANT]
> **Password Check**: The login backend currently accepts any username with no password check. I will add a hardcoded demo credential (`admin` / `swasthya2024`) so the system is no longer completely open. You can change this later or confirm if you want to keep it open for demo purposes.

> [!NOTE]
> **Settings persistence**: Settings page has 4 tabs — I will only wire up the profile tab since the backend has no user profile storage yet. Security/2FA/data retention tabs will be marked "Coming Soon" visually but left as-is.

---

## Phase 1: Delete Dead Files

### [DELETE] [backend/__init__.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/__init__.py)
Broken import (`from backend.app import create_app`) — file not needed.

### [DELETE] [backend/celery_tasks.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/celery_tasks.py)
Imports 4 non-existent modules. Celery is never initialized. Dead code.

### [DELETE] [frontend/src/components/Login.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/components/Login.jsx)
Orphaned — never rendered. Uses `react-icons` (not installed) causing build failure.

### [DELETE] [frontend/src/components/Upload.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/components/Upload.jsx)
Orphaned — never rendered. Uses `react-icons` (not installed) causing build failure.

### [DELETE] [frontend/src/components/Processing.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/components/Processing.jsx)
Orphaned — never rendered. Uses `react-icons` causing build failure.

---

## Phase 2: Backend API Fixes

### [MODIFY] [enhanced_app.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/enhanced_app.py)

**Fix 1 — Add credential check to `/api/auth/token`:**
```python
DEMO_USERS = {
    'admin': 'swasthya2024',
    'demo_user': 'demo123',
}
# Check credentials before issuing token
if username not in DEMO_USERS or password != DEMO_USERS[username]:
    return jsonify({'error': 'Invalid credentials'}), 401
```

**Fix 2 — Remove 2 duplicate login endpoints:**
- Delete `POST /api/cdsco/auth/login` (line 361)
- Delete `POST /api/auth/login` (line 421)
- Keep only `POST /api/auth/token` (used by frontend)

**Fix 3 — Secure `GET /api/submissions` (add `@jwt_required()`):**
Remove the anonymous fallback. Add `@jwt_required()` decorator so unauthenticated requests get 401.

**Fix 4 — Add [app.log](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/app.log) to [.gitignore](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/.gitignore)**

---

## Phase 3: Frontend API Layer Fix

### [MODIFY] [api.js](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/services/api.js)

**Fix — `authAPI.logout()` uses wrong key:**
```js
// Line 43: Change 'auth_token' → 'access_token'
logout: () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
},
```

**Fix — `authAPI.getToken()` needs to send username+password:**
```js
getToken: (username, password) =>
  apiClient.post('/auth/token', { username, password }),
```

---

## Phase 4: Frontend Navigation Fixes

### [MODIFY] [Results.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/pages/Results.jsx)

**Fix — Line 68: `/dashboard` → `/`:**
```js
navigate('/');  // was: navigate('/dashboard')
```

### [MODIFY] [ProcessingStatus.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/pages/ProcessingStatus.jsx)

**Fix — stale closure in `useEffect`:**
Wrap [fetchStatus](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/pages/Results.jsx#45-60) with `useCallback` and add to deps array.

---

## Phase 5: Wire Compliance Page to Real API Data

### [MODIFY] [Compliance.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/pages/Compliance.jsx)

The page already fetches [results](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/enhanced_app.py#1396-1479) from the API. Replace [getComplianceScore()](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/pages/Compliance.jsx#103-113) to:
1. Derive a real score from `results.checks_passed / results.total_checks * 100`
2. Set overall status from `results.overall_status` (not always "PASS")
3. Show "Processing..." if results have no checks yet

---

## Phase 6: Fix Login Page to Send Password

### [MODIFY] [Login.jsx (pages)](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/pages/Login.jsx)

The login form currently collects both username and password but only sends username to the API. Fix `authAPI.getToken(username, password)` to include password.

---

## Verification Plan

### Manual Testing Steps

1. **Start backend:**
   ```
   cd "c:\Users\email\OneDrive\Desktop\SwasthyaAI Regulator"
   .venv\Scripts\python.exe backend/enhanced_app.py
   ```

2. **Start frontend:**
   ```
   cd frontend
   npm run dev
   ```

3. **Test: Build succeeds** — `npm run dev` should start without "Cannot find module 'react-icons'" errors.

4. **Test: Login with wrong password** — Go to `http://localhost:5173/login`. Enter `admin` / `wrongpass`. Should show an error toast.

5. **Test: Login with correct credentials** — Enter `admin` / `swasthya2024`. Should redirect to `/` (Dashboard).

6. **Test: Upload and process a PDF file** — Click "New Submission", upload any PDF. Should auto-navigate to `/submission/:id/status` and run processing stages.

7. **Test: View Results** — After processing completes, click "View Results". Results page should load. "Back to Dashboard" button should go to `/` (not 404).

8. **Test: Compliance page shows real data** — From Results page, click "View Compliance". Scores should reflect actual validation pass/fail rate, not always 94%/87%.

9. **Test: Logout** — Click logout from header. Should clear session, redirect to `/login`. Refreshing should NOT re-authenticate (token must be cleared).

10. **Test: Unauthenticated API access** — After logout, open browser devtools and run `fetch('http://localhost:5000/api/submissions')`. Should return `401 Unauthorized`, not a list of submissions.
