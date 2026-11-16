# Dhaka South City Corporation — Integrated Digital Service Platform (Demo)

A working Django demo of the Dhaka South City Corporation service portal, prepared for Adcelerete Technologies Limited. This folder is the **city-only** build: one organisation, one portal, four demo roles.

The demo is designed for a single laptop, fully offline: SQLite database, server-rendered templates, vendored CSS/JS, no Node build, no API keys, no real SMS/email/payments.

---

## 1. What works

- **City service catalogue**: 14 services, 21 application forms, 16 offices in five groups, and an Acts / rules / gazettes library.
- **Online applications**: typed, paper-style forms (text, date, NID, mobile, select, radio, attachments), bilingual labels, printable blank/sample PDFs, submitted PDFs and approval certificates.
- **Verification route**: ward councillor → department officer → mayor, driven by database records, with returned files, resubmission and notifications.
- **Role dashboards**: a separate desk for each role, a verification queue and citizen application tracking.
- **Zones, wards and offices**: 10 zones, 75 wards and editable head title/name.
- **English / বাংলা switch**, DSCC crest and green/red government theme, Adcelerete supplier marks.

No payroll, biometrics, GIS, digital signatures, mobile app or real payment gateway is included.

---

## 2. Run it

The folder already contains a ready `.venv`. In VS Code, select `\.venv\Scripts\python.exe` as the interpreter, or from this folder:

```bash
source .venv/Scripts/activate
python manage.py migrate
python manage.py seed_organizations
python manage.py runserver
```

Open <http://127.0.0.1:8000/> — it opens the city portal at `/dscc/`.

To rebuild the virtualenv on another machine:

```bash
python -m venv .venv
pip install -r requirements.txt
```

`seed_organizations` is safe to re-run. It creates only the Dhaka South City Corporation data set: 4 demo accounts, 14 services, 21 forms, 10 zones, 75 wards, 16 departments and four sample applications. Reset at any time before a presentation:

```bash
python manage.py seed_organizations
```

Tests:

```bash
python manage.py test
```

---

## 3. Demo accounts

Every demo account uses the password **`Demo@12345`**. The login page has a one-click quick sign-in panel for these four accounts.

| Username | Role | Where it lands |
|---|---|---|
| `dscc_citizen` | Citizen / Applicant | `/dscc/applications/` |
| `dscc_councillor` | Ward Councillor | `/app/city/` |
| `dscc_officer` | Department Officer | `/app/city/` |
| `dscc_mayor` | Mayor / Administrator | `/app/city/` |

Main pages: `/dscc/` (city home), `/dscc/forms/` (application forms), `/dscc/offices/`, `/dscc/acts/`, `/app/city/` (staff dashboard), `/app/city/queue/` (verification queue).

---

## 4. Notes

- Seed data is fictional; use sample NID and mobile numbers only.
- The platform complements D-Nothi/e-Nothi, e-GP and statutory approvals; it does not replace or bypass them.
- Prepared by Adcelerete Technologies Limited.
