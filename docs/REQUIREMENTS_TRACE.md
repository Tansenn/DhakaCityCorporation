# Requirements Trace — Gazipur Zila Parishad Integrated Digital Platform

**Source document:** *Proposed Scope of Work — Integrated Digital Automation, Management Information System & Dakbungalow E-Booking with Payment Integration*, Adcelerete Technologies Limited, revised draft 28 October 2026 (11 pages).

**Build:** Django 5.2.19 demo, SQLite, server-rendered templates, no external services or API keys.

**Purpose of this file:** show where each SoW requirement is implemented, what is simulated in the demo, and what remains partial or intentionally excluded. It is an internal/demo trace, not a signed acceptance certificate.

---

## 1. Status legend

| Status | Meaning |
|---|---|
| **Done** | Implemented and exercised by the automated tests and/or the recorded golden-path run. |
| **Simulated** | The full local workflow works, but an external channel (payment gateway, SMS, email, OTP, backup destination) is replaced by a clearly labelled demo implementation. |
| **Partial** | The main flow works, but a named sub-item from the SoW is simplified or not present. The gap is stated in the row and in section 13. |
| **Out of scope** | Intentionally excluded by the demo constraints or by SoW sections 11 and 13; not claimed as delivered. |

Routes are relative to the site root. `app/` routes require a staff session; `/citizen/`, `/book/...`, `/facilities/<code>/`, `/track/` and `/verify/...` are the public/citizen surface.

---

## 2. SoW sections 1–14

### Section 1 — Background, purpose and objectives

| Requirement | Where it works | Status | Evidence / notes |
|---|---|---|---|
| Digitise registers, workflow steps, status tracking and management reporting | `/app/documents/`, `/app/tasks/`, `/app/mis/`, all module registers | Done | Document/file register, workflow designer and task inbox, booking register, MIS dashboards and exports. |
| Citizens discover, request and pay for approved Dakbungalow facilities | `/` (catalogue), `/facilities/<code>/`, `/book/<facility>/`, `/book/details/`, `/citizen/` | Done | Four facilities, availability, application, approval and payment. |
| Role-based dashboards, auditable approvals, secure payment confirmation, downloadable permits | `/app/`, `/app/tasks/`, `/app/audit/`, `/pay/<txn>/`, `/bookings/<id>/permit.pdf` | Done | Dashboard, task decisions, audit entries, HMAC-verified callback, PDF permit and QR. |
| Controlled, supportable solution with three years of maintenance | `/app/support/`, `/app/acceptance/`, `/app/change-requests/` | Partial | Demo includes ticket register, 45-day plan, deliverables/UAT checklist and change requests. A signed 36-month support contract and monthly support reporting are commercial deliverables outside the app. |
| Complement, not replace, D-Nothi/e-Nothi, e-GP or statutory authority | Banner/footer text on every page; no integration that bypasses statutory approval | Done | The platform never calls or impersonates a government service. |

### Section 2 — Included functional modules A–G

| Module | Implemented surface | Status | Notes |
|---|---|---|---|
| **A. Digital Document & File Management** | `/app/documents/`, `/app/documents/files/`, `/app/documents/overdue/`, `/app/documents/access/`, `/app/documents/<id>/` | **Partial** | Register, metadata, upload, search/filter, attachment download, movement timeline (register/forward/receive/return/close/note), due dates, overdue queue, confidentiality restriction, access log and audit are working. **Missing:** version history/revision list and a separate inward/outward register flag (the register records “received from” but does not classify direction). |
| **B. Workflow & Approval Management** | `/app/tasks/`, `/app/workflow/`, `/app/workflow/matrix/`, `/app/mis/workflow/` | Done | DB-driven templates/steps/conditions, authority matrix, task inbox, decisions, reminders/escalation, performance. See Annex A.3. |
| **C. HR & People Management — core** | `/app/hr/`, `/app/hr/employees/`, `/app/hr/attendance/`, `/app/hr/leave/`, `/app/hr/roster/`, `/app/hr/training/` | **Partial** | Register, search/filter, attendance, leave routed through the workflow engine, roster, training and expiry reminders, HR reports. No payroll or biometric integration, as required. **Missing:** edit/archive an existing employee from the UI, a department/designation master-data screen, and a drawn organogram. |
| **D. Project & Development Monitoring** | `/app/projects/`, `/app/projects/<id>/`, `/app/projects/inspections/` | **Partial** | Project register, budget/spent, progress %, status, milestones/due dates, inspection findings/rating/follow-up, overdue timeline. **Missing:** issue/follow-up register, work-order/vendor reference, bill/payment-status field, and photograph attachments. |
| **E. Meeting & Committee Management** | `/app/meetings/`, `/app/meetings/<id>/`, `/app/meetings/actions/` | **Partial** | Meeting schedule, agenda text, attendees/attendance, minutes, decisions as action items with owner/deadline/status, follow-up queue and searchable list. **Missing:** agenda/attachment upload, a graphical calendar view, automatic action reminders and an explicit archive action. |
| **F. MIS & Management Dashboards** | `/app/`, `/app/mis/`, `/app/mis/department/`, `/app/mis/bookings/`, `/app/mis/reports/`, `/app/mis/workflow/` | Done | Role-filtered dashboards, pending approvals, HR/project/meeting/booking indicators, Chart.js views, workflow performance, CSV/PDF report exports and report-access log. |
| **G. Dakbungalow E-Booking — four facilities** | Public catalogue and full booking/admin surface | Done (payment **Simulated**) | Four seeded facilities, rooms/halls, category tariffs, holiday rates, deposits, blackouts, holds, approvals, payment, permit, reception, refunds, reports. See Annex A.7. |

### Section 3 — Citizen workflow (eight steps)

| Step | Implementation | Status |
|---|---|---|
| 1. Browse facilities | `/` (catalogue) and `/facilities/<code>/`: descriptions, amenities, photos, location, booking types, tariffs, rules, availability and blackout dates. | Done |
| 2. Register / verify | `/register/`, `/verify-email/`, `/resend-otp/`: email/OTP verification, resend, attempt limit and expiry. OTP is displayed on the verification page and written to the demo outbox. SMS delivery is labelled client-paid. | Simulated |
| 3. Select and apply | `/book/<facility>/` → `/book/details/`: unit/slot, dates, purpose, applicant category, guests, contact, notes; tariff preview and terms. | Done |
| 4. Submit request | Booking saved with reference `GZP-DB-YYYY-NNNNNN`; confirmation page and detail page with next action. | Done |
| 5. Track progress | `/citizen/`, `/bookings/<id>/`, `/track/`: Submitted, Under Review, Clarification Required, Recommended, Approved, Rejected, Awaiting Payment, Paid/Confirmed, Cancelled, Completed and payment-window Expired. Status history shows actor/time/comment. | Done |
| 6. Pay securely | `/bookings/<id>/pay/` → `/pay/<txn>/` → `/pay/<txn>/callback/`: simulated gateway, HMAC-signed callback, server-side amount/reference verification, duplicate handling, retry after failure. | Simulated |
| 7. Receive permit | `/bookings/<id>/receipt.pdf`, `/bookings/<id>/permit.pdf`, `/bookings/<id>/qr.png`, `/verify/<token>/`: permit only after final approval and verified payment; QR verification is public and read-only. | Done |
| 8. Manage request | `/bookings/<id>/`: clarification responses, messages, document upload, cancellation request, refund status, receipt/permit download and history. | Done (refund execution is simulated) |

The exact availability rules, advance-booking limit, maximum stay/guests, holiday tariff, hold/payment windows, refund percentages and minimum notice are **settings**, seeded with sample values and editable at `/app/settings/`. Approval routes are **database rows**, not hard-coded.

### Section 4 — Internal workflow, ACL and approvals

| SoW role | Demo account | Implemented permissions / restrictions | Status |
|---|---|---|---|
| Citizen / Applicant | `citizen1`, `citizen2` | Own profile, applications, uploads, messages, payment, receipt/permit only. Citizen blocked from `/app/`. | Done |
| Reception / Facility Operator | `reception` | Assigned facility only; view bookings, verify reference/QR, check-in/out. Foreign facility returns 403. | Done |
| Dealing Assistant / Booking Desk | `bookingdesk` | Review, request correction, recommend, reject; no final approval. | Done |
| Assistant Engineer / Technical Reviewer | `engineer` | Reviews only when the step condition requires it (suite/hall); recommend/correct/reject. | Done |
| Executive Officer / Authorized Reviewer | `eo` | Approve within the `AuthorityMatrix` limit (seeded ৳20,000 for bookings); above limit must recommend upward. | Done |
| CEO / Chairman / Authorized Approver | `ceo` | Final approval where the route/amount requires it; unlimited booking authority in the seed matrix. | Done |
| Finance / Accounts Officer | `finance` | Approved demands, receipts, reconciliation, refunds, financial reports; settled transactions not editable. | Done |
| System Administrator | `admin` | Roles, users, master data, settings, workflow design, audit. Cannot decide a booking task: engine returns 403. | Done |
| Management / Auditor | `management` | Read-only dashboards, histories, audit and exports; middleware blocks every non-GET request. | Done |

Every decision stores the actor, role, timestamp, decision code and comments in `StepRecord`; material actions are also written to the audit log.

### Section 5 — Dashboards, reporting and notifications

| SoW dashboard/page | Route | Status |
|---|---|---|
| Overview: applications by status, facility bookings, upcoming occupancy, pending approvals, collection, overdue items, alerts | `/app/` | Done |
| Booking management: list, filters, applicant, documents, approval history, clarifications, status changes | `/app/bookings/`, `/app/bookings/<id>/` | Done |
| Facility and availability: four facilities, units, blackout dates, tariffs, calendar | `/app/facilities/`, `/app/facilities/<id>/` | Done |
| Payments and reconciliation: demand vs collection, paid/unpaid, gateway reference, failed/duplicate, refunds | `/app/payments/`, `/app/refunds/` | Done (simulated gateway data) |
| Automation modules: files, HR, projects, meetings, tasks | module routes + `/app/tasks/` | Done |
| Reports: daily/weekly/monthly booking, occupancy, revenue, pending, departmental and exportable summaries | `/app/mis/bookings/`, `/app/mis/reports/`, `/app/mis/reports/export/` | Done (CSV/PDF) |
| Audit and settings: roles, workflow matrix, master data, notification templates, audit/security logs | `/app/users/`, `/app/roles/`, `/app/settings/`, `/app/audit/`, `/app/outbox/templates/` | Done |
| Email verification/confirmation and transactional email templates | `/verify-email/`, `/app/outbox/templates/`, demo outbox | Simulated (no external email) |
| SMS integration subject to client-paid credits | Demo outbox + SMS notice in settings | Simulated |
| Gateway charges pass-through only when lawful/disclosed/approved | `gateway_charge_paid_by_user`, `gateway_charge_amount` settings; checkout shows charge | Done (configurable, default absorbed) |

### Section 6 — Security, hosting, backup and integration

| SoW control | Demo implementation | Status |
|---|---|---|
| HTTPS/TLS, encryption of sensitive data and protected backups | Session/auth controls and role isolation are implemented; the local demo runs over HTTP and SQLite is not encrypted at rest. Production TLS, disk encryption and protected storage are hosting actions. | Partial / demo limitation |
| Firewall and WAF / rate limiting | Login rate limit (6 failures per 15 minutes) is enforced. Network firewall/WAF is not present in a local demo. | Partial / demo limitation |
| VPN or secure remote administration, least privilege | Least-privilege RBAC, permission decorators and read-only middleware are implemented. VPN is a deployment control. | Partial / demo limitation |
| Authentication: password/session, email/OTP, role segregation, audit logs | Implemented. Passwords are hashed by Django; OTP has expiry/attempts; material actions audited. | Done (OTP simulated delivery) |
| Payment protection: gateway-hosted flow, signed callback, server verification, duplicate handling | Simulated gateway with HMAC-SHA256 signatures, amount/reference checks, duplicate and forged callback rejection. | Simulated |
| Backup and recovery: scheduled backups, protected storage, documented recovery, restore verification | `/app/security/` creates a timestamped SQLite online backup and runs an integrity/restore test; retention setting exists. No scheduler or off-site copy in the demo. | Simulated |
| Monitoring and updates: availability/error monitoring, patching, incident diagnosis | `/app/health/` shows database, storage, backup readiness and recent events; `/app/support/` records incidents. No external monitoring agent. | Partial |
| Hosting options, domain, third-party fees, on-premises server | Documented as client/supplier decisions; the demo is self-contained locally. | Commercial / deployment |
| External integrations (National ID, government platforms, SMS, email, gateways) only when feasible/authorised | Only the simulated gateway and simulated notification channels exist. No National ID, D-Nothi/e-GP or paid API integration is claimed. | Out of scope for demo |

### Section 7 — Feasibility and 45-working-day timeline

The demo includes the 45-day plan as data at `/app/acceptance/` (seven phases, owners, deliverables, status), matching the SoW windows: Days 1–7 feasibility/field assessment, 8–15 design/setup, 16–30 parallel development, 31–38 integration/test, 39–42 deploy/train, 43–45 final UAT/handover. Status: **Done as a planning/demo artefact**. The duration is not a contractual commitment in this demo.

### Section 8 — Team structure and client dependencies

The SoW team roles (PM/BA, solution architect/security, backend/database, frontend, QA/UAT, DevOps/support) and client dependencies (project owner, focal points, authority matrix, facility inventory, tariffs, hosting/domain, gateway onboarding, UAT representatives) are reflected in the README demo script and the acceptance/support pages. No separate staffing module is needed. Status: **Documented, not a software feature**.

### Section 9 — Deliverables and acceptance

| Deliverable | Demo location | Status |
|---|---|---|
| Inception/feasibility report, SRS, workflow/ACL matrix, data model, plan | `/app/acceptance/`, `/app/workflow/`, `/app/workflow/matrix/`, `/app/roles/` | Partial (tracker and matrices; formal SRS/PDF pack is a project document) |
| Operational modules plus four-facility booking | All module routes | Done |
| Citizen portal, admin dashboards, payment and notification integrations | Public + staff routes | Done (integrations simulated) |
| Security/backup configuration, QA/UAT scripts, issue log, blocking-defect resolution | `/app/security/`, `/app/acceptance/checklists/`, `/app/support/` | Partial (tracking exists; signed QA pack is a project document) |
| Training, operating manuals, as-built configuration, access handover | `/app/acceptance/`, README | Partial (demo guide and checklists; formal manuals not produced) |
| Signed acceptance and 36-month support plan | `/app/acceptance/` | Partial (checklist/sign-off tracker, not an electronic signature) |

Acceptance against reproducible requirements, consolidated defect lists and third-party outage exclusions are contractual text; the app supports the evidence but does not replace the signed agreement.

### Section 10 / 10.1 — Three-year support, response and escalation

| Requirement | Implementation | Status |
|---|---|---|
| 36 months of support after operational acceptance | Stated in support pages and README; ticket register and change control support the process. | Commercial (tracked, not enforced by code) |
| Bug fixing, incident troubleshooting | `/app/support/` tickets with category, priority, assignee, status, resolution. | Done |
| Minor updates, security maintenance, backup/restore support, payment/API troubleshooting, performance checks, UAT/releases, training, monthly reporting | Represented by support categories and the acceptance/checklist pages; no automated monthly PDF report. | Partial |
| Acknowledgement targets: Critical 2 business hours, High 4 business hours, Medium 1 business day, Low 2 business days | Ticket `response_due_at` is set from priority. | Done (targets, not an SLA clock) |
| Coverage hours, on-site visits, final SLAs | Not configured; stated as a signed support schedule item. | Commercial |

### Section 11 — Chargeable work and client-paid expenses

`/app/change-requests/` records proposed changes with impact, requester, decision note and status. The SoW exclusions (major workflow redesign, new modules, additional facilities, new integrations, domain/hosting, SMS credits, gateway fees, hardware, bulk migration, legal/policy reengineering, out-of-scope on-site support) are listed in the app and README. No chargeable item is started automatically; a change request is required. Status: **Done as a control/tracker**.

### Section 12 — Ownership, confidentiality and contractual conditions

| Requirement | Implementation | Status |
|---|---|---|
| Parishad owns official data, documents, booking records and reports | Data remains in the local SQLite database and uploaded files; export routes are permission-controlled. | Done (demo) |
| Supplier retains pre-existing software/frameworks; client receives operational licence | Stated in README/support text; no licence enforcement in code. | Commercial |
| New source-code ownership, escrow, portability, exit assistance only if specified | Not implemented; contractual. | Out of scope |
| Written authorisation for changes; no additional features without change control | Change-request register; no automatic scope expansion. | Done |
| No bypass of D-Nothi/e-Nothi, e-GP, statutory approvals | No such integration or bypass exists. | Done |
| Hosting/data location, confidentiality, retention, backup responsibility, incident escalation, procurement/legal terms | Settings and security page document the demo behaviour; formal clauses are contractual. | Partial |

### Section 13 — Optional future modules (not included)

Procurement/vendor monitoring, finance/budget summaries, asset/property register, citizen complaints, biometric/payroll, native mobile apps, GIS, digital signatures and additional Dakbungalow/property modules are **not implemented**. The demo deliberately stops at the seven approved modules and four facilities. Status: **Out of scope**.

### Section 14 — Approval and sign-off

`/app/acceptance/` and `/app/acceptance/checklists/` provide a plan and deliverable/UAT checklist with status, note, checker and timestamp. They are demo trackers, not a legally binding electronic signature. Status: **Partial**.

---

## 3. Annex A — detailed module trace

### A.1 Human Resource Management (HRM)

| SoW feature | Implementation | Status | Gap / note |
|---|---|---|---|
| Employee Master Register | `/app/hr/employees/`: add employee (ID, name, department, designation, joining date, type, phone, email), search by name/ID/designation, filter by department/status; employee detail shows attendance, leave, training, supervisor. | Partial | No edit/archive action from the UI. |
| Department & Reporting Structure | Department and Designation models, department heads and employee supervisor; department-filtered lists and counts. | Partial | No department/designation management screen and no drawn organogram. |
| Employee Self-Service | `/app/hr/employees/<id>/` restricted to own record unless `hr.view`; `/app/hr/leave/` for own leave; attendance/leave/training summaries; `/app/tasks/` for users with workflow access. | Partial | `employee1` has no `workflow.view`, so assigned tasks are not shown on the employee dashboard. |
| Attendance Register | `/app/hr/attendance/`: daily present/absent/late/leave marking with recorder and audit; monthly summaries on the HR dashboard. | Done | Bulk daily entry, not an import file. |
| Leave Application & Approval | `/app/hr/leave/` submits leave and starts the seeded `leave` workflow (supervisor → HR), with status/history and task inbox decisions. | Done | — |
| Duty Roster & Assignments | `/app/hr/roster/`: employee, date, shift, facility, note; roster list. | Done | No separate assignment-completion tracking. |
| Training & Expiry Tracking | `/app/hr/training/`: title, provider, completion, expiry, certificate upload, notes; expiring-within-60-days panel. | Done | Reminders are shown in the dashboard, not pushed as scheduled messages. |
| HR Reports & ACL | HR dashboard counts, department filtering, CSV/PDF employee register export (`mis` reports), permission-protected routes. | Done | — |
| No payroll / biometric integration | Not present. | Out of scope | Per SoW. |

### A.2 Digital Document & File Management

| SoW feature | Implementation | Status | Gap / note |
|---|---|---|---|
| Incoming/Outgoing Register | `/app/documents/`: file number, subject, category, department, priority, confidentiality, received-from, assignee, due date, notes, attachment; search/filter. | Partial | No explicit inward/outward direction field or separate outward register. |
| Electronic File Creation | Auto file number `GZP-FL-...`; metadata, attachment upload, assignment, confidentiality. | Done | — |
| Movement & Tracking | `/app/documents/<id>/`: forward, receive, return, close, note; movement timeline with sender, recipient, note, timestamp; current holder. | Done | — |
| Review & Decisions | Return/close and notes; `Document file decision` workflow template exists in the designer. | Partial | The file screen does not launch that workflow; decisions are recorded as movements, and the template is demonstrated through the workflow designer/task engine rather than from the file page. |
| Versioning & Archive | Status includes `archived`; closed/archived counted and excluded from overdue; searchable register. | Partial | No revision/version history. |
| Search & Filters | By file number, subject, sender; category and status filters; confidential files hidden without permission. | Done | No date-range filter. |
| Overdue Alerts | `/app/documents/overdue/`: files past due and not closed/archived; dashboard counts. | Done | Alerts are queues, not scheduled messages. |
| Audit & Restricted Access | `/app/documents/access/` movement log; confidentiality check returns 403; audit entries on create/move; audit log export. | Done | — |

### A.3 Workflow & Approval Management

| SoW feature | Implementation | Status |
|---|---|---|
| Workflow Designer / Setup | `/app/workflow/`: templates by category, ordered steps, role, allowed decisions, JSON conditions, SLA hours, final flag; create/edit/delete steps. | Done |
| Submission & Assignment | Booking and leave submissions create an instance, tracking ID, first task and role notification. | Done |
| My Tasks & Queues | `/app/tasks/`: pending, completed, returned, cancelled, overdue; priority, status and search filters; task detail with payload, history and decision form. | Done |
| Review & Clarification | Decisions `forward`, `recommend`, `correct`, `return`, `approve`, `reject`; server checks step, role, task state and authority. `correct`/`return` maps the booking to Clarification Required. | Done |
| Approval Sequence | Route resolved from DB steps and JSON conditions; authority matrix enforces category, role and maximum amount. Seeded booking route: desk → technical (suite/hall only) → EO → CEO (above ৳20,000). | Done |
| Reminders & Escalation | `/app/workflow/reminders/run/` (permission-controlled) sends reminders within the configured window and escalates overdue tasks to the role supervisor; fields record reminder/escalation time and recipient. | Done |
| Cross-Module Reuse | Booking and leave launch the engine; file and project templates are seeded and configurable. | Partial (file/project not launched from their screens) |
| Tracking & Audit | `/app/mis/workflow/`: counts by status/step/role, turnaround and pending views; every decision in `StepRecord`; workflow instances viewable. | Done |

### A.4 Project & Development Monitoring

| SoW feature | Implementation | Status | Gap / note |
|---|---|---|---|
| Project Register | `/app/projects/`: code, name, department, description, location, budget, spent, start/end, status, manager; search/filter; totals. | Partial | No vendor/work-order reference field. |
| Milestones & Schedule | `/app/projects/<id>/`: milestone title, due date, note, done action; overdue timeline indicator. | Partial | No dependencies between milestones. |
| Progress Updates | Progress %, spent, status, manager; update history is audited. | Partial | No free-text progress note or photograph attachment. |
| Field Inspection | `/app/projects/inspections/`: project, date, inspector, location text, findings, rating, follow-up date; project detail shows recent inspections. | Partial | Location is free text, not GIS; no attachment/photo. |
| Issues & Follow-Up | — | Not implemented | No issue/severity/owner/closure register. |
| Bill / Payment Reference | Budget and spent totals only. | Partial | No official bill/payment status reference field; does not replace treasury/accounts. |
| Management Dashboard | Project filters, budget/spent/progress, delayed counts, CSV/PDF project register, department dashboard. | Done | — |

### A.5 Meeting & Committee Management

| SoW feature | Implementation | Status | Gap / note |
|---|---|---|---|
| Meeting Calendar | `/app/meetings/`: schedule date, time, venue, chair, secretary, agenda, status; list and filters. | Partial | List/table, not a graphical month calendar. |
| Agenda & Attachments | Agenda text is saved and shown; minutes editable. | Partial | No attachment upload or revision history. |
| Attendance & Minutes | Attendee add/attendance toggle; minutes save; searchable meeting list/detail. | Done | — |
| Decision Register | Action items with description, owner, due date, status, note, completion time. | Done | Decisions are actions, not a separate numbered decision register. |
| Action Follow-Up | `/app/meetings/actions/`: open/overdue/completed filters, status update, note, audit. | Done | — |
| Reminders & Archive | Meeting status includes cancelled/held; past meetings remain searchable. | Partial | No automatic action reminders and no archive action. |

### A.6 MIS, Analytics & Reporting

| SoW feature | Implementation | Status |
|---|---|---|
| Executive Dashboard | `/app/mis/`: KPI cards, booking status, collections, HR/project/meeting indicators, trend chart. | Done |
| Department Dashboards | `/app/mis/department/`: department-filtered pending files, leave, tasks, milestones and actions. | Done |
| Booking & Revenue Reports | `/app/mis/bookings/`: status, occupancy, payments, refunds, reconciled collection; daily/weekly/monthly and facility filters. | Done (simulated gateway data) |
| Workflow Performance | `/app/mis/workflow/`: received/pending/overdue/approved/rejected, step/role counts, turnaround. | Done |
| HR / Project / Meeting Reports | Report library and HR/project exports; meeting actions in dashboards. | Done (meeting-specific export is Partial) |
| Access & Exports | Permission checks, date/facility filters, CSV and PDF exports, `/app/mis/access-log/`. | Done |
| Audit & Definitions | Settings page documents keys/values; report access log; audit log. | Done |

### A.7 Dakbungalow E-Booking — four facilities

| SoW feature | Implementation | Status |
|---|---|---|
| Public Facility Catalogue | `/` (catalogue) and `/facilities/<code>/`: four facilities, photos (where seeded), amenities, rules, tariffs, blackout dates, availability, booking types. | Done |
| Account Registration & Verification | `/register/`, `/verify-email/`, `/resend-otp/`; OTP expiry/attempts; demo code shown locally; SMS labelled client-paid. | Simulated |
| Application & Slot Selection | `/book/<facility>/`, `/book/details/`: unit/room/hall, dates, slot (full day/morning/afternoon/evening), category, purpose, guests, documents; reference on submit. | Done |
| Availability Hold & Conflict Prevention | `InventoryLock` rows per night (rooms) or per date/slot (halls) with partial unique constraint; holds expire; release on rejection/cancel/expiry; double-booking raises `IntegrityError` and is tested. | Done |
| Citizen Tracking Portal | `/citizen/`, `/bookings/<id>/`, `/track/`: all SoW statuses plus Expired; timeline, next action, messages, documents. | Done |
| Booking Desk Review | `/app/bookings/?queue=desk`, `/app/bookings/<id>/`: completeness, correction request, recommend, reject. | Done |
| Technical / Executive Review | Engineer step condition for suite/hall; EO approval within matrix; CEO above threshold; rejection/correction reasons recorded. | Done |
| Final Approval | CEO/Chairman (or EO within delegation) with reasons and timestamps; authority enforced server-side. | Done |
| Payment Gateway Integration | `/pay/<txn>/`: simulated checkout, success/failure/cancel, HMAC callback, server verification, duplicate/mismatch/forged rejection, receipt PDF. | Simulated |
| Permit & Verification | Permit PDF with QR, public `/verify/<token>/`, reception reference/QR check; permit only after approval + verified payment. | Done |
| Cancellation & Refund Requests | Citizen cancellation request; finance refund queue with policy percentage; refund records and gateway reference; refund execution is simulated. | Done (execution Simulated) |
| Facility Operations & Reports | `/app/reception/` check-in/out; `/app/facilities/` tariffs/blackouts/holds; `/app/payments/` reconciliation; booking/revenue and occupancy reports; CSV/PDF. | Done |

---

## 4. Cross-module and non-functional requirements

| Requirement | Implementation | Status |
|---|---|---|
| One identity/access layer across modules | Custom `accounts.User` + Role/Permission M2M, `@perm_required`, `@staff_required`, `@citizen_required`, navigation filtering. | Done |
| Shared audit trail | `audit.AuditEntry` with actor, action, object, description, IP, module; list/filter/export. | Done |
| Shared notification infrastructure | `notifications.Notification`, `OutboxMessage`, editable `NotificationTemplate`; email/SMS are demo outbox entries. | Simulated |
| Shared management reporting | MIS dashboards and report library across HR, documents, projects, meetings, workflow and bookings. | Done |
| Bengali/English switch | `/lang/<code>/`, `{% t %}` tag, `|tr` filter, 300+ translated strings; session language; switch on public and staff layout. | Done |
| Demo banner on every page | `demo_ribbon` setting rendered in base/auth templates. | Done |
| Branding (logo as supplied, navy/lime palette) | `static/img/` logo, CSS variables, header/footer with app name and supplier attribution. | Done |
| Offline laptop demo | All CSS/JS vendored locally; SQLite; no API keys or network calls. | Done |
| Sample data | `seed_demo --reset` creates 18 accounts, 4 facilities/24 units/72 tariffs, 30 employees, 60 files, 12 projects, 8 meetings, 40+ bookings across statuses, workflow instances/tasks, payments, refunds, audit, notifications, support and plan data. | Done |
| Automated tests | 36 Django tests across access control, workflow routing/authority, double booking/holds and payment callbacks. | Done |
| README/run guide | Project README (setup, accounts, demo script, tests, limitations). | Done |

---

## 5. Demo accounts

Password for every seeded account: **`Demo@12345`**. Citizens land on `/citizen/`; staff land on `/app/`.

| Username | Role | Suggested route |
|---|---|---|
| `citizen1` | Citizen / Applicant | `/citizen/` |
| `citizen2` | Citizen / Applicant | `/citizen/` |
| `bookingdesk` | Dealing Assistant / Booking Desk | `/app/tasks/` |
| `engineer` | Assistant Engineer / Technical Reviewer | `/app/tasks/` |
| `eo` | Executive Officer | `/app/tasks/` |
| `ceo` | CEO / Chairman | `/app/tasks/` |
| `reception` | Reception / Facility Operator | `/app/reception/` |
| `finance` | Finance / Accounts | `/app/payments/` |
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

A demo role switcher is available at `/demo/switch/` for staff accounts; it is sample-only and does not bypass permissions.

---

## 6. Verification evidence

| Check | Result |
|---|---|
| `python manage.py check` | No issues. |
| `python manage.py test` | **36 tests, OK** — role access, read-only middleware, workflow routing and authority, citizen/staff portal separation, facility tariffs, double-booking/holds, hold expiry, payment callback verification/duplicates/mismatch, gateway access, report permissions. |
| Role/page smoke run (all 18 accounts, every navigation URL and dynamic detail) | 280 requests: 243 × HTTP 200, 36 expected login/register redirects for authenticated users, 1 corrected bad test URL. |
| Golden-path run | Citizen application → desk → EO approval → awaiting payment → simulated gateway → permit `GZP-PRM-2026-000043` → duplicate/forged callbacks rejected → receipt/permit/QR/verify 200 → finance refund → reception check-in/out. |
| Bengali switch | `/lang/bn/` shows Bengali labels and demo ribbon; switching back restores English. |

Re-run:

```bash
python manage.py test
python manage.py seed_demo --reset
python manage.py runserver
```

---

## 7. Known gaps and unfinished items

These are the honest gaps against the full SoW. They do not block the demo flow, but they are called out so the trace is not read as claiming 100% coverage.

1. **Documents:** no revision/version history; no explicit inward vs outward register; the file-decision workflow template is not launched from the file screen.
2. **Projects:** no issue/follow-up register, work-order/vendor reference, bill/payment status field, or photo attachment on progress/inspection.
3. **Meetings:** no agenda/attachment upload, graphical calendar, automatic action reminders, or explicit archive action.
4. **HR:** employees can be added but not edited/archived in the UI; no department/designation master-data screen or drawn organogram; the `employee` role does not see assigned workflow tasks because it lacks `workflow.view`.
5. **File/project workflow reuse:** the workflow designer includes file and project templates, but only booking and leave submissions start an instance. Demonstrating those routes requires the workflow designer/task engine rather than a screen action.
6. **External channels:** email, SMS, OTP delivery and the payment gateway are simulations. No real money, SMS credits, email delivery, National ID, D-Nothi/e-GP or other paid API is connected.
7. **Production security/hosting:** local demo runs over HTTP with SQLite; TLS, WAF, VPN, encrypted storage, off-site backup scheduling and external monitoring are deployment actions, not provisioned here.
8. **Commercial artefacts:** signed acceptance, 36-month support contract, formal SRS/manuals, monthly support reports, licence/escrow and SLA coverage hours are documents/agreements, not enforced by the app. The app provides trackers and evidence.
9. **Explicitly out of scope:** payroll, biometrics, native mobile app, GIS, digital signatures, more than four facilities, procurement/asset/complaints modules and bulk historical migration.

No gap above is presented as a delivered feature in the UI; where the app is partial, the screen shows only what it actually does.
