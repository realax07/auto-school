# Registration & Admin Contour Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Working registration → SQLite → admin login → users list + CSV export, serving the approved static mockups.

**Architecture:** Single FastAPI service: static frontend + JSON API. SQLite file DB in `data/`. Admin auth via in-memory token issued from `.env` credentials (bcrypt hash).

**Tech Stack:** Python 3.11+, FastAPI, uvicorn, bcrypt, pytest; plain HTML/CSS/JS frontend (no build).

**Spec:** `docs/superpowers/specs/2026-10-08-registration-admin-design.md`

## Global Constraints

- Python ≥ 3.11; deps: fastapi, uvicorn, bcrypt, httpx (tests), pytest — nothing else
- DB file: `data/app.db`, SQLite WAL; `data/` in .gitignore
- Passwords: bcrypt cost 12; SQL parameterized only
- CSV: UTF-8 BOM, `;` separator, columns ФИО;Email;Телефон;Роль;Дата регистрации
- Admin creds from env: `ADMIN_USER`, `ADMIN_PASSWORD_HASH` (bcrypt hash, not plaintext)
- Copy of frontend pages = approved mockups verbatim (СберАвтошкола texts stay until customer says replace)

## Review Focus

- Duplicate email registration → must return 422 with `email: уже зарегистрирован`, not a 500 (test_register.py::test_duplicate_email)
- Mismatched password_confirm → 422, nothing written (test_register.py::test_password_mismatch)
- Export CSV without/with-bad token → 401, empty body (test_admin.py::test_export_requires_token)
- Admin login with wrong password → 401 and no token issued (test_admin.py::test_wrong_password)
- Users list ordering → newest first (created_at DESC) so admin sees fresh registrations on top (test_admin.py::test_users_ordered_newest_first)

---

### Task 1: Project scaffold + DB layer

**Files:**
- Create: `backend/db.py`, `backend/config.py`, `backend/__init__.py`, `requirements.txt`, `.env.example`, `.gitignore` (append `data/`, `.env`)
- Test: `tests/test_db.py`

**Interfaces:**
- Produces: `db.get_conn() -> sqlite3.Connection` (row_factory=Row, WAL), `db.init_db()` (creates users table per spec schema), `config.ADMIN_USER: str`, `config.ADMIN_PASSWORD_HASH: str`

- [ ] **Step 1: Write failing test**

```python
# tests/test_db.py
import db as db_mod

def test_init_db_creates_users_table(tmp_path, monkeypatch):
    monkeypatch.setattr(db_mod, "DB_PATH", tmp_path / "app.db")
    conn = db_mod.get_conn()
    db_mod.init_db(conn)
    names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "users" in names
    cols = {r[1] for r in conn.execute("PRAGMA table_info(users)")}
    assert {"id","surname","name","patronymic","email","phone","password_hash","created_at"} <= cols
```

- [ ] **Step 2: Run** `python3 -m pytest tests/test_db.py -v` → FAIL (no module db)

- [ ] **Step 3: Implement `backend/db.py` + `backend/config.py`** — `get_conn()` opens `data/app.db` (path from `DB_PATH`, default `data/app.db`), `PRAGMA journal_mode=WAL`, row_factory Row; `init_db(conn)` executes spec schema (CREATE TABLE IF NOT EXISTS). `config.py` reads env with `os.environ.get` at import: `ADMIN_USER` (default `admin`), `ADMIN_PASSWORD_HASH` (no default — KeyError with clear message if missing in prod paths that need it).

- [ ] **Step 4: Run** `python3 -m pytest tests/test_db.py -v` → PASS

- [ ] **Step 5: Commit** `git add -A && git commit -m "feat(db): sqlite layer + config"`

### Task 2: POST /api/register

**Files:**
- Create: `backend/register.py`, `backend/app.py`, `tests/conftest.py`
- Test: `tests/test_register.py`

**Interfaces:**
- Consumes: `db.get_conn/init_db`, bcrypt
- Produces: FastAPI app factory `app.create_app() -> FastAPI` (routers included); route `POST /api/register` per spec (200 `{ok:true}` / 422 `{ok:false,error}`); helper `register.validate(payload: dict, conn) -> str|None` returning first error message or None.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_register.py — use fixture client from conftest (tmp DB)
def test_register_ok(client):
    r = client.post("/api/register", json={...full valid payload...})
    assert r.status_code == 200 and r.json() == {"ok": True}

def test_register_persists(client):  # row count == 1, email matches
def test_duplicate_email(client):    # second POST → 422, "email"
def test_password_mismatch(client):  # password != password_confirm → 422
def test_short_password(client):     # len < 8 → 422
def test_bad_email(client):          # no '@' → 422
def test_missing_field(client):      # any required missing → 422
```

- [ ] **Step 2: Run** → FAIL

- [ ] **Step 3: Implement** `register.py` router + `app.py` (`create_app()` runs `init_db` on startup via lifespan; includes register router). Validation order: required fields → email format (`@`, `.` in domain) → phone ≥ 10 digits → password ≥ 8 → confirm match → duplicate email (SELECT by email). bcrypt hash cost 12. Error message format: `"<field-ru>: <причина>"`.

- [ ] **Step 4: Run** `python3 -m pytest tests/test_register.py -v` → PASS

- [ ] **Step 5: Commit** `git commit -m "feat(register): POST /api/register with validation"`

### Task 3: Admin auth + users list + CSV export

**Files:**
- Create: `backend/admin.py`
- Modify: `backend/app.py` (include admin router)
- Test: `tests/test_admin.py`, `tests/conftest.py` (add admin-token fixture: patch config env, bcrypt-hash a test password)

**Interfaces:**
- Consumes: `db`, `config.ADMIN_USER/ADMIN_PASSWORD_HASH`
- Produces: `POST /api/admin/login` → 200 `{ok:true, token}` / 401; dependency `admin.require_admin(request)` → 401 or None; `GET /api/admin/users` → `{count, users:[{id,fio,email,phone,created_at}]}` (fio = surname+name+patronymic joined with space, newest first); `GET /api/admin/users/export.csv` → text/csv with BOM, `;`, columns ФИО;Email;Телефон;Роль;Дата регистрации (role literal «Ученик», date as `DD.MM.YYYY` from created_at)

- [ ] **Step 1: Write failing tests**

```python
# tests/test_admin.py
def test_login_ok(client):           # correct creds → 200, token in json
def test_wrong_password(client):     # → 401, no token key
def test_users_requires_token(client)    # no header → 401
def test_users_bad_token(client)         # wrong header → 401
def test_users_list_and_order(client)    # register 2 users → count 2, newest first
def test_export_requires_token(client)   # → 401
def test_export_csv_format(client)       # BOM b'\xef\xbb\xbf', ';' sep, 5 header cols, 1 data row per user, «Ученик» present
```

- [ ] **Step 2: Run** → FAIL

- [ ] **Step 3: Implement** `admin.py`: `secrets.token_urlsafe(32)` on login, store in module-level dict {token: expires}; `require_admin` checks `X-Admin-Token` header + expiry → else raise 401. bcrypt.checkpw against ADMIN_PASSWORD_HASH. CSV via io.StringIO + csv.writer(delimiter=';'), prepend BOM, Response media_type text/csv with Content-Disposition attachment `users.csv`.

- [ ] **Step 4: Run** `python3 -m pytest tests/test_admin.py -v` → PASS

- [ ] **Step 5: Commit** `git commit -m "feat(admin): login, users list, csv export"`

### Task 4: Static frontend wiring

**Files:**
- Create: `frontend/index.html`, `frontend/registered.html`, `frontend/admin-login.html`, `frontend/admin-dashboard.html` (from design/mocks, with wiring changes below)
- Modify: `backend/app.py` (mount static)
- Test: `tests/test_static.py`

**Interfaces:**
- Consumes: API routes from Tasks 2–3
- Produces: `/` serves index.html; `/registered`, `/admin-login`, `/admin-dashboard` serve pages; `/api/health` → `{ok:true}`

Wiring changes vs mockups (only these):
1. index.html register modal: add Пароль + Подтверждение password fields (min 8 hint); submit → `fetch('/api/register', {method:'POST', body: JSON.stringify(...)})` → ok: `location.href='/registered'`; 422: show `error` text in a `.form-error` div under the form
2. index.html login modal submit: alert stub stays (cabinet is next sprint)
3. registered.html: keep as-is (links to `/`)
4. admin-login.html: real fetch `POST /api/admin/login` → ok: store token in `sessionStorage`, redirect `/admin-dashboard`; 401: show error div
5. admin-dashboard.html: on load read token, `GET /api/admin/users` with `X-Admin-Token`; render rows; count; CSV button → fetch export with token → download blob; 401 → redirect `/admin-login`

- [ ] **Step 1: Write failing tests** — test_static.py: `GET /` contains `СберАвтошкола`; `/registered` 200; `/admin-login` 200; `/admin-dashboard` 200; `/api/health` `{ok:true}`

- [ ] **Step 2: Run** → FAIL

- [ ] **Step 3: Copy mockups + apply wiring changes + mount StaticFiles(html=True) in app.py**

- [ ] **Step 4: Run** `python3 -m pytest tests/ -v` → ALL PASS

- [ ] **Step 5: Commit** `git commit -m "feat(frontend): wire mockups to API"`

### Task 5: Docs, PLAN/BACKLOG update, PR

**Files:**
- Modify: `PLAN.md` (Спринт 0 tasks → [x]), `BACKLOG.md` (1e → 📦 в спринте status note), `.env.example`

- [ ] **Step 1:** Update PLAN.md sprint-0 checklist with what shipped
- [ ] **Step 2:** Create `.env.example` with ADMIN_USER, ADMIN_PASSWORD_HASH + `python3 -c "import bcrypt;print(bcrypt.hashpw(b'...', bcrypt.gensalt()).decode())"` hint
- [ ] **Step 3:** Run full suite `python3 -m pytest tests/ -q` → all green; `python3 scripts/flow_check.py .` → OK
- [ ] **Step 4:** Commit + push branch + PR (marker [change-id] per pr_validate) — merge after green CI
