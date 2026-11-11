"""Populate the demo database with a complete, coherent sample dataset.

Usage:
    python manage.py seed_demo --reset

Everything created here is fictional sample data. No real personal data,
messages or money are involved. The command is safe to re-run with --reset.
"""
from __future__ import annotations

import random
import sqlite3
from datetime import datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.demo import DEMO_PASSWORD
from accounts.models import Permission, Role, User
from accounts.permissions import PERMISSIONS, ROLE_DEFINITIONS, ROLE_PERMISSIONS
from audit.models import AuditEntry
from bookings.models import (
    Booking,
    BookingDocument,
    BookingMessage,
    BookingStatusChange,
)
from core.defaults import SETTING_DEFS
from core.models import (
    AppSetting,
    BackupRecord,
    HealthEvent,
    SettingHistory,
    set_setting,
)
from documents.models import DocumentFile, FileMovement
from facilities import availability
from facilities.models import BlackoutDate, Facility, InventoryLock, Tariff, Unit
from hr.models import (
    Attendance,
    Department,
    Designation,
    Employee,
    LeaveRequest,
    Roster,
    TrainingRecord,
)
from meetings.models import ActionItem, Attendee, Meeting
from mis.models import ReportAccessLog
from notifications.models import Notification, NotificationTemplate, OutboxMessage
from payments import gateway
from payments.models import Payment, PaymentCallback, Refund
from projects.models import Inspection, Milestone, Project
from support.models import ChangeRequest, ChecklistItem, PlanPhase, Ticket
from workflow import engine
from workflow.models import (
    AuthorityMatrix,
    StepRecord,
    WorkflowInstance,
    WorkflowStep,
    WorkflowTask,
    WorkflowTemplate,
)

random.seed(20261108)

HALL_SLOTS = ['morning', 'afternoon', 'evening']


class Command(BaseCommand):
    help = 'Create the complete demo dataset (facilities, users, bookings, modules).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset', action='store_true',
            help='Flush the database before seeding. Required when data exists.',
        )

    def handle(self, *args, **options):
        if options['reset']:
            call_command('flush', interactive=False, verbosity=0)
            self.stdout.write(self.style.WARNING('Database flushed.'))
        elif User.objects.filter(username='admin').exists() or Facility.objects.exists():
            self.stdout.write(self.style.WARNING(
                'Demo data already exists. Re-run with --reset to rebuild it.'))
            return

        self.now = timezone.now()
        self.today = timezone.localdate()
        self.year = self.today.year
        with transaction.atomic():
            self._seed_settings()
            self._seed_roles()
            self._seed_departments()
            self._seed_facilities()
            self._seed_users()
            self._seed_notification_templates()
            self._seed_workflows()
            self._seed_employees()
            self._seed_documents()
            self._seed_projects()
            self._seed_meetings()
            self._seed_support()
            self._seed_bookings()
            self._seed_communications()
            self._seed_audit()
            self._seed_health()
            self._post_seed_settings()

        call_command('seed_assets')
        self._create_backup()
        self._summarise()

    # ------------------------------------------------------------------ helpers
    def _at(self, days=0, hours=0, minutes=0):
        return self.now - timedelta(days=days, hours=hours, minutes=minutes)

    def _day(self, offset=0):
        return self.today + timedelta(days=offset)

    def _write_pdf(self, relative_path, title, lines):
        from reportlab.pdfgen import canvas

        path = Path(settings.MEDIA_ROOT) / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        pdf = canvas.Canvas(str(path), pagesize=(595, 842))
        pdf.setFont('Helvetica-Bold', 15)
        pdf.drawString(50, 790, title[:80])
        pdf.setFont('Helvetica', 10)
        y = 760
        for line in lines:
            pdf.drawString(50, y, str(line)[:95])
            y -= 16
            if y < 60:
                pdf.showPage()
                pdf.setFont('Helvetica', 10)
                y = 790
        pdf.setFont('Helvetica-Oblique', 8)
        pdf.drawString(50, 40, 'Demo version - sample data only.')
        pdf.save()
        return relative_path

    # ----------------------------------------------------------------- settings
    def _seed_settings(self):
        for key, default, label, group, desc in SETTING_DEFS:
            AppSetting.objects.update_or_create(
                key=key,
                defaults={'value': default, 'label': label, 'group': group,
                          'description': desc},
            )
        self.stdout.write('  settings: %d values' % AppSetting.objects.count())

    def _post_seed_settings(self):
        admin = self.users['admin']
        AppSetting.objects.update(updated_by=admin)
        history = [
            ('payment_window_hours', '12', '24', 12,
             'Extended to 24 hours for the district rollout.'),
            ('hold_hours', '24', '48', 8,
             'Holds kept for two days while applications are reviewed.'),
            ('refund_policy', '7:100,3:50,1:0', '7:100,3:50,1:25,0:0', 4,
             'Finance approved a 25 percent band for late cancellations.'),
        ]
        for key, old, new, days, note in history:
            SettingHistory.objects.create(
                key=key, old_value=old, new_value=new,
                changed_by=admin, changed_at=self._at(days=days), note=note,
            )

    # -------------------------------------------------------------------- roles
    def _seed_roles(self):
        perms = {}
        for code, label, module in PERMISSIONS:
            perm, _ = Permission.objects.update_or_create(
                code=code, defaults={'label': label, 'module': module})
            perms[code] = perm
        self.roles = {}
        for code, name, description, order, read_only in ROLE_DEFINITIONS:
            role, _ = Role.objects.update_or_create(
                code=code,
                defaults={'name': name, 'description': description,
                          'sort_order': order, 'is_read_only': read_only},
            )
            role.permissions.set(
                [perms[c] for c in ROLE_PERMISSIONS.get(code, []) if c in perms])
            self.roles[code] = role
        self.stdout.write('  roles: %d, permissions: %d'
                          % (len(self.roles), len(perms)))

    # -------------------------------------------------------------- organisation
    def _seed_departments(self):
        specs = [
            ('Administration', 'admin'), ('Finance & Accounts', 'finance'),
            ('Engineering', 'engineering'), ('Health & Family Planning', 'health'),
            ('Education', 'education'), ('Agriculture', 'agriculture'),
            ('Establishment', 'establishment'), ('ICT', 'ict'),
        ]
        self.departments = {}
        for name, code in specs:
            dept, _ = Department.objects.update_or_create(
                code=code, defaults={'name': name})
            self.departments[code] = dept
        designations = [
            ('admin', 'Chief Executive Officer'), ('admin', 'Executive Officer'),
            ('admin', 'Administrative Officer'), ('admin', 'Registry Officer'),
            ('admin', 'Facility Caretaker'), ('admin', 'Meeting Secretary'),
            ('admin', 'Auditor'),
            ('finance', 'Accounts Officer'), ('finance', 'Accountant'),
            ('engineering', 'Assistant Engineer'), ('engineering', 'Project Officer'),
            ('engineering', 'Inspector'), ('engineering', 'Sub-Assistant Engineer'),
            ('health', 'Medical Officer'), ('health', 'Health Inspector'),
            ('education', 'Education Officer'), ('education', 'Assistant Teacher'),
            ('agriculture', 'Agriculture Officer'),
            ('establishment', 'HR Officer'), ('establishment', 'Supervisor'),
            ('establishment', 'Office Assistant'),
            ('ict', 'ICT Officer'), ('ict', 'Data Entry Operator'),
        ]
        self.designations = {}
        for dept_code, name in designations:
            desig, _ = Designation.objects.get_or_create(
                name=name, department=self.departments[dept_code])
            self.designations[name] = desig
        self.stdout.write('  departments: %d, designations: %d'
                          % (len(self.departments), len(self.designations)))

    # ---------------------------------------------------------------- facilities
    def _seed_facilities(self):
        specs = [
            {
                'code': 'gazipur-sadar', 'name': 'Gazipur Sadar Dakbungalow',
                'location': 'Court Road, Gazipur Sadar, Gazipur',
                'description': 'The main district guesthouse beside the Parishad '
                               'office, used for official guests and citizens.',
                'contact': '+880 0000 000101',
                'units': [
                    ('R1', 'Room 1 - Standard', 'room', 2),
                    ('R2', 'Room 2 - Standard', 'room', 2),
                    ('R3', 'Room 3 - Standard', 'room', 2),
                    ('S1', 'VIP Suite 1', 'suite', 4),
                    ('S2', 'VIP Suite 2', 'suite', 4),
                    ('H1', 'Conference Hall', 'hall', 60),
                ],
            },
            {
                'code': 'kaliakair', 'name': 'Kaliakair Dakbungalow',
                'location': 'Kaliakair Bus Stand Road, Gazipur',
                'description': 'A quiet guesthouse for official visits to the '
                               'Kaliakair upazila complex.',
                'contact': '+880 0000 000102',
                'units': [
                    ('R1', 'Room 1 - Standard', 'room', 2),
                    ('R2', 'Room 2 - Standard', 'room', 2),
                    ('R3', 'Room 3 - Family', 'room', 3),
                    ('S1', 'VIP Suite', 'suite', 4),
                    ('H1', 'Meeting Hall', 'hall', 40),
                ],
            },
            {
                'code': 'sreepur', 'name': 'Sreepur Dakbungalow',
                'location': 'Sreepur Sadar, Gazipur',
                'description': 'The largest facility, with family rooms, suites '
                               'and a training hall.',
                'contact': '+880 0000 000103',
                'units': [
                    ('R1', 'Room 1 - Standard', 'room', 2),
                    ('R2', 'Room 2 - Standard', 'room', 2),
                    ('R3', 'Room 3 - Standard', 'room', 2),
                    ('R4', 'Room 4 - Family', 'room', 3),
                    ('R5', 'Room 5 - Family', 'room', 3),
                    ('S1', 'VIP Suite 1', 'suite', 4),
                    ('S2', 'VIP Suite 2', 'suite', 4),
                    ('H1', 'Training Hall', 'hall', 80),
                ],
            },
            {
                'code': 'kapasia', 'name': 'Kapasia Dakbungalow',
                'location': 'Kapasia Bazar Road, Gazipur',
                'description': 'A small guesthouse for field officers and '
                               'visiting officials in Kapasia.',
                'contact': '+880 0000 000104',
                'units': [
                    ('R1', 'Room 1 - Standard', 'room', 2),
                    ('R2', 'Room 2 - Standard', 'room', 2),
                    ('R3', 'Room 3 - Family', 'room', 3),
                    ('S1', 'VIP Suite', 'suite', 4),
                    ('H1', 'Conference Room', 'hall', 50),
                ],
            },
        ]
        self.facilities = {}
        self.units = {}
        self.facility_units = {}
        tariff_bases = {
            'room': {'government': 1200, 'citizen': 1500, 'organization': 2000,
                     'holiday': {'government': 1500, 'citizen': 1800,
                                 'organization': 2400}, 'deposit': 1000},
            'suite': {'government': 3000, 'citizen': 3500, 'organization': 4200,
                      'holiday': {'government': 3600, 'citizen': 4200,
                                  'organization': 5000}, 'deposit': 2000},
            'hall': {'government': 6000, 'citizen': 8000, 'organization': 10000,
                     'holiday': {'government': 7500, 'citizen': 10000,
                                 'organization': 12000}, 'deposit': 3000},
        }
        multipliers = {'gazipur-sadar': 1.0, 'kaliakair': 0.9,
                       'sreepur': 1.15, 'kapasia': 0.85}
        amenities = ('Attached bathroom, Air conditioning, Wi-Fi, '
                     'Generator backup, Parking')
        rules = ('Check-in from 12:00, check-out by 11:00. Photo ID required. '
                 'No smoking indoors. Sample rules for the demo.')
        for spec in specs:
            facility, _ = Facility.objects.update_or_create(
                code=spec['code'],
                defaults={
                    'name': spec['name'], 'location': spec['location'],
                    'description': spec['description'], 'contact': spec['contact'],
                    'amenities': amenities, 'rules': rules,
                    'booking_types': 'Official meeting, Individual stay, '
                                     'Government delegation, Training',
                    'is_sample': True, 'is_active': True,
                },
            )
            self.facilities[spec['code']] = facility
            factor = multipliers[spec['code']]
            units = []
            for code, name, kind, capacity in spec['units']:
                unit, _ = Unit.objects.update_or_create(
                    facility=facility, code=code,
                    defaults={'name': name, 'kind': kind, 'capacity': capacity,
                              'description': f'{name} at {facility.name}',
                              'amenities': 'Air conditioning, Wi-Fi, Hot water',
                              'is_active': True},
                )
                self.units[f'{facility.code}/{code}'] = unit
                units.append(unit)
                base = tariff_bases[kind]
                for category in ('government', 'citizen', 'organization'):
                    amount = round(base[category] * factor / 10) * 10
                    holiday = round(base['holiday'][category] * factor / 10) * 10
                    deposit = round(base['deposit'] * factor / 10) * 10
                    Tariff.objects.update_or_create(
                        unit=unit, category=category,
                        defaults={'amount': Decimal(amount),
                                  'holiday_amount': Decimal(holiday),
                                  'deposit': Decimal(deposit),
                                  'is_sample': True},
                    )
            self.facility_units[facility.code] = units

        blackouts = [
            ('gazipur-sadar', 18, 'Municipal election duty'),
            ('sreepur', 32, 'Annual building maintenance'),
            ('kapasia', 25, 'District sports event'),
        ]
        for code, offset, reason in blackouts:
            BlackoutDate.objects.update_or_create(
                facility=self.facilities[code], date=self._day(offset),
                defaults={'reason': reason})
        self.stdout.write('  facilities: %d, units: %d, tariffs: %d'
                          % (len(self.facilities), Unit.objects.count(),
                             Tariff.objects.count()))

    # -------------------------------------------------------------------- users
    def _seed_users(self):
        specs = [
            # username, full name, role, department, designation, facility
            ('citizen1', 'Md. Rakib Hasan', 'citizen', None, None, None),
            ('citizen2', 'Nusrat Jahan', 'citizen', None, None, None),
            ('bookingdesk', 'Abdul Karim', 'bookingdesk', 'admin',
             'Administrative Officer', None),
            ('engineer', 'Engr. Shahidul Islam', 'engineer', 'engineering',
             'Assistant Engineer', None),
            ('eo', 'Md. Anwar Hossain', 'eo', 'admin', 'Executive Officer', None),
            ('ceo', 'Dr. A. K. M. Fazlul Haque', 'ceo', 'admin',
             'Chief Executive Officer', None),
            ('reception', 'Jahangir Alam', 'reception', 'admin',
             'Facility Caretaker', 'gazipur-sadar'),
            ('finance', 'Farhana Akter', 'finance', 'finance',
             'Accounts Officer', None),
            ('hradmin', 'Shirin Sultana', 'hradmin', 'establishment',
             'HR Officer', None),
            ('supervisor', 'Mizanur Rahman', 'supervisor', 'establishment',
             'Supervisor', None),
            ('employee1', 'Rafiqul Islam', 'employee', 'establishment',
             'Office Assistant', None),
            ('depthead', 'Prof. Nazmul Huda', 'depthead', 'education',
             'Education Officer', None),
            ('registry', 'Kamal Uddin', 'registry', 'admin',
             'Registry Officer', None),
            ('projectofficer', 'Tahmina Begum', 'projectofficer', 'engineering',
             'Project Officer', None),
            ('inspector', 'S. M. Imran', 'inspector', 'engineering',
             'Inspector', None),
            ('secretary', 'Rehana Parvin', 'secretary', 'admin',
             'Meeting Secretary', None),
            ('management', 'Board Audit Cell', 'management', 'admin',
             'Auditor', None),
            ('admin', 'System Administrator', 'admin', 'ict',
             'ICT Officer', None),
        ]
        phones = {
            'citizen1': '01711000001', 'citizen2': '01711000002',
            'bookingdesk': '01711000003', 'engineer': '01711000004',
            'eo': '01711000005', 'ceo': '01711000006',
            'reception': '01711000007', 'finance': '01711000008',
            'hradmin': '01711000009', 'supervisor': '01711000010',
            'employee1': '01711000011', 'depthead': '01711000012',
            'registry': '01711000013', 'projectofficer': '01711000014',
            'inspector': '01711000015', 'secretary': '01711000016',
            'management': '01711000017', 'admin': '01711000018',
        }
        self.users = {}
        for username, full_name, role_code, dept_code, desig_name, fac_code in specs:
            parts = full_name.split()
            first = parts[0]
            last = ' '.join(parts[1:])
            user = User.objects.create_user(
                username=username,
                email=f'{username}@example.test',
                password=DEMO_PASSWORD,
                first_name=first,
                last_name=last,
                phone=phones[username],
                role=self.roles[role_code],
                department=self.departments[dept_code] if dept_code else None,
                designation=self.designations.get(desig_name) if desig_name else None,
                facility=self.facilities[fac_code] if fac_code else None,
                email_verified=True,
                is_demo=True,
            )
            self.users[username] = user
        self.stdout.write('  demo accounts: %d (password %s)'
                          % (len(self.users), DEMO_PASSWORD))

    # ------------------------------------------------------------ notifications
    def _seed_notification_templates(self):
        templates = [
            ('confirmation', 'Application received',
             'Application received - {{ reference }}',
             'Dear {{ user }},\n\nWe received your application {{ reference }}. '
             '{{ message }}\n\nYou can track progress from your dashboard.\n\n'
             'Gazipur Zila Parishad (demo)'),
            ('task_assigned', 'New workflow task',
             'New task: {{ step }} ({{ reference }})',
             'Dear {{ user }},\n\nA new task is waiting for you at the '
             '"{{ step }}" step.\nReference: {{ reference }}\nSubject: {{ subject }}\n'
             'Due: {{ due }}\n\nOpen My Tasks to review it.'),
            ('status_update', 'Application status update',
             'Update on {{ reference }}',
             'Dear {{ user }},\n\n{{ message }}\n\nReference: {{ reference }}\n'
             'Status: {{ status }}\n\nGazipur Zila Parishad (demo)'),
            ('clarification', 'Correction requested',
             'Clarification needed for {{ reference }}',
             'Dear {{ user }},\n\n{{ message }}\n\nPlease open the application '
             'and respond or upload the requested document.\n\n'
             'Gazipur Zila Parishad (demo)'),
            ('approval', 'Application approved',
             'Your request {{ reference }} was approved',
             'Dear {{ user }},\n\n{{ message }}\n\nOpen the application for the '
             'next steps.\n\nGazipur Zila Parishad (demo)'),
            ('rejection', 'Application rejected',
             'Your request {{ reference }} was not approved',
             'Dear {{ user }},\n\n{{ message }}\n\nYou may contact the booking '
             'desk for guidance.\n\nGazipur Zila Parishad (demo)'),
            ('payment_receipt', 'Payment receipt',
             'Payment received - {{ reference }}',
             'Dear {{ user }},\n\n{{ message }}\n\nAmount: {{ amount }}\n'
             'Receipt: {{ receipt }}\n\nThis is a demo gateway receipt; no real '
             'money was transferred.'),
            ('permit_ready', 'Permit ready',
             'Your permit is ready - {{ reference }}',
             'Dear {{ user }},\n\n{{ message }}\n\nPresent the permit and a photo '
             'ID at reception.\n\nGazipur Zila Parishad (demo)'),
            ('reminder', 'Task reminder',
             'Reminder: {{ step }} due for {{ reference }}',
             'Dear {{ user }},\n\nThis is a reminder that the "{{ step }}" task '
             'for {{ reference }} is due at {{ due }}.\n\nOpen My Tasks.'),
            ('escalation', 'Task escalated',
             'Escalation: {{ reference }} is overdue',
             'Dear {{ user }},\n\nThe "{{ step }}" task for {{ reference }} was '
             'due at {{ due }} and has been escalated for review.\n\n'
             'Open My Tasks.'),
            ('refund_update', 'Refund update',
             'Refund update for {{ reference }}',
             'Dear {{ user }},\n\n{{ message }}\n\nGazipur Zila Parishad (demo)'),
        ]
        for code, name, subject, body in templates:
            NotificationTemplate.objects.update_or_create(
                code=code,
                defaults={'name': name, 'subject': subject, 'body': body,
                          'channel': 'all', 'description': name},
            )
        self.stdout.write('  notification templates: %d'
                          % NotificationTemplate.objects.count())

    # --------------------------------------------------------------- workflows
    def _seed_workflows(self):
        templates = [
            ('booking', 'Dakbungalow booking approval', 'booking',
             'Desk review, optional technical review, then approval within the '
             'delegated authority. Amounts above BDT 20,000 go to the CEO.'),
            ('leave', 'Employee leave approval', 'leave',
             'Supervisor recommends, HR approves.'),
            ('file', 'Document file decision', 'file',
             'Registry forwards, Executive Officer approves.'),
            ('project', 'Project action approval', 'project',
             'Project officer forwards, Executive Officer approves.'),
        ]
        self.templates = {}
        for code, name, category, description in templates:
            tpl, _ = WorkflowTemplate.objects.update_or_create(
                code=code,
                defaults={'name': name, 'category': category,
                          'description': description, 'is_active': True},
            )
            self.templates[code] = tpl

        steps = {
            'booking': [
                (1, 'Booking desk review', 'bookingdesk',
                 ['forward', 'correct', 'reject'], None, 24, False),
                (2, 'Technical / facility review', 'engineer',
                 ['recommend', 'correct', 'reject'],
                 {'unit_kind': ['suite', 'hall']}, 24, False),
                (3, 'Executive Officer approval', 'eo',
                 ['approve', 'recommend', 'reject', 'correct'], None, 24, False),
                (4, 'CEO / Chairman final approval', 'ceo',
                 ['approve', 'reject', 'correct'],
                 {'min_amount': 20000.01}, 48, True),
            ],
            'leave': [
                (1, 'Supervisor recommendation', 'supervisor',
                 ['recommend', 'correct', 'reject'], None, 12, False),
                (2, 'HR approval', 'hradmin',
                 ['approve', 'reject', 'correct'], None, 24, True),
            ],
            'file': [
                (1, 'Registry review and forward', 'registry',
                 ['forward', 'return', 'reject'], None, 24, False),
                (2, 'Executive Officer decision', 'eo',
                 ['approve', 'reject', 'return'], None, 48, True),
            ],
            'project': [
                (1, 'Project officer review', 'projectofficer',
                 ['forward', 'reject'], None, 24, False),
                (2, 'Executive Officer approval', 'eo',
                 ['approve', 'reject'], None, 48, True),
            ],
        }
        self.steps = {}
        for code, rows in steps.items():
            for order, name, role_code, decisions, condition, sla, final in rows:
                step, _ = WorkflowStep.objects.update_or_create(
                    template=self.templates[code], order=order,
                    defaults={'name': name, 'role': self.roles[role_code],
                              'allowed_decisions': decisions,
                              'condition': condition, 'sla_hours': sla,
                              'is_final': final},
                )
                self.steps[(code, order)] = step

        matrix = [
            ('eo', 'booking', True, Decimal('20000.00'),
             'Delegated approval up to BDT 20,000'),
            ('ceo', 'booking', True, None,
             'Final approval above the Executive Officer delegation'),
            ('hradmin', 'leave', True, None, 'All leave applications'),
            ('eo', 'file', True, Decimal('500000.00'),
             'Document decisions within the delegated limit'),
            ('eo', 'project', True, Decimal('1000000.00'),
             'Project approvals within the delegated limit'),
            ('bookingdesk', 'booking', False, None, 'Review only'),
            ('engineer', 'booking', False, None, 'Technical review only'),
            ('supervisor', 'leave', False, None, 'Recommendation only'),
            ('registry', 'file', False, None, 'Forwarding only'),
            ('projectofficer', 'project', False, None, 'Forwarding only'),
        ]
        for role_code, category, can_approve, max_amount, note in matrix:
            AuthorityMatrix.objects.update_or_create(
                role=self.roles[role_code], category=category,
                defaults={'can_approve': can_approve, 'max_amount': max_amount,
                          'note': note},
            )
        self.stdout.write('  workflow templates: %d, steps: %d, matrix rows: %d'
                          % (len(self.templates), WorkflowStep.objects.count(),
                             AuthorityMatrix.objects.count()))

    # --------------------------------------------------------------------- HR
    def _seed_employees(self):
        extra_people = [
            ('Md. Shafiqul Islam', 'establishment', 'Office Assistant'),
            ('Rokeya Begum', 'finance', 'Accountant'),
            ('Abdus Salam', 'engineering', 'Sub-Assistant Engineer'),
            ('Nazma Akter', 'health', 'Health Inspector'),
            ('Harun-or-Rashid', 'education', 'Assistant Teacher'),
            ('Sufia Khatun', 'agriculture', 'Agriculture Officer'),
            ('Jasim Uddin', 'ict', 'Data Entry Operator'),
            ('Marium Sultana', 'admin', 'Administrative Officer'),
            ('Belal Hossain', 'engineering', 'Inspector'),
            ('Ayesha Siddika', 'health', 'Medical Officer'),
            ('Mokbul Hossain', 'establishment', 'Office Assistant'),
            ('Taslima Nasrin', 'education', 'Assistant Teacher'),
            ('Sohel Rana', 'ict', 'Data Entry Operator'),
            ('Parveen Akter', 'finance', 'Accountant'),
        ]
        staff_order = [
            ('ceo', 'admin', 'Chief Executive Officer', 2015),
            ('eo', 'admin', 'Executive Officer', 2016),
            ('bookingdesk', 'admin', 'Administrative Officer', 2018),
            ('engineer', 'engineering', 'Assistant Engineer', 2017),
            ('reception', 'admin', 'Facility Caretaker', 2021),
            ('finance', 'finance', 'Accounts Officer', 2019),
            ('hradmin', 'establishment', 'HR Officer', 2018),
            ('supervisor', 'establishment', 'Supervisor', 2020),
            ('employee1', 'establishment', 'Office Assistant', 2022),
            ('depthead', 'education', 'Education Officer', 2014),
            ('registry', 'admin', 'Registry Officer', 2019),
            ('projectofficer', 'engineering', 'Project Officer', 2021),
            ('inspector', 'engineering', 'Inspector', 2022),
            ('secretary', 'admin', 'Meeting Secretary', 2020),
            ('admin', 'ict', 'ICT Officer', 2023),
            ('management', 'admin', 'Auditor', 2013),
        ]
        self.employees = {}
        self.staff_employees = {}
        rows = []
        for i, (username, dept_code, desig_name, join_year) in enumerate(
                staff_order, start=1):
            user = self.users[username]
            join_date = self._day(-(
                365 * (self.year - join_year) + random.randint(0, 300)))
            rows.append({
                'user': user, 'name': user.display_name, 'dept': dept_code,
                'desig': desig_name, 'join': join_date,
                'phone': user.phone, 'email': user.email,
                'type': 'permanent', 'status': 'active',
            })
        for name, dept_code, desig_name in extra_people:
            rows.append({
                'user': None, 'name': name, 'dept': dept_code,
                'desig': desig_name,
                'join': self._day(-random.randint(200, 2600)),
                'phone': f'018{random.randint(10000000, 99999999)}',
                'email': '',
                'type': random.choice(['permanent', 'permanent', 'contract',
                                       'deputation', 'daily']),
                'status': random.choice(['active'] * 8 + ['leave', 'inactive']),
            })
        for i, row in enumerate(rows, start=1):
            employee = Employee.objects.create(
                user=row['user'], employee_no=f'GZP-EMP-{i:04d}',
                name=row['name'], department=self.departments[row['dept']],
                designation=self.designations[row['desig']],
                joining_date=row['join'], employment_type=row['type'],
                phone=row['phone'], email=row['email'],
                emergency_contact='Family contact (sample)',
                status=row['status'],
            )
            self.employees[employee.employee_no] = employee
            if row['user']:
                self.staff_employees[row['user'].username] = employee

        ceo_emp = self.staff_employees['ceo']
        eo_emp = self.staff_employees['eo']
        depthead_emp = self.staff_employees['depthead']
        supervisor_emp = self.staff_employees['supervisor']
        for employee in self.employees.values():
            if employee.user and employee.user.username == 'ceo':
                continue
            if employee.user and employee.user.username == 'depthead':
                employee.supervisor = ceo_emp
            elif employee.user and employee.user.username == 'supervisor':
                employee.supervisor = depthead_emp
            elif employee.department and employee.department.code == 'establishment':
                employee.supervisor = supervisor_emp
            elif employee.department and employee.department.code == 'education':
                employee.supervisor = depthead_emp
            else:
                employee.supervisor = eo_emp
            employee.save(update_fields=['supervisor'])

        # attendance for the last two working weeks
        statuses = ['present'] * 82 + ['late'] * 8 + ['leave'] * 5 + ['absent'] * 5
        records = []
        seen = set()
        attendance_people = [e for e in self.employees.values() if e.status == 'active']
        for offset in range(14):
            day = self._day(-offset)
            if day.weekday() >= 5 and offset != 0:
                continue
            for index, employee in enumerate(attendance_people):
                if (employee.pk, day) in seen:
                    continue
                if offset == 0:
                    # Keep today's sheet readable for the executive dashboard.
                    if index < 17:
                        status = 'present'
                    elif index < 21:
                        status = 'late'
                    elif index < 23:
                        status = 'absent'
                    else:
                        status = 'leave'
                else:
                    status = random.choice(statuses)
                in_time = time(9, random.randint(0, 45)) if status in (
                    'present', 'late') else None
                out_time = time(17, random.randint(0, 30)) if status in (
                    'present', 'late') else None
                records.append(Attendance(
                    employee=employee, date=day, status=status,
                    in_time=in_time, out_time=out_time,
                    note='Late arrival' if status == 'late' else '',
                    recorded_by=self.users['hradmin'],
                ))
                seen.add((employee.pk, day))
        Attendance.objects.bulk_create(records)

        # duty roster for the coming week
        roster_people = list(self.employees.values())[2:10]
        facilities = list(self.facilities.values())
        shifts = ['day', 'evening', 'night', 'day', 'off', 'day', 'evening']
        for employee in roster_people:
            for offset in range(7):
                day = self._day(offset)
                Roster.objects.update_or_create(
                    employee=employee, date=day,
                    defaults={'shift': shifts[(offset + employee.pk) % len(shifts)],
                              'facility': facilities[employee.pk % len(facilities)],
                              'note': 'Demo roster'},
                )

        training = [
            ('Fire safety and evacuation', 'Civil Defence', 300, 30),
            ('First aid refresher', 'Red Crescent (sample)', 200, 55),
            ('Records management', 'Parishad training unit', 120, 400),
            ('Cyber hygiene', 'ICT Division (sample)', 90, -10),
            ('Procurement rules', 'IMED (sample)', 400, 220),
            ('Disaster response', 'DDM (sample)', 150, 170),
            ('Customer service', 'Parishad training unit', 60, 120),
            ('Data protection', 'ICT Division (sample)', 75, 45),
            ('Dakbungalow operations', 'Parishad training unit', 30, 500),
            ('Financial reporting', 'Finance Division (sample)', 250, 90),
            ('Team leadership', 'BPATC (sample)', 500, 700),
            ('Field inspection', 'Engineering unit', 100, 25),
        ]
        for index, (title, provider, completed_ago, expires_in) in enumerate(training):
            employee = list(self.employees.values())[index % len(self.employees)]
            TrainingRecord.objects.create(
                employee=employee, title=title, provider=provider,
                completed_on=self._day(-completed_ago),
                expires_on=self._day(expires_in),
                note='Sample certificate reference',
            )

        self._seed_leaves()
        self.stdout.write('  employees: %d, attendance: %d, leave requests: %d'
                          % (Employee.objects.count(), Attendance.objects.count(),
                             LeaveRequest.objects.count()))

    def _advance(self, current, hours=18):
        return min(current + timedelta(hours=hours + random.randint(0, 6)),
                   self.now - timedelta(hours=1))

    def _seed_leaves(self):
        people = list(self.employees.values())
        admin = self.users['hradmin']
        supervisor_user = self.users['supervisor']
        specs = [
            (self.staff_employees['employee1'], 'casual', 0, 1,
             'Family programme', 'approved'),
            (self.staff_employees['depthead'], 'annual', 10, 14,
             'Annual leave', 'approved'),
            (people[16], 'sick', -1, 0, 'Fever, advised rest', 'approved'),
            (people[17], 'casual', 20, 21, 'Personal work', 'submitted'),
            (people[18], 'annual', 25, 28, 'Family visit', 'submitted'),
            (people[19], 'sick', 5, 6, 'Medical check-up', 'under_review'),
            (people[20], 'special', 30, 30, 'Official examination duty', 'recommended'),
            (people[21], 'casual', -10, -9, 'Unplanned absence', 'rejected'),
            (people[22], 'annual', 40, 44, 'Family holiday', 'clarification'),
            (people[23], 'casual', 50, 51, 'Personal work', 'cancelled'),
            (people[24], 'sick', 3, 4, 'Dental treatment', 'submitted'),
            (people[25], 'annual', 60, 63, 'Annual leave', 'submitted'),
        ]
        template = self.templates['leave']
        step_sup = self.steps[('leave', 1)]
        step_hr = self.steps[('leave', 2)]
        staff = [self.users['supervisor'], admin]
        for index, (employee, leave_type, start_offset, end_offset, reason,
                    status) in enumerate(specs):
            applied = self._at(days=3 + index, hours=index)
            leave = LeaveRequest.objects.create(
                employee=employee, leave_type=leave_type,
                start_date=self._day(start_offset),
                end_date=self._day(end_offset), reason=reason,
                status=status, applied_at=applied,
                decided_at=self._at(days=1 + index // 2) if status in (
                    'approved', 'rejected') else None,
            )
            payload = {
                'subject': f'{employee.name} - {leave.get_leave_type_display()}',
                'amount': 0, 'days': leave.days,
                'url': '/app/hr/leave/',
            }
            inst = WorkflowInstance.objects.create(
                template=template, object_type='hr.LeaveRequest',
                object_id=leave.pk,
                tracking_id=f'GZP-LV-{self.year}-{index + 1:06d}',
                requester=employee.user or admin, payload=payload,
                created_at=applied,
            )
            StepRecord.objects.create(
                instance=inst,
                actor=employee.user or admin,
                actor_role=employee.user.role.code if employee.user and employee.user.role else '',
                decision='submit', comments='Leave application submitted',
                created_at=applied,
            )
            t = applied
            if status == 'approved':
                t = self._advance(t, 8)
                self._workflow_task(inst, step_sup, 'completed', t)
                self._workflow_record(inst, step_sup, supervisor_user,
                                      'recommend', t, 'Recommended')
                t = self._advance(t, 12)
                self._workflow_task(inst, step_hr, 'completed', t)
                self._workflow_record(inst, step_hr, admin, 'approve', t,
                                      'Leave approved')
                inst.status = 'approved'
                inst.completed_at = t
                inst.note = 'Approved by HR'
                inst.save(update_fields=['status', 'completed_at', 'note'])
                if leave.start_date <= self.today <= leave.end_date:
                    employee.status = 'leave'
                    employee.save(update_fields=['status'])
                else:
                    employee.status = 'active'
                    employee.save(update_fields=['status'])
            elif status == 'rejected':
                t = self._advance(t, 10)
                self._workflow_task(inst, step_sup, 'completed', t)
                self._workflow_record(inst, step_sup, supervisor_user, 'reject',
                                      t, 'Operational exigency')
                inst.status = 'rejected'
                inst.completed_at = t
                inst.note = 'Operational exigency'
                inst.save(update_fields=['status', 'completed_at', 'note'])
                leave.decided_at = t
                leave.decision_note = 'Operational exigency'
                leave.save(update_fields=['decided_at', 'decision_note'])
            elif status == 'clarification':
                t = self._advance(t, 8)
                self._workflow_task(inst, step_sup, 'completed', t)
                self._workflow_record(inst, step_sup, supervisor_user, 'correct',
                                      t, 'Please attach the medical certificate')
                inst.status = 'returned'
                inst.current_step = step_sup
                inst.note = 'Please attach the medical certificate'
                inst.save(update_fields=['status', 'current_step', 'note'])
            elif status in ('under_review', 'recommended'):
                t = self._advance(t, 8)
                self._workflow_task(inst, step_sup, 'completed', t)
                self._workflow_record(inst, step_sup, supervisor_user,
                                      'recommend', t, 'Recommended')
                inst.current_step = step_hr
                inst.status = 'running'
                inst.save(update_fields=['current_step', 'status'])
                self._workflow_task(inst, step_hr, 'pending', t)
            elif status == 'cancelled':
                inst.status = 'cancelled'
                inst.completed_at = self._at(days=1)
                inst.note = 'Cancelled by the employee'
                inst.save(update_fields=['status', 'completed_at', 'note'])
            else:  # submitted
                inst.current_step = step_sup
                inst.status = 'running'
                inst.save(update_fields=['current_step', 'status'])
                self._workflow_task(inst, step_sup, 'pending', applied)

    def _workflow_task(self, instance, step, status='pending', when=None,
                       overdue=False, escalated=False):
        when = when or self._at(days=1)
        if status == 'pending':
            due = (self.now - timedelta(hours=8) if overdue
                   else self.now + timedelta(hours=step.sla_hours or 24))
        else:
            due = when + timedelta(hours=step.sla_hours or 24)
        task = WorkflowTask.objects.create(
            instance=instance, step=step, role=step.role, status=status,
            due_at=due, created_at=when,
        )
        if status == 'completed':
            task.completed_at = when
        if escalated:
            task.reminder_sent_at = self.now - timedelta(hours=4)
            task.escalated_at = self.now - timedelta(hours=2)
            task.escalated_to = self.users.get('supervisor')
        task.save()
        return task

    def _workflow_record(self, instance, step, actor, decision, when, comments=''):
        return StepRecord.objects.create(
            instance=instance, step=step, actor=actor,
            actor_role=actor.role.code if actor and actor.role else '',
            decision=decision, comments=comments, created_at=when,
        )

    # --------------------------------------------------------------- documents
    def _seed_documents(self):
        bases = [
            'Approval of annual work plan', 'Procurement of office stationery',
            'Repair of boundary wall', 'Audit observation reply',
            'Transfer of a records officer', 'Dakbungalow tariff revision',
            'Union parishad coordination', 'Road maintenance request',
            'Training programme approval', 'Budget re-appropriation',
            'Land acquisition correspondence', 'Health camp permission',
            'School furniture distribution', 'Agricultural subsidy list',
            'ICT equipment purchase', 'Meeting minutes circulation',
            'Citizen complaint disposal', 'Vehicle maintenance',
            'Cleanliness campaign', 'Disaster preparedness plan',
        ]
        staff = [self.users['registry'], self.users['eo'],
                 self.users['depthead'], self.users['bookingdesk']]
        departments = list(self.departments.values())
        for index in range(1, 61):
            base = bases[(index - 1) % len(bases)]
            status = ('closed' if index % 10 in (0, 1, 2)
                      else 'archived' if index % 10 == 3
                      else 'in_progress' if index % 10 in (4, 5)
                      else 'open')
            category = ['general', 'procurement', 'legal', 'hr', 'project',
                        'finance'][index % 6]
            priority = 'urgent' if index % 17 == 0 else (
                'high' if index % 5 == 0 else 'normal')
            due = None
            if status in ('open', 'in_progress'):
                due = self._day((index % 25) - 10)
            created = self._at(days=max(0, 50 - index), hours=index % 12)
            document = DocumentFile.objects.create(
                file_no=f'GZP-FL-{self.year}-{index:06d}',
                subject=f'{base} - {self.year} / {index:02d}',
                category=category,
                department=departments[index % len(departments)],
                status=status, priority=priority,
                confidentiality='confidential' if index % 11 == 0 else 'normal',
                received_from=('District office' if index % 3 == 0
                               else 'Upazila office' if index % 3 == 1
                               else 'Citizen application'),
                assigned_to=staff[index % len(staff)],
                created_by=self.users['registry'],
                due_date=due,
                notes='Sample register entry. No real correspondence.',
                created_at=created,
            )
            if index <= 15:
                path = self._write_pdf(
                    f'documents/sample_document_{index:02d}.pdf',
                    f'Document {document.file_no}',
                    [document.subject, f'Category: {category}',
                     f'Department: {document.department}',
                     'Sample attachment for the demo register.'],
                )
                document.attachment = path
                document.save(update_fields=['attachment'])

            FileMovement.objects.create(
                file=document, action='register',
                to_user=self.users['registry'],
                note='Entered in the register', created_at=created,
            )
            if index % 3 == 0:
                FileMovement.objects.create(
                    file=document, action='forward',
                    from_user=self.users['registry'],
                    to_user=document.assigned_to,
                    note='Forwarded for action',
                    created_at=created + timedelta(hours=4),
                )
            if index % 4 == 0:
                FileMovement.objects.create(
                    file=document, action='receive',
                    from_user=document.assigned_to,
                    to_user=self.users['registry'],
                    note='Received back with comments',
                    created_at=created + timedelta(hours=20),
                )
            if status in ('closed', 'archived'):
                FileMovement.objects.create(
                    file=document, action='close',
                    from_user=document.assigned_to,
                    note='Disposed and closed',
                    created_at=created + timedelta(days=2),
                )

        # a handful of files carry a workflow instance for every state
        docs = list(DocumentFile.objects.order_by('created_at')[:6])
        file_states = ['at_eo', 'at_registry', 'approved', 'approved',
                       'returned', 'at_eo']
        template = self.templates['file']
        step_reg = self.steps[('file', 1)]
        step_eo = self.steps[('file', 2)]
        for index, (document, state) in enumerate(zip(docs, file_states), start=1):
            payload = {
                'subject': document.subject, 'amount': 0,
                'url': f'/app/documents/{document.pk}/',
            }
            inst = WorkflowInstance.objects.create(
                template=template, object_type='documents.DocumentFile',
                object_id=document.pk, tracking_id=document.file_no,
                requester=self.users['registry'], payload=payload,
                created_at=document.created_at,
            )
            StepRecord.objects.create(
                instance=inst, actor=self.users['registry'],
                actor_role='registry', decision='submit',
                comments='File submitted for decision',
                created_at=document.created_at,
            )
            t = self._advance(document.created_at, 6)
            if state == 'at_registry':
                inst.current_step = step_reg
                inst.status = 'running'
                inst.save(update_fields=['current_step', 'status'])
                self._workflow_task(inst, step_reg, 'pending', t,
                                    overdue=(index == 1))
            elif state == 'returned':
                self._workflow_task(inst, step_reg, 'completed', t)
                self._workflow_record(inst, step_reg, self.users['registry'],
                                      'return', t, 'Attach the prior approval')
                inst.status = 'returned'
                inst.current_step = step_reg
                inst.note = 'Attach the prior approval'
                inst.save(update_fields=['status', 'current_step', 'note'])
                document.status = 'open'
                document.save(update_fields=['status'])
            elif state == 'approved':
                self._workflow_task(inst, step_reg, 'completed', t)
                self._workflow_record(inst, step_reg, self.users['registry'],
                                      'forward', t, 'Forwarded for approval')
                t = self._advance(t, 8)
                self._workflow_task(inst, step_eo, 'completed', t)
                self._workflow_record(inst, step_eo, self.users['eo'],
                                      'approve', t, 'Approved')
                inst.status = 'approved'
                inst.completed_at = t
                inst.note = 'Approved'
                inst.save(update_fields=['status', 'completed_at', 'note'])
                document.status = 'closed'
                document.save(update_fields=['status'])
            else:  # at_eo
                self._workflow_task(inst, step_reg, 'completed', t)
                self._workflow_record(inst, step_reg, self.users['registry'],
                                      'forward', t, 'Forwarded for approval')
                inst.current_step = step_eo
                inst.status = 'running'
                inst.save(update_fields=['current_step', 'status'])
                self._workflow_task(inst, step_eo, 'pending', t)
                document.status = 'in_progress'
                document.save(update_fields=['status'])

        self.stdout.write('  documents: %d, movements: %d, attachments: %d'
                          % (DocumentFile.objects.count(),
                             FileMovement.objects.count(),
                             DocumentFile.objects.exclude(attachment='').count()))

    # ---------------------------------------------------------------- projects
    def _seed_projects(self):
        specs = [
            ('Rehabilitation of union roads', 'engineering', 12000000, 7800000,
             'ongoing', 65, -180, 60),
            ('Union Digital Centre upgrade', 'ict', 4500000, 2100000,
             'ongoing', 45, -120, 90),
            ('Cyclone shelter repair', 'engineering', 8000000, 8000000,
             'completed', 100, -420, -30),
            ('Upazila health camp equipment', 'health', 2500000, 1900000,
             'ongoing', 75, -90, 30),
            ('School furniture distribution', 'education', 3200000, 1200000,
             'delayed', 35, -150, -10),
            ('Agricultural demonstration plots', 'agriculture', 1800000, 900000,
             'ongoing', 50, -60, 120),
            ('Dakbungalow room renovation', 'engineering', 6000000, 1500000,
             'planning', 10, 15, 180),
            ('District e-office rollout', 'ict', 7500000, 3000000,
             'ongoing', 40, -100, 150),
            ('Market drainage improvement', 'engineering', 9500000, 0,
             'planning', 5, 30, 240),
            ('Community clinic solar power', 'health', 2800000, 2800000,
             'completed', 100, -300, -45),
            ('Tree plantation drive', 'agriculture', 900000, 200000,
             'ongoing', 25, -30, 60),
            ('Office records digitisation', 'admin', 1500000, 0,
             'cancelled', 0, -80, -20),
        ]
        self.projects = []
        for index, (name, dept, budget, spent, status, progress, start, end) in enumerate(
                specs, start=1):
            project = Project.objects.create(
                code=f'GZP-PR-{self.year}-{index:03d}', name=name,
                department=self.departments[dept],
                description=f'Sample project: {name}. Fictional figures for the demo.',
                location='Gazipur District',
                budget=Decimal(budget), spent=Decimal(spent),
                start_date=self._day(start), end_date=self._day(end),
                status=status, progress=progress,
                manager=self.users['projectofficer'],
            )
            self.projects.append(project)
            milestone_titles = [
                'Administrative approval and site handover',
                'Procurement and contractor mobilisation',
                'Implementation and field supervision',
                'Completion, testing and handover',
            ]
            for m_index, title in enumerate(milestone_titles, start=1):
                if status == 'completed':
                    m_status = 'done'
                    completed_on = self._day(start + int((end - start) * m_index / 4))
                elif status == 'planning':
                    m_status = 'pending'
                    completed_on = None
                elif status == 'cancelled':
                    m_status = 'pending'
                    completed_on = None
                elif m_index == 1:
                    m_status = 'done'
                    completed_on = self._day(start + 5)
                elif m_index == 2:
                    m_status = 'in_progress' if progress >= 30 else 'pending'
                    completed_on = None
                else:
                    m_status = 'pending'
                    completed_on = None
                if status == 'delayed' and m_index == 2:
                    m_status = 'slipped'
                Milestone.objects.create(
                    project=project, title=title,
                    due_date=self._day(start + int((end - start) * m_index / 4)),
                    completed_on=completed_on, status=m_status,
                    note='Demo milestone',
                )

        inspection_findings = [
            ('pass', 'Works progressing as scheduled; records available.'),
            ('minor', 'Minor curing issue observed near the eastern wall.'),
            ('pass', 'Materials stored properly and labour registers maintained.'),
            ('fail', 'Drainage slope not as per drawing; rework advised.'),
            ('pass', 'Safety signage and first aid box present.'),
            ('minor', 'Daily progress register needs signatures.'),
            ('pass', 'Completed works verified with the community representative.'),
            ('pass', 'Solar panels installed and tested successfully.'),
            ('minor', 'Furniture inventory partial; balance expected next week.'),
            ('pass', 'Tree plantation survival rate above target.'),
        ]
        for index, (rating, finding) in enumerate(inspection_findings):
            project = self.projects[index % 6]
            Inspection.objects.create(
                project=project, date=self._day(-5 - index * 4),
                inspector=self.users['inspector'],
                location='Field site, Gazipur',
                finding=finding, rating=rating,
                follow_up_date=(self._day(10 + index)
                                if rating != 'pass' else None),
            )

        # project workflow examples
        template = self.templates['project']
        step_po = self.steps[('project', 1)]
        step_eo = self.steps[('project', 2)]
        for index, (project, state) in enumerate(
                [(self.projects[0], 'running'), (self.projects[2], 'approved')]):
            payload = {'subject': project.name, 'amount': float(project.budget),
                       'url': f'/app/projects/{project.pk}/'}
            inst = WorkflowInstance.objects.create(
                template=template, object_type='projects.Project',
                object_id=project.pk,
                tracking_id=f'GZP-PA-{self.year}-{index + 1:06d}',
                requester=self.users['projectofficer'], payload=payload,
                created_at=self._at(days=20 - index),
            )
            StepRecord.objects.create(
                instance=inst, actor=self.users['projectofficer'],
                actor_role='projectofficer', decision='submit',
                comments='Project action submitted',
                created_at=self._at(days=20 - index),
            )
            t = self._advance(self._at(days=19 - index), 8)
            self._workflow_task(inst, step_po, 'completed', t)
            self._workflow_record(inst, step_po, self.users['projectofficer'],
                                  'forward', t, 'Forwarded for approval')
            if state == 'approved':
                t = self._advance(t, 10)
                self._workflow_task(inst, step_eo, 'completed', t)
                self._workflow_record(inst, step_eo, self.users['eo'],
                                      'approve', t, 'Approved')
                inst.status = 'approved'
                inst.completed_at = t
                inst.note = 'Approved'
                inst.save(update_fields=['status', 'completed_at', 'note'])
            else:
                inst.current_step = step_eo
                inst.status = 'running'
                inst.save(update_fields=['current_step', 'status'])
                self._workflow_task(inst, step_eo, 'pending', t)

        self.stdout.write('  projects: %d, milestones: %d, inspections: %d'
                          % (Project.objects.count(), Milestone.objects.count(),
                             Inspection.objects.count()))

    # ---------------------------------------------------------------- meetings
    def _seed_meetings(self):
        specs = [
            ('Monthly coordination meeting', -18, time(10, 0), time(12, 0),
             'Conference room, Parishad office', 'held',
             'Review progress of ongoing projects and pending files.'),
            ('Dakbungalow tariff review', -8, time(11, 0), time(12, 30),
             'Executive Officer chamber', 'held',
             'Review tariff structure and family room demand.'),
            ('Budget review for the next quarter', -2, time(10, 30), time(12, 0),
             'Conference room, Parishad office', 'held',
             'Approve re-appropriation proposals and review expenditure.'),
            ('Weekly coordination with department heads', 0, time(10, 30), time(12, 0),
             'Conference room, Parishad office', 'scheduled',
             'Review the weekly service delivery report and pending decisions.'),
            ('Inter-agency disaster preparedness', 3, time(10, 0), time(11, 30),
             'Conference room, Parishad office', 'scheduled',
             'Coordinate cyclone preparedness with upazila offices.'),
            ('Project steering committee', 8, time(14, 0), time(16, 0),
             'Conference room, Parishad office', 'scheduled',
             'Review project progress and resolve bottlenecks.'),
            ('Records digitisation review', 12, time(11, 0), time(12, 0),
             'Registry room', 'scheduled',
             'Review scanning progress and access controls.'),
            ('Health camp coordination', 18, time(9, 30), time(11, 0),
             'Health office', 'scheduled',
             'Finalise logistics for the upcoming health camp.'),
            ('Year-end procurement planning', 24, time(10, 0), time(12, 0),
             'Conference room, Parishad office', 'cancelled',
             'Cancelled due to the revised procurement calendar.'),
        ]
        attendees = [
            self.users['ceo'], self.users['eo'], self.users['finance'],
            self.users['engineer'], self.users['hradmin'], self.users['depthead'],
            self.users['registry'], self.users['projectofficer'],
        ]
        self.meetings = []
        for index, (title, day_offset, start, end, venue, status, agenda) in enumerate(
                specs, start=1):
            minutes = ''
            if status == 'held':
                minutes = (
                    'The chair reviewed the agenda. Decisions:\n'
                    '1. Departments will submit updated progress by the next week.\n'
                    '2. Pending files older than 30 days will be escalated.\n'
                    '3. Finance will circulate the revised expenditure statement.'
                )
            meeting = Meeting.objects.create(
                title=title, date=self._day(day_offset), start_time=start,
                end_time=end, venue=venue, agenda=agenda, minutes=minutes,
                status=status, chair=self.users['ceo'],
                secretary=self.users['secretary'],
            )
            self.meetings.append(meeting)
            for a_index, user in enumerate(attendees):
                Attendee.objects.create(
                    meeting=meeting, user=user, name=user.display_name,
                    role=user.role_name, present=(status == 'held' and a_index != 5),
                )
            if status == 'held':
                action_specs = [
                    ('Circulate updated project progress', self.users['projectofficer'],
                     -5 + index, 'open'),
                    ('Escalate files older than 30 days', self.users['registry'],
                     -2 + index, 'in_progress'),
                    ('Circulate revised expenditure statement', self.users['finance'],
                     index + 7, 'done'),
                ]
                for description, owner, due_offset, action_status in action_specs:
                    ActionItem.objects.create(
                        meeting=meeting, description=description, owner=owner,
                        owner_label=owner.display_name,
                        due_date=self._day(due_offset), status=action_status,
                        completed_at=self._at(days=1) if action_status == 'done' else None,
                        note='Demo action',
                    )
        self.stdout.write('  meetings: %d, actions: %d'
                          % (Meeting.objects.count(), ActionItem.objects.count()))

    # ----------------------------------------------------------------- support
    def _seed_support(self):
        ticket_specs = [
            ('Cannot upload a supporting document', 'incident', 'high', 'open',
             self.users['citizen1'], 0, -6),
            ('Need access for the new registry officer', 'access', 'medium',
             'acknowledged', self.users['registry'], 1, -12),
            ('Booking reference not found at reception', 'incident', 'critical',
             'in_progress', self.users['reception'], 2, -20),
            ('Refund not showing in the finance list', 'incident', 'high',
             'resolved', self.users['finance'], 3, -34),
            ('Correct spelling of an applicant name', 'data', 'low', 'resolved',
             self.users['bookingdesk'], 4, -40),
            ('Add a new conference hall to Sreepur', 'request', 'medium',
             'in_progress', self.users['eo'], 5, -48),
            ('Password reset for a demo account', 'access', 'low', 'closed',
             self.users['employee1'], 6, -60),
            ('Report export shows an empty file', 'incident', 'medium', 'open',
             self.users['management'], 7, -70),
        ]
        for index, (subject, category, priority, status, requester,
                    owner_index, age) in enumerate(ticket_specs, start=1):
            created = self._at(days=abs(age) // 24, hours=owner_index)
            due = created + timedelta(hours={
                'critical': 2, 'high': 4, 'medium': 8, 'low': 16}[priority] * 3)
            resolved = (created + timedelta(hours=12)
                        if status in ('resolved', 'closed') else None)
            Ticket.objects.create(
                number=f'GZP-ST-{self.year}-{index:04d}', subject=subject,
                description=('Sample support ticket. The user reports: '
                             + subject.lower() + '.'),
                category=category, priority=priority, status=status,
                requester=requester, assignee=self.users['admin'],
                response_due_at=due if status not in ('resolved', 'closed') else None,
                resolution=('Guided the user and confirmed the fix.'
                            if resolved else ''),
                created_at=created, resolved_at=resolved,
            )

        phases = [
            ('Inception and mobilisation', 'Day 1-5',
             'Kick-off, access, environment and plan sign-off', 'done',
             'Adcelerete delivery lead', 10),
            ('Discovery and design', 'Day 6-12',
             'Requirement workshops, process maps and data model', 'done',
             'Business analyst', 20),
            ('Platform core and security', 'Day 13-20',
             'Authentication, roles, audit, notifications and workflow engine',
             'done', 'Technical lead', 30),
            ('Dakbungalow and payments', 'Day 21-30',
             'Availability, booking flow, permits, simulated gateway, reception',
             'done', 'Full-stack team', 40),
            ('Ancillary modules and MIS', 'Day 31-36',
             'HR, documents, projects, meetings, dashboards and reports', 'done',
             'Full-stack team', 50),
            ('UAT, training and go-live', 'Day 37-45',
             'User acceptance testing, training, data load and go-live', 'active',
             'Delivery manager', 60),
        ]
        for phase, window, deliverable, status, owner, order in phases:
            PlanPhase.objects.create(
                phase=phase, window=window, deliverable=deliverable,
                status=status, owner=owner, sort_order=order,
                notes='Sample 45-day delivery plan.',
            )

        deliverables = [
            ('Platform', 'Working demo on the supplied laptop with sample data'),
            ('Platform', 'Source code, requirements file and setup instructions'),
            ('Workflow', 'Database-driven workflow designer and authority matrix'),
            ('Dakbungalow', 'Booking, approval, payment, permit and reception flow'),
            ('Payments', 'Signed callback verification and duplicate handling'),
            ('Reports', 'Executive, department, booking and revenue reports'),
            ('Security', 'Role matrix, audit log, backup and health checks'),
            ('Documentation', 'Requirements traceability and demo script'),
            ('Training', 'Two orientation sessions for nominated officers'),
            ('Support', '36-month support and maintenance commitment'),
        ]
        for index, (area, item) in enumerate(deliverables, start=1):
            ChecklistItem.objects.create(
                kind='deliverable', area=area, item=item,
                status='passed' if index <= 8 else 'pending',
                note='Verified in the demo build' if index <= 8 else '',
                checked_by=self.users['admin'] if index <= 8 else None,
                checked_at=self._at(days=5) if index <= 8 else None,
                sort_order=index * 10,
            )
        uat_items = [
            ('Access', 'Citizen can register, verify and apply for a room'),
            ('Access', 'Management and auditor roles are read-only everywhere'),
            ('Access', 'Admin cannot approve bookings without the approval permission'),
            ('Booking', 'Two applicants cannot hold the same room and dates'),
            ('Workflow', 'Route changes when the amount crosses BDT 20,000'),
            ('Workflow', 'Clarification returns the case to the requester'),
            ('Payments', 'Forged callback is rejected and recorded'),
            ('Payments', 'Duplicate callback does not confirm twice'),
            ('Reception', 'Reference lookup and check-in work at the facility'),
            ('Reports', 'Report access is logged and export permissions are enforced'),
        ]
        for index, (area, item) in enumerate(uat_items, start=1):
            status = 'passed' if index <= 6 else ('failed' if index == 8 else 'pending')
            ChecklistItem.objects.create(
                kind='uat', area=area, item=item, status=status,
                note=('Signed off' if status == 'passed'
                      else 'Retest planned' if status == 'failed' else ''),
                checked_by=self.users['admin'] if status == 'passed' else None,
                checked_at=self._at(days=3) if status == 'passed' else None,
                sort_order=index * 10,
            )

        changes = [
            ('Move the payment window from 12 to 24 hours', 'medium', 'implemented',
             self.users['eo'], 'Approved and configured in Settings.'),
            ('Add a family room at Sreepur', 'high', 'approved',
             self.users['depthead'], 'Approved; to be configured after handover.'),
            ('Add Bangla labels to the public booking page', 'low', 'implemented',
             self.users['secretary'], 'Included in the demo.'),
            ('Connect a live SMS gateway', 'high', 'proposed',
             self.users['finance'], 'Awaiting client decision and SMS credits.'),
        ]
        for index, (title, impact, status, requester, note) in enumerate(
                changes, start=1):
            ChangeRequest.objects.create(
                reference=f'GZP-CR-{self.year}-{index:03d}', title=title,
                description='Sample change request raised during the demo review.',
                impact=impact, status=status, requested_by=requester,
                decision_note=note,
                created_at=self._at(days=30 - index * 5),
                decided_at=self._at(days=20 - index * 4)
                if status != 'proposed' else None,
            )
        self.stdout.write('  support tickets: %d, plan phases: %d, checklists: %d, '
                          'change requests: %d'
                          % (Ticket.objects.count(), PlanPhase.objects.count(),
                             ChecklistItem.objects.count(),
                             ChangeRequest.objects.count()))

    # ---------------------------------------------------------------- bookings
    def _free_start(self, unit, preferred, nights, slot):
        day = preferred
        for _ in range(500):
            days = [day + timedelta(days=i) for i in range(nights)]
            if not InventoryLock.objects.filter(
                    unit=unit, date__in=days, slot=slot,
                    released=False).exists():
                return day
            day += timedelta(days=1)
        raise RuntimeError(f'No free inventory for {unit} from {preferred}')

    def _success_payment(self, booking, when):
        txn = f'GZP-TXN-{when:%Y%m%d%H%M%S}-{random.randint(1000, 9999)}'
        payment = Payment.objects.create(
            booking=booking, txn_id=txn, gateway='Demo gateway',
            amount=booking.total, initiated_at=when,
            raw={'booking': booking.reference, 'amount': str(booking.total)},
        )
        payload = {
            'txn_id': txn, 'booking': booking.reference,
            'amount': str(payment.amount), 'currency': 'BDT',
            'status': 'SUCCESS', 'store_amount': str(payment.amount),
            'nonce': f'{random.getrandbits(48):012x}',
            'gateway_time': when.isoformat(timespec='seconds'),
        }
        signature = gateway.sign_payload(payload)
        payment.status = 'success'
        payment.verified_at = when
        payment.receipt_no = f'GZP-RCP-{booking.reference.split("-")[-1]}'
        payment.signature = signature
        payment.raw = payload
        payment.save()
        PaymentCallback.objects.create(
            payment=payment, txn_id=txn, signature=signature,
            signature_valid=True, kind='SUCCESS', payload=payload,
            result='confirmed', created_at=when,
        )
        return payment

    def _failed_payment(self, booking, when):
        txn = f'GZP-TXN-{when:%Y%m%d%H%M%S}-{random.randint(1000, 9999)}'
        payment = Payment.objects.create(
            booking=booking, txn_id=txn, gateway='Demo gateway',
            amount=booking.total, status='failed', initiated_at=when,
        )
        payload = {
            'txn_id': txn, 'booking': booking.reference,
            'amount': str(payment.amount), 'currency': 'BDT',
            'status': 'FAILED', 'nonce': f'{random.getrandbits(48):012x}',
            'gateway_time': when.isoformat(timespec='seconds'),
        }
        signature = gateway.sign_payload(payload)
        payment.signature = signature
        payment.raw = payload
        payment.save(update_fields=['signature', 'raw'])
        PaymentCallback.objects.create(
            payment=payment, txn_id=txn, signature=signature,
            signature_valid=True, kind='FAILED', payload=payload,
            result='failed', created_at=when,
        )
        return payment

    def _booking_timeline(self, booking, rows):
        previous = 'submitted'
        for to_status, actor, comment, hours in rows:
            when = min(booking.created_at + timedelta(hours=hours),
                       self.now - timedelta(minutes=20))
            BookingStatusChange.objects.create(
                booking=booking, from_status=previous, to_status=to_status,
                actor=actor, comment=comment, created_at=when,
            )
            previous = to_status

    def _booking_instance(self, booking, kind, reject_note='',
                          overdue_first=False):
        template = self.templates['booking']
        payload = {
            'subject': f'{booking.applicant_name} - {booking.facility.name} / '
                       f'{booking.unit.name}',
            'url': f'/bookings/{booking.pk}/',
            'amount': float(booking.total),
            'nights': booking.nights,
            'unit_kind': booking.unit.kind,
            'facility': booking.facility.code,
            'applicant_category': booking.category,
            'slot': booking.slot or 'room',
            'check_in': booking.check_in.isoformat(),
            'check_out': booking.check_out.isoformat(),
        }
        steps = engine.applicable_steps(template, payload)
        instance = WorkflowInstance.objects.create(
            template=template, object_type='bookings.Booking',
            object_id=booking.pk, tracking_id=booking.reference,
            requester=booking.applicant, payload=payload,
            created_at=booking.created_at,
        )
        StepRecord.objects.create(
            instance=instance, actor=booking.applicant, actor_role='citizen',
            decision='submit', comments='Application submitted',
            created_at=booking.created_at,
        )
        actors = {
            'bookingdesk': self.users['bookingdesk'],
            'engineer': self.users['engineer'],
            'eo': self.users['eo'],
            'ceo': self.users['ceo'],
        }
        t = booking.created_at

        def advance(hours=18):
            nonlocal t
            t = min(t + timedelta(hours=hours + random.randint(0, 6)),
                    self.now - timedelta(hours=1))
            return t

        def complete(step, decision, comments=''):
            when = advance()
            self._workflow_task(instance, step, 'completed', when)
            self._workflow_record(instance, step,
                                  actors.get(step.role.code), decision,
                                  when, comments)
            return when

        eo_index = next(
            (i for i, step in enumerate(steps) if step.role.code == 'eo'), -1)

        if kind == 'submitted':
            instance.current_step = steps[0]
            instance.status = 'running'
            instance.save(update_fields=['current_step', 'status'])
            self._workflow_task(instance, steps[0], 'pending',
                                booking.created_at,
                                overdue=overdue_first)
            return

        if kind == 'under_review':
            complete(steps[0], 'forward', 'Completeness check passed')
            instance.current_step = steps[1]
            instance.status = 'running'
            instance.save(update_fields=['current_step', 'status'])
            self._workflow_task(instance, steps[1], 'pending', t)
            return

        if kind.startswith('clarification'):
            if len(steps) > 1 and kind == 'clarification_engineer':
                complete(steps[0], 'forward', 'Completeness check passed')
                when = advance()
                self._workflow_task(instance, steps[1], 'completed', when)
                self._workflow_record(
                    instance, steps[1], actors['engineer'], 'correct', when,
                    'Please upload the structural clearance certificate')
                instance.current_step = steps[1]
                instance.note = 'Please upload the structural clearance certificate'
            else:
                when = advance()
                self._workflow_task(instance, steps[0], 'completed', when)
                self._workflow_record(
                    instance, steps[0], actors['bookingdesk'], 'correct', when,
                    'Please upload a clearer copy of the national ID')
                instance.current_step = steps[0]
                instance.note = 'Please upload a clearer copy of the national ID'
            instance.status = 'returned'
            instance.save(update_fields=['current_step', 'status', 'note'])
            return

        if kind.startswith('recommended'):
            for index in range(max(1, eo_index)):
                step = steps[index]
                decision = ('recommend' if step.role.code in ('engineer', 'eo')
                            else 'forward')
                complete(step, decision, 'Review completed')
            if kind == 'recommended_ceo':
                complete(steps[eo_index], 'recommend',
                         'Recommended; amount exceeds the delegated limit')
                instance.current_step = steps[eo_index + 1]
            else:
                instance.current_step = steps[eo_index]
            instance.status = 'running'
            instance.save(update_fields=['current_step', 'status'])
            self._workflow_task(instance, instance.current_step, 'pending', t)
            return

        if kind == 'approved':
            for index, step in enumerate(steps):
                if index == len(steps) - 1:
                    complete(step, 'approve', 'Final approval recorded')
                else:
                    decision = ('recommend' if step.role.code in ('engineer', 'eo')
                                else 'forward')
                    complete(step, decision, 'Reviewed and forwarded')
            instance.status = 'approved'
            instance.current_step = None
            instance.completed_at = t
            instance.note = 'Approved'
            instance.save(update_fields=['status', 'current_step',
                                         'completed_at', 'note'])
            return

        if kind.startswith('rejected'):
            if kind == 'rejected_desk':
                reject_index = 0
            elif kind == 'rejected_eo':
                reject_index = eo_index
            else:
                reject_index = len(steps) - 1
            for index in range(reject_index):
                step = steps[index]
                decision = ('recommend' if step.role.code in ('engineer', 'eo')
                            else 'forward')
                complete(step, decision, 'Reviewed and forwarded')
            when = advance()
            self._workflow_task(instance, steps[reject_index], 'completed', when)
            self._workflow_record(
                instance, steps[reject_index],
                actors.get(steps[reject_index].role.code), 'reject', when,
                reject_note or 'Not approved')
            instance.status = 'rejected'
            instance.current_step = None
            instance.completed_at = when
            instance.note = (reject_note or 'Not approved')[:255]
            instance.save(update_fields=['status', 'current_step',
                                         'completed_at', 'note'])
            return

        if kind == 'cancelled_review':
            self._workflow_task(instance, steps[0], 'cancelled', booking.created_at)
            instance.status = 'cancelled'
            instance.current_step = None
            instance.completed_at = self._at(days=2)
            instance.note = 'Cancelled by the applicant before approval'
            instance.save(update_fields=['status', 'current_step',
                                         'completed_at', 'note'])

    def _booking_locks(self, booking):
        days = [booking.check_in + timedelta(days=i)
                for i in range((booking.check_out - booking.check_in).days)]
        slot = booking.slot if booking.unit.is_hall else ''
        released = booking.status in ('cancelled', 'rejected', 'expired')
        if booking.status in ('submitted', 'under_review', 'clarification',
                              'recommended', 'approved'):
            hold = booking.hold_expires_at or (self.now + timedelta(hours=48))
        elif booking.status == 'awaiting_payment':
            hold = booking.payment_deadline
        else:
            hold = None
        for day in days:
            InventoryLock.objects.create(
                unit=booking.unit, date=day, slot=slot, booking=booking,
                hold_expires_at=hold, released=released,
                created_at=booking.created_at,
            )

    def _refund(self, booking, payment, status, percent, when):
        amount = (booking.total * percent / Decimal('100')).quantize(
            Decimal('0.01'))
        refund = Refund.objects.create(
            booking=booking, payment=payment, amount=amount, percent=percent,
            reason='Applicant cancelled the booking',
            status=status, requested_by=booking.applicant,
            created_at=when,
        )
        booking.refund_percent = percent
        booking.refund_amount = amount
        booking.refund_requested_at = when
        if status == 'processed':
            refund.processed_by = self.users['finance']
            refund.processed_at = when + timedelta(hours=6)
            refund.gateway_ref = f'GZP-RFD-{random.getrandbits(32):08X}'
            refund.save(update_fields=['processed_by', 'processed_at',
                                       'gateway_ref'])
            payment.status = 'refunded'
            payment.refunded_amount = amount
            payment.refunded_at = when + timedelta(hours=6)
            payment.save(update_fields=['status', 'refunded_amount',
                                        'refunded_at'])
            booking.refund_status = 'processed'
        else:
            booking.refund_status = 'requested'
        booking.save(update_fields=['refund_status', 'refund_percent',
                                    'refund_amount', 'refund_requested_at'])

    def _seed_bookings(self):
        specs = [
            # unit, category, status, nights, slot, purpose, kind, flags
            ('gazipur-sadar/R1', 'citizen', 'paid', 2, '',
             'Family visit during winter vacation', 'approved', {'offset': 1}),
            ('gazipur-sadar/R2', 'citizen', 'paid', 2, '',
             'Official training at Gazipur', 'approved',
             {'offset': 0, 'checked_in': True}),
            ('kapasia/R2', 'government', 'paid', 3, '',
             'Divisional inspection team', 'approved', {'offset': -1}),
            ('sreepur/S2', 'organization', 'completed', 2, '',
             'Official delegation stay', 'approved',
             {'offset': -2, 'completed': True}),
            ('gazipur-sadar/R3', 'citizen', 'completed', 2, '',
             'Wedding family stay', 'approved', {'offset': -3, 'completed': True}),
            ('sreepur/R1', 'citizen', 'paid', 1, '',
             'Weekend visit to relatives', 'approved',
             {'failed_attempt': True, 'duplicate': True}),
            ('kaliakair/S1', 'government', 'paid', 2, '',
             'Official inspection visit', 'approved', {}),
            ('kapasia/R1', 'organization', 'paid', 2, '',
             'NGO field coordination', 'approved', {}),
            ('gazipur-sadar/S1', 'organization', 'paid', 5, '',
             'Government delegation accommodation', 'approved', {}),
            ('sreepur/H1', 'government', 'paid', 1, 'evening',
             'District training closing ceremony', 'approved', {}),
            ('gazipur-sadar/S2', 'organization', 'awaiting_payment', 6, '',
             'Donor delegation accommodation', 'approved',
             {'deadline_hours': 18, 'supporting_doc': True}),
            ('sreepur/R2', 'citizen', 'awaiting_payment', 1, '',
             'Personal visit', 'approved', {'deadline_hours': 8}),
            ('kaliakair/R1', 'government', 'awaiting_payment', 2, '',
             'Sub-registry inspection', 'approved', {'deadline_hours': -3}),
            ('kapasia/H1', 'organization', 'awaiting_payment', 1, 'morning',
             'Community consultation', 'approved', {'deadline_hours': 20}),
            ('gazipur-sadar/S1', 'government', 'awaiting_payment', 3, '',
             'Divisional review team', 'approved', {'deadline_hours': 10}),
            ('gazipur-sadar/R1', 'citizen', 'approved', 1, '',
             'Short family visit', 'approved', {'deadline_hours': 20}),
            ('sreepur/S1', 'citizen', 'submitted', 2, '',
             'Anniversary trip', 'submitted', {}),
            ('kapasia/R2', 'government', 'submitted', 1, '',
             'Field office visit', 'submitted', {}),
            ('gazipur-sadar/H1', 'organization', 'submitted', 1, 'afternoon',
             'Training workshop', 'submitted', {}),
            ('kaliakair/R2', 'citizen', 'submitted', 2, '',
             'Family gathering', 'submitted', {}),
            ('sreepur/S2', 'government', 'under_review', 2, '',
             'Official guest accommodation', 'under_review', {}),
            ('gazipur-sadar/S1', 'organization', 'under_review', 2, '',
             'Partner organisation visit', 'under_review', {}),
            ('kaliakair/H1', 'citizen', 'under_review', 1, 'morning',
             'Community meeting', 'under_review', {}),
            ('kapasia/R3', 'citizen', 'under_review', 2, '',
             'Visiting family', 'under_review', {}),
            ('sreepur/R3', 'citizen', 'clarification', 1, '',
             'Business trip', 'clarification_desk', {}),
            ('gazipur-sadar/R2', 'organization', 'clarification', 2, '',
             'NGO training participants', 'clarification_desk',
             {'message': True}),
            ('kaliakair/S1', 'government', 'clarification', 3, '',
             'Inter-district delegation', 'clarification_engineer', {}),
            ('gazipur-sadar/R3', 'citizen', 'recommended', 2, '',
             'Family holiday', 'recommended', {'message': True}),
            ('kapasia/R1', 'citizen', 'recommended', 1, '',
             'Attending a wedding', 'recommended', {}),
            ('sreepur/S1', 'organization', 'recommended', 7, '',
             'International delegation', 'recommended_ceo', {}),
            ('gazipur-sadar/R2', 'citizen', 'rejected', 2, '',
             'Extended family stay', 'rejected_desk',
             {'reject_note': 'The facility is reserved for official duty '
                             'during these dates.'}),
            ('kaliakair/R1', 'government', 'rejected', 2, '',
             'Personal visit', 'rejected_eo',
             {'reject_note': 'Personal use of an official guesthouse is not '
                             'permitted under the sample policy.'}),
            ('sreepur/S2', 'organization', 'rejected', 5, '',
             'Corporate retreat', 'rejected_ceo',
             {'reject_note': 'The request exceeds the approved delegation for '
                             'this period.'}),
            ('gazipur-sadar/R1', 'citizen', 'cancelled', 1, '',
             'Short stay', 'cancelled_review',
             {'cancel_reason': 'Plans changed before approval.'}),
            ('kapasia/R2', 'citizen', 'cancelled', 2, '',
             'Family visit', 'approved',
             {'refund': 'requested', 'cancel_reason': 'Family emergency.'}),
            ('sreepur/R3', 'government', 'cancelled', 2, '',
             'Official visit', 'approved',
             {'refund': 'processed', 'cancel_reason': 'Office programme revised.'}),
            ('kaliakair/R2', 'citizen', 'completed', 2, '',
             'Family trip', 'approved', {'offset': -8, 'completed': True}),
            ('sreepur/R4', 'government', 'completed', 1, '',
             'Inspection stay', 'approved', {'offset': -14, 'completed': True}),
            ('kapasia/R1', 'organization', 'completed', 2, '',
             'Training participants', 'approved',
             {'offset': -20, 'completed': True}),
            ('gazipur-sadar/R3', 'citizen', 'expired', 1, '',
             'Weekend visit', 'approved',
             {'deadline_hours': -18, 'failed_attempt': True}),
            ('sreepur/R1', 'government', 'expired', 2, '',
             'Official visit', 'approved', {'deadline_hours': -36}),
            ('gazipur-sadar/S2', 'citizen', 'paid', 1, '',
             'Anniversary stay', 'approved', {}),
            ('gazipur-sadar/R1', 'citizen', 'submitted', 2, '',
             'Family visit', 'submitted', {'overdue_task': True}),
        ]
        counter = 0
        applicant_index = 0
        for spec in specs:
            unit_key, category, status, nights, slot, purpose, kind, flags = spec
            facility_code = unit_key.split('/')[0]
            facility = self.facilities[facility_code]
            unit = self.units[unit_key]
            if unit.is_hall:
                nights = 1
                slot = slot or random.choice(HALL_SLOTS)
            else:
                slot = ''
            if 'offset' in flags:
                preferred = self._day(flags['offset'])
            else:
                counter += 1
                preferred = self._day(1 + counter * 2)
            start = self._free_start(unit, preferred, nights, slot)
            end = start + timedelta(days=nights)
            applicant = self.users[
                'citizen1' if applicant_index % 2 == 0 else 'citizen2']
            applicant_index += 1
            price = availability.quote(unit, category, start, end, slot)
            created_at = self._at(days=random.randint(2, 25),
                                  hours=random.randint(0, 10))
            booking = Booking.objects.create(
                applicant=applicant, facility=facility, unit=unit,
                category=category, check_in=start, check_out=end, slot=slot,
                guests=min(unit.capacity, random.randint(1, 4)),
                purpose=purpose, contact_phone=applicant.phone,
                notes='Sample application for the demo.',
                status=status,
                amount=price['charges'], deposit=price['deposit'],
                gateway_charge=price['gateway_charge'], total=price['total'],
                price_breakdown=price['lines'],
                created_at=created_at,
            )

            deadline = None
            payment_deadline = None
            if status in ('awaiting_payment', 'approved'):
                payment_deadline = self.now + timedelta(
                    hours=flags.get('deadline_hours', 24))
                booking.payment_deadline = payment_deadline
            elif status == 'expired':
                payment_deadline = self.now + timedelta(
                    hours=flags.get('deadline_hours', -12))
                booking.payment_deadline = payment_deadline
            if status in ('submitted', 'under_review', 'clarification',
                          'recommended'):
                booking.hold_expires_at = self.now + timedelta(hours=48)
            elif status in ('awaiting_payment', 'approved'):
                booking.hold_expires_at = payment_deadline
            else:
                booking.hold_expires_at = None
            if status in ('approved', 'awaiting_payment', 'paid', 'completed',
                          'expired'):
                booking.approved_at = created_at + timedelta(hours=30)
            if status == 'rejected':
                booking.rejected_at = created_at + timedelta(hours=30)
                booking.rejection_reason = flags.get(
                    'reject_note', 'Not approved')[:255]
            if status == 'cancelled':
                booking.cancelled_at = self._at(days=1)
                booking.cancelled_by = (applicant if flags.get('refund')
                                        else self.users['bookingdesk'])
                booking.cancellation_reason = flags.get(
                    'cancel_reason', 'Cancelled')[:255]
            booking.save()

            self._booking_locks(booking)
            self._booking_instance(
                booking, kind, flags.get('reject_note', ''),
                overdue_first=bool(flags.get('overdue_task')))

            # booking status timeline
            desk = self.users['bookingdesk']
            eo = self.users['eo']
            ceo = self.users['ceo']
            rows = []
            if status in ('under_review', 'clarification', 'recommended',
                          'approved', 'awaiting_payment', 'paid', 'completed',
                          'expired'):
                rows.append(('under_review', desk,
                             'Completeness check passed', 8))
            if status in ('clarification',):
                rows.append(('clarification', desk,
                             'Correction requested', 18))
            if status in ('recommended', 'approved', 'awaiting_payment',
                          'paid', 'completed', 'expired'):
                rows.append(('recommended', eo,
                             'Recommended by the reviewing officer', 22))
            if status in ('approved', 'awaiting_payment', 'paid', 'completed',
                          'expired'):
                final_actor = (ceo if booking.total > Decimal('20000')
                               else eo)
                rows.append(('approved', final_actor,
                             'Final approval recorded', 34))
                rows.append(('awaiting_payment', None,
                             'Payment window opened', 35))
            if status in ('paid', 'completed'):
                rows.append(('paid', None,
                             'Payment verified by gateway callback', 40))
            if status == 'completed':
                rows.append(('completed', self.users['reception'],
                             'Checked out at reception', 60))
            if status == 'rejected':
                rows.append(('under_review', desk,
                             'Completeness check passed', 8))
                reject_actor = (desk if kind == 'rejected_desk'
                                else ceo if kind == 'rejected_ceo' else eo)
                rows.append(('rejected', reject_actor,
                             flags.get('reject_note', 'Not approved'), 30))
            if status == 'cancelled':
                if flags.get('refund'):
                    final_actor = (ceo if booking.total > Decimal('20000')
                                   else eo)
                    rows.extend([
                        ('under_review', desk, 'Completeness check passed', 8),
                        ('recommended', eo, 'Recommended', 22),
                        ('approved', final_actor, 'Final approval recorded', 34),
                        ('awaiting_payment', None, 'Payment window opened', 35),
                        ('paid', None, 'Payment verified by gateway callback', 40),
                        ('cancelled', applicant,
                         flags.get('cancel_reason', 'Cancelled'), 55),
                    ])
                else:
                    rows.extend([
                        ('under_review', desk, 'Completeness check passed', 8),
                        ('cancelled', applicant,
                         flags.get('cancel_reason', 'Cancelled'), 16),
                    ])
            if status == 'expired':
                rows.append(('expired', None,
                             'Payment window expired; inventory released', 75))
            self._booking_timeline(booking, rows)

            paid_when = min(created_at + timedelta(hours=41),
                            self.now - timedelta(hours=2))
            if status in ('paid', 'completed') or flags.get('refund'):
                if flags.get('failed_attempt'):
                    self._failed_payment(booking, paid_when - timedelta(hours=3))
                payment = self._success_payment(booking, paid_when)
                booking.permit_no = booking.reference.replace(
                    'GZP-DB', 'GZP-PRM')
                booking.permit_issued_at = paid_when
                booking.payment_deadline = None
                booking.hold_expires_at = None
                booking.save(update_fields=['permit_no', 'permit_issued_at',
                                            'payment_deadline',
                                            'hold_expires_at'])
                if flags.get('duplicate'):
                    PaymentCallback.objects.create(
                        payment=payment, txn_id=payment.txn_id,
                        signature=payment.signature, signature_valid=True,
                        kind='SUCCESS', payload=payment.raw,
                        result='duplicate',
                        created_at=paid_when + timedelta(minutes=5),
                    )
                if flags.get('refund') == 'requested':
                    self._refund(booking, payment, 'requested',
                                 Decimal('100.00'), self._at(days=1))
                elif flags.get('refund') == 'processed':
                    self._refund(booking, payment, 'processed',
                                 Decimal('100.00'), self._at(days=2))
                if status == 'completed':
                    booking.checked_in_at = self._at(days=4, hours=2)
                    booking.checked_out_at = self._at(days=2, hours=1)
                    booking.checked_in_by = self.users['reception']
                    booking.save(update_fields=['checked_in_at',
                                                'checked_out_at',
                                                'checked_in_by'])
                elif flags.get('checked_in'):
                    booking.checked_in_at = self.now - timedelta(hours=2)
                    booking.checked_in_by = self.users['reception']
                    booking.save(update_fields=['checked_in_at',
                                                'checked_in_by'])
            elif status == 'expired':
                if flags.get('failed_attempt'):
                    self._failed_payment(
                        booking, self.now - timedelta(hours=24))
                booking.hold_expires_at = None
                booking.save(update_fields=['hold_expires_at'])

            # a couple of citizen/desk messages for realism
            if flags.get('message'):
                BookingMessage.objects.create(
                    booking=booking, author=applicant,
                    body='I have attached the requested document. Please let me '
                         'know if anything else is needed.',
                    created_at=self._at(days=1, hours=3),
                )
                BookingMessage.objects.create(
                    booking=booking, author=self.users['bookingdesk'],
                    body='Thank you. The document is under review and we will '
                         'update you shortly.',
                    created_at=self._at(days=1, hours=1),
                )
            if flags.get('supporting_doc'):
                path = self._write_pdf(
                    f'bookings/supporting_{booking.pk:03d}.pdf',
                    'Supporting document (sample)',
                    [f'Booking {booking.reference}',
                     f'Applicant: {booking.applicant_name}',
                     f'Facility: {facility.name} / {unit.name}',
                     'This is a sample supporting document.'],
                )
                BookingDocument.objects.create(
                    booking=booking, label='Organisation request letter (sample)',
                    file=path, kind='supporting', uploaded_by=applicant,
                    uploaded_at=booking.created_at,
                )

            # add one forged callback so the reconciliation screen has evidence
            success = booking.payments.filter(status='success').first()
            if success and success == booking.payments.first():
                forged = dict(success.raw)
                forged['nonce'] = 'forged-nonce'
                PaymentCallback.objects.create(
                    payment=success, txn_id=success.txn_id,
                    signature='forged-signature', signature_valid=False,
                    kind='SUCCESS', payload=forged, result='rejected',
                    created_at=self._at(days=1, hours=5),
                )

        # show today's collection on the executive dashboard
        latest = Payment.objects.filter(status='success').order_by(
            '-verified_at').first()
        if latest:
            latest.verified_at = self.now - timedelta(hours=2)
            latest.initiated_at = self.now - timedelta(hours=2, minutes=12)
            latest.save(update_fields=['verified_at', 'initiated_at'])

        self.stdout.write(
            '  bookings: %d, locks: %d, payments: %d, refunds: %d'
            % (Booking.objects.count(), InventoryLock.objects.count(),
               Payment.objects.count(), Refund.objects.count()))

    # ----------------------------------------------------- notifications + audit
    def _seed_communications(self):
        notes = []
        citizen1 = self.users['citizen1']
        citizen2 = self.users['citizen2']
        bookings = list(Booking.objects.order_by('created_at'))
        for booking in bookings[:6]:
            notes.append((
                booking.applicant,
                f'Update on {booking.reference}',
                f'Booking {booking.reference} at {booking.facility.name} is '
                f'now {booking.status_label}.',
                f'/bookings/{booking.pk}/', 'status_update',
                booking.created_at + timedelta(hours=2),
            ))
        for booking in bookings[-5:]:
            notes.append((
                self.users['bookingdesk'],
                f'New task: booking desk review ({booking.reference})',
                'A new booking application is waiting for completeness review.',
                '/app/tasks/?status=pending', 'task_assigned',
                booking.created_at + timedelta(hours=1),
            ))
        notes.extend([
            (self.users['ceo'],
             'Approval waiting at your desk',
             'A booking application needs the final approval today.',
             '/app/tasks/?status=pending', 'task_assigned', self._at(hours=2)),
            (self.users['ceo'],
             'Meeting today: Weekly coordination with department heads',
             'Starts at 10:30 AM in the conference room, Parishad office.',
             '/app/meetings/', 'reminder', self._at(hours=5)),
            (self.users['ceo'],
             'Revenue summary for November',
             'This month\u2019s collections and pending payments are ready in the '
             'executive summary.', '/app/mis/', 'status_update',
             self._at(days=1, hours=2)),
            (self.users['admin'],
             'Nightly backup completed',
             'The database backup finished and the integrity check passed.',
             '/app/security/', 'status_update', self._at(hours=3)),
            (self.users['admin'],
             'System health summary',
             'No errors were recorded in the last 24 hours.',
             '/app/health/', 'status_update', self._at(hours=7)),
            (self.users['reception'],
             'Upcoming confirmed stays', 'Three confirmed bookings are due in '
             'the next three days at Gazipur Sadar.', '/app/reception/',
             'status_update', self._at(days=1)),
            (self.users['finance'],
             'Refund request awaiting action', 'A cancellation refund is '
             'awaiting finance processing.', '/app/refunds/',
             'refund_update', self._at(hours=5)),
            (self.users['eo'],
             'Task reminder', 'A booking approval task is due today.',
             '/app/tasks/', 'reminder', self._at(hours=8)),
            (self.users['engineer'],
             'Technical review pending', 'A suite booking needs a facility '
             'readiness check.', '/app/tasks/', 'task_assigned',
             self._at(days=1, hours=2)),
            (self.users['hradmin'],
             'Leave applications pending', 'Two leave applications are waiting '
             'for HR approval.', '/app/hr/leave/', 'task_assigned',
             self._at(hours=6)),
            (self.users['registry'],
             'Files forwarded', 'Two files were forwarded for your review.',
             '/app/documents/', 'status_update', self._at(days=2)),
            (self.users['management'],
             'Monthly report ready', 'The monthly booking and revenue report is '
             'ready for review.', '/app/mis/bookings/', 'status_update',
             self._at(days=5)),
            (citizen1, 'Permit ready', 'Your permit is available to download.',
             '/bookings/', 'permit_ready', self._at(days=3)),
            (citizen2, 'Payment receipt', 'Your demo payment was verified.',
             '/bookings/', 'payment_receipt', self._at(days=4)),
        ])
        for index, (user, subject, body, url, code, created) in enumerate(notes):
            Notification.objects.create(
                user=user, channel='inapp', subject=subject, body=body,
                url=url, template_code=code, created_at=created,
                read_at=(created + timedelta(hours=2)
                         if index % 3 == 0 else None),
            )

        for index, (user, subject, body, url, code, created) in enumerate(notes[:18]):
            if user.email:
                OutboxMessage.objects.create(
                    channel='email', recipient=user.email, subject=subject,
                    body=body, template_code=code, created_at=created,
                    simulated=True,
                )
            if user.phone and index % 2 == 0:
                OutboxMessage.objects.create(
                    channel='sms', recipient=user.phone,
                    subject=subject[:160], body=body, template_code=code,
                    created_at=created, simulated=True,
                )
        self.stdout.write('  notifications: %d, outbox: %d'
                          % (Notification.objects.count(),
                             OutboxMessage.objects.count()))

    def _seed_audit(self):
        entries = [
            ('admin', 'settings', 'core', 'app_name',
             'Application name reviewed for the demo', 40),
            ('admin', 'create', 'accounts', 'bookingdesk',
             'Demo account created', 38),
            ('admin', 'settings', 'accounts', 'management role',
             'Management role confirmed read-only', 36),
            ('ceo', 'decision', 'bookings', 'Booking approval',
             'Final approval recorded within delegation', 34),
            ('eo', 'decision', 'bookings', 'Booking approval',
             'Approved a booking within BDT 20,000', 33),
            ('bookingdesk', 'update', 'bookings', 'Application review',
             'Completeness check completed', 32),
            ('engineer', 'update', 'bookings', 'Technical review',
             'Facility readiness confirmed', 31),
            ('finance', 'payment', 'payments', 'Gateway payment',
             'Payment verified from a signed callback', 30),
            ('finance', 'payment', 'payments', 'Refund processed',
             'Sample refund processed in the demo gateway', 29),
            ('finance', 'payment', 'payments', 'Callback rejected',
             'Forged callback rejected and recorded', 28),
            ('reception', 'verify', 'bookings', 'Check-in',
             'Guest checked in after reference verification', 27),
            ('reception', 'verify', 'bookings', 'Check-out',
             'Booking marked completed at reception', 26),
            ('hradmin', 'create', 'hr', 'Employee record',
             'Employee record added', 25),
            ('supervisor', 'decision', 'hr', 'Leave recommendation',
             'Leave recommended to HR', 24),
            ('hradmin', 'decision', 'hr', 'Leave approval',
             'Leave approved', 23),
            ('registry', 'move', 'documents', 'File movement',
             'File forwarded to the Executive Officer', 22),
            ('registry', 'move', 'documents', 'File received',
             'File received back with comments', 21),
            ('eo', 'decision', 'documents', 'File decision',
             'File closed after approval', 20),
            ('projectofficer', 'update', 'projects', 'Progress update',
             'Project progress updated to 65 percent', 19),
            ('inspector', 'create', 'projects', 'Field inspection',
             'Inspection recorded with a minor observation', 18),
            ('secretary', 'create', 'meetings', 'Meeting scheduled',
             'Meeting scheduled with agenda', 17),
            ('secretary', 'update', 'meetings', 'Minutes recorded',
             'Minutes and action items recorded', 16),
            ('hradmin', 'update', 'hr', 'Attendance',
             'Attendance sheet finalised', 15),
            ('management', 'export', 'mis', 'Report export',
             'Monthly report exported as CSV', 14),
            ('management', 'login', 'accounts', 'Login',
             'Read-only management session', 13),
            ('admin', 'backup', 'core', 'Backup',
             'On-demand backup created', 12),
            ('admin', 'verify', 'core', 'Backup',
             'Restore test passed with PRAGMA integrity_check', 11),
            ('bookingdesk', 'export', 'bookings', 'Booking export',
             'Booking list exported', 10),
            ('citizen1', 'create', 'bookings', 'Booking application',
             'Application submitted', 9),
            ('citizen2', 'create', 'bookings', 'Booking application',
             'Application submitted', 8),
            ('finance', 'export', 'payments', 'Payment export',
             'Payment list exported', 7),
            ('admin', 'settings', 'notifications', 'Notification template',
             'Template body reviewed', 6),
            ('admin', 'update', 'accounts', 'Role matrix',
             'Permission matrix reviewed', 5),
            ('eo', 'decision', 'workflow', 'Workflow task',
             'Task approved at the Executive Officer step', 4),
            ('ceo', 'decision', 'workflow', 'Workflow task',
             'Task approved at the final step', 3),
            ('bookingdesk', 'logout', 'accounts', 'Logout',
             'Session ended', 2),
            ('admin', 'login', 'accounts', 'Login',
             'Administrator signed in', 1),
            ('registry', 'update', 'documents', 'Register entry',
             'Register note added', 1),
            ('finance', 'update', 'payments', 'Reconciliation',
             'Expired holds released', 0),
        ]
        for index, (username, action, module, repr_text, changes, days) in enumerate(
                entries):
            user = self.users.get(username)
            AuditEntry.objects.create(
                actor=user,
                actor_label=user.display_name if user else 'system',
                action=action, module=module,
                model=f'{module}.sample', object_id=str(index + 1),
                object_repr=repr_text,
                changes=changes,
                ip=f'127.0.0.1' if index % 2 == 0 else '192.168.10.24',
                created_at=self._at(days=days, hours=index % 9),
            )
        reports = [
            ('executive', 'Executive dashboard', 5),
            ('booking_report', 'Booking and revenue report', 4),
            ('department', 'Department dashboard', 3),
            ('workflow', 'Workflow performance', 2),
            ('booking_report', 'Booking and revenue report', 1),
            ('executive', 'Executive dashboard', 0),
        ]
        users = [self.users['ceo'], self.users['management'],
                 self.users['admin'], self.users['finance']]
        for index, (report, label, days) in enumerate(reports):
            ReportAccessLog.objects.create(
                user=users[index % len(users)], report=report,
                parameters={'label': label, 'from': 'demo'},
                ip='127.0.0.1', created_at=self._at(days=days, hours=index),
            )
        self.stdout.write('  audit entries: %d, report access logs: %d'
                          % (AuditEntry.objects.count(),
                             ReportAccessLog.objects.count()))

    def _seed_health(self):
        events = [
            ('info', 'Application started', '/'),
            ('info', 'Database connectivity check passed', '/health/'),
            ('info', 'Vendored static assets loaded', '/static/'),
            ('warning', 'Payment callback with an invalid signature was '
             'rejected (sample)', '/payments/'),
            ('info', 'Backup completed', '/security/'),
            ('warning', 'Two workflow tasks are overdue and awaiting escalation',
             '/app/tasks/'),
            ('info', 'Report export completed', '/app/mis/reports/'),
            ('info', 'Nightly maintenance placeholder completed', '/health/'),
        ]
        for index, (kind, message, path) in enumerate(events):
            HealthEvent.objects.create(
                kind=kind, message=message, path=path,
                created_at=self._at(days=index // 2, hours=index + 1),
            )
        self.stdout.write('  health events: %d' % HealthEvent.objects.count())

    # ------------------------------------------------------------------ backup
    def _create_backup(self):
        folder = Path(settings.BASE_DIR) / 'backups'
        folder.mkdir(exist_ok=True)
        stamp = timezone.localtime().strftime('%Y%m%d-%H%M%S')
        target = folder / f'gzp-backup-{stamp}.sqlite3'
        try:
            source = sqlite3.connect(str(settings.DATABASES['default']['NAME']))
            dest = sqlite3.connect(str(target))
            try:
                source.backup(dest)
            finally:
                dest.close()
                source.close()
            check = sqlite3.connect(str(target))
            try:
                ok = check.execute('PRAGMA integrity_check').fetchone()[0]
            finally:
                check.close()
            admin = self.users.get('admin')
            BackupRecord.objects.create(
                filename=target.name, size_bytes=target.stat().st_size,
                created_by=admin, verified=ok == 'ok',
                verified_at=timezone.now() if ok == 'ok' else None,
                note=f'Seed backup; integrity check: {ok}',
            )
            self.stdout.write('  backup: %s (%d KB, integrity %s)'
                              % (target.name, target.stat().st_size // 1024, ok))
        except Exception as exc:  # pragma: no cover - environment dependent
            self.stdout.write(self.style.WARNING(f'  backup skipped: {exc}'))

    # ---------------------------------------------------------------- summary
    def _summarise(self):
        from payments.models import Payment as P

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Demo data ready.'))
        self.stdout.write(
            '  users=%d  facilities=%d  units=%d  bookings=%d  payments=%d'
            % (User.objects.count(), Facility.objects.count(), Unit.objects.count(),
               Booking.objects.count(), P.objects.count()))
        self.stdout.write(
            '  employees=%d  projects=%d  meetings=%d  documents=%d  tickets=%d'
            % (Employee.objects.count(), Project.objects.count(),
               Meeting.objects.count(), DocumentFile.objects.count(),
               Ticket.objects.count()))
        self.stdout.write(
            '  workflow instances=%d  tasks=%d  notifications=%d  audit=%d'
            % (WorkflowInstance.objects.count(), WorkflowTask.objects.count(),
               Notification.objects.count(), AuditEntry.objects.count()))
        self.stdout.write('')
        self.stdout.write('Sign in at /login/ with any demo account and '
                          'password %s.' % DEMO_PASSWORD)
        self.stdout.write('Example: citizen1 / %s, or admin / %s.'
                          % (DEMO_PASSWORD, DEMO_PASSWORD))
