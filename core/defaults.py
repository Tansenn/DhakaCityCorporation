"""Default configuration values. Editable in the app under Settings.

Every value is a sample value for the demo; the UI labels them as such.
"""

SETTING_DEFS = [
    # key, default, label, group, description
    ('app_name', 'Gazipur Zila Parishad: Integrated Digital Platform',
     'Application name', 'General',
     'Shown in the header, page titles and PDFs. Change it once to rename the platform.'),
    ('organisation_name', 'Gazipur Zila Parishad', 'Organisation name', 'General', ''),
    ('support_email', 'support@adcelerete.example', 'Support email', 'General',
     'Displayed on the support page. No real email is sent in the demo.'),
    ('support_phone', '+880 0000 000000', 'Support phone', 'General', 'Sample number.'),

    ('hold_hours', '48', 'Temporary hold (hours)', 'Booking rules',
     'How long a room or slot is held while the application is under review.'),
    ('payment_window_hours', '24', 'Payment window (hours)', 'Booking rules',
     'Time allowed to pay after final approval before the hold is released.'),
    ('advance_booking_days', '90', 'Advance booking limit (days)', 'Booking rules',
     'How far ahead a citizen may apply.'),
    ('max_nights', '14', 'Maximum stay (nights)', 'Booking rules', ''),
    ('max_guests', '12', 'Maximum guests per application', 'Booking rules', ''),
    ('holiday_rule', 'Friday and Saturday nights use the published holiday tariff.',
     'Holiday rule note', 'Booking rules', 'Sample rule shown to citizens before payment.'),
    ('refund_policy', '7:100,3:50,1:25,0:0', 'Refund policy', 'Booking rules',
     'days_before_checkin:percent pairs. Sample policy editable by the administrator.'),
    ('min_notice_hours', '24', 'Minimum notice (hours)', 'Booking rules',
     'Earliest check-in date that can be requested.'),

    ('payment_gateway_provider', 'SSLCommerz / bKash (demo)',
     'Payment gateway', 'Payments', 'Simulated gateway. No real money moves.'),
    ('gateway_charge_paid_by_user', '0', 'Gateway charge paid by the user', 'Payments',
     '1 = show and add the gateway charge at checkout; 0 = absorbed under the contract.'),
    ('gateway_charge_amount', '20', 'Gateway charge amount (BDT)', 'Payments', ''),

    ('reminder_hours', '6', 'Reminder before due (hours)', 'Workflow',
     'Reminders are sent within this window before a task is due.'),
    ('escalation_hours', '12', 'Escalate after overdue (hours)', 'Workflow',
     'Overdue tasks escalate to the nominated supervisor role.'),
    ('otp_valid_minutes', '10', 'OTP validity (minutes)', 'Security', ''),
    ('login_rate_limit', '6', 'Allowed failed logins per 15 minutes', 'Security', ''),
    ('backup_retention_days', '30', 'Backup retention (days)', 'Security', ''),

    ('sms_client_paid', '1', 'SMS credits are client-paid', 'Notifications',
     '1 = the demo shows the client-paid SMS notice. Email app logic is included.'),

    ('demo_banner', 'Demo version - sample data', 'Demo ribbon text', 'General',
     'Shown on every page while the platform runs in demo mode.'),
]
