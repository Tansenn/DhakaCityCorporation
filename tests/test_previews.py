from datetime import timedelta
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlsplit

from django.core.paginator import Page
from django.db import connection
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from audit.models import AuditEntry
from core.models import AppSetting, BackupRecord, HealthEvent
from core.utils import paginate
from core.views import (
    _admin_summary, _application_summary, _approval_summary,
    _attendance_summary, _mail_summary, _meeting_summary,
)
from hr.models import Attendance, Department, Employee, LeaveRequest, TrainingRecord
from meetings.models import ActionItem, Meeting
from notifications.models import Notification
from support.models import ChangeRequest, ChecklistItem, PlanPhase, Ticket
from workflow.models import WorkflowInstance, WorkflowStep, WorkflowTask, WorkflowTemplate

from .factories import booking, facility, role, unit, user


class Links(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.urls = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.urls.append(dict(attrs).get('href', ''))


class PaginationPreviewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Employee.objects.bulk_create([
            Employee(employee_no=f'P{i:02}', name=f'Preview {i}') for i in range(37)
        ])

    def test_default_pages_keep_every_record_reachable(self):
        rows = Employee.objects.all()
        for normal_size in (10, 20, 25, 30):
            with self.subTest(normal_size=normal_size):
                first = paginate(RequestFactory().get('/'), rows, normal_size)
                self.assertEqual(len(first), 3)
                self.assertEqual(first.paginator.count, 37)
                seen = []
                for number in first.paginator.page_range:
                    page = paginate(RequestFactory().get('/', {'page': number}), rows, normal_size)
                    seen.extend(row.pk for row in page)
                self.assertEqual(seen, list(rows.values_list('pk', flat=True)))
        self.assertEqual(Employee.objects.count(), 37)

    def test_view_all_honors_normal_size_and_still_paginates(self):
        for size in (10, 20, 25, 30):
            page = paginate(RequestFactory().get('/', {'view': 'all'}), Employee.objects.all(), size)
            self.assertEqual(len(page), size)
            self.assertEqual(page.paginator.count, 37)
            self.assertTrue(page.has_next())
        page = paginate(RequestFactory().get('/', {'view': 'all'}), Employee.objects.all())
        self.assertEqual(len(page), 25)

    def test_navigation_and_toggles_preserve_all_filters(self):
        for view, label, expected in (('', 'View all', ['all']), ('all', 'Show fewer', None)):
            request = RequestFactory().get('/?q=a%26b&status=open&tag=x&tag=y&page=2&view=' + view)
            page = paginate(request, Employee.objects.all(), 10)
            html = render_to_string('partials/pagination.html', {'page_obj': page}, request=request)
            self.assertIn(label, html)
            links = [parse_qs(urlsplit(url).query) for url in Links(html).urls]
            self.assertTrue(links)
            for query in links:
                self.assertEqual(query['q'], ['a&b'])
                self.assertEqual(query['status'], ['open'])
                self.assertEqual(query['tag'], ['x', 'y'])
            self.assertTrue(any(query.get('view') == expected and query.get('page') == ['1']
                                for query in links))
            self.assertTrue(any(query.get('page') == ['3'] for query in links))
            self.assertIn('37', html)

    def test_single_page_and_empty_results_keep_total_and_controls(self):
        for count in (0, 2, 7):
            request = RequestFactory().get('/?view=all')
            page = paginate(request, Employee.objects.all()[:count])
            html = render_to_string('partials/pagination.html', {'page_obj': page}, request=request)
            self.assertIn(f'{count} records', html)
            self.assertIn('Show fewer', html)
        for value in ('bad', '-1', '999'):
            page = paginate(RequestFactory().get('/', {'page': value}), Employee.objects.all())
            self.assertIsInstance(page, Page)
            self.assertLessEqual(len(page), 3)


class ListPreviewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.day = timezone.localdate()
        cls.staff = user('preview-staff', role('preview-staff', perms=[
            'hr.view', 'hr.attendance', 'hr.roster', 'hr.training', 'hr.self',
            'meetings.view', 'support.view', 'accounts.manage_settings',
        ]))
        cls.departments = [Department.objects.create(name=f'Department {i}', code=f'd{i}')
                           for i in range(7)]
        for i in range(7):
            employee = Employee.objects.create(employee_no=f'L{i}', name=f'Employee {i}',
                                               department=cls.departments[i])
            Attendance.objects.create(employee=employee, date=cls.day, status='present')
            LeaveRequest.objects.create(employee=employee, start_date=cls.day,
                                        end_date=cls.day, reason='Test', status='approved')
            TrainingRecord.objects.create(employee=employee, title=f'Training {i}',
                                          expires_on=cls.day)
            meeting = Meeting.objects.create(title=f'Meeting {i}', date=cls.day)
            ActionItem.objects.create(meeting=meeting, description=f'Action {i}',
                                      due_date=cls.day - timedelta(days=1))
            Ticket.objects.create(number=f'T{i}', subject=f'Ticket {i}', priority='high')
            PlanPhase.objects.create(phase=f'Phase {i}', status='done' if i < 5 else 'planned',
                                     sort_order=i)
            ChecklistItem.objects.create(item=f'Item {i}', kind='uat', sort_order=i,
                                         status='passed' if i < 5 else 'pending')
            ChangeRequest.objects.create(reference=f'C{i}', title=f'Change {i}')
            HealthEvent.objects.create(message=f'Event {i}')
            BackupRecord.objects.create(filename=f'backup-{i}')
            AppSetting.objects.create(key=f'preview-{i}', value=str(i))

    def setUp(self):
        self.client.force_login(self.staff)

    def test_lists_preview_and_expand_without_losing_records(self):
        cases = [
            ('hr_employees', 'page_obj', {}), ('hr_leave', 'page_obj', {'status': 'approved'}),
            ('hr_attendance', 'employees', {'date': str(self.day)}),
            ('hr_roster', 'page_obj', {}), ('hr_training', 'rows', {}),
            ('meetings_list', 'page_obj', {'status': 'scheduled'}),
            ('meetings_actions', 'rows', {'status': 'overdue'}),
            ('support_tickets', 'page_obj', {'priority': 'high', 'status': 'open'}),
            ('support_acceptance', 'phases', {}), ('support_checklists', 'rows', {'kind': 'uat'}),
            ('support_changes', 'rows', {}), ('health', 'events', {}),
            ('security', 'backups', {}), ('settings', 'history', {}),
        ]
        for name, key, filters in cases:
            with self.subTest(view=name):
                response = self.client.get(reverse(name), filters)
                self.assertEqual(response.status_code, 200)
                self.assertIn(key, response.context)
                page = response.context[key]
                self.assertIsInstance(page, Page)
                self.assertEqual(len(page), 3)
                self.assertEqual(page.paginator.count, 7)
                self.assertContains(response, 'View all')
                self.assertTemplateUsed(response, 'partials/pagination.html')
                ids = []
                for number in (1, 2, 3):
                    other = self.client.get(reverse(name), {**filters, 'page': number})
                    ids.extend(row.pk for row in other.context[key])
                self.assertEqual(len(set(ids)), 7)
                expanded = self.client.get(reverse(name), {**filters, 'view': 'all'})
                self.assertEqual(len(expanded.context[key]), 7)
                self.assertContains(expanded, 'Show fewer')

    def test_totals_and_selection_options_are_not_preview_counts(self):
        plan = self.client.get(reverse('support_acceptance'))
        self.assertEqual(plan.context['total'], 7)
        self.assertEqual(plan.context['done'], 5)
        self.assertEqual(plan.context['percent'], 71)
        checklist = self.client.get(reverse('support_checklists'), {'kind': 'uat'})
        self.assertEqual(checklist.context['passed'], 5)
        self.assertEqual(checklist.context['page_obj'].paginator.count, 7)
        attendance = self.client.get(reverse('hr_attendance'))
        self.assertEqual(attendance.context['counts']['present'], 7)
        roster = self.client.get(reverse('hr_roster'))
        self.assertEqual(len(roster.context['employees']), 7)
        employees = self.client.get(reverse('hr_employees'))
        self.assertEqual(len(employees.context['departments']), 7)
        tickets = self.client.get(reverse('support_tickets'))
        self.assertEqual(tickets.context['stats']['open'], 7)
        self.assertEqual(tickets.context['categories'], Ticket.CATEGORIES)

    def test_hr_dashboard_previews_and_expiring_total(self):
        response = self.client.get(reverse('hr_dashboard'))
        for key in ('employees', 'upcoming_leave', 'expiring'):
            self.assertEqual(len(response.context[key]), 3)
        self.assertEqual(response.context['expiring_count'], 7)
        self.assertEqual(response.context['stats']['total'], 7)
        self.assertEqual(len(response.context['departments']), 7)

    def test_hr_employee_snapshot_link_preserves_department(self):
        response = self.client.get(reverse('hr_dashboard'), {'department': 'd4'})
        links = [parse_qs(urlsplit(url).query) for url in Links(response.content.decode()).urls
                 if urlsplit(url).path == reverse('hr_employees')]
        self.assertTrue(any(query.get('department') == ['d4'] and query.get('view') == ['all']
                            for query in links))

    def test_attendance_edit_on_later_page_preserves_other_records(self):
        employee = Employee.objects.order_by('employee_no')[4]
        response = self.client.post(reverse('hr_attendance') + '?page=2', {
            'date': str(self.day), f'status_{employee.pk}': 'absent',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Attendance.objects.filter(status='absent').count(), 1)
        self.assertEqual(Attendance.objects.filter(status='present').count(), 6)


class DashboardPreviewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.day = timezone.localdate()
        cls.staff = user('preview-dashboard', role('preview-dashboard', perms=['hr.view']))
        cls.unit = unit(facility('preview'))
        template = WorkflowTemplate.objects.create(code='preview', name='Preview')
        step = WorkflowStep.objects.create(template=template, order=1, name='Review', role=cls.staff.role)
        for i in range(7):
            Notification.objects.create(user=cls.staff, subject=f'Mail {i}', body='Message body')
            Meeting.objects.create(title=f'Today {i}', date=cls.day)
            Meeting.objects.create(title=f'Upcoming {i}', date=cls.day + timedelta(days=1))
            booking(cls.staff, cls.unit, start_days=0, status='paid')
            booking(cls.staff, cls.unit, start_days=-2, status='paid')
            HealthEvent.objects.create(message=f'Health {i}')
            AuditEntry.objects.create(action='update', changes=f'Audit {i}')
            AppSetting.objects.create(key=f'dashboard-{i}', value=str(i))
            instance = WorkflowInstance.objects.create(template=template, object_type='core.AppSetting',
                object_id=i + 1, tracking_id=f'W{i}', requester=cls.staff)
            WorkflowTask.objects.create(instance=instance, step=step, role=cls.staff.role,
                                        due_at=timezone.now() - timedelta(hours=1))
            for status in ('present', 'absent', 'leave', 'missing'):
                employee = Employee.objects.create(employee_no=f'{status}{i}', name=f'{status} {i}')
                if status != 'missing':
                    Attendance.objects.create(employee=employee, date=cls.day, status=status)
        Meeting.objects.create(title='Cancelled', date=cls.day, status='cancelled')

    def test_mail_preview_keeps_unread_total(self):
        result = _mail_summary(self.staff, self.day)
        self.assertEqual(len(result['items']), 3)
        self.assertEqual(result['unread'], 7)
        self.assertEqual(result['today'], 7)
        self.assertEqual(Notification.objects.count(), 7)

    def test_attendance_names_and_more_counts(self):
        result = _attendance_summary(self.day)
        for key in ('present', 'absent', 'leave', 'not_marked'):
            self.assertEqual(result[key], 7)
            self.assertEqual(len(result[f'{key}_names']), 3)
            self.assertEqual(result[f'{key}_more'], 4)
        self.assertEqual(result['total'], 28)

    def test_meeting_preview_uses_full_count_query(self):
        with CaptureQueriesContext(connection) as queries:
            result = _meeting_summary(self.day)
        self.assertEqual(result['count'], 7)
        self.assertEqual(len(result['today']), 3)
        self.assertEqual(len(result['upcoming']), 3)
        meeting_queries = [q['sql'].upper() for q in queries if 'meetings_meeting' in q['sql']]
        self.assertTrue(any('COUNT(' in sql for sql in meeting_queries))
        self.assertTrue(all('COUNT(' in sql or 'LIMIT 3' in sql for sql in meeting_queries))
        self.assertEqual(result['next'], result['today'][0])

    def test_approvals_and_dashboard_tasks_keep_totals(self):
        result = _approval_summary(self.staff)
        self.assertEqual(result['mine'], 7)
        self.assertEqual(result['pending'], 7)
        self.assertEqual(len(result['waiting']), 3)
        self.client.force_login(self.staff)
        response = self.client.get('/app/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['my_tasks_list']), 3)
        self.assertEqual(response.context['my_pending'], 7)

    def test_applications_keep_full_arrival_and_departure_counts(self):
        result = _application_summary(self.day)
        for key in ('arrivals', 'departures', 'recent'):
            self.assertEqual(len(result[key]), 3)
        self.assertEqual(result['arrival_count'], 7)
        self.assertEqual(result['departure_count'], 7)
        self.assertEqual(self.unit.bookings.count(), 14)

    def test_admin_previews(self):
        result = _admin_summary()
        for key in ('health', 'audit', 'settings_changed'):
            self.assertEqual(len(result[key]), 3)
        self.assertEqual(AppSetting.objects.count(), 7)
