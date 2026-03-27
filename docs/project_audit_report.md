# 🔍 SwasthyaAI Regulator — Comprehensive Deep Audit Report

**Date:** 2026-03-27 | **Scope:** Every file in the project

---

## 📁 Project Structure (Full Map)

```
SwasthyaAI Regulator/
├── .env                          ← Config (PostgreSQL URL but app ignores it)
├── .env.example                  ← ✅ Clean
├── .gitignore                    ← ✅ Clean
├── Dockerfile                    ← ✅ Present
├── docker-compose.yml            ← ✅ Present
├── app.log                       ← Log file in root (not gitignored)
├── CHECKPOINT.md / QUICKSTART.md / DEPLOYMENT_GUIDE.md / FINAL_REPORT.md / README.md
├── debug_extraction.py           ← ⚠️ Dev script in root
├── test_*.py (×6)                ← ⚠️ Test scripts in root
│
├── backend/
│   ├── enhanced_app.py           ← ✅ Main app (1606 lines) — RUNS
│   ├── __init__.py               ← 🔴 BROKEN import
│   ├── models.py                 ← 🟡 Orphaned (enhanced_app defines its own models)
│   ├── config.py                 ← 🟡 Orphaned (not imported by enhanced_app)
│   ├── celery_tasks.py           ← 🔴 4 broken imports + never connected
│   ├── synthetic_data_generator.py ← 🟡 Dev utility, dead in prod
│   ├── debug_extraction.py       ← 🟡 Dev script
│   └── modules/
│       ├── pdf_extractor.py      ← ✅ Clean, well-implemented
│       ├── duplicate_detector.py ← ✅ Clean, well-implemented
│       ├── field_validator.py    ← ✅ Clean, well-implemented (Form44 + MD14)
│       ├── consistency_checker.py ← ✅ Clean, well-implemented
│       ├── adr_validator.py      ← ✅ Clean, well-implemented
│       └── naranjo_scorer.py     ← ✅ Clean, well-implemented
│
└── frontend/
    ├── package.json              ← 🔴 react-icons missing
    ├── vite.config.js            ← ✅ Clean
    └── src/
        ├── App.jsx               ← ✅ Routes correct
        ├── main.jsx              ← ✅ Clean
        ├── App.css               ← ✅ Clean
        ├── pages/
        │   ├── Login.jsx         ← ✅ Active, uses lucide-react
        │   ├── Dashboard.jsx     ← ✅ Active, uses lucide-react
        │   ├── Upload.jsx        ← ✅ Active, uses lucide-react
        │   ├── ProcessingStatus.jsx ← ⚠️ Minor: missing dep in useEffect
        │   ├── Results.jsx       ← 🔴 Navigates to /dashboard (doesn't exist)
        │   ├── Compliance.jsx    ← ⚠️ Hardcoded fake scores
        │   ├── Settings.jsx      ← ⚠️ No backend persistence — UI-only
        │   └── NotFound.jsx      ← ✅ Clean
        ├── components/
        │   ├── Header.jsx        ← ✅ Active, lucide-react
        │   ├── Sidebar.jsx       ← ✅ Active, lucide-react
        │   ├── Login.jsx         ← 🔴 ORPHANED: wrong route + react-icons
        │   ├── Upload.jsx        ← 🔴 ORPHANED: wrong route + react-icons
        │   └── Processing.jsx    ← 🔴 ORPHANED: react-icons, never used
        ├── services/
        │   └── api.js            ← 🔴 logout() uses wrong localStorage key
        ├── stores/
        │   └── index.js          ← ✅ Clean (Zustand auth + submission store)
        └── utils/                ← 🟡 EMPTY folder
```

---

## 🔴 CRITICAL BUGS (Must Fix — Will Break the App)

### 1. `react-icons` not in [package.json](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/package.json) → Build Fails

Three component files import from `react-icons/fi` which is **not installed**:

| File | Imports |
|------|---------|
| [components/Login.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/components/Login.jsx) | `FiMail, FiLock, FiLoader` |
| [components/Upload.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/components/Upload.jsx) | `FiUpload, FiFile, FiX, FiLoader` |
| [components/Processing.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/components/Processing.jsx) | `FiRefreshCw, FiLoader, FiCheckCircle, FiAlertCircle` |

> [!CAUTION]
> These 3 files are **never imported or used** by [App.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/App.jsx) or any other active file. The cleanest fix is to **delete all 3 files** — this resolves the build error without installing any new package.

---

### 2. [backend/__init__.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/__init__.py) — Broken Import

```python
# backend/__init__.py
from backend.app import create_app   # ❌ No file named app.py exists
from backend.models import db        # ❌ models.py models not used by enhanced_app.py
```

[enhanced_app.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/enhanced_app.py) is a self-contained Flask app. This [__init__.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/__init__.py) will crash on import and is not needed.

**Fix:** Delete [backend/__init__.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/__init__.py).

---

### 3. [Results.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/pages/Results.jsx) — Wrong Route Navigation

```js
// Results.jsx line ~68
navigate('/dashboard');   // ❌ /dashboard does not exist in App.jsx
```

The dashboard route in [App.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/App.jsx) is `/` (root).

**Fix:** `navigate('/')` → affects the "Back to Dashboard" button in Results page.

---

### 4. [api.js](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/services/api.js) — `authAPI.logout()` Uses Wrong localStorage Key

```js
// services/api.js line 43
logout: () => {
  localStorage.removeItem('auth_token');  // ❌ Key is 'access_token' everywhere else
},
```

The token is stored under `'access_token'` in [stores/index.js](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/stores/index.js) and [App.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/App.jsx). This logout call silently fails to clear the token.

**Fix:**
```js
logout: () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
},
```

---

### 5. [celery_tasks.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/celery_tasks.py) — 4 Non-Existent Module Imports

```python
# celery_tasks.py lines 14-17
from backend.modules.ocr_engine import OCREngine           # ❌ File does not exist
from backend.modules.anonymizer import DPDPAnonymizer      # ❌ File does not exist
from backend.modules.summarizer import SummarizationEngine # ❌ File does not exist
from backend.modules.compliance_validator import ComplianceValidator  # ❌ File does not exist
```

These 4 modules are referenced in [celery_tasks.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/celery_tasks.py) but **were never created**. Additionally, Celery is **never initialized** in [enhanced_app.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/enhanced_app.py) — the app skips async processing entirely and runs the validation pipeline synchronously in the HTTP request handler.

**Status:** [celery_tasks.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/celery_tasks.py) is completely **dead code** and will crash on import.

**Fix:** Delete [backend/celery_tasks.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/celery_tasks.py).

---

## 🔴 SECURITY ISSUES

### 6. No Password Validation — Anyone Can Login

```python
# enhanced_app.py: /api/auth/token, /api/auth/login, /api/cdsco/auth/login
access_token = create_access_token(identity=username)
# ❌ No password check. ANY username gets a valid token.
```

All 3 login endpoints accept any username/password and return a valid JWT. There is no user database, no credential check.

**Three duplicate login endpoints with same behavior:**
- `POST /api/auth/token` — used by frontend
- `POST /api/auth/login` — alternative
- `POST /api/cdsco/auth/login` — legacy

**Fix (minimum):** Add at least a hardcoded credential check or a simple user table. In production this MUST use hashed passwords.

---

### 7. [get_submissions](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/enhanced_app.py#762-842) Endpoint — Unauthenticated Access Allowed

```python
# enhanced_app.py line 771-784
try:
    user = get_jwt_identity()
except:
    user = 'anonymous'

if user == 'anonymous':
    submissions_query = Submission.query  # ❌ Returns ALL submissions to anyone
```

Unauthenticated users can fetch **all submissions from all users** via `GET /api/submissions`.

---

### 8. Weak Secret Keys in [.env](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/.env)

```env
SECRET_KEY=swasthyaai-dev-secret-key-2024-change-in-production
JWT_SECRET_KEY=swasthyaai-jwt-secret-key-2024-change-in-production
```

These are committed to [.env](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/.env) (not [.env.example](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/.env.example)). If this is pushed to a public repo, the JWT can be forged.

---

## 🟠 LOGIC/UX BUGS

### 9. [components/Login.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/components/Login.jsx) — Wrong Navigation After Login

```js
// components/Login.jsx line ~15
navigate('/dashboard');  // ❌ Route doesn't exist
```

This is an orphaned file, but documents the same bug that was replicated in Results.jsx.

---

### 10. [components/Upload.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/components/Upload.jsx) — Wrong Redirect After Upload

```js
// components/Upload.jsx line ~92
window.location.href = `/results/${submission_id}`;  // ❌ Route is /submission/:id/results
```

Again this is orphaned, but the pattern should not propagate.

---

### 11. [Compliance.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/pages/Compliance.jsx) — Scores Are Completely Hardcoded

```js
// Compliance.jsx lines 103-112
const getComplianceScore = (framework) => {
  const scores = { DPDP: 94, NDHM: 89, ICMR: 92, CDSCO: 87 };  // ❌ Hardcoded
  return scores[framework] || 85;
};
```

The compliance page **always shows a passing score** (87-94%) and "✓ Compliant" for every document, regardless of the actual validation results from the backend. The [results](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/enhanced_app.py#1396-1479) API response from `GET /api/submissions/:id/results` is fetched but never used for the compliance scores.

---

### 12. [ProcessingStatus.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/pages/ProcessingStatus.jsx) — Stale Closure Risk in `useEffect`

```js
useEffect(() => {
  fetchStatus();
  const interval = autoRefresh ? setInterval(fetchStatus, 2000) : null;
  ...
}, [id, autoRefresh]);  // ⚠️ fetchStatus is used but not in deps array
```

[fetchStatus](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/pages/Results.jsx#45-60) is defined inside the component and is not memoized. The effect captures a stale version. This can cause bugs with React Strict Mode.

**Fix:** Either add [fetchStatus](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/pages/Results.jsx#45-60) to deps or wrap it with `useCallback`.

---

### 13. [.env](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/.env) — DATABASE_URL Points to PostgreSQL, App Uses SQLite

```env
# .env
DATABASE_URL=postgresql://postgres:password@localhost:5432/swasthyaai
```

```python
# enhanced_app.py line 41
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///swasthyaai_dev.db'  # Ignores DATABASE_URL
```

The app **hardcodes SQLite** and never reads `DATABASE_URL` from [.env](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/.env). The [.env](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/.env) PostgreSQL config is entirely unused. This is fine for dev but the configuration mismatch will confuse anyone trying to deploy.

---

### 14. [Settings.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/pages/Settings.jsx) — All Settings Are UI-Only (Not Persisted)

```js
const handleSaveProfile = () => {
  toast.success('Profile settings saved');  // ⚠️ Nothing actually saved
  setProfileEditing(false);
};
```

All 4 settings tabs (Profile, Security, Notifications, Data) display "saved" toasts but make no API calls. Settings reset on page refresh.

---

### 15. [pdf_extractor.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/modules/pdf_extractor.py) Exists But Is **Never Used** by [enhanced_app.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/enhanced_app.py)

[enhanced_app.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/enhanced_app.py) has its own inline extraction code:
- PyMuPDF (fitz) → PyPDF2 → plain text fallback

The [modules/pdf_extractor.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/modules/pdf_extractor.py) file (571 lines, with OCR fallback via pytesseract) is a far more robust implementation but is **never imported or called**.

This means:
- OCR fallback for scanned PDFs is not available
- The sophisticated [ExtractionResult](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/modules/pdf_extractor.py#20-49) class is dead code
- `pytesseract` and [pdfplumber](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/modules/pdf_extractor.py#240-284) are installed but unused

---

### 16. [naranjo_scorer.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/modules/naranjo_scorer.py) Exists But Is Never Used by [enhanced_app.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/enhanced_app.py)

[enhanced_app.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/enhanced_app.py) has its own hardcoded [generate_naranjo_evidence_quotes()](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/enhanced_app.py#185-221) function (lines 185-220) which returns **static/fake evidence quotes** regardless of the actual document content.

The real [NaranjoScorer](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/modules/naranjo_scorer.py#40-349) in [modules/naranjo_scorer.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/modules/naranjo_scorer.py) (349 lines, with proper keyword-based text analysis) is never imported or called.

---

### 17. [models.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/models.py) vs [enhanced_app.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/enhanced_app.py) Model Mismatch

[backend/models.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/models.py) defines a complex ORM:
- [Submission](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/models.py#8-46) with 25+ columns (extracted_text, anonymized_text, pii_found, compliance_score, etc.)
- `AnonymizationResult`, `SummarizationResult`, [ComplianceResult](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/models.py#95-123), [AuditLog](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/models.py#125-143) (separate tables)

[enhanced_app.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/enhanced_app.py) defines its own **completely different** minimal ORM:
- [Submission](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/models.py#8-46) with only 6 columns (id, filename, submission_type, status, created_at, submitted_by)
- [ValidationResult](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/enhanced_app.py#95-103), [AuditLog](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/models.py#125-143) (different schema)

These two model files are **completely incompatible** and [models.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/models.py) is never imported.

---

## 🟡 DEAD CODE / UNUSED FILES

### Backend

| File | Why It's Dead |
|------|--------------|
| [backend/__init__.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/__init__.py) | Broken import, not needed |
| [backend/models.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/models.py) | Never imported by [enhanced_app.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/enhanced_app.py), different schema |
| [backend/config.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/config.py) | Never imported by [enhanced_app.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/enhanced_app.py) |
| [backend/celery_tasks.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/celery_tasks.py) | 4 broken imports, Celery never initialized |
| [backend/synthetic_data_generator.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/synthetic_data_generator.py) | Dev utility, not part of runtime |
| [backend/debug_extraction.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/debug_extraction.py) | Debug script |
| [backend/modules/pdf_extractor.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/modules/pdf_extractor.py) | Never called by enhanced_app (has its own inline extraction) |
| [backend/modules/naranjo_scorer.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/modules/naranjo_scorer.py) | Never called by enhanced_app (has its own inline scoring) |

### Frontend Components (Never Rendered)

| File | Why It's Dead |
|------|--------------|
| [src/components/Login.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/components/Login.jsx) | [App.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/App.jsx) routes to [pages/Login.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/pages/Login.jsx) only |
| [src/components/Upload.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/components/Upload.jsx) | [App.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/App.jsx) routes to [pages/Upload.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/pages/Upload.jsx) only |
| [src/components/Processing.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/components/Processing.jsx) | [App.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/App.jsx) routes to [pages/ProcessingStatus.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/pages/ProcessingStatus.jsx) only |
| `src/utils/` | Empty folder |

### Root Level

| File | Note |
|------|------|
| [test_complete_pipeline_working.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/test_complete_pipeline_working.py) | Test script in root |
| [test_progressive_flow.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/test_progressive_flow.py) | Test script in root |
| [test_results_working.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/test_results_working.py) | Test script in root |
| [test_success_flow.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/test_success_flow.py) | Test script in root |
| [test_user_journey.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/test_user_journey.py) | Test script in root |
| [test_with_valid_form44.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/test_with_valid_form44.py) | Test script in root |
| [debug_extraction.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/debug_extraction.py) | Duplicate of [backend/debug_extraction.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/debug_extraction.py) |
| [app.log](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/app.log) | Log file committed to repo (not in .gitignore) |

---

## ✅ What Works Correctly

| Module | Status |
|--------|--------|
| [enhanced_app.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/enhanced_app.py) Flask server | ✅ Starts and runs |
| [modules/duplicate_detector.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/modules/duplicate_detector.py) | ✅ Imported and used |
| [modules/field_validator.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/modules/field_validator.py) | ✅ Imported and used (Form44 + MD14) |
| [modules/consistency_checker.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/modules/consistency_checker.py) | ✅ Imported and used |
| [modules/adr_validator.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/modules/adr_validator.py) | ✅ Imported and used |
| JWT auth flow (frontend → backend) | ✅ Works (no password check though) |
| File upload pipeline | ✅ Works |
| Form44 extraction | ✅ Works (inline PyMuPDF + PyPDF2) |
| Processing pipeline (5 stages) | ✅ Synchronous but works |
| [pages/Login.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/pages/Login.jsx) | ✅ Correct implementation |
| [pages/Dashboard.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/pages/Dashboard.jsx) | ✅ Correct implementation |
| [pages/Upload.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/pages/Upload.jsx) | ✅ Correct implementation |
| [pages/ProcessingStatus.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/pages/ProcessingStatus.jsx) | ✅ Works with minor warning |
| [pages/Settings.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/pages/Settings.jsx) | ✅ UI works (no backend persistence) |
| [pages/NotFound.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/pages/NotFound.jsx) | ✅ Clean |
| [stores/index.js](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/stores/index.js) (Zustand) | ✅ Clean |
| [services/api.js](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/services/api.js) interceptors | ✅ Correct (except logout key) |

---

## 🗺️ Application Flow (How It Actually Works)

```
Browser → /login
  → pages/Login.jsx → POST /api/auth/token { username: "..." }
  → Backend returns JWT (no credential check!)
  → Token stored in localStorage['access_token'] + Zustand
  → Redirect to /

/ → pages/Dashboard.jsx
  → GET /api/submissions?page=1&per_page=10
  → Shows table of submissions

/upload → pages/Upload.jsx
  → POST /api/submissions/upload (multipart)
  → Backend saves file, creates Submission(status='uploaded')
  → Redirect to /submission/:id/status

/submission/:id/status → pages/ProcessingStatus.jsx
  → Auto-triggers: POST /api/submissions/:id/extract-form44
    → Backend: PyMuPDF → PyPDF2 → plaintext fallback
    → Extracts fields with Form44Parser (regex-based)
  → Auto-triggers: POST /api/submissions/:id/process { submission_data: {...} }
    → Backend: 5-stage synchronous pipeline:
       Stage 1: duplicate check (if candidate data provided)
       Stage 2: consistency check
       Stage 3: ADR or Form44 validation
       Stage 4: MD-14 validation (if records provided)
       Stage 5: Naranjo scoring (if drug/event data provided)
    → Updates submission.status → 'completed' or 'failed'
  → Polls GET /api/submissions/:id/status every 2s
  → On 'completed' → user clicks "View Results"

/submission/:id/results → pages/Results.jsx
  → GET /api/submissions/:id/results
  → Shows validation results in 4 tabs
  → "View Compliance" → /submission/:id/compliance

/submission/:id/compliance → pages/Compliance.jsx
  → Fetches results but IGNORES them
  → Shows hardcoded scores (87-94%) always
  → Always shows "✓ Compliant"

/settings → pages/Settings.jsx
  → UI only, no API calls, no persistence
```

---

## 🔥 Priority Fix Table

| Priority | Issue | File | Fix |
|----------|-------|------|-----|
| 🔴 Critical | Build failure: react-icons missing | [components/Login.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/components/Login.jsx), [Upload.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/pages/Upload.jsx), [Processing.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/components/Processing.jsx) | **Delete all 3 files** |
| 🔴 Critical | Broken [__init__.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/__init__.py) import | [backend/__init__.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/__init__.py) | **Delete file** |
| 🔴 Critical | celery_tasks.py imports 4 missing modules | [backend/celery_tasks.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/celery_tasks.py) | **Delete file** |
| 🔴 High | logout() clears wrong localStorage key | [services/api.js](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/services/api.js) line 43 | Change `'auth_token'` → `'access_token'` |
| 🔴 High | `/dashboard` route doesn't exist | [pages/Results.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/pages/Results.jsx) | Change `navigate('/dashboard')` → `navigate('/')` |
| 🔴 Security | No password validation on any login endpoint | [enhanced_app.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/enhanced_app.py) | Add credential check |
| 🔴 Security | Unauthenticated users see all submissions | [enhanced_app.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/enhanced_app.py) line 780-781 | Remove anonymous fallback or add auth |
| 🟠 Medium | Compliance page shows hardcoded scores | [pages/Compliance.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/pages/Compliance.jsx) | Use actual `results?.compliance_results` from API |
| 🟠 Medium | [pdf_extractor.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/modules/pdf_extractor.py) + [naranjo_scorer.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/modules/naranjo_scorer.py) never used | [enhanced_app.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/enhanced_app.py) | Wire up or document as future modules |
| 🟠 Medium | Settings save buttons do nothing | [pages/Settings.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/pages/Settings.jsx) | Add API endpoints or mark as "coming soon" |
| 🟡 Low | `useEffect` missing fetchStatus in deps | [pages/ProcessingStatus.jsx](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/pages/ProcessingStatus.jsx) | Add `useCallback` or include [fetchStatus](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/frontend/src/pages/Results.jsx#45-60) in deps |
| 🟡 Low | DATABASE_URL in .env ignored | [.env](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/.env) + [enhanced_app.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/enhanced_app.py) | Read DATABASE_URL or remove from .env |
| 🟡 Low | Weak dev secrets committed in .env | [.env](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/.env) | Move to .env.example, generate real secrets |
| 🟡 Low | [app.log](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/app.log) committed to repo | root | Add to [.gitignore](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/.gitignore) |
| 🟢 Cleanup | Dead backend files | [models.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/models.py), [config.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/config.py), [synthetic_data_generator.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/backend/synthetic_data_generator.py), [debug_extraction.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/debug_extraction.py) | Delete or move to `/dev` folder |
| 🟢 Cleanup | Test scripts in root | 6× `test_*.py` + [debug_extraction.py](file:///c:/Users/email/OneDrive/Desktop/SwasthyaAI%20Regulator/debug_extraction.py) | Move to `/tests/` or delete |
| 🟢 Cleanup | Empty `utils/` folder | `frontend/src/utils/` | Delete |
| 🟢 Cleanup | 3 duplicate login endpoints | `enhanced_app.py` | Keep only `/api/auth/token`, remove others |
