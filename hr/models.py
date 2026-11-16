from django.conf import settings
from django.db import models
from django.utils import timezone


class Department(models.Model):
    name = models.CharField(max_length=120)
    code = models.SlugField(max_length=30, unique=True)
    organization = models.ForeignKey(
        'organizations.Organization', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='departments',
    )
    head = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                             on_delete=models.SET_NULL, related_name='headed_departments')

    class Meta:
        ordering = ['name']
        unique_together = [('organization', 'name')]

    def __str__(self):
        return self.name


class Designation(models.Model):
    name = models.CharField(max_length=120)
    department = models.ForeignKey(Department, null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name='designations')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Employee(models.Model):
    STATUS = [('active', 'Active'), ('leave', 'On leave'), ('inactive', 'Inactive')]
    TYPES = [('permanent', 'Permanent'), ('contract', 'Contract'),
             ('deputation', 'Deputation'), ('daily', 'Daily wage')]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True,
                                on_delete=models.SET_NULL, related_name='employee')
    employee_no = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=160)
    department = models.ForeignKey(Department, null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name='employees')
    designation = models.ForeignKey(Designation, null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name='employees')
    joining_date = models.DateField(null=True, blank=True)
    employment_type = models.CharField(max_length=20, choices=TYPES, default='permanent')
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    supervisor = models.ForeignKey('self', null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name='team')
    emergency_contact = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='active')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['employee_no']

    def __str__(self):
        return f'{self.employee_no} - {self.name}'

    @property
    def service_years(self):
        if not self.joining_date:
            return 0
        return round((timezone.localdate() - self.joining_date).days / 365.25, 1)


class Attendance(models.Model):
    STATUS = [('present', 'Present'), ('absent', 'Absent'), ('late', 'Late'),
              ('leave', 'Leave'), ('holiday', 'Holiday')]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance')
    date = models.DateField()
    status = models.CharField(max_length=12, choices=STATUS, default='present')
    in_time = models.TimeField(null=True, blank=True)
    out_time = models.TimeField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name='+')

    class Meta:
        ordering = ['-date', 'employee__employee_no']
        unique_together = [('employee', 'date')]

    def __str__(self):
        return f'{self.employee.employee_no} {self.date} {self.status}'


class LeaveRequest(models.Model):
    TYPES = [('casual', 'Casual leave'), ('sick', 'Sick leave'),
             ('annual', 'Annual leave'), ('special', 'Special leave')]
    STATUS = [('submitted', 'Submitted'), ('under_review', 'Under review'),
              ('clarification', 'Clarification required'), ('recommended', 'Recommended'),
              ('approved', 'Approved'), ('rejected', 'Rejected'),
              ('cancelled', 'Cancelled')]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leaves')
    leave_type = models.CharField(max_length=20, choices=TYPES, default='casual')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS, default='submitted')
    applied_at = models.DateTimeField(default=timezone.now)
    decided_at = models.DateTimeField(null=True, blank=True)
    decision_note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-applied_at']

    def __str__(self):
        return f'{self.employee.employee_no} {self.start_date}'

    @property
    def days(self):
        return (self.end_date - self.start_date).days + 1

    @property
    def status_label(self):
        return self.get_status_display()

    @property
    def workflow_instance(self):
        from workflow.models import WorkflowInstance

        return WorkflowInstance.objects.filter(
            object_type='hr.LeaveRequest', object_id=self.pk
        ).order_by('-created_at').first()

    def on_workflow_decision(self, decision, instance):
        mapping = {
            'correct': 'clarification', 'return': 'clarification',
            'reject': 'rejected', 'recommend': 'recommended',
        }
        if instance.status == 'approved':
            self.status = 'approved'
            self.decided_at = timezone.now()
            self.decision_note = (instance.note or '')[:255]
            self.employee.status = 'leave'
            self.employee.save(update_fields=['status'])
        elif decision in mapping:
            self.status = mapping[decision]
            if decision == 'reject':
                self.decided_at = timezone.now()
                self.decision_note = (instance.note or '')[:255]
        else:
            self.status = 'under_review'
        self.save(update_fields=['status', 'decided_at', 'decision_note'])


class Roster(models.Model):
    SHIFTS = [('day', 'Day (09:00-17:00)'), ('evening', 'Evening (14:00-22:00)'),
              ('night', 'Night (22:00-06:00)'), ('off', 'Off duty')]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='roster')
    date = models.DateField()
    shift = models.CharField(max_length=12, choices=SHIFTS, default='day')
    facility = models.ForeignKey('facilities.Facility', null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name='rosters')
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['date', 'employee__employee_no']
        unique_together = [('employee', 'date')]

    def __str__(self):
        return f'{self.employee.employee_no} {self.date} {self.shift}'


class TrainingRecord(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='training')
    title = models.CharField(max_length=160)
    provider = models.CharField(max_length=160, blank=True)
    completed_on = models.DateField(null=True, blank=True)
    expires_on = models.DateField(null=True, blank=True)
    certificate = models.FileField(upload_to='training/', blank=True, null=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['expires_on', 'title']

    def __str__(self):
        return f'{self.employee.employee_no} {self.title}'

    @property
    def is_expired(self):
        return bool(self.expires_on and self.expires_on < timezone.localdate())

    @property
    def days_left(self):
        if not self.expires_on:
            return None
        return (self.expires_on - timezone.localdate()).days
