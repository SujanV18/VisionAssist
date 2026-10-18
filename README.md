# VisionAssist — Milestone 1

A working local college prototype: **customer enquiry → manager assignment or salesperson referral → salesperson review → verified catalogue → private quotation draft**.

**Out-of-pocket cost: ₹0.** React + TypeScript, FastAPI, SQLite, SQLAlchemy and Alembic. No API keys, paid services, cloud accounts, domain, hosting subscription, or credit card. Package downloads require internet for first-time installation; the built app works offline.

**Cloned from GitHub?** Follow **First-time setup on another computer** below. Local databases, installed dependencies, generated builds, and supplied PDF files are intentionally excluded from the repository. The reviewed catalogue records and source hashes are included; import your authorized copy of the archive to enable source PDF viewing.

## Run on this computer

The dependencies, database, demo accounts and frontend build have already been prepared in this folder.

1. Double-click `Start-VisionAssist.cmd` in this folder.
2. Open **http://127.0.0.1:8000** in your browser.
3. Expand **Local demo accounts** and choose an account.

If the preview from development is still running, just open the URL. If the launcher says port 8000 is occupied, use the already-running preview or stop its terminal before starting another. Keep the server window open; Ctrl+C stops it. Data persists in `data/visionassist.db` between restarts.

| Role | Email | Password |
| --- | --- | --- |
| Sales manager, Meera | manager@visionassist.demo | VisionDemo!2026 |
| Salesperson, Arjun | arjun@visionassist.demo | VisionDemo!2026 |
| Salesperson, Priya | priya@visionassist.demo | VisionDemo!2026 |

These are intentionally public **local demo credentials**. All four seeded enquiries are synthetic and clearly prefixed “Demo”. Browser walkthroughs may have assigned or drafted one of them.

## Try the complete workflow

1. Open `/enquire` and submit a fictional enquiry. Save the private tracking link displayed after submission.
2. Sign in as the manager. Open the new enquiry, choose Arjun, and provide an assignment reason.
3. Sign out, then sign in as Arjun. Open the enquiry and review its requirements.
4. Choose one of the verified camera models. Select a lens and quantity, add notes, and save a private draft.
5. Expand the saved version. Use **Use as next draft** to prepare a second version; the earlier version remains intact.
6. Reopen the customer tracking link. It displays progress, not the private draft or contact details.
7. Try `/enquire?ref=priya-demo`. The new enquiry goes straight to Priya; a later manager reassignment keeps Priya recorded as the original referrer.

## What is built

- Responsive customer, salesperson and manager views in one React app.
- Session-based staff login, logout, password hashing and role checks on the server.
- General and referral enquiries, manager assignment/reassignment/unassignment, and audit history.
- Salespeople see only their currently assigned leads. The manager sees the latest 200 enquiries.
- Private customer tracking with a random, hashed token and 30-day expiry. No customer login.
- Three catalogue models with reviewed specification fields, source page references and source PDF links.
- Immutable quotation draft versions with server-calculated integer-paise totals and snapshots of product facts, sources and prices.
- Four realistic, fictional demo enquiries, two salespeople and one manager.
- Database migrations, automated workflow/security tests, and a guarded archive inspection utility.

## The source catalogue

The uploaded `OneDrive_1_25-11-2025.zip` was recovered from the referenced chat attachment. It contains **66 PDFs**, not 66 automatically verified products. The archive was checked for unsafe paths, duplicate names, symlinks, encryption, excessive sizes/compression and CRC integrity before PDF extraction. These PDFs allow reading with an empty password; password-protected PDFs requiring a password are rejected.

All 66 PDFs have text extracted for review. **Only three models' selected fields have been reviewed and admitted to the catalogue**:

- PT-NC120D3-N(D2)
- PT-NC140D3-N(D2)
- PT-NC320P1-N(D2)

The checked fields are title, resolution, lens options, IR range, protection and WDR. Evidence is in `data/verified_catalogue.json`; every entry records a PDF hash and field-level page references. The remaining 63 PDFs are pending catalogue review. Datasheets state that specifications may change. Verification means consistency with the supplied documents, not current manufacturer certification or a stock guarantee.

**Every price is an invented, clearly labelled DEMO amount.** No actual PRAMA/Hikvision price, discount, tax, stock, integration, or permission to access internal systems is represented. Demo quotation totals cover equipment only; installation, tax, cabling, storage and delivery remain unassessed. No company endorsement or official integration is claimed.

Original synced project files under `../sources/` are untouched. PDF working copies live in `data/datasheets/`; they are ignored by Git. Do not publish the supplied source archive or PDFs without checking your sharing permission.

To re-import the archive on another computer:

```powershell
.\.venv\Scripts\python.exe scripts/inspect_archive.py "C:\path\to\OneDrive_1_25-11-2025.zip"
```

Re-import rebuilds the inspection manifest with pending review statuses; it does not auto-approve catalogue facts or alter the curated catalogue. Run the tests to verify the curated file hashes still match. Source PDF links need the imported local PDF files. The reviewed catalogue JSON remains usable when PDFs are absent.

## First-time setup on another computer

Use Python **3.11 or newer** and Node.js **22 or newer**. Python 3.8 is installed as the system default on this computer, so this workspace uses the bundled Python 3.12 runtime in its virtual environment. Always use `.venv\Scripts\python.exe` for this project.

From the `visionassist` folder in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.lock.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m backend.seed
cd frontend
npm.cmd ci
npm.cmd run build
cd ..
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Select your installed Python 3.11+ version if `py -3.12` is unavailable. On macOS/Linux use `python3 -m venv .venv`, `.venv/bin/python` and `npm` in the equivalent commands. The `.venv` folder itself is machine-specific: recreate it when moving the project. The dependency lock file records the versions tested here; `requirements.txt` records the intended version ranges.

`backend.seed` is an explicit, idempotent demo initializer. It does not reset existing records or overwrite passwords or catalogue prices. Do not run it against a future real database.

## Development and checks

For frontend hot reload, run the backend as above, then `npm.cmd run dev` inside `frontend` and open http://127.0.0.1:5173. Vite forwards `/api` to FastAPI, keeping browser requests on the same origin.

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q
.\.venv\Scripts\python.exe -m alembic check
cd frontend
npm.cmd run build
```

Tests create isolated databases and do not modify your demo database. In a restricted environment, a unique writable `--basetemp=tmp/test-run-04` may be necessary; the execution sandbox here also required an approved local runner for threaded tests and network sockets. Ordinary local PowerShell does not have that sandbox restriction.

The test run currently emits one dependency deprecation warning about Starlette's HTTPX test adapter. All tests pass; the warning does not affect the app. API reference: `/api/docs` (its Swagger UI assets require internet; the application itself does not).

## Learn the architecture

React draws the screens and submits requests. FastAPI validates each request and decides who may access each record. SQLAlchemy writes the records into SQLite. Alembic tracks database schema changes. The browser never decides a role, assignee permission, final product price or total.

See `docs/ARCHITECTURE.md` for the data flow, permission table and PostgreSQL migration plan, and `docs/ROADMAP.md` for the next small milestones.

## What comes next

This milestone stops at a **private draft**, not a customer-ready sales system. Quotation release/customer responses, request-and-confirm appointments, site visits, uploads, checklists and AI assistance are intentionally not implemented yet.

The guaranteed zero-service-cost demo path is the local app on your existing computer, including a projector demonstration. No public deployment has been made. Public hosting is a later decision only if its terms are genuinely ₹0 and require no card; do not assume any provider's free tier will remain free. Before public use, replace demo accounts, require HTTPS, configure trusted hosts and secure cookies, add shared abuse protection, account lifecycle tools, backups and a retention policy. PostgreSQL support is planned and the schema is portable, but a PostgreSQL migration has **not** been executed or tested yet.
