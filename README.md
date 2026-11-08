# Gazipur Zila Parishad — Integrated Digital Platform (Demo)

A working Django demo of the Gazipur Zila Parishad **Integrated Digital Automation, Management Information System and Dakbungalow E-Booking** platform, prepared for Adcelerete Technologies Limited.

The demo is designed for a single laptop, fully offline: SQLite database, server-rendered templates, vendored CSS/JS, no Node build, no API keys, no real SMS/email/payments.

- Scope source: `docs/Gazipur_SoW.pdf` (revised 28 October 2026)
- Requirement-by-requirement trace: [`docs/REQUIREMENTS_TRACE.md`](docs/REQUIREMENTS_TRACE.md)
- The trace marks every SoW feature **Done**, **Simulated**, **Partial** or **Out of scope**. Read it before presenting the demo so the claims match the build.

---

## 1. What works

- **Dakbungalow e-booking for four facilities** (Gazipur Sadar, Kaliakair, Sreepur, Kapasia) with rooms and halls, category tariffs, holiday rates, deposits, blackout dates, per-night/per-slot inventory locks, a full citizen journey, approval routing, simulated payment, PDF receipt/permit, QR verification, reception check-in/out, refunds and reports.
- **Database-driven workflow engine**: templates, ordered steps, roles, JSON conditions, allowed decisions, SLAs, authority matrix, My Tasks, reminders/escalation and performance reporting. Booking and leave submissions start instances; the designer includes file and project templates.
- **Role-based access control** for 17 roles and 57 permissions, enforced on the server. Management/Auditor is read-only; the System Administrator cannot approve booking tasks.
- **HR**: employee register, attendance, leave with supervisor → HR workflow, duty roster, training/expiry tracking and HR dashboard.
- **Documents**: register, metadata, uploads, search, movement timeline, overdue queue, confidentiality restriction and access log.
- **Projects**: register, budget/spend, progress, milestones, inspections and delay indicators.
- **Meetings**: schedule, agenda, attendees, minutes, action items with owners/deadlines and follow-up queue.
- **MIS**: executive and department dashboards, booking/revenue reports, workflow performance, report library with CSV/PDF export and a report-access log.
- **Governance**: audit log and export, users/roles matrix, editable settings, notification templates, demo outbox, backup/restore test, health page.
- **Delivery controls**: support tickets, 45-day plan, deliverables/UAT checklist and change requests.
- **English/Bengali switch**, Adcelerete branding, app-name setting and a demo-data ribbon on every page.

---

## 2. Requirements

- Python **3.11+** (tested with 3.11.8)
- Git Bash, PowerShell or any shell
- No Node.js, no internet connection, no database server

Python packages (in `requirements.txt`):

```text
Django==5.2.19
reportlab==5.1.0
qrcode[pil]==8.2
Pillow==12.3.0
```

---

## 3. Run it

From the project root:

```bash
python -m venv .venv
```

Windows (Git Bash):

```bash
source .venv/Scripts/activate
```

macOS / Linux:

```bash
source .venv/bin/activate
```

Then:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo --reset
python manage.py runserver
```

Open <http://127.0.0.1:8000/>.

`seed_demo --reset` flushes the database and rebuilds the complete sample dataset: 18 accounts, 4 facilities with 24 units and 72 tariff rows, 30 employees, 60 register files, 12 projects, 8 meetings, 40+ bookings across all statuses, payments/refunds, workflow instances/tasks, audit entries, notifications, support tickets, plan/checklist data and a verified backup record.

**Reset at any time** (recommended before a presentation):

```bash
python manage.py seed_demo --reset
```

Seed data is fictional. The command is safe to re-run; do not point it at a database you care about.

### Static files

All Bootstrap 5.3.3, Bootstrap Icons 1.11.3, Chart.js 4.4.7, Alpine 3.14.8, HTMX 2.0.4 and Noto Sans Bengali files are vendored under `static/vendor/`. With `DEBUG=True` the development server serves them directly; no `collectstatic` or Node build is needed.

---

## 4. Demo accounts

Every seeded account uses the password **`Demo@12345`**. The login page also has a one-click demo quick sign-in panel, and `/demo/switch/` switches between demo users.

| Username | Role | Start here |
|---|---|---|
| `citizen1` / `citizen2` | Citizen / Applicant | `/citizen/` |
| `bookingdesk` | Dealing Assistant / Booking Desk | `/app/tasks/` |
| `engineer` | Assistant Engineer / Technical Reviewer | `/app/tasks/` |
| `eo` | Executive Officer | `/app/tasks/` |
| `ceo` | CEO / Chairman | `/app/tasks/` |
| `reception` | Reception / Facility Operator | `/app/reception/` |
| `finance` | Finance / Accounts Officer | `/app/payments/` |
| `hradmin` | HR Admin | `/app/hr/` |
| `supervisor` | Supervisor | `/app/tasks/` |
| `employee1` | Employee | `/app/hr/leave/` |
| `depthead` | Department Head | `/app/mis/department/` |
| `registry` | Registry / Section Officer | `/app/documents/` |
| `projectofficer` | Project Admin / Officer | `/app/projects/` |
| `inspector` | Inspector | `/app/projects/inspections/` |
| `secretary` | Meeting Secretary / Coordinator | `/app/meetings/` |
| `management` | Management / Auditor (read-only) | `/app/mis/` |
| `admin` | System Administrator | `/app/users/` |

Citizens land on `/citizen/`; staff land on `/app/`. Permissions are enforced by the server, not merely hidden in the menu.

---

## 5. Ten-minute demo script

### 0:00 — Public catalogue and trust surface (1 min)

1. Open `/` — four Dakbungalows, facilities, tariffs and availability. Note the demo ribbon and the “complements D-Nothi/e-Nothi, e-GP” footer.
2. Open a facility, then `/track/` and `/verify/<any-permit-token>/` from a seeded permit. Explain that QR verification is public and read-only.

### 1:00 — Citizen applies (2 min)

1. Sign in as `citizen1` (quick sign-in).
2. Choose a facility → **Apply** → select a room or hall, dates at least two weeks out, purpose and category.
3. Show the tariff preview, terms, reference number and status timeline.
4. Open `/citizen/` and point out the application in **Submitted**.

### 3:00 — Desk review and approval route (2 min)

1. Switch to `bookingdesk` → `/app/tasks/`.
2. Open the new task; show the payload, applicant details and route.
3. Choose **Reviewed and forwarded**. If the unit is a suite or hall, a technical step appears; otherwise it goes to the Executive Officer.
4. Switch to `eo` → open the task. Demonstrate that an amount above the ৳20,000 matrix limit is refused with the authority message; use **Recommend** and send it to the CEO, or approve a smaller booking directly.
5. Switch to `ceo` if the CEO step was required and approve.
6. The booking becomes **Awaiting Payment**; the citizen is notified in-app (demo outbox for email/SMS).

### 5:00 — Payment and permit (2 min)

1. Switch back to `citizen1`, open the booking and choose **Pay**.
2. On the simulated gateway page, pay successfully.
3. Point out the callback log: valid HMAC signature, then use **Send duplicate callback** and **Send forged callback** to show they are stored and rejected, not applied twice.
4. Open the receipt PDF, permit PDF and QR. The permit is issued only after approval + verified payment.
5. `/verify/<token>/` shows the public permit check.

### 7:00 — Operations and finance (1 min)

1. `reception`: open `/app/reception/`, verify the reference/QR and check the guest in, then out.
2. `finance`: `/app/payments/` for reconciliation and `/app/refunds/` for a seeded refund request; process it with the configured percentage.

### 8:00 — Workflow, HR, documents, projects, meetings (1 min)

- `admin`: `/app/workflow/` shows steps and JSON conditions; `/app/workflow/matrix/` shows delegated limits; change a limit and explain that routes are data, not code.
- `hradmin`: attendance and leave. `registry`: file movement and overdue queue. `projectofficer`: progress, milestones, inspections. `secretary`: minutes and action follow-up.

### 9:00 — MIS, governance and read-only enforcement (1 min)

- `ceo`: `/app/mis/` executive dashboard and `/app/mis/bookings/`.
- `management`: try to submit a change — the read-only middleware blocks every non-GET request. `/app/audit/` shows the trail.
- `admin`: `/app/security/` creates a backup and runs a restore/integrity test; `/app/health/` shows system status.
- Switch language to বাংলা with the header switch, then back to English.

---

## 6. Tests

```bash
python manage.py test
```

Expected: **36 tests, OK**.

Coverage includes:

- server-enforced role access, read-only middleware, admin-can-open-but-not-approve, reception facility scoping, report export permissions;
- workflow route resolution from DB conditions, authority limits, decisions and records;
- double-booking prevention per night/slot, hold release and expiry, payment-window expiry;
- HMAC callback verification, duplicate replay, forged signature, amount/reference mismatch, retry after failure, gateway owner-only access.

The full evidence table and known gaps are in [`docs/REQUIREMENTS_TRACE.md`](docs/REQUIREMENTS_TRACE.md).

---

## 7. What is simulated or partial

The demo is honest about its boundaries:

- **Payments:** simulated gateway. No real money, no SSLCommerz/bKash credentials. The HMAC signing, server-side verification and duplicate handling are real.
- **Email, SMS, OTP:** written to the demo outbox and shown locally. No external provider; SMS credits are labelled client-paid.
- **Backup:** a timestamped SQLite online backup plus an integrity/restore test under `backups/`. No scheduler or off-site copy.
- **Hosting/security:** local HTTP/SQLite. TLS, WAF, VPN, encrypted storage, external monitoring and off-site backup are production deployment actions and are not provisioned here.
- **Partial SoW items:** document versioning and inward/outward classification; project issues/bill reference/photos/work-order; meeting attachments/calendar/reminders/archive; HR employee editing/archiving and organogram; file/project workflows are configurable but not launched from their screens. The trace lists each gap.
- **Out of scope:** payroll, biometrics, native mobile app, GIS, digital signatures, more than four facilities, procurement/asset/complaints modules and bulk historical migration.

---

## 8. Project layout

```text
accounts/       custom user, roles, permissions, OTP, demo switcher, read-only middleware
workflow/       templates, steps, conditions, tasks, authority matrix, engine, reminders
audit/          audit entries and CSV export
notifications/  in-app notifications, editable templates, simulated email/SMS outbox
facilities/     facilities, units, tariffs, blackout dates, inventory locks, availability
bookings/       citizen applications, staff review, reception, status history, PDF permits
payments/       simulated gateway, HMAC callbacks, reconciliation, refunds
hr/             employees, attendance, leave, roster, training
documents/      register, files, movement, overdue, access log
projects/       projects, milestones, inspections
meetings/       meetings, attendees, minutes, actions
mis/            executive/department dashboards, reports, exports, report access log
support/        tickets, 45-day plan, deliverables/UAT checklist, change requests
core/           home, tracking, permit verification, settings, security, health, PDF/QR helpers
templates/      server-rendered templates with shared base layout and branding
static/         vendored Bootstrap/Bootstrap Icons/Chart.js/Alpine/HTMX/fonts + local CSS
docs/           SoW PDF and requirements trace
tests/          Django test suite and factories
```

Key configuration lives in `gzp/settings.py`; demo toggles and sample values are in `core/defaults.py` and can be edited at `/app/settings/`. The app name is a single setting (`app_name`).

---

## 9. Backup and restore

- Create a backup: sign in as `admin` → `/app/security/` → **Create backup now**.
- The backup is written to `backups/gzp-backup-<timestamp>.sqlite3` and recorded in the database.
- **Run restore test** opens the copy with SQLite and runs an integrity check; the result is stored and shown in the backup table.
- Manual restore for a demo laptop: stop the server, copy the chosen backup over `db.sqlite3`, and restart. This replaces all data; take a copy of the current database first.
- Uploaded files live under `media/`; the SQLite backup does not contain them. For a full clone, copy `db.sqlite3` and `media/`.

---

## 10. Troubleshooting

| Symptom | Fix |
|---|---|
| Port 8000 already in use | `python manage.py runserver 8001` or stop the other process. |
| Login says the account has no role | Run `python manage.py seed_demo --reset`. |
| Styles or charts missing | Confirm `DEBUG=True` and that `static/vendor/` is present. |
| Old behaviour after code changes | The demo may have been started with `--noreload`; restart the server. |
| Want a clean dataset | `python manage.py seed_demo --reset` (this destroys current data). |
| Bengali labels missing | Use the language switch; translations are bundled in `core/i18n.py`. |

---

## 11. Attribution

Prepared for **Gazipur Zila Parishad** by **Adcelerete Technologies Limited**. Demo version with fictional sample data. The platform complements, and does not replace or bypass, D-Nothi/e-Nothi, e-GP or statutory approval authority.
