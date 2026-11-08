from django.core.exceptions import PermissionDenied
from django.test import TestCase

from workflow import engine
from workflow.models import AuthorityMatrix, StepRecord, WorkflowTask

from .factories import booking, booking_template, facility, role, unit, user


class WorkflowRoutingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.template = booking_template()
        cls.citizen_role = role('citizen', 'Citizen')
        cls.applicant = user('applicant', cls.citizen_role)
        cls.unit_room = unit(facility('route'), 'R1', 'room')
        cls.unit_suite = unit(facility('route2'), 'S1', 'suite')

    def route(self, unit_kind, amount):
        payload = {'unit_kind': unit_kind, 'amount': amount}
        return [step.role.code for step in engine.applicable_steps(self.template, payload)]

    def test_room_route_skips_engineer_and_ceo(self):
        self.assertEqual(self.route('room', 5000), ['bookingdesk', 'eo'])

    def test_suite_route_includes_engineer(self):
        self.assertEqual(self.route('suite', 15000),
                         ['bookingdesk', 'engineer', 'eo'])

    def test_large_amount_adds_ceo_step(self):
        self.assertEqual(self.route('room', 25000),
                         ['bookingdesk', 'eo', 'ceo'])

    def test_condition_any_and_all_helpers(self):
        self.assertTrue(engine.condition_matches(
            {'any': [{'min_amount': 99999}, {'unit_kind': ['hall']}]},
            {'unit_kind': 'hall', 'amount': 100}))
        self.assertFalse(engine.condition_matches(
            {'all': [{'min_amount': 1000}, {'unit_kind': ['hall']}]},
            {'unit_kind': 'hall', 'amount': 100}))

    def test_authority_limit_blocks_eo_above_matrix(self):
        eo_role = role('eo', 'Executive Officer')
        eo_user = user('eo1', eo_role)
        b = booking(self.applicant, self.unit_room, amount='25000.00')
        instance = engine.start(
            self.template, b,
            {'unit_kind': 'room', 'amount': 25000.0, 'subject': 'Big booking'},
            self.applicant, tracking_id='GZP-TEST-1')
        desk_task = instance.tasks.get(status='pending')
        desk_user = user('desk1', role('bookingdesk', 'Booking Desk'))
        ok, _ = engine.decide(desk_task, desk_user, 'forward', 'forwarded')
        self.assertTrue(ok)
        eo_task = instance.tasks.get(status='pending')
        self.assertEqual(eo_task.role.code, 'eo')
        ok, message = engine.decide(eo_task, eo_user, 'approve', 'approve')
        self.assertFalse(ok)
        self.assertIn('may approve up to', message)
        self.assertEqual(WorkflowTask.objects.get(pk=eo_task.pk).status, 'pending')

    def test_ceo_can_approve_within_unlimited_authority(self):
        b = booking(self.applicant, self.unit_room, amount='25000.00')
        instance = engine.start(
            self.template, b, {'unit_kind': 'room', 'amount': 25000.0}, self.applicant)
        engine.decide(instance.tasks.get(status='pending'),
                      user('desk2', role('bookingdesk')), 'forward', 'ok')
        # EO is above its ৳20,000 limit, so it must recommend rather than approve.
        engine.decide(instance.tasks.get(status='pending'),
                      user('eo2', role('eo')), 'recommend', 'within CEO authority')
        ceo_task = instance.tasks.get(status='pending')
        self.assertEqual(ceo_task.role.code, 'ceo')
        ok, _ = engine.decide(ceo_task, user('ceo1', role('ceo')), 'approve', 'ok')
        self.assertTrue(ok)
        instance.refresh_from_db()
        self.assertEqual(instance.status, 'approved')

    def test_engine_rejects_user_of_another_role(self):
        b = booking(self.applicant, self.unit_room)
        instance = engine.start(self.template, b, {'unit_kind': 'room', 'amount': 5000},
                                self.applicant)
        task = instance.tasks.get(status='pending')
        with self.assertRaises(PermissionDenied):
            engine.decide(task, user('eo9', role('eo')), 'forward', 'nope')

    def test_step_records_the_submission_and_decisions(self):
        b = booking(self.applicant, self.unit_room)
        instance = engine.start(self.template, b, {'unit_kind': 'room', 'amount': 5000},
                                self.applicant)
        engine.decide(instance.tasks.get(status='pending'),
                      user('desk3', role('bookingdesk')), 'forward', 'note')
        self.assertEqual(StepRecord.objects.filter(instance=instance).count(), 2)
