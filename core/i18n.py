"""Lightweight English / Bangla string table for navigation, headings,
buttons and status names (per the scope's language requirement).

Only presentation strings live here; data and audit records stay in English.
"""
from __future__ import annotations

import contextvars
import re
from html import escape, unescape

CURRENT_LANG = contextvars.ContextVar('gzp_lang', default='en')

BN_MONTHS = {
    'January': 'জানুয়ারি', 'February': 'ফেব্রুয়ারি', 'March': 'মার্চ',
    'April': 'এপ্রিল', 'May': 'মে', 'June': 'জুন', 'July': 'জুলাই',
    'August': 'আগস্ট', 'September': 'সেপ্টেম্বর', 'October': 'অক্টোবর',
    'November': 'নভেম্বর', 'December': 'ডিসেম্বর',
    'Jan': 'জানু', 'Feb': 'ফেব', 'Mar': 'মার্চ', 'Apr': 'এপ্রি',
    'Jun': 'জুন', 'Jul': 'জুলাই', 'Aug': 'আগ', 'Sep': 'সেপ্ট',
    'Sept': 'সেপ্ট', 'Oct': 'অক্টো', 'Nov': 'নভে', 'Dec': 'ডিসে',
}

BN_DAYS = {
    'Monday': 'সোমবার', 'Tuesday': 'মঙ্গলবার', 'Wednesday': 'বুধবার',
    'Thursday': 'বৃহস্পতিবার', 'Friday': 'শুক্রবার', 'Saturday': 'শনিবার',
    'Sunday': 'রবিবার',
    'Mon': 'সোম', 'Tue': 'মঙ্গল', 'Wed': 'বুধ', 'Thu': 'বৃহঃ',
    'Fri': 'শুক্র', 'Sat': 'শনি', 'Sun': 'রবি',
}

BN_DIGITS = str.maketrans('0123456789', '০১২৩৪৫৬৭৮৯')

_MONTH_KEYS = sorted(BN_MONTHS, key=len, reverse=True)
_DAY_KEYS = sorted(BN_DAYS, key=len, reverse=True)


def localize(text):
    """Rewrite an English formatted date in Bengali when the session is Bangla."""
    if CURRENT_LANG.get() != 'bn' or not text:
        return text
    for key in _DAY_KEYS:
        text = text.replace(key, BN_DAYS[key])
    for key in _MONTH_KEYS:
        text = text.replace(key, BN_MONTHS[key])
    return text.translate(BN_DIGITS)

DEFAULT_LANG = 'en'

BN = {
    # Brand / chrome
    'Gazipur Zila Parishad: Integrated Digital Platform': 'গাজীপুর জেলা পরিষদ: সমন্বিত ডিজিটাল প্ল্যাটফর্ম',
    'Demo version - sample data': 'ডেমো সংস্করণ - নমুনা তথ্য',
    'Demo version': 'ডেমো সংস্করণ',
    'Prepared by Adcelerete Technologies Limited. Demo version.':
        'অ্যাডসেলেরেট টেকনোলজিস লিমিটেড প্রস্তুতকৃত। ডেমো সংস্করণ।',
    'Skip to content': 'মূল বিষয়বস্তুতে যান',
    'Search': 'অনুসন্ধান',
    'Filter': 'ফিল্টার',
    'Apply': 'প্রয়োগ করুন',
    'Reset': 'রিসেট',
    'Actions': 'কার্যক্রম',
    'View': 'দেখুন',
    'View all': 'সব দেখুন',
    'Open': 'খুলুন',
    'Close': 'বন্ধ',
    'Back': 'ফিরে যান',
    'Next': 'পরবর্তী',
    'Previous': 'পূর্ববর্তী',
    'Save': 'সংরক্ষণ',
    'Save changes': 'পরিবর্তন সংরক্ষণ',
    'Submit': 'জমা দিন',
    'Cancel': 'বাতিল',
    'Delete': 'মুছুন',
    'Edit': 'সম্পাদনা',
    'Create': 'তৈরি করুন',
    'Add': 'যোগ করুন',
    'Update': 'হালনাগাদ',
    'Download': 'ডাউনলোড',
    'Print': 'প্রিন্ট',
    'Upload': 'আপলোড',
    'Login': 'লগইন',
    'Logout': 'লগআউট',
    'Sign in': 'সাইন ইন',
    'Register': 'নিবন্ধন',
    'Password': 'পাসওয়ার্ড',
    'Email': 'ইমেইল',
    'Phone': 'ফোন',
    'Name': 'নাম',
    'Date': 'তারিখ',
    'Dates': 'তারিখসমূহ',
    'Time': 'সময়',
    'Status': 'স্ট্যাটাস',
    'Type': 'ধরন',
    'Category': 'শ্রেণি',
    'Department': 'বিভাগ',
    'Designation': 'পদবি',
    'Description': 'বিবরণ',
    'Amount': 'পরিমাণ',
    'Total': 'মোট',
    'Deposit': 'জামানত',
    'Notes': 'মন্তব্য',
    'Reason': 'কারণ',
    'Priority': 'গুরুত্ব',
    'Attachment': 'সংযুক্তি',
    'Attachments': 'সংযুক্তিসমূহ',
    'No records found.': 'কোনো তথ্য পাওয়া যায়নি।',
    'None': 'নেই',
    'Yes': 'হ্যাঁ',
    'No': 'না',
    'All': 'সব',
    'Today': 'আজ',
    'Days': 'দিন',
    'Home': 'হোম',
    'Dashboard': 'ড্যাশবোর্ড',
    'Overview': 'সংক্ষিপ্তসার',
    'Workspace': 'কর্মক্ষেত্র',
    'Approvals': 'অনুমোদন',
    'My Tasks': 'আমার কাজ',
    'Tasks': 'কাজসমূহ',
    'Workflow': 'কার্যপ্রবাহ',
    'Workflow designer': 'কার্যপ্রবাহ ডিজাইনার',
    'Authority matrix': 'কর্তৃত্ব ম্যাট্রিক্স',
    'Reminders': 'স্মারক',
    'Run reminders now': 'এখনই স্মারক চালান',
    'Bookings': 'বুকিং',
    'My tasks': 'আমার কাজ',
    'Total bookings': 'মোট বুকিং',
    'Collection this month': 'এই মাসের আদায়',
    'Open workflow tasks': 'চলমান কার্যপ্রবাহ কাজ',
    'Overdue tasks': 'মেয়াদোত্তীর্ণ কাজ',
    'Booking pipeline': 'বুকিং পাইপলাইন',
    'Upcoming confirmed stays': 'আসন্ন নিশ্চিত অবস্থান',
    'Bookings by facility': 'সুবিধাভিত্তিক বুকিং',
    'Latest applications': 'সর্বশেষ আবেদন',
    'All applications in the register': 'রেজিস্টারে সব আবেদন',
    'Verified payments only': 'শুধু যাচাইকৃত পেমেন্ট',
    'for your role': 'আপনার ভূমিকার জন্য',
    'Reminders and escalation apply': 'স্মারক ও এসকেলেশন প্রযোজ্য',
    'Every status is driven by the workflow engine, not a fixed route.':
        'প্রতিটি স্ট্যাটাস কার্যপ্রবাহ ইঞ্জিন নিয়ন্ত্রিত, নির্দিষ্ট রুট নয়।',
    'Confirmed vs total': 'নিশ্চিত বনাম মোট',
    'No confirmed stays in the next 7 days.': 'আগামী ৭ দিনে কোনো নিশ্চিত অবস্থান নেই।',
    'No facilities configured.': 'কোনো সুবিধা কনফিগার করা নেই।',
    'No applications yet.': 'এখনো কোনো আবেদন নেই।',
    'Open booking management': 'বুকিং ব্যবস্থাপনা খুলুন',
    'Signed in as': 'সাইন ইন করেছেন',
    'night(s)': 'রাত',
    'Facility': 'সুবিধা',
    'Confirmed': 'নিশ্চিত',
    'Unit': 'ইউনিট',
    'Booking management': 'বুকিং ব্যবস্থাপনা',
    'Booking desk queue': 'বুকিং ডেস্ক কিউ',
    'Reception desk': 'রিসেপশন ডেস্ক',
    'Facilities & availability': 'সুবিধা ও প্রাপ্যতা',
    'Facilities': 'সুবিধাসমূহ',
    'Payments & reconciliation': 'পেমেন্ট ও সমন্বয়',
    'Payments': 'পেমেন্ট',
    'Refunds': 'ফেরত',
    'People': 'জনবল',
    'Human resources': 'মানবসম্পদ',
    'Employees': 'কর্মকর্তা-কর্মচারী',
    'Attendance': 'উপস্থিতি',
    'Leave': 'ছুটি',
    'Roster': 'ডিউটি রোস্টার',
    'Training & expiry': 'প্রশিক্ষণ ও মেয়াদ',
    'My profile': 'আমার প্রোফাইল',
    'Records': 'নথি',
    'Document register': 'নথি রেজিস্টার',
    'Files': 'ফাইল',
    'Overdue files': 'সময়োত্তীর্ণ ফাইল',
    'Projects': 'প্রকল্প',
    'Project register': 'প্রকল্প রেজিস্টার',
    'Inspections': 'পরিদর্শন',
    'Meetings': 'সভা',
    'Meeting calendar': 'সভা ক্যালেন্ডার',
    'Action follow-up': 'কার্যক্রম অনুসরণ',
    'Insight': 'বিশ্লেষণ',
    'Executive dashboard': 'নির্বাহী ড্যাশবোর্ড',
    'Department dashboard': 'বিভাগীয় ড্যাশবোর্ড',
    'Booking & revenue': 'বুকিং ও রাজস্ব',
    'Workflow performance': 'কার্যপ্রবাহ কর্মক্ষমতা',
    'Report library': 'প্রতিবেদন গ্রন্থাগার',
    'Reports': 'প্রতিবেদন',
    'Audit log': 'অডিট লগ',
    'Audit': 'অডিট',
    'Administration': 'প্রশাসন',
    'Settings': 'সেটিংস',
    'Users & roles': 'ব্যবহারকারী ও ভূমিকা',
    'Security & backup': 'নিরাপত্তা ও ব্যাকআপ',
    'System health': 'সিস্টেম সাস্থ্য',
    'Demo outbox': 'ডেমো আউটবক্স',
    'Notifications': 'বিজ্ঞপ্তি',
    'Support': 'সহায়তা',
    'Support tickets': 'সহায়তা টিকিট',
    '45-day plan': '৪৫ দিনের পরিকল্পনা',
    'Change requests': 'পরিবর্তন অনুরোধ',
    'Included & chargeable': 'অন্তর্ভুক্ত ও চার্জযোগ্য',
    'UAT checklist': 'ইউএটি চেকলিস্ট',
    'Deliverables': 'প্রদেয়',
    'My applications': 'আমার আবেদনসমূহ',
    'Track application': 'আবেদন ট্র্যাক করুন',
    'Book a Dakbungalow': 'ডাকবাংলো বুক করুন',
    'Book now': 'এখনই বুক করুন',
    'Apply for booking': 'বুকিংয়ের আবেদন',
    'Application': 'আবেদন',
    'Applications': 'আবেদনসমূহ',
    'Reference': 'রেফারেন্স',
    'Applicant': 'আবেদনকারী',
    'Purpose': 'উদ্দেশ্য',
    'Guests': 'অতিথি',
    'Check-in': 'চেক-ইন',
    'Check-out': 'চেক-আউট',
    'Availability': 'প্রাপ্যতা',
    'Available': 'উপলব্ধ',
    'Booked': 'বুকিং হয়েছে',
    'Tariff': 'শুল্ক',
    'Rules & terms': 'নিয়ম ও শর্তাবলি',
    'Amenities': 'সুবিধাদি',
    'Location': 'অবস্থান',
    'Photo': 'ছবি',
    'Payment': 'পেমেন্ট',
    'Pay now': 'এখনই পরিশোধ',
    'Receipt': 'রসিদ',
    'Permit': 'পরমিট',
    'Download permit': 'পরমিট ডাউনলোড',
    'Download receipt': 'রসিদ ডাউনলোড',
    'Verify permit': 'পরমিট যাচাই',
    'Verification': 'যাচাই',
    'Cancellation & refund': 'বাতিল ও ফেরত',
    'Request cancellation': 'বাতিলের অনুরোধ',
    'Messages': 'বার্তা',
    'Timeline': 'সময়রেখা',
    'Documents': 'নথিপত্র',
    'Required documents': 'প্রয়োজনীয় নথি',
    'Upload documents': 'নথি আপলোড',
    'Review': 'পর্যালোচনা',
    'Approve': 'অনুমোদন',
    'Reject': 'প্রত্যাখ্যান',
    'Recommend': 'সুপারিশ',
    'Request correction': 'সংশোধন অনুরোধ',
    'Return': 'ফেরত দিন',
    'Forward': 'ফরওয়ার্ড',
    'Claim': 'গ্রহণ',
    'Reassign': 'পুনরায় বরাদ্দ',
    'Decision': 'সিদ্ধান্ত',
    'Comments': 'মন্তব্য',
    'History': 'ইতিহাস',
    'Approval history': 'অনুমোদনের ইতিহাস',
    'Current holder': 'বর্তমান ধারক',
    'Confidentiality': 'গোপনীয়তা',
    'Version': 'সংস্করণ',
    'Archive': 'আর্কাইভ',
    'Archived': 'আর্কাইভকৃত',
    'Overdue': 'সময়োত্তীর্ণ',
    'Pending': 'অপেক্ষমাণ',
    'Completed': 'সম্পন্ন',
    'In progress': 'চলমান',
    'Resolved': 'সমাধানকৃত',
    'Closed': 'বন্ধ',
    'Open': 'খোলা',
    'Active': 'সক্রিয়',
    'Inactive': 'নিষ্ক্রিয়',
    'Verified': 'যাচাইকৃত',
    'Simulated': 'সিমুলেটেড',
    'Sample data': 'নমুনা তথ্য',
    'Severity': 'তীব্রতা',
    'Subject': 'বিষয়',
    'Sender': 'প্রেরক',
    'Recipient': 'প্রাপক',
    'Milestones': 'মাইলফলক',
    'Progress': 'অগ্রগতি',
    'Issues': 'সমস্যা',
    'Decisions': 'সিদ্ধান্তসমূহ',
    'Minutes': 'কার্যবিবরণী',
    'Agenda': 'আলোচ্যসূচি',
    'Attendance register': 'উপস্থিতি রেজিস্টার',
    'Duty roster': 'ডিউটি রোস্টার',
    'Leave balance': 'ছুটির ব্যালেন্স',
    'Leave ledger': 'ছুটি খতিয়ান',
    'Self service': 'স্ব-সেবা',
    'Reports & exports': 'প্রতিবেদন ও রপ্তানি',
    'Export CSV': 'সিএসভি রপ্তানি',
    'Export PDF': 'পিডিএফ রপ্তানি',
    'KPI dictionary': 'কেপিআই অভিধান',
    'Report access log': 'প্রতিবেদন অ্যাক্সেস লগ',
    'Backup': 'ব্যাকআপ',
    'Run backup now': 'এখনই ব্যাকআপ চালান',
    'Restore test': 'রিস্টোর পরীক্ষা',
    'Integrations': 'ইন্টিগ্রেশন',
    'Not connected': 'সংযুক্ত নয়',
    'Configuration history': 'কনফিগারেশন ইতিহাস',
    'Notification templates': 'বিজ্ঞপ্তি টেমপ্লেট',
    'Master data': 'মাস্টার ডেটা',
    'Role permissions': 'ভূমিকার অনুমতি',
    'Demo accounts': 'ডেমো অ্যাকাউন্ট',
    'Demo role switcher': 'ডেমো ভূমিকা পরিবর্তন',
    'English': 'ইংরেজি',
    'Bangla': 'বাংলা',
    'Name of applicant': 'আবেদনকারীর নাম',
    'Mobile': 'মোবাইল',
    'National ID': 'জাতীয় পরিচয়পত্র',
    'Organization': 'সংস্থা',
    'Government official': 'সরকারি কর্মকর্তা',
    'Public citizen': 'সাধারণ নাগরিক',
    'AC double room': 'এসি ডাবল রুম',
    'Non-AC room': 'নন-এসি রুম',
    'VIP suite': 'ভিআইপি স্যুট',
    'Conference hall': 'কনফারেন্স হল',
    'Morning': 'সকাল',
    'Afternoon': 'দুপুর',
    'Evening': 'সন্ধ্যা',
    'Room': 'রুম',
    'Hall': 'হল',
    'Application submitted': 'আবেদন জমা হয়েছে',
    'Payment successful': 'পেমেন্ট সফল',
    'Demo gateway': 'ডেমো গেটওয়ে',
    'Send duplicate callback': 'ডুপ্লিকেট কলব্যাক পাঠান',
    'Fail payment': 'পেমেন্ট ব্যর্থ করুন',
    'Cancel payment': 'পেমেন্ট বাতিল',
    'Back to application': 'আবেদনে ফিরে যান',
    'Support and maintenance': 'সহায়তা ও রক্ষণাবেক্ষণ',
    'Ticket register': 'টিকিট রেজিস্টার',
    'Monthly support report': 'মাসিক সহায়তা প্রতিবেদন',
    'Request change': 'পরিবর্তন অনুরোধ',
    'Sign out': 'সাইন আউট',
    'Your account': 'আপনার অ্যাকাউন্ট',
    'Notifications': 'বিজ্ঞপ্তি',
    'View notifications': 'বিজ্ঞপ্তি দেখুন',
    'Acknowledgment': 'প্রাপ্তিস্বীকার',
    'Print acknowledgment': 'প্রাপ্তিস্বীকার প্রিন্ট',
    'Continue': 'চালিয়ে যান',
    'Confirm': 'নিশ্চিত করুন',
    'Pay': 'পরিশোধ',
    'Amount payable': 'প্রদেয় পরিমাণ',
    'Security deposit': 'নিরাপত্তা জামানত',
    'Gateway charge': 'গেটওয়ে চার্জ',
    'Payment window': 'পেমেন্ট সময়সীমা',
    'Expires': 'মেয়াদ শেষ',
    'Total payable': 'মোট প্রদেয়',
    'Available rooms': 'প্রাপ্য রুম',
    'Select dates': 'তারিখ নির্বাচন',
    'Search facility': 'সুবিধা খুঁজুন',
    'Filter by facility': 'সুবিধা অনুযায়ী ফিল্টার',
    'View details': 'বিস্তারিত দেখুন',
    'Continue to apply': 'আবেদনে এগিয়ে যান',
    'Confirm & submit': 'নিশ্চিত করে জমা দিন',
    'Uploaded': 'আপলোডকৃত',
    'Not uploaded': 'আপলোড হয়নি',
    'Requested': 'অনুরোধকৃত',
    'Processed': 'প্রক্রিয়াকৃত',
    'Failed': 'ব্যর্থ',
    'Refunded': 'ফেরতকৃত',
    'Duplicate': 'ডুপ্লিকেট',
    'Matched': 'মিলেছে',
    'Mismatched': 'মেলেনি',
    'Turnaround': 'সম্পাদন সময়',
    'Received': 'গৃহীত',
    'Rejected': 'প্রত্যাখ্যাত',
    'Approved': 'অনুমোদিত',
    'Submitted': 'জমা দেওয়া হয়েছে',
    'Under Review': 'পর্যালোচনাধীন',
    'Clarification Required': 'সংশোধন প্রয়োজন',
    'Recommended': 'সুপারিশকৃত',
    'Awaiting Payment': 'পেমেন্টের অপেক্ষায়',
    'Paid / Confirmed': 'পরিশোধিত / নিশ্চিত',
    'Cancelled': 'বাতিল',
    'Completed': 'সম্পন্ন',
    # Plain dashboards and navigation
    'CEO dashboard': 'সিইও ড্যাশবোর্ড',
    'Administrator dashboard': 'প্রশাসক ড্যাশবোর্ড',
    'My dashboard': 'আমার ড্যাশবোর্ড',
    'Office of the Chief Executive Officer': 'প্রধান নির্বাহী কর্মকর্তার কার্যালয়',
    'System administration': 'সিস্টেম প্রশাসন',
    'Mail': 'ডাক ও বার্তা',
    'Mail & notices': 'ডাক ও বিজ্ঞপ্তি',
    'Mail outbox': 'মেইল আউটবক্স',
    'Open mail': 'ডাক খুলুন',
    'unread': 'অপঠিত',
    'No mail yet.': 'এখনো কোনো ডাক নেই।',
    'No further detail.': 'আর কোনো বিবরণ নেই।',
    'received today': 'আজ গৃহীত',
    "Today's meetings": 'আজকের সভা',
    'today': 'আজ',
    'All meetings': 'সব সভা',
    'No meeting is scheduled today.': 'আজ কোনো সভা নির্ধারিত নেই।',
    'Next meetings': 'আসন্ন সভা',
    'Staff attendance today': 'আজকের কর্মী উপস্থিতি',
    'present': 'উপস্থিত',
    'absent': 'অনুপস্থিত',
    'on leave': 'ছুটিতে',
    'not marked': 'চিহ্নিত হয়নি',
    'Present': 'উপস্থিত',
    'Absent': 'অনুপস্থিত',
    'On leave': 'ছুটিতে',
    'Not marked': 'চিহ্নিত হয়নি',
    'Attendance register': 'উপস্থিতি রেজিস্টার',
    'Attendance has not been marked for today yet.': 'আজকের উপস্থিতি এখনো চিহ্নিত করা হয়নি।',
    'Came in': 'উপস্থিত হয়েছেন',
    'Nobody marked yet.': 'এখনো কেউ চিহ্নিত হননি।',
    'Not in today': 'আজ অনুপস্থিত',
    'Everyone is accounted for.': 'সবাই হিসাবভুক্ত।',
    'Revenue this month': 'এই মাসের রাজস্ব',
    'payments': 'পেমেন্ট',
    'Approvals at my desk': 'আমার ডেস্কে অনুমোদন',
    'overdue': 'মেয়াদোত্তীর্ণ',
    'in the system': 'সিস্টেমে',
    'Approvals in the system': 'সিস্টেমে অনুমোদন',
    'Staff present today': 'আজ উপস্থিত কর্মী',
    'Approval route - who checks what': 'অনুমোদন পথ - কে কী যাচাই করেন',
    'Your office is step': 'আপনার কার্যালয় ধাপ',
    'Dakbungalows today': 'আজকের ডাকবাংলো',
    'Arrivals': 'আগমন',
    'Departures': 'প্রস্থান',
    'In house': 'অবস্থানরত',
    'New applications': 'নতুন আবেদন',
    'Arriving today': 'আজ আগমন',
    'No arrivals due today.': 'আজ কোনো আগমন নেই।',
    'Approved but unpaid': 'অনুমোদিত কিন্তু অপরিশোধিত',
    'booking(s)': 'বুকিং',
    'Approvals waiting for you': 'আপনার জন্য অপেক্ষমাণ অনুমোদন',
    'Open all tasks': 'সব কাজ খুলুন',
    'Step': 'ধাপ',
    'Due': 'সময়সীমা',
    'Nothing is waiting at your desk.': 'আপনার ডেস্কে কিছু অপেক্ষমাণ নেই।',
    'Common tasks': 'সাধারণ কাজ',
    'Everything the administrator needs, in one place.': 'প্রশাসকের প্রয়োজনীয় সবকিছু এক জায়গায়।',
    'Approval steps': 'অনুমোদন ধাপ',
    'Approval limits': 'অনুমোদনের সীমা',
    'Approval speed': 'অনুমোদনের গতি',
    'Guesthouses & tariffs': 'ডাকবাংলো ও শুল্ক',
    'Activity log': 'কার্যক্রম লগ',
    'System status': 'সিস্টেম অবস্থা',
    'Recent health notices': 'সাম্প্রতিক স্বাস্থ্য বিজ্ঞপ্তি',
    'No health notices.': 'কোনো স্বাস্থ্য বিজ্ঞপ্তি নেই।',
    'Last backup': 'সর্বশেষ ব্যাকআপ',
    'No backup recorded yet.': 'এখনো কোনো ব্যাকআপ নেই।',
    'Recent activity': 'সাম্প্রতিক কার্যক্রম',
    'Open activity log': 'কার্যক্রম লগ খুলুন',
    'Open system status': 'সিস্টেম অবস্থা খুলুন',
    'When': 'কখন',
    'User': 'ব্যবহারকারী',
    'Action': 'কার্যক্রম',
    'Detail': 'বিবরণ',
    'No activity yet.': 'এখনো কোনো কার্যক্রম নেই।',
    'System': 'সিস্টেম',
    'Active users': 'সক্রিয় ব্যবহারকারী',
    'All users': 'সব ব্যবহারকারী',
    'Roles': 'ভূমিকা',
    'Open approvals': 'চলমান অনুমোদন',
    'waiting at your desk': 'আপনার ডেস্কে অপেক্ষমাণ',
    'Reminders are sent automatically': 'স্মারক স্বয়ংক্রিয়ভাবে পাঠানো হয়',
    'How a Dakbungalow booking is approved': 'ডাকবাংলো বুকিং কীভাবে অনুমোদিত হয়',
    'You check step': 'আপনি যাচাই করেন ধাপ',
    'Your part': 'আপনার অংশ',
    'You can': 'আপনি করতে পারেন',
    'No task is waiting at your desk.': 'আপনার ডেস্কে কোনো কাজ অপেক্ষমাণ নেই।',
    'Only the items your role can use are shown.': 'শুধু আপনার ভূমিকার ব্যবহারযোগ্য বিষয় দেখানো হয়েছে।',
    'Review queue': 'পর্যালোচনা সারি',
    'Check-in desk': 'চেক-ইন ডেস্ক',
    'Staff list': 'কর্মী তালিকা',
    'File register': 'ফাইল রেজিস্টার',
    'File store': 'ফাইল ভান্ডার',
    'All bookings': 'সব বুকিং',
    'HR overview': 'এইচআর সারসংক্ষেপ',
    'Training': 'প্রশিক্ষণ',
    'Site visits': 'সাইট পরিদর্শন',
    'Meeting actions': 'সভার কার্যক্রম',
    'Executive summary': 'নির্বাহী সারসংক্ষেপ',
    'Department summary': 'বিভাগীয় সারসংক্ষেপ',
    'Revenue report': 'রাজস্ব প্রতিবেদন',
    'Support plan': 'সহায়তা পরিকল্পনা',
    'Work': 'কাজ',
    # Booking journey
    'Application status': 'আবেদনের অবস্থা',
    'Waiting here': 'এখানে অপেক্ষমাণ',
    'Next': 'পরবর্তী',
    'Done': 'সম্পন্ন',
    'your desk': 'আপনার ডেস্ক',
    'Your desk': 'আপনার ডেস্ক',
    'Waiting for': 'অপেক্ষমাণ:',
    'to review your application.': 'আপনার আবেদন পর্যালোচনা করবেন।',
    'Application received': 'আবেদন গৃহীত',
    'Booking desk review': 'বুকিং ডেস্ক পর্যালোচনা',
    'Technical review': 'কারিগরি পর্যালোচনা',
    'Executive Officer approval': 'নির্বাহী কর্মকর্তার অনুমোদন',
    'CEO / Chairman approval': 'সিইও / চেয়ারম্যানের অনুমোদন',
    'Permit issued': 'পরমিট ইস্যু',
    'Booking desk': 'বুকিং ডেস্ক',
    'Technical reviewer': 'কারিগরি পর্যালোচক',
    'Executive Officer': 'নির্বাহী কর্মকর্তা',
    'CEO / Chairman': 'সিইও / চেয়ারম্যান',
    'Finance officer': 'অর্থ কর্মকর্তা',
    'Checks the application and documents': 'আবেদন ও নথি যাচাই করেন',
    'Checks the room or hall is ready': 'রুম বা হল প্রস্তুত আছে কি না যাচাই করেন',
    'Approves within the delegated limit': 'অর্পিত সীমার মধ্যে অনুমোদন করেন',
    'Gives the final approval': 'চূড়ান্ত অনুমোদন দেন',
    'Checks the permit at the desk': 'ডেস্কে পরমিট যাচাই করেন',
    'Confirms the payment': 'পেমেন্ট নিশ্চিত করেন',
    'Reviews this application': 'এই আবেদন পর্যালোচনা করেন',
    'Complete payment on the demo gateway': 'ডেমো গেটওয়েতে পেমেন্ট সম্পন্ন করুন',
    'Download and show the permit at reception': 'পরমিট ডাউনলোড করে রিসেপশনে দেখান',
    'The application was rejected. See the approval history for the reason.':
        'আবেদনটি প্রত্যাখ্যাত হয়েছে। কারণ জানতে অনুমোদনের ইতিহাস দেখুন।',
    'The application was cancelled. You can apply again for another date.':
        'আবেদনটি বাতিল হয়েছে। অন্য তারিখের জন্য আবার আবেদন করতে পারেন।',
    'The payment window closed. The hold was released; please apply again.':
        'পেমেন্টের সময়সীমা শেষ হয়েছে। হোল্ড ছেড়ে দেওয়া হয়েছে; আবার আবেদন করুন।',
    'The stay is complete. Thank you for using the Dakbungalow.':
        'অবস্থান সম্পন্ন হয়েছে। ডাকবাংলো ব্যবহারের জন্য ধন্যবাদ।',
    'Approved and paid. Your permit is ready to download and show at reception.':
        'অনুমোদিত ও পরিশোধিত। আপনার পরমিট ডাউনলোড করে রিসেপশনে দেখানোর জন্য প্রস্তুত।',
    'A correction was requested. Reply in the message section below.':
        'সংশোধন অনুরোধ করা হয়েছে। নিচের বার্তা অংশে উত্তর দিন।',
    'Your application is approved. Pay on the demo gateway to confirm the booking.':
        'আপনার আবেদন অনুমোদিত হয়েছে। বুকিং নিশ্চিত করতে ডেমো গেটওয়েতে পেমেন্ট করুন।',
    'Your application is in the queue. The booking desk will review it next.':
        'আপনার আবেদন সারিতে আছে। এরপর বুকিং ডেস্ক পর্যালোচনা করবে।',
    'All approval steps are complete. Payment is next.':
        'সব অনুমোদন ধাপ সম্পন্ন। এরপর পেমেন্ট।',
    'This application is at your desk. Check the documents and forward it.':
        'এই আবেদন আপনার ডেস্কে আছে। নথি যাচাই করে ফরওয়ার্ড করুন।',
    'This application is at your desk. Check the room or hall and recommend it.':
        'এই আবেদন আপনার ডেস্কে আছে। রুম বা হল যাচাই করে সুপারিশ করুন।',
    'This application is at your desk. Approve within the delegated limit or forward it.':
        'এই আবেদন আপনার ডেস্কে আছে। অর্পিত সীমার মধ্যে অনুমোদন করুন বা ফরওয়ার্ড করুন।',
    'This application is at your desk. Give the final approval or reject it.':
        'এই আবেদন আপনার ডেস্কে আছে। চূড়ান্ত অনুমোদন দিন বা প্রত্যাখ্যান করুন।',
    'This application is at your desk.': 'এই আবেদন আপনার ডেস্কে আছে।',
    'Waiting for the next officer to review this application.':
        'পরবর্তী কর্মকর্তার পর্যালোচনার জন্য অপেক্ষা করা হচ্ছে।',
    'hours to decide': 'ঘণ্টায় সিদ্ধান্ত',
    'The applicant pays after final approval': 'চূড়ান্ত অনুমোদনের পর আবেদনকারী পেমেন্ট করেন',
    'forward': 'ফরওয়ার্ড',
    'recommend': 'সুপারিশ',
    'approve': 'অনুমোদন',
    'reject': 'প্রত্যাখ্যান',
    'correct': 'সংশোধন',
    'return': 'ফেরত',
    # Booking step 1
    'Next: review the price and submit': 'পরবর্তী: মূল্য পর্যালোচনা করে জমা দিন',
    'Nothing is submitted at this step and no payment is taken yet.':
        'এই ধাপে কিছু জমা হয় না এবং এখনো কোনো পেমেন্ট নেওয়া হয় না।',
    'Continue to review': 'পর্যালোচনায় এগিয়ে যান',
    # Citizen booking flow
    'Apply for': 'আবেদন করুন',
    'Step 1 of 3 - choose a room or hall and your dates.':
        'ধাপ ১/৩ - কক্ষ বা হল এবং তারিখ নির্বাচন করুন।',
    'Facility details': 'সুবিধার বিবরণ',
    'Choose room and dates': 'কক্ষ ও তারিখ নির্বাচন',
    'Review price and documents': 'মূল্য ও কাগজপত্র যাচাই',
    'Submit and track': 'জমা দিন ও অগ্রগতি দেখুন',
    'Please correct the following:': 'অনুগ্রহ করে নিচের বিষয়গুলো ঠিক করুন:',
    'Choose a room or facility': 'কক্ষ বা সুবিধা নির্বাচন করুন',
    'up to': 'সর্বোচ্চ',
    'guests': 'জন অতিথি',
    'night': 'রাত',
    'No units are published for this facility.': 'এই সুবিধার জন্য কোনো কক্ষ প্রকাশ করা হয়নি।',
    'Tariffs differ by applicant category. The exact breakdown, holiday rate and deposit are shown at the next step before you submit.':
        'আবেদনকারীর ধরন অনুযায়ী শুল্ক ভিন্ন। জমা দেওয়ার আগে পরবর্তী ধাপে সম্পূর্ণ হিসাব, ছুটির দিনের হার ও জামানত দেখানো হবে।',
    'Dates and applicant category': 'তারিখ ও আবেদনকারীর ধরন',
    'Check-in / event date': 'চেক-ইন / অনুষ্ঠানের তারিখ',
    'Check-out (rooms)': 'চেক-আউট (কক্ষের জন্য)',
    'For a conference hall choose the day after the event.': 'কনফারেন্স হলের জন্য অনুষ্ঠানের পরের দিন নির্বাচন করুন।',
    'Applicant category': 'আবেদনকারীর ধরন',
    'Hall slot': 'হলের সময়',
    'Required for conference halls only.': 'শুধু কনফারেন্স হলের জন্য প্রযোজ্য।',
    'Live availability': 'সরাসরি প্রাপ্যতা',
    'Mon': 'সোম', 'Tue': 'মঙ্গল', 'Wed': 'বুধ', 'Thu': 'বৃহস্পতি',
    'Fri': 'শুক্র', 'Sat': 'শনি', 'Sun': 'রবি',
    'free': 'খালি',
    'Full': 'পূর্ণ',
    'How this works': 'এটি যেভাবে কাজ করে',
    'Choose a room and dates. A temporary hold protects the inventory while your application is reviewed.':
        'কক্ষ ও তারিখ নির্বাচন করুন। আবেদন পর্যালোচনার সময় একটি অস্থায়ী হোল্ড কক্ষটি সংরক্ষিত রাখে।',
    'The route and approvers come from the Parishad authority matrix, not from hard-coded rules.':
        'অনুমোদনের ধারা ও অনুমোদনকারী পরিষদের ক্ষমতা তালিকা থেকে নির্ধারিত হয়, কোনো নির্দিষ্ট নিয়মে আবদ্ধ নয়।',
    'After approval you pay on the demo gateway. Payment is confirmed only by a verified signed callback.':
        'অনুমোদনের পর ডেমো গেটওয়েতে পেমেন্ট করবেন। যাচাইকৃত স্বাক্ষরযুক্ত কনফার্মেশন ছাড়া পেমেন্ট নিশ্চিত হয় না।',
    'A permit with a QR verification code is issued once approvals and payment are complete.':
        'সব অনুমোদন ও পেমেন্ট সম্পন্ন হলে QR যাচাই কোডসহ পারমিট ইস্যু হয়।',
    'Review and submit': 'যাচাই ও জমা দিন',
    'Review your application': 'আপনার আবেদন যাচাই করুন',
    'Step 2 of 3 - check the price and submit the details.':
        'ধাপ ২/৩ - মূল্য যাচাই করে তথ্য জমা দিন।',
    'Change room or dates': 'কক্ষ বা তারিখ পরিবর্তন',
    'Applicant and visit details': 'আবেদনকারী ও ভ্রমণের তথ্য',
    'Applicant': 'আবেদনকারী',
    'Purpose of visit / meeting': 'ভ্রমণ / সভার উদ্দেশ্য',
    'e.g. Official field visit, district coordination meeting': 'যেমন: সরকারি মাঠ পরিদর্শন, জেলা সমন্বয় সভা',
    'Number of guests': 'অতিথির সংখ্যা',
    'Contact number': 'যোগাযোগ নম্বর',
    'Sample number only': 'শুধু নমুনা নম্বর',
    'Notes for the booking desk': 'বুকিং ডেস্কের জন্য নোট',
    'Supporting documents': 'সহায়ক কাগজপত্র',
    'Required for': 'প্রয়োজনীয়',
    'In this demo you may submit now and the booking desk can request documents through a clarification message.':
        'এই ডেমোতে এখনই জমা দিতে পারেন; বুকিং ডেস্ক প্রয়োজন হলে অনুরোধ বার্তার মাধ্যমে কাগজপত্র চাইতে পারে।',
    'Attach files (PDF, JPG, PNG, TXT; up to 5 MB each)': 'ফাইল সংযুক্ত করুন (PDF, JPG, PNG, TXT; প্রতিটি সর্বোচ্চ ৫ এমবি)',
    'Files are stored locally. Sample data only.': 'ফাইলগুলো স্থানীয়ভাবে সংরক্ষিত হয়। শুধু নমুনা তথ্য।',
    'Declaration': 'ঘোষণাপত্র',
    'I have read and accept the published terms, tariff, holiday rate, security deposit and the sample cancellation and refund policy. I understand that approval is subject to the Parishad authority matrix and that a permit is issued only after verified payment.':
        'প্রকাশিত শর্তাবলি, শুল্ক, ছুটির দিনের হার, জামানত এবং নমুনা বাতিল ও ফেরত নীতি আমি পড়েছি ও গ্রহণ করেছি। আমি বুঝি যে অনুমোদন পরিষদের ক্ষমতা তালিকার অধীন এবং যাচাইকৃত পেমেন্টের পরেই পারমিট ইস্যু হয়।',
    'Your booking': 'আপনার বুকিং',
    'Facility': 'সুবিধা',
    'Room / hall': 'কক্ষ / হল',
    'Dates': 'তারিখ',
    'to': 'থেকে',
    'Slot': 'সময়',
    'Category': 'ধরন',
    'Charges': 'চার্জ',
    'Security deposit (refundable)': 'জামানত (ফেরতযোগ্য)',
    'Gateway charge (paid by user)': 'গেটওয়ে চার্জ (ব্যবহারকারী পরিশোধিত)',
    'Total payable after approval': 'অনুমোদনের পর মোট প্রদেয়',
    'Payment is collected only after approval. A temporary hold is created now and released if the application is rejected, cancelled or the payment window lapses.':
        'অনুমোদনের পরেই পেমেন্ট গ্রহণ করা হয়। এখন একটি অস্থায়ী হোল্ড তৈরি হয়; আবেদন প্রত্যাখ্যাত, বাতিল বা পেমেন্টের সময় শেষ হলে তা ছেড়ে দেওয়া হয়।',
    'Submit application': 'আবেদন জমা দিন',
    'You will receive a reference number and an acknowledgment.':
        'আপনি একটি রেফারেন্স নম্বর ও প্রাপ্তিস্বীকার পাবেন।',
    'Application submitted': 'আবেদন জমা হয়েছে',
    'Application received': 'আবেদন গৃহীত হয়েছে',
    'Your application reference is': 'আপনার আবেদনের রেফারেন্স নম্বর',
    'Keep this reference. You can track the status from your account or the public tracking page.':
        'এই রেফারেন্সটি সংরক্ষণ করুন। আপনার অ্যাকাউন্ট বা পাবলিক ট্র্যাকিং পাতা থেকে অগ্রগতি দেখতে পারেন।',
    'Status': 'অবস্থা',
    'Total after approval': 'অনুমোদনের পর মোট',
    'Temporary hold': 'অস্থায়ী হোল্ড',
    'Track this application': 'এই আবেদনের অগ্রগতি দেখুন',
    'My applications': 'আমার আবেদনসমূহ',
    'Print acknowledgment': 'প্রাপ্তিস্বীকার প্রিন্ট করুন',
    'A confirmation has been placed in the demo outbox (email/SMS are simulated). The booking desk will review the application next.':
        'ডেমো আউটবক্সে একটি নিশ্চিতকরণ রাখা হয়েছে (ইমেইল/এসএমএস অনুকরণকৃত)। এরপর বুকিং ডেস্ক আবেদনটি পর্যালোচনা করবে।',
    'Your Dakbungalow applications and their current status.':
        'আপনার ডাকবাংলো আবেদনসমূহ ও তাদের বর্তমান অবস্থা।',
    'New booking': 'নতুন বুকিং',
    'You have an unfinished application draft.': 'আপনার একটি অসম্পূর্ণ আবেদন খসড়া আছে।',
    'Resume': 'পুনরায় শুরু',
    'Active applications': 'সক্রিয় আবেদন',
    'Including approvals and payment': 'অনুমোদন ও পেমেন্টসহ',
    'All applications': 'সব আবেদন',
    'Sample records for this account': 'এই অ্যাকাউন্টের নমুনা রেকর্ড',
    'Verification': 'যাচাই',
    'Email + OTP': 'ইমেইল + ওটিপি',
    'Verified': 'যাচাইকৃত',
    'Pending verification': 'যাচাই বাকি',
    'Reference': 'রেফারেন্স',
    'Total': 'মোট',
    'Open': 'খুলুন',
    'You have no applications yet.': 'আপনার এখনো কোনো আবেদন নেই।',
    'Browse the four Dakbungalows': 'চারটি ডাকবাংলো দেখুন',
    'Quick login as any demo account. Password:': 'যেকোনো ডেমো অ্যাকাউন্টে দ্রুত লগইন। পাসওয়ার্ড:',
    'Booking management': 'বুকিং ব্যবস্থাপনা',
    'Application PDF': 'আবেদনের PDF',
    'Permit': 'পারমিট',
    'Receipt': 'রসিদ',
    'Correction or clarification requested.': 'সংশোধন বা স্পষ্টীকরণ চাওয়া হয়েছে।',
    'Read the latest message in the thread below, attach any evidence and reply. Your application is paused until you respond.':
        'নিচের বার্তায় সর্বশেষ নির্দেশনা পড়ুন, প্রয়োজনীয় প্রমাণ সংযুক্ত করুন এবং উত্তর দিন। আপনার উত্তর দেওয়ার আগে আবেদন স্থগিত থাকবে।',
    'Application rejected.': 'আবেদন প্রত্যাখ্যাত হয়েছে।',
    'See the approval history for the reason.': 'কারণ জানতে অনুমোদনের ইতিহাস দেখুন।',
    'Payment window expired.': 'পেমেন্টের সময়সীমা শেষ হয়েছে।',
    'The hold was released. You may apply again for the facility.':
        'হোল্ডটি ছেড়ে দেওয়া হয়েছে। আপনি এই সুবিধার জন্য আবার আবেদন করতে পারেন।',
    'Approved - payment required': 'অনুমোদিত - পেমেন্ট প্রয়োজন',
    'Demo gateway': 'ডেমো গেটওয়ে',
    'Amount payable': 'প্রদেয় অর্থ',
    'Pay before': 'পেমেন্ট করুন',
    'The hold is released if the window closes.': 'সময়সীমা শেষ হলে হোল্ড ছেড়ে দেওয়া হবে।',
    'Pay on the demo gateway': 'ডেমো গেটওয়েতে পেমেন্ট করুন',
    'Application timeline': 'আবেদনের সময়রেখা',
    'Approval route and decisions': 'অনুমোদনের ধারা ও সিদ্ধান্ত',
    'Workflow detail': 'প্রক্রিয়ার বিবরণ',
    'Now at:': 'বর্তমানে:',
    'Step': 'ধাপ',
    'Actor': 'কর্মকর্তা',
    'Decision': 'সিদ্ধান্ত',
    'When': 'সময়',
    'Comments': 'মন্তব্য',
    'Submitted': 'জমা দেওয়া হয়েছে',
    'Respond in the message thread to resume the route.':
        'ধারা চালু করতে বার্তার মাধ্যমে উত্তর দিন।',
    'Messages and clarification': 'বার্তা ও স্পষ্টীকরণ',
    'System': 'সিস্টেম',
    'internal note': 'অভ্যন্তরীণ নোট',
    'No messages yet. The booking desk will contact you here if anything needs clarification.':
        'এখনো কোনো বার্তা নেই। কোনো বিষয় স্পষ্ট করার প্রয়োজন হলে বুকিং ডেস্ক এখানে যোগাযোগ করবে।',
    'Message to the applicant': 'আবেদনকারীকে বার্তা',
    'Your reply': 'আপনার উত্তর',
    'Provide the requested clarification or information': 'চাওয়া স্পষ্টীকরণ বা তথ্য দিন',
    'Write a message': 'বার্তা লিখুন',
    'Internal note (not emailed to the applicant)': 'অভ্যন্তরীণ নোট (আবেদনকারীকে পাঠানো হয় না)',
    'Send message': 'বার্তা পাঠান',
    'Documents': 'কাগজপত্র',
    'Document': 'নথি',
    'Type': 'ধরন',
    'Uploaded': 'আপলোড হয়েছে',
    'No documents attached.': 'কোনো কাগজপত্র সংযুক্ত নেই।',
    'Label (e.g. service ID)': 'লেবেল (যেমন: সার্ভিস আইডি)',
    'Upload': 'আপলোড',
    'Booking details': 'বুকিংয়ের বিবরণ',
    'Guests': 'অতিথি',
    'Purpose': 'উদ্দেশ্য',
    'Contact': 'যোগাযোগ',
    'Price breakdown': 'মূল্যের হিসাব',
    'Security deposit': 'জামানত',
    'Gateway charge': 'গেটওয়ে চার্জ',
    'Payment:': 'পেমেন্ট:',
    'Transaction': 'লেনদেন',
    'Refund:': 'ফেরত:',
    'under the sample policy.': 'নমুনা নীতির অধীনে।',
    'Permit and verification': 'পারমিট ও যাচাই',
    'Permit QR code': 'পারমিট QR কোড',
    'Download permit PDF': 'পারমিট PDF ডাউনলোড',
    'Public verification page': 'পাবলিক যাচাই পাতা',
    'Present this at reception. The QR opens the verification page.':
        'রিসেপশনে এটি দেখান। QR স্ক্যান করলে যাচাই পাতা খুলবে।',
    'Staff actions': 'কর্মকর্তার কার্যাবলি',
    'Checked in': 'চেক-ইন হয়েছে',
    'Checked out': 'চেক-আউট হয়েছে',
    'Record check-in': 'চেক-ইন লিপিবদ্ধ করুন',
    'Record check-out': 'চেক-আউট লিপিবদ্ধ করুন',
    'Cancel with reason': 'কারণসহ বাতিল করুন',
    'Reason recorded in the audit log': 'কারণ অডিট লগে সংরক্ষিত হবে',
    'Cancel this booking? A paid booking creates a refund request.':
        'এই বুকিং বাতিল করবেন? পরিশোধিত বুকিং হলে ফেরতের আবেদন তৈরি হবে।',
    'Cancel booking': 'বুকিং বাতিল',
    'Approval decisions are taken in': 'অনুমোদনের সিদ্ধান্ত নেওয়া হয়',
    'My Tasks': 'আমার কাজ',
    'and are recorded against the authority matrix.': 'এবং ক্ষমতা তালিকার বিপরীতে লিপিবদ্ধ হয়।',
    'Need to cancel?': 'বাতিল করতে চান?',
    'Refund under the sample policy:': 'নমুনা নীতি অনুযায়ী ফেরত:',
    'Reason for cancellation': 'বাতিলের কারণ',
    'Request cancellation of this booking?': 'এই বুকিং বাতিলের অনুরোধ করবেন?',
    'Request cancellation': 'বাতিলের অনুরোধ',
    # Role names used in the demo account switcher
    'Citizen / Applicant': 'নাগরিক / আবেদনকারী',
    'Dealing Assistant / Booking Desk': 'ডিলিং অ্যাসিস্ট্যান্ট / বুকিং ডেস্ক',
    'Assistant Engineer / Technical Reviewer': 'সহকারী প্রকৌশলী / কারিগরি পর্যালোচক',
    'Executive Officer / Authorized Reviewer': 'নির্বাহী কর্মকর্তা / ক্ষমতাপ্রাপ্ত পর্যালোচক',
    'CEO / Chairman / Authorized Approver': 'সিইও / চেয়ারম্যান / ক্ষমতাপ্রাপ্ত অনুমোদনকারী',
    'Reception / Facility Operator': 'রিসেপশন / সুবিধা পরিচালক',
    'Finance / Accounts Officer': 'অর্থ / হিসাব কর্মকর্তা',
    'HR Admin': 'এইচআর প্রশাসক',
    'Supervisor': 'সুপারভাইজার',
    'Employee': 'কর্মচারী',
    'Department Head': 'বিভাগীয় প্রধান',
    'Registry / Section Officer': 'রেজিস্ট্রি / শাখা কর্মকর্তা',
    'Project Admin / Officer': 'প্রকল্প প্রশাসক / কর্মকর্তা',
    'Inspector': 'পরিদর্শক',
    'Meeting Secretary / Coordinator': 'সভা সচিব / সমন্বয়ক',
    'Management / Auditor': 'ব্যবস্থাপনা / নিরীক্ষক',
    'System Administrator': 'সিস্টেম প্রশাসক',
    'Delivery': 'বাস্তবায়ন',
    'Dakbungalow': 'ডাকবাংলো',
    'Approver': 'অনুমোদনকারী',
    # Secondary staff pages
    'Booking management': 'বুকিং ব্যবস্থাপনা',
    'All Dakbungalow applications, filters, status and approval history.':
        'সব ডাকবাংলো আবেদন, ফিল্টার, অবস্থা ও অনুমোদনের ইতিহাস।',
    'Export CSV': 'সিএসভি রপ্তানি',
    'All facilities': 'সব সুবিধা',
    'verify booking codes and record check-in / check-out.':
        'বুকিং কোড যাচাই করুন এবং চেক-ইন / চেক-আউট লিপিবদ্ধ করুন।',
    'Booking list': 'বুকিং তালিকা',
    'Users & roles': 'ব্যবহারকারী ও ভূমিকা',
    'Accounts, role display names and the server-enforced permission matrix.':
        'অ্যাকাউন্ট, ভূমিকার প্রদর্শন নাম এবং সার্ভার-প্রয়োগকৃত অনুমতি তালিকা।',
    'Role permissions': 'ভূমিকার অনুমতি',
    'Roles, display names & permission matrix': 'ভূমিকা, প্রদর্শন নাম ও অনুমতি তালিকা',
    'Edit role display names and tick the permissions each role receives. Changes apply immediately and are audited.':
        'ভূমিকার প্রদর্শন নাম সম্পাদনা করুন এবং প্রতিটি ভূমিকার অনুমতি টিক দিন। পরিবর্তন সঙ্গে সঙ্গে কার্যকর হয় ও অডিট হয়।',
    'Accounts': 'অ্যাকাউন্ট',
    'Facilities and availability': 'সুবিধা ও প্রাপ্যতা',
    'Four sample Dakbungalows, room and hall inventory, tariffs and blackout dates.':
        'চারটি নমুনা ডাকবাংলো, কক্ষ ও হলের তালিকা, শুল্ক এবং বন্ধের তারিখ।',
    'Payments and reconciliation': 'পেমেন্ট ও মিলকরণ',
    'Demand versus collection, gateway references, failed and duplicate callbacks and refunds.':
        'চাহিদা ও আদায়, গেটওয়ে রেফারেন্স, ব্যর্থ ও পুনরাবৃত্ত কনফার্মেশন এবং ফেরত।',
    'Cancellation refund requests under the published sample policy. The gateway refund is simulated.':
        'প্রকাশিত নমুনা নীতি অনুযায়ী বাতিলের ফেরত আবেদন। গেটওয়ে ফেরত অনুকরণকৃত।',
    'Pending value:': 'অপেক্ষমাণ অর্থ:',
    'Who may give final approval, in which request category and up to what amount. Approvals outside this matrix are refused by the server.':
        'কে কোন ধরনের আবেদনে ও সর্বোচ্চ কত অর্থ পর্যন্ত চূড়ান্ত অনুমোদন দিতে পারবেন। এই তালিকার বাইরের অনুমোদন সার্ভার গ্রহণ করে না।',
    'Routes are stored in the database: ordered steps, role, allowed decisions and conditional rules. Nothing is hard-coded in module views.':
        'অনুমোদনের ধারা ডেটাবেসে সংরক্ষিত: ক্রমানুসারে ধাপ, ভূমিকা, অনুমোদিত সিদ্ধান্ত ও শর্তাধীন নিয়ম। কোনো কিছু কোডে নির্দিষ্ট করা নেই।',
    'New template': 'নতুন টেমপ্লেট',
    'Track an application': 'আবেদনের অগ্রগতি দেখুন',
    'Enter the booking reference printed on your acknowledgement or permit. Public tracking shows status only; documents and personal details require sign-in.':
        'আপনার প্রাপ্তিস্বীকার বা পারমিটে মুদ্রিত বুকিং রেফারেন্স লিখুন। পাবলিক ট্র্যাকিং শুধু অবস্থা দেখায়; কাগজপত্র ও ব্যক্তিগত তথ্যের জন্য সাইন-ইন প্রয়োজন।',
    'Roles & permissions': 'ভূমিকা ও অনুমতি',
    'Verify account': 'অ্যাকাউন্ট যাচাই',
    'Access denied': 'প্রবেশ অনুমোদিত নয়',
    'Not found': 'পাওয়া যায়নি',
    'Server error': 'সার্ভার ত্রুটি',
    'Security and backup': 'নিরাপত্তা ও ব্যাকআপ',
    'Permit verification': 'পারমিট যাচাই',
    'Document access log': 'নথি প্রবেশের লগ',
    'Training and expiry': 'প্রশিক্ষণ ও মেয়াদ',
    'Booking and revenue report': 'বুকিং ও রাজস্ব প্রতিবেদন',
    'Demo payment gateway': 'ডেমো পেমেন্ট গেটওয়ে',
    'Deliverables and UAT': 'প্রদেয় ও ইউএটি',
    'Workflow step': 'প্রক্রিয়ার ধাপ',
    'Workflow template': 'প্রক্রিয়া টেমপ্লেট',
    'Task': 'কাজ',
    'Settings and master data': 'সেটিংস ও মূল তথ্য',
    'Deliverables & UAT': 'প্রদেয় ও ইউএটি',
    'completed stays': 'সম্পন্ন অবস্থান',
    'records': 'রেকর্ড',
    'active': 'সক্রিয়',
    'day(s)': 'দিন',
    'phases complete': 'ধাপ সম্পন্ন',
    'paid or completed': 'পরিশোধিত বা সম্পন্ন',
    'refunded': 'ফেরত দেওয়া',
    'net': 'নিট',
    'open support ticket(s)': 'খোলা সহায়তা টিকিট',
    'matching entries': 'মিলে যাওয়া এন্ট্রি',
    'Logins, decisions, settings changes, payments, exports and backups are recorded.':
        'লগইন, সিদ্ধান্ত, সেটিংস পরিবর্তন, পেমেন্ট, এক্সপোর্ট ও ব্যাকআপ রেকর্ড করা হয়।',
    'Demo accounts and the password': 'ডেমো অ্যাকাউন্ট ও পাসওয়ার্ড',
    'are created by': 'তৈরি হয়',
    '. Role names are editable in the matrix; permissions are enforced on the server for every page and file.':
        '। ভূমিকার নাম ম্যাট্রিক্সে সম্পাদনাযোগ্য; প্রতিটি পৃষ্ঠা ও ফাইলে অনুমতি সার্ভারে প্রয়োগ করা হয়।',
    'Facility / unit': 'স্থাপনা / ইউনিট',
    'Friday and Saturday nights are charged at the holiday tariff.':
        'শুক্র ও শনিবার রাতে ছুটির দিনের হার প্রযোজ্য।',
    'A security deposit may apply; the exact amount is shown before payment.':
        'নিরাপত্তা জামানত প্রযোজ্য হতে পারে; সঠিক পরিমাণ পেমেন্টের আগে দেখানো হয়।',
    'Sample refund policy': 'নমুনা রিফান্ড নীতি',
    'No refund requests match the filter.': 'কোনো রিফান্ড অনুরোধ ফিল্টারের সাথে মেলেনি।',
    '100% if cancelled 7 or more days before check-in; 50% at 3-6 days; 25% at 1-2 days; 0% on the check-in day. The policy is editable in Settings. Refunds are computed on the total paid and are processed in the demo gateway only; no real money moves.':
        'চেক-ইনের ৭ বা তার বেশি দিন আগে বাতিলে ১০০%; ৩-৬ দিনে ৫০%; ১-২ দিনে ২৫%; চেক-ইনের দিনে ০%। নীতিটি সেটিংসে সম্পাদনাযোগ্য। রিফান্ড মোট পরিশোধিত অর্থের ওপর গণনা করা হয় এবং শুধু ডেমো গেটওয়েতে প্রক্রিয়া করা হয়; প্রকৃত অর্থ লেনদেন হয় না।',
    'Daily attendance for': 'দৈনিক উপস্থিতি',
    'Existing records are shown and can be corrected.': 'বিদ্যমান রেকর্ড দেখানো হয়েছে এবং সংশোধন করা যাবে।',
    'booking(s) in this view. Values come from stored bookings and verified payments.':
        'এই দৃশ্যে বুকিং। মান সংরক্ষিত বুকিং ও যাচাইকৃত পেমেন্ট থেকে আসে।',
    'Edit template': 'টেমপ্লেট সম্পাদনা',
    'Add step': 'ধাপ যোগ করুন',
    'Role': 'ভূমিকা',
    'Gazipur Zila Parishad': 'গাজীপুর জেলা পরিষদ',
    'A quiet guesthouse for official visits to the Kaliakair upazila complex.':
        'কালিয়াকৈর উপজেলা কমপ্লেক্সে সরকারি সফরের জন্য একটি শান্ত অতিথিশালা।',
    'A small guesthouse for field officers and visiting officials in Kapasia.':
        'কাপাসিয়ায় মাঠ কর্মকর্তা ও সফররত কর্মকর্তাদের জন্য একটি ছোট অতিথিশালা।',
    'The largest facility, with family rooms, suites and a training hall.':
        'সবচেয়ে বড় সুবিধা, পারিবারিক রুম, স্যুট ও একটি প্রশিক্ষণ হলসহ।',
    'Official meeting, Individual stay, Government delegation, Training':
        'সরকারি সভা, ব্যক্তিগত অবস্থান, সরকারি প্রতিনিধি দল, প্রশিক্ষণ',
    'Permitted booking types:': 'অনুমোদিত বুকিংয়ের ধরন:',
    'Check-in from 12:00, check-out by 11:00. Photo ID required. No smoking indoors. Sample rules for the demo.':
        'চেক-ইন দুপুর ১২:০০ থেকে, চেক-আউট সকাল ১১:০০টার মধ্যে। ছবিসহ পরিচয়পত্র আবশ্যক। ভেতরে ধূমপান নিষিদ্ধ। ডেমোর জন্য নমুনা নিয়ম।',
    'Closed': 'বন্ধ',
    'Full': 'পূর্ণ',
    'Contact phone': 'যোগাযোগ ফোন',
    'Terms': 'শর্তাবলি',
    'Check in': 'চেক-ইন',
    'Check out': 'চেক-আউট',
    'This field is required.': 'এই ঘরটি পূরণ করা আবশ্যক।',
    'Enter a valid date.': 'সঠিক তারিখ দিন।',
    'Enter a valid integer.': 'সঠিক পূর্ণসংখ্যা দিন।',
    'Enter a valid value.': 'সঠিক মান দিন।',
    'Ensure this value is greater than or equal to 1.': 'এই মান ১ বা তার বেশি হতে হবে।',
    'Select a valid choice. That choice is not one of the available choices.': 'সঠিক বিকল্প নির্বাচন করুন।',
    'This field may not be null.': 'এই ঘরটি খালি রাখা যাবে না।',
    'Enter a number.': 'একটি সংখ্যা দিন।',
}

BN_EXTRA = {
    'Meeting calendar': 'সভা ক্যালেন্ডার',
    'System health': 'সিস্টেম স্বাস্থ্য',
    'Human resources': 'মানবসম্পদ',
    'Records': 'নথি',
    'Included & chargeable': 'অন্তর্ভুক্ত ও চার্জযোগ্য',
    'UAT checklist': 'ইউএটি চেকলিস্ট',
    'Deliverables': 'প্রদেয়সমূহ',
    '45-day plan': '৪৫ দিনের পরিকল্পনা',
    'Included in routine maintenance': 'নিয়মিত রক্ষণাবেক্ষণে অন্তর্ভুক্ত',
    'Chargeable / client-paid': 'চার্জযোগ্য / ক্লায়েন্ট-পরিশোধিত',
    'Availability calendar': 'প্রাপ্যতা ক্যালেন্ডার',
    'Browse facilities': 'সুবিধা ব্রাউজ করুন',
    'Sample facilities': 'নমুনা সুবিধা',
    'Public citizen': 'সাধারণ নাগরিক',
    'Government official': 'সরকারি কর্মকর্তা',
    'Organization': 'সংস্থা',
    'Staff and citizen access to the integrated platform.': 'কর্মকর্তা ও নাগরিকদের জন্য সমন্বিত প্ল্যাটফর্মে প্রবেশ।',
    'Username': 'ব্যবহারকারীর নাম',
    'New citizen applicant?': 'নতুন নাগরিক আবেদনকারী?',
    'Demo quick sign-in - password': 'দ্রুত ডেমো প্রবেশ - পাসওয়ার্ড',
    'All demo accounts share the same password. Roles are enforced on the server, not only in the menu.': 'সব ডেমো অ্যাকাউন্টের পাসওয়ার্ড একই। ভূমিকা কেবল মেনুতে নয়, সার্ভারেও নিয়ন্ত্রিত হয়।',
    'Integrated Digital Platform': 'সমন্বিত ডিজিটাল প্ল্যাটফর্ম',
    'One platform for records, approvals, projects and Dakbungalow bookings.': 'নথি, অনুমোদন, প্রকল্প ও ডাকবাংলো বুকিংয়ের একক প্ল্যাটফর্ম।',
    'Integrated digital automation, management information and citizen-facing Dakbungalow e-booking with verified payment confirmation.': 'সমন্বিত ডিজিটাল অটোমেশন, ব্যবস্থাপনা তথ্য এবং যাচাইকৃত পেমেন্ট নিশ্চিতকরণসহ নাগরিকদের জন্য ডাকবাংলো ই-বুকিং।',
    'Seven modules sharing one identity, audit trail and workflow engine': 'সাতটি মডিউল, একই পরিচয়, অডিট ট্রেইল ও ওয়ার্কফ্লো ইঞ্জিন',
    'Configurable approval routes and an editable authority matrix': 'কনফিগারযোগ্য অনুমোদন পথ ও সম্পাদনযোগ্য ক্ষমতা ম্যাট্রিক্স',
    'Signed gateway callbacks, printable permits and QR verification': 'স্বাক্ষরিত গেটওয়ে কলব্যাক, মুদ্রণযোগ্য পারমিট ও QR যাচাই',
    'Role-based dashboards with least-privilege enforcement': 'ভূমিকা-ভিত্তিক ড্যাশবোর্ড ও সর্বনিম্ন ক্ষমতা প্রয়োগ',
    'Complements D-Nothi/e-Nothi, e-GP and statutory approvals; does not replace or bypass them.': 'ডি-নথি/ই-নথি, ই-জিপি ও বিধিবদ্ধ অনুমোদনের সহায়ক; এগুলো প্রতিস্থাপন বা বাইপাস করে না।',
    'Prepared by': 'প্রস্তুত করেছে',
    'This platform complements D-Nothi/e-Nothi, e-GP and statutory approvals; it does not replace or bypass them.': 'এই প্ল্যাটফর্ম ডি-নথি/ই-নথি, ই-জিপি ও বিধিবদ্ধ অনুমোদনের সহায়ক; এগুলো প্রতিস্থাপন বা বাইপাস করে না।',
    'This system complements D-Nothi/e-Nothi, e-GP and other mandatory government platforms. It does not replace or bypass statutory approval authority. Tariffs, rules and approval routes shown are sample values.': 'এই সিস্টেম ডি-নথি/ই-নথি, ই-জিপি ও অন্যান্য বাধ্যতামূলক সরকারি প্ল্যাটফর্মের সহায়ক। এটি বিধিবদ্ধ অনুমোদনের ক্ষমতা প্রতিস্থাপন বা বাইপাস করে না। এখানে দেখানো ভাড়া, নিয়ম ও অনুমোদন পথ নমুনা মান।',
    'Official booking service': 'সরকারি বুকিং সেবা',
    'Book a Gazipur Zila Parishad Dakbungalow': 'গাজীপুর জেলা পরিষদ ডাকবাংলো বুক করুন',
    'Four Parishad Dakbungalows with rooms, VIP suites and conference halls. Check live availability, apply online, track approval and pay securely.': 'রুম, ভিআইপি স্যুট ও কনফারেন্স হলসহ চারটি জেলা পরিষদ ডাকবাংলো। লাইভ প্রাপ্যতা দেখুন, অনলাইনে আবেদন করুন, অনুমোদন ট্র্যাক করুন এবং নিরাপদে পেমেন্ট করুন।',
    'All four facilities': 'চারটি সুবিধাই',
    'Check availability': 'প্রাপ্যতা দেখুন',
    'Approved Dakbungalows': 'অনুমোদিত ডাকবাংলো',
    'Online': 'অনলাইন',
    'Application and approval tracking': 'আবেদন ও অনুমোদন ট্র্যাকিং',
    'Signed payment confirmation': 'স্বাক্ষরিত পেমেন্ট নিশ্চিতকরণ',
    'Available facilities': 'উপলব্ধ সুবিধা',
    'Availability for': 'প্রাপ্যতা',
    'Showing sample inventory of rooms and halls.': 'রুম ও হলের নমুনা তালিকা দেখানো হচ্ছে।',
    'room(s) / hall(s)': 'রুম / হল',
    'From': 'শুরু',
    'Tariff on request': 'ভাড়া অনুরোধে',
    'No facilities are published yet.': 'এখনো কোনো সুবিধা প্রকাশ করা হয়নি।',
    'Browse and choose': 'দেখুন ও বেছে নিন',
    'See facilities, rooms, photos, tariffs, blackout dates and live availability.': 'সুবিধা, রুম, ছবি, ভাড়া, বন্ধের তারিখ ও লাইভ প্রাপ্যতা দেখুন।',
    'Apply with documents': 'নথিসহ আবেদন',
    'Register, choose dates and attach the documents for your category.': 'নিবন্ধন করুন, তারিখ বেছে নিন এবং আপনার শ্রেণির নথি সংযুক্ত করুন।',
    'Track approval': 'অনুমোদন ট্র্যাক',
    'Follow every step from the booking desk to the authorised approver.': 'বুকিং ডেস্ক থেকে অনুমোদিত কর্মকর্তা পর্যন্ত প্রতিটি ধাপ অনুসরণ করুন।',
    'Pay and get the permit': 'পেমেন্ট করুন ও পারমিট নিন',
    'Pay through the gateway and download the permit with a verification QR code.': 'গেটওয়ে দিয়ে পেমেন্ট করুন এবং যাচাই QR কোডসহ পারমিট ডাউনলোড করুন।',
    'Before you apply': 'আবেদনের আগে',
    'Documents by category': 'শ্রেণি অনুযায়ী নথি',
    'Government official: service ID or office order.': 'সরকারি কর্মকর্তা: সার্ভিস আইডি বা অফিস আদেশ।',
    'Public citizen: national ID and a contact number.': 'সাধারণ নাগরিক: জাতীয় পরিচয়পত্র ও একটি যোগাযোগ নম্বর।',
    'Organization: request letter on letterhead.': 'সংস্থা: লেটারহেডে অনুরোধপত্র।',
    'Sample rules': 'নমুনা নিয়ম',
    'Friday and Saturday nights use the holiday tariff.': 'শুক্র ও শনিবার রাতে ছুটির দিনের ভাড়া প্রযোজ্য।',
    'A security deposit may apply and is shown before payment.': 'নিরাপত্তা জামানত প্রযোজ্য হতে পারে, যা পেমেন্টের আগে দেখানো হয়।',
    'Technical review for conference halls and VIP suites.': 'কনফারেন্স হল ও ভিআইপি স্যুটের জন্য কারিগরি পর্যালোচনা।',
    'Not a statutory platform': 'বিধিবদ্ধ প্ল্যাটফর্ম নয়',
    'This portal complements D-Nothi/e-Nothi, e-GP and statutory approvals. It does not replace or bypass them.': 'এই পোর্টাল ডি-নথি/ই-নথি, ই-জিপি ও বিধিবদ্ধ অনুমোদনের সহায়ক। এটি সেগুলো প্রতিস্থাপন বা বাইপাস করে না।',
    'approved booking(s) passed the payment window.': 'অনুমোদিত বুকিং পেমেন্টের সময়সীমা অতিক্রম করেছে।',
    'refund request(s) awaiting finance action.': 'ফেরত অনুরোধ অর্থ বিভাগের ব্যবস্থা গ্রহণের অপেক্ষায়।',
    'approval task(s) are overdue.': 'অনুমোদনের কাজ মেয়াদোত্তীর্ণ হয়েছে।',
    'Approval waiting at your desk': 'আপনার ডেস্কে অনুমোদন অপেক্ষমাণ',
    'A booking application needs the final approval today.': 'একটি বুকিং আবেদনের আজ চূড়ান্ত অনুমোদন প্রয়োজন।',
    'Meeting today: Weekly coordination with department heads': 'আজ সভা: বিভাগীয় প্রধানদের সঙ্গে সাপ্তাহিক সমন্বয়',
    'Starts at 10:30 AM in the conference room, Parishad office.': 'সকাল ১০:৩০টায় পরিষদ কার্যালয়ের কনফারেন্স রুমে শুরু হবে।',
    'Revenue summary for November': 'নভেম্বরের রাজস্ব সারসংক্ষেপ',
    'This month’s collections and pending payments are ready in the executive summary.': 'এই মাসের আদায় ও বকেয়া পেমেন্ট নির্বাহী সারসংক্ষেপে প্রস্তুত।',
    'Nightly backup completed': 'রাতের ব্যাকআপ সম্পন্ন',
    'The database backup finished and the integrity check passed.': 'ডেটাবেজ ব্যাকআপ শেষ হয়েছে এবং অখণ্ডতা যাচাই সফল হয়েছে।',
    'System health summary': 'সিস্টেম স্বাস্থ্য সারসংক্ষেপ',
    'No errors were recorded in the last 24 hours.': 'গত ২৪ ঘণ্টায় কোনো ত্রুটি রেকর্ড হয়নি।',
    'Weekly coordination with department heads': 'বিভাগীয় প্রধানদের সঙ্গে সাপ্তাহিক সমন্বয়',
    'Monthly coordination meeting': 'মাসিক সমন্বয় সভা',
    'Budget review for the next quarter': 'আগামী প্রান্তিকের বাজেট পর্যালোচনা',
    'Dakbungalow tariff review': 'ডাকবাংলো ভাড়া পর্যালোচনা',
    'Health camp coordination': 'স্বাস্থ্য শিবির সমন্বয়',
    'Inter-agency disaster preparedness': 'আন্তঃসংস্থা দুর্যোগ প্রস্তুতি',
    'Project steering committee': 'প্রকল্প স্টিয়ারিং কমিটি',
    'Records digitisation review': 'নথি ডিজিটাইজেশন পর্যালোচনা',
    'Year-end procurement planning': 'বর্ষশেষ ক্রয় পরিকল্পনা',
    'Conference room, Parishad office': 'কনফারেন্স রুম, পরিষদ কার্যালয়',
    'Executive Officer chamber': 'নির্বাহী কর্মকর্তার কক্ষ',
    'Health office': 'স্বাস্থ্য অফিস',
    'Registry room': 'রেজিস্ট্রি কক্ষ',
    'Scheduled': 'নির্ধারিত',
    'Held': 'অনুষ্ঠিত',
    'Cancelled': 'বাতিল',
    'CEO / Chairman final approval': 'সিইও / চেয়ারম্যানের চূড়ান্ত অনুমোদন',
    'No further detail.': 'অতিরিক্ত বিবরণ নেই।',
    'Gazipur Sadar Dakbungalow': 'গাজীপুর সদর ডাকবাংলো',
    'Kaliakair Dakbungalow': 'কালিয়াকৈর ডাকবাংলো',
    'Kapasia Dakbungalow': 'কাপাসিয়া ডাকবাংলো',
    'Sreepur Dakbungalow': 'শ্রীপুর ডাকবাংলো',
    'Conference Hall': 'কনফারেন্স হল',
    'Conference Room': 'কনফারেন্স রুম',
    'Meeting Hall': 'মিটিং হল',
    'Training Hall': 'প্রশিক্ষণ হল',
    'Room 1 - Standard': 'রুম ১ - স্ট্যান্ডার্ড',
    'Room 2 - Standard': 'রুম ২ - স্ট্যান্ডার্ড',
    'Room 3 - Standard': 'রুম ৩ - স্ট্যান্ডার্ড',
    'Room 3 - Family': 'রুম ৩ - ফ্যামিলি',
    'Room 4 - Family': 'রুম ৪ - ফ্যামিলি',
    'Room 5 - Family': 'রুম ৫ - ফ্যামিলি',
    'VIP Suite': 'ভিআইপি স্যুট',
    'VIP Suite 1': 'ভিআইপি স্যুট ১',
    'VIP Suite 2': 'ভিআইপি স্যুট ২',
    'Information': 'তথ্য',
    'Warning': 'সতর্কতা',
    'Error': 'ত্রুটি',
    'Settings change': 'সেটিংস পরিবর্তন',
    'File movement': 'নথি স্থানান্তর',
    'Export': 'রপ্তানি',
    'Application started': 'অ্যাপ্লিকেশন চালু হয়েছে',
    'Backup completed': 'ব্যাকআপ সম্পন্ন হয়েছে',
    'Database connectivity check passed': 'ডেটাবেজ সংযোগ পরীক্ষা সফল',
    'Nightly maintenance placeholder completed': 'রাতের রক্ষণাবেক্ষণ সম্পন্ন',
    'Payment callback with an invalid signature was rejected (sample)': 'অবৈধ স্বাক্ষরযুক্ত পেমেন্ট কলব্যাক প্রত্যাখ্যাত হয়েছে (নমুনা)',
    'Report export completed': 'প্রতিবেদন রপ্তানি সম্পন্ন',
    'Two workflow tasks are overdue and awaiting escalation': 'দুটি ওয়ার্কফ্লো কাজ মেয়াদোত্তীর্ণ এবং এস্কেলেশনের অপেক্ষায়',
    'Vendored static assets loaded': 'স্ট্যাটিক ফাইল লোড হয়েছে',
    'Full day / overnight': 'পূর্ণ দিন / রাত',
    'Morning (09:00-13:00)': 'সকাল (০৯:০০-১৩:০০)',
    'Afternoon (13:00-17:00)': 'দুপুর (১৩:০০-১৭:০০)',
    'Evening (17:00-21:00)': 'সন্ধ্যা (১৭:০০-২১:০০)',
    'Room': 'রুম',
    'VIP suite': 'ভিআইপি স্যুট',
    'Conference hall': 'কনফারেন্স হল',
    'Meeting hall': 'মিটিং হল',
    'Training hall': 'প্রশিক্ষণ হল',
    'view': 'দেখা',
    'citizen': 'সাধারণ নাগরিক',
    'government': 'সরকারি কর্মকর্তা',
    'organization': 'সংস্থা',
    'National ID (sample) and a contact number': 'জাতীয় পরিচয়পত্র (নমুনা) ও একটি যোগাযোগ নম্বর',
    'Government service ID or office order (sample)': 'সরকারি পরিচয়পত্র বা অফিস আদেশ (নমুনা)',
    'Organisation request letter on letterhead (sample)': 'লেটারহেডে সংস্থার অনুরোধপত্র (নমুনা)',
    'Your role does not include this permission. Access is enforced on the server, not only by hiding the menu link.': 'আপনার ভূমিকায় এই অনুমতি নেই। এটি শুধু মেনু লুকিয়ে নয়, সার্ভারেই নিয়ন্ত্রিত হয়।',
    'a guest': 'অতিথি',
    'Back to dashboard': 'ড্যাশবোর্ডে ফিরে যান',
    'Public home': 'পাবলিক হোম',
    'If you believe this is wrong, ask an administrator to review your role in': 'এটি ভুল মনে হলে প্রশাসককে আপনার ভূমিকা পর্যালোচনা করতে বলুন —',
    'Users and roles': 'ব্যবহারকারী ও ভূমিকা',
    'Approvals waiting': 'অনুমোদনের অপেক্ষায়',
    'Waiting at your desk': 'আপনার ডেস্কে অপেক্ষমাণ',
    'Arrivals today': 'আজ আগমন',
    'Guests to check in at the desk': 'ডেস্কে চেক-ইন করার অতিথি',
    'Refunds to process': 'ফেরত প্রক্রিয়ার অপেক্ষায়',
    'Requests waiting for finance': 'অর্থ শাখার অপেক্ষায় অনুরোধ',
    'Staff present today': 'আজ উপস্থিত কর্মী',
    'Marked on the attendance register': 'উপস্থিতি খাতায় লিপিবদ্ধ',
    'Meetings today': 'আজকের সভা',
    'Scheduled for today': 'আজকের জন্য নির্ধারিত',
    'A new booking application is waiting for completeness review.': 'সম্পূর্ণতা যাচাইয়ের জন্য একটি নতুন বুকিং আবেদন অপেক্ষা করছে।',
    'Mark all read': 'সব পড়া হয়েছে বলে চিহ্নিত করুন',
    'Unread': 'অপঠিত',
    'Notification': 'বিজ্ঞপ্তি',
    'No notifications yet.': 'এখনো কোনো বিজ্ঞপ্তি নেই।',
    'In-app': 'অ্যাপের ভেতরে',
    'In-app notifications for your account. Email and SMS copies are in the demo outbox.': 'আপনার অ্যাকাউন্টের অ্যাপ-বিজ্ঞপ্তি। ইমেইল ও এসএমএসের অনুলিপি ডেমো আউটবক্সে আছে।',
    'Templates': 'টেমপ্লেট',
    'Channel': 'মাধ্যম',
    'SMS': 'এসএমএস',
    'Body': 'বার্তা',
    'Template': 'টেমপ্লেট',
    'Code': 'কোড',
    'No templates seeded.': 'কোনো টেমপ্লেট নেই।',
    'Save template': 'টেমপ্লেট সংরক্ষণ করুন',
    'and': 'এবং',
    'Every email and SMS the platform would send. Nothing leaves this machine; entries are labelled simulated.': 'প্ল্যাটফর্ম যে সব ইমেইল ও এসএমএস পাঠাত, তার সব এখানে। কিছুই এই মেশিনের বাইরে যায় না; প্রতিটি এন্ট্রি অনুকরণকৃত।',
    'Recipient or body': 'প্রাপক বা বার্তা',
    'No messages yet. Run a booking or workflow action.': 'এখনো কোনো বার্তা নেই। একটি বুকিং বা ওয়ার্কফ্লো কাজ চালান।',
    'Notification templates in use': 'ব্যবহৃত বিজ্ঞপ্তি টেমপ্লেট',
    'Editable templates. Placeholders like': 'সম্পাদনযোগ্য টেমপ্লেট। প্লেসহোল্ডার যেমন',
    'are filled when a message is generated.': 'বার্তা তৈরির সময় পূরণ হয়।',
    'Pending, overdue and completed tasks for your role. Filters by date, priority and status.': 'আপনার ভূমিকার অপেক্ষমাণ, মেয়াদোত্তীর্ণ ও সম্পন্ন কাজ। তারিখ, অগ্রাধিকার ও অবস্থা দিয়ে ফিল্টার করুন।',
    'Open tasks': 'খোলা কাজ',
    'Assigned to': 'নিযুক্তি',
    'Escalated after the configured hours': 'নির্ধারিত সময়ের পর এসকেলেট হয়',
    'Decisions recorded by your role': 'আপনার ভূমিকা কর্তৃক লিপিবদ্ধ সিদ্ধান্ত',
    'SLA': 'নির্ধারিত সময়',
    'Due time comes from the workflow step': 'সময়সীমা আসে ওয়ার্কফ্লো ধাপ থেকে',
    'Reference, subject or step': 'রেফারেন্স, বিষয় বা ধাপ',
    'Requester': 'আবেদনকারী',
    'Urgent': 'জরুরি',
    'High': 'উচ্চ',
    'Normal': 'স্বাভাবিক',
    'Low': 'নিম্ন',
    'Returned': 'ফেরত পাঠানো',
    'Escalated': 'এসকেলেট করা',
    'To': 'পর্যন্ত',
    'Step': 'ধাপ',
    'No tasks in this view.': 'এই তালিকায় কোনো কাজ নেই।',
    'Dakbungalow booking approval': 'ডাকবাংলো বুকিং অনুমোদন',
    'Request submitted': 'আবেদন জমা হয়েছে',
    'In review': 'পর্যালোচনাধীন',
    'Under review / clarification': 'পর্যালোচনাধীন / স্পষ্টীকরণ',
    'Awaiting payment': 'পেমেন্টের অপেক্ষায়',
    'Approved, payment window open': 'অনুমোদিত, পেমেন্টের সময় উন্মুক্ত',
    'Confirmed / completed': 'নিশ্চিত / সম্পন্ন',
    'Payment window expired': 'পেমেন্টের সময়সীমা শেষ',
    'Waiting for the booking desk': 'বুকিং ডেস্কের অপেক্ষায়',
    'Queue': 'সারি',
    'Approvals / payment': 'অনুমোদন / পেমেন্ট',
    'Reception (next 2 days)': 'রিসেপশন (আগামী ২ দিন)',
    'Check-in from': 'চেক-ইন শুরু',
    'Check-out to': 'চেক-আউট পর্যন্ত',
    'All statuses': 'সব অবস্থা',
    'Paid': 'পরিশোধিত',
    'Booking reference': 'বুকিং রেফারেন্স',
    'Track': 'ট্র্যাক করুন',
    'Passed': 'উত্তীর্ণ',
    'Waived': 'মওকুফ',
    'Registered': 'নিবন্ধিত',
    'Entered in the register': 'রেজিস্টারে লিপিবদ্ধ',
    'Disposed and closed': 'নিষ্পত্তি ও বন্ধ',
    'Forwarded': 'ফরওয়ার্ড করা হয়েছে',
    'Forwarded for action': 'ব্যবস্থা গ্রহণের জন্য ফরওয়ার্ড',
    'Received back with comments': 'মন্তব্যসহ ফেরত পাওয়া গেছে',
    'Under review': 'পর্যালোচনাধীন',
    'Operational exigency': 'অপরিহার্য চাহিদা',
    'Clarification required': 'স্পষ্টীকরণ প্রয়োজন',
    'Signed off': 'চূড়ান্ত অনুমোদিত',
    'Satisfactory': 'সন্তোষজনক',
    'Unsatisfactory': 'অসন্তোষজনক',
    'Minor observation': 'সামান্য পর্যবেক্ষণ',
    'Retest planned': 'পুনঃপরীক্ষা নির্ধারিত',
    'Proposed': 'প্রস্তাবিত',
    'Implemented': 'বাস্তবায়িত',
    'Planning': 'পরিকল্পনা',
    'Ongoing': 'চলমান',
    'Delayed': 'বিলম্বিত',
    'Permanent': 'স্থায়ী',
    'Contract': 'চুক্তিভিত্তিক',
    'Deputation': 'প্রেষণ',
    'Daily wage': 'দৈনিক মজুরি',
    'Day': 'দিন',
    'Night': 'রাত',
    'Off': 'বন্ধ',
    'Evening': 'সন্ধ্যা',
    'Expired': 'মেয়াদোত্তীর্ণ',
    'Critical': 'অতি জরুরি',
    'Medium': 'মধ্যম',
    'Acknowledged': 'স্বীকৃত',
    'All time': 'সর্বকালীন',
    'On duty': 'ডিউটিতে',
    'Off duty': 'ডিউটি বন্ধ',
    'Day (09:00-17:00)': 'দিন (০৯:০০-১৭:০০)',
    'Evening (14:00-22:00)': 'সন্ধ্যা (১৪:০০-২২:০০)',
    'Night (22:00-06:00)': 'রাত (২২:০০-০৬:০০)',
    'Administration': 'প্রশাসন',
    'Engineering': 'প্রকৌশল',
    'Finance & Accounts': 'অর্থ ও হিসাব',
    'Establishment': 'প্রতিষ্ঠান',
    'Education': 'শিক্ষা',
    'ICT': 'তথ্য ও যোগাযোগপ্রযুক্তি',
    'Health & Family Planning': 'স্বাস্থ্য ও পরিবার পরিকল্পনা',
    'Agriculture': 'কৃষি',
    'Board Audit Cell': 'বোর্ড অডিট সেল',
    'Chief Executive Officer': 'প্রধান নির্বাহী কর্মকর্তা',
    'Administrative Officer': 'প্রশাসনিক কর্মকর্তা',
    'Assistant Engineer': 'সহকারী প্রকৌশলী',
    'Facility Caretaker': 'সুবিধা রক্ষণাবেক্ষণকারী',
    'Accounts Officer': 'হিসাব কর্মকর্তা',
    'HR Officer': 'এইচআর কর্মকর্তা',
    'Office Assistant': 'অফিস সহকারী',
    'Education Officer': 'শিক্ষা কর্মকর্তা',
    'Registry Officer': 'রেজিস্ট্রি কর্মকর্তা',
    'Project Officer': 'প্রকল্প কর্মকর্তা',
    'Meeting Secretary': 'সভা সচিব',
    'ICT Officer': 'তথ্যপ্রযুক্তি কর্মকর্তা',
    'Auditor': 'নিরীক্ষক',
    'Accountant': 'হিসাবরক্ষক',
    'Sub-Assistant Engineer': 'উপ-সহকারী প্রকৌশলী',
    'Health Inspector': 'স্বাস্থ্য পরিদর্শক',
    'Assistant Teacher': 'সহকারী শিক্ষক',
    'Agriculture Officer': 'কৃষি কর্মকর্তা',
    'Data Entry Operator': 'ডেটা এন্ট্রি অপারেটর',
    'Medical Officer': 'মেডিকেল অফিসার',
    'Executive Officer': 'নির্বাহী কর্মকর্তা',
    'Supervisor': 'সুপারভাইজার',
    'Inspector': 'পরিদর্শক',
    'Role display names': 'ভূমিকার প্রদর্শন নাম',
    'Display name': 'প্রদর্শন নাম',
    'Read-only': 'কেবল পঠনযোগ্য',
    'Permission matrix': 'অনুমতি ম্যাট্রিক্স',
    'Permission': 'অনুমতি',
    'Scroll horizontally for all 17 roles': 'সব ১৭টি ভূমিকা দেখতে অনুভূমিকভাবে স্ক্রল করুন',
    'The System Administrator role never holds booking approval permissions, and the Management / Auditor role is always read-only. These two rules are enforced when this form is saved.': 'সিস্টেম প্রশাসক ভূমিকার কখনো বুকিং অনুমোদনের অনুমতি থাকে না, এবং ব্যবস্থাপনা / নিরীক্ষক ভূমিকা সর্বদা কেবল পঠনযোগ্য। ফর্ম সংরক্ষণের সময় এই দুই নিয়ম প্রয়োগ হয়।',
    'Every change is recorded in the audit log.': 'প্রতিটি পরিবর্তন অডিট লগে লিপিবদ্ধ হয়।',
    'Edit roles and the permission matrix': 'ভূমিকা ও অনুমতি ম্যাট্রিক্স সম্পাদনা',
    'Manage settings, master data and security': 'সেটিংস, মূল ডেটা ও নিরাপত্তা পরিচালনা',
    'Create and edit user accounts': 'ব্যবহারকারী অ্যাকাউন্ট তৈরি ও সম্পাদনা',
    'View user accounts': 'ব্যবহারকারী অ্যাকাউন্ট দেখা',
    'Export the audit log': 'অডিট লগ রপ্তানি',
    'View the audit log': 'অডিট লগ দেখা',
    'Apply for a booking (citizen)': 'বুকিংয়ের আবেদন (নাগরিক)',
    'Executive Officer approval within delegation': 'অর্পিত ক্ষমতার মধ্যে নির্বাহী কর্মকর্তার অনুমোদন',
    'Process cancellation and refund requests': 'বাতিল ও ফেরত অনুরোধ নিষ্পত্তি',
    'View approved demands and booking finances': 'অনুমোদিত দাবি ও বুকিং আর্থিক তথ্য দেখা',
    'Reception verification and check-in / check-out': 'রিসেপশন যাচাই ও চেক-ইন / চেক-আউট',
    'Booking desk review and recommendation': 'বুকিং ডেস্ক পর্যালোচনা ও সুপারিশ',
    'Technical / facility readiness review': 'কারিগরি / সুবিধা প্রস্তুতি পর্যালোচনা',
    'View booking applications': 'বুকিং আবেদন দেখা',
    'Audit document access and movements': 'নথি প্রবেশ ও স্থানান্তর নিরীক্ষা',
    'Access confidential files': 'গোপনীয় নথিতে প্রবেশ',
    'Create register entries and files': 'রেজিস্টার এন্ট্রি ও নথি তৈরি',
    'Move and receive files': 'নথি স্থানান্তর ও গ্রহণ',
    'Review and decide on files': 'নথি পর্যালোচনা ও সিদ্ধান্ত',
    'View the document register and files': 'নথি রেজিস্টার ও ফাইল দেখা',
    'Edit facilities, units, tariffs and blackout dates': 'সুবিধা, ইউনিট, শুল্ক ও বন্ধের তারিখ সম্পাদনা',
    'View facilities, tariffs and calendar': 'সুবিধা, শুল্ক ও ক্যালেন্ডার দেখা',
    'Enter and correct attendance': 'উপস্থিতি এন্ট্রি ও সংশোধন',
    'Approve leave as HR': 'এইচআর হিসেবে ছুটি অনুমোদন',
    'Approve leave as supervisor': 'সুপারভাইজার হিসেবে ছুটি অনুমোদন',
    'Create and edit employee records': 'কর্মী রেকর্ড তৈরি ও সম্পাদনা',
    'Manage duty roster and assignments': 'ডিউটি রোস্টার ও নিয়োগ পরিচালনা',
    'Employee self-service': 'কর্মী স্ব-সেবা',
    'Manage training and expiry records': 'প্রশিক্ষণ ও মেয়াদ রেকর্ড পরিচালনা',
    'View employee records': 'কর্মী রেকর্ড দেখা',
    'Update action follow-up': 'কার্যক্রম ফলোআপ হালনাগাদ',
    'Schedule meetings and agendas': 'সভা ও আলোচ্যসূচি নির্ধারণ',
    'Record minutes and decisions': 'কার্যবিবরণী ও সিদ্ধান্ত লিপিবদ্ধ',
    'View meetings, minutes and actions': 'সভা, কার্যবিবরণী ও কার্যক্রম দেখা',
    'View the report access log': 'প্রতিবেদন প্রবেশ লগ দেখা',
    'Export reports to CSV and PDF': 'প্রতিবেদন CSV ও PDF-এ রপ্তানি',
    'View operational and financial reports': 'পরিচালন ও আর্থিক প্রতিবেদন দেখা',
    'View department dashboards': 'বিভাগীয় ড্যাশবোর্ড দেখা',
    'View executive dashboards': 'নির্বাহী ড্যাশবোর্ড দেখা',
    'Edit notification templates': 'বিজ্ঞপ্তি টেমপ্লেট সম্পাদনা',
    'View notifications and demo outbox': 'বিজ্ঞপ্তি ও ডেমো আউটবক্স দেখা',
    'Reconcile gateway transactions': 'গেটওয়ে লেনদেন মিলন',
    'Process refunds': 'ফেরত প্রক্রিয়া',
    'View payments and receipts': 'পেমেন্ট ও রসিদ দেখা',
    'Record field inspections': 'মাঠ পরিদর্শন লিপিবদ্ধ',
    'Create and edit projects': 'প্রকল্প তৈরি ও সম্পাদনা',
    'Post progress updates': 'অগ্রগতি হালনাগাদ প্রকাশ',
    'View projects and progress': 'প্রকল্প ও অগ্রগতি দেখা',
    'Submit and decide change requests': 'পরিবর্তন অনুরোধ জমা ও সিদ্ধান্ত',
    'Manage support tickets and monthly reports': 'সহায়তা টিকিট ও মাসিক প্রতিবেদন পরিচালনা',
    'Record UAT results': 'UAT ফলাফল লিপিবদ্ধ',
    'View support tickets and project acceptance': 'সহায়তা টিকিট ও প্রকল্প গ্রহণ দেখা',
    'View workflow performance': 'ওয়ার্কফ্লো কর্মদক্ষতা দেখা',
    'Configure workflow templates and authority matrix': 'ওয়ার্কফ্লো টেমপ্লেট ও ক্ষমতা ম্যাট্রিক্স কনফিগার',
    'Run reminders and escalation': 'রিমাইন্ডার ও এসকেলেশন চালান',
    'View workflow tasks and history': 'ওয়ার্কফ্লো কাজ ও ইতিহাস দেখা',
    'Every value below is editable at runtime and audited. Changes take effect immediately for new applications. Existing records keep their stored values.': 'নিচের প্রতিটি মান চলমান অবস্থায় সম্পাদনযোগ্য এবং নিরীক্ষিত। পরিবর্তন নতুন আবেদনে তাৎক্ষণিক প্রযোজ্য হয়; পুরোনো রেকর্ডে সংরক্ষিত মানই থাকে।',
    'General': 'সাধারণ',
    'Application name': 'অ্যাপ্লিকেশনের নাম',
    'Shown in the header, page titles and PDFs. Change it once to rename the platform.': 'হেডার, পৃষ্ঠার শিরোনাম ও PDF-এ দেখানো হয়। প্ল্যাটফর্মের নাম বদলাতে একবার পরিবর্তন করুন।',
    'Organisation name': 'সংস্থার নাম',
    'Support email': 'সহায়তা ইমেইল',
    'Displayed on the support page. No real email is sent in the demo.': 'সহায়তা পৃষ্ঠায় দেখানো হয়। ডেমোতে কোনো প্রকৃত ইমেইল পাঠানো হয় না।',
    'Support phone': 'সহায়তা ফোন',
    'Sample number.': 'নমুনা নম্বর।',
    'Demo ribbon text': 'ডেমো রিবনের লেখা',
    'Shown on every page while the platform runs in demo mode.': 'ডেমো মোডে থাকাকালীন প্রতিটি পৃষ্ঠায় দেখানো হয়।',
    'Booking rules': 'বুকিং নিয়ম',
    'Temporary hold (hours)': 'সাময়িক হোল্ড (ঘণ্টা)',
    'How long a room or slot is held while the application is under review.': 'আবেদন পর্যালোচনাধীন থাকাকালীন রুম বা স্লট কতক্ষণ সংরক্ষিত থাকে।',
    'Payment window (hours)': 'পেমেন্টের সময়সীমা (ঘণ্টা)',
    'Time allowed to pay after final approval before the hold is released.': 'চূড়ান্ত অনুমোদনের পর হোল্ড ছাড়ার আগে পেমেন্টের জন্য বরাদ্দ সময়।',
    'Advance booking limit (days)': 'অগ্রিম বুকিং সীমা (দিন)',
    'How far ahead a citizen may apply.': 'নাগরিক কত দিন আগে পর্যন্ত আবেদন করতে পারেন।',
    'Maximum stay (nights)': 'সর্বোচ্চ অবস্থান (রাত)',
    'Maximum guests per application': 'প্রতি আবেদনে সর্বোচ্চ অতিথি',
    'Holiday rule note': 'ছুটির দিনের নিয়ম',
    'Sample rule shown to citizens before payment.': 'পেমেন্টের আগে নাগরিকদের দেখানো নমুনা নিয়ম।',
    'Refund policy': 'ফেরত নীতি',
    'days_before_checkin:percent pairs. Sample policy editable by the administrator.': 'চেক-ইনের দিন:শতাংশ জোড়া। প্রশাসক সম্পাদনযোগ্য নমুনা নীতি।',
    'Minimum notice (hours)': 'সর্বনিম্ন নোটিশ (ঘণ্টা)',
    'Earliest check-in date that can be requested.': 'অনুরোধযোগ্য সর্বপ্রথম চেক-ইন তারিখ।',
    'Payment gateway': 'পেমেন্ট গেটওয়ে',
    'Simulated gateway. No real money moves.': 'অনুকরণকৃত গেটওয়ে। প্রকৃত অর্থ লেনদেন হয় না।',
    'Gateway charge paid by the user': 'ব্যবহারকারীর বহন করা গেটওয়ে চার্জ',
    '1 = show and add the gateway charge at checkout; 0 = absorbed under the contract.': '১ = চেকআউটে গেটওয়ে চার্জ দেখিয়ে যোগ করা হয়; ০ = চুক্তির আওতায় বহন করা হয়।',
    'Gateway charge amount (BDT)': 'গেটওয়ে চার্জের পরিমাণ (টাকা)',
    'Reminder before due (hours)': 'সময়সীমার আগে রিমাইন্ডার (ঘণ্টা)',
    'Reminders are sent within this window before a task is due.': 'কাজের সময়সীমার আগে এই সময়ের মধ্যে রিমাইন্ডার পাঠানো হয়।',
    'Escalate after overdue (hours)': 'মেয়াদোত্তীর্ণের পর এসকেলেশন (ঘণ্টা)',
    'Overdue tasks escalate to the nominated supervisor role.': 'মেয়াদোত্তীর্ণ কাজ নির্ধারিত সুপারভাইজার ভূমিকার কাছে এসকেলেট হয়।',
    'Security': 'নিরাপত্তা',
    'OTP validity (minutes)': 'OTP বৈধতা (মিনিট)',
    'Allowed failed logins per 15 minutes': 'প্রতি ১৫ মিনিটে অনুমোদিত ব্যর্থ লগইন',
    'Backup retention (days)': 'ব্যাকআপ সংরক্ষণ (দিন)',
    'SMS credits are client-paid': 'SMS ক্রেডিট ক্লায়েন্ট বহন করে',
    '1 = the demo shows the client-paid SMS notice. Email app logic is included.': '১ = ডেমোতে ক্লায়েন্ট-বহন SMS নোটিশ দেখানো হয়। ইমেইল অ্যাপ লজিক অন্তর্ভুক্ত।',
    'Save settings': 'সেটিংস সংরক্ষণ করুন',
    'Discard changes': 'পরিবর্তন বাতিল করুন',
    'Recently changed values': 'সাম্প্রতিক পরিবর্তিত মান',
    'Every change is also written to the audit log': 'প্রতিটি পরিবর্তন অডিট লগেও লেখা হয়',
    'Key': 'কী',
    'Value': 'মান',
    'Updated': 'হালনাগাদ',
    'By': 'কর্তৃক',
    'SSLCommerz / bKash (demo)': 'SSLCommerz / বিকাশ (ডেমো)',
    'Friday and Saturday nights use the published holiday tariff.': 'শুক্র ও শনিবার রাতে প্রকাশিত ছুটির দিনের ভাড়া প্রযোজ্য।',
    'New account': 'নতুন অ্যাকাউন্ট',
    'All roles': 'সব ভূমিকা',
    'Account': 'অ্যাকাউন্ট',
    'Last login': 'সর্বশেষ লগইন',
    'Cross-module view for management. Read-only: this role cannot approve or change records.': 'ব্যবস্থাপনার জন্য আন্তঃমডিউল দৃশ্য। কেবল পঠনযোগ্য: এই ভূমিকা অনুমোদন বা রেকর্ড পরিবর্তন করতে পারে না।',
    'Department view': 'বিভাগীয় দৃশ্য',
    'Verified collection': 'যাচাইকৃত আদায়',
    'Active records': 'সক্রিয় রেকর্ড',
    'Collection trend': 'আদায়ের প্রবণতা',
    'Verified bookings, last 6 months': 'যাচাইকৃত বুকিং, গত ৬ মাস',
    'Booking status mix': 'বুকিং অবস্থার মিশ্রণ',
    'Facilities performance': 'সুবিধার কর্মদক্ষতা',
    'Revenue': 'রাজস্ব',
    'Capital projects': 'মূলধনী প্রকল্প',
    'All projects': 'সব প্রকল্প',
    'Project': 'প্রকল্প',
    'Headcount, documents, projects and leave movement by department.': 'বিভাগ অনুযায়ী জনবল, নথি, প্রকল্প ও ছুটির গতিবিধি।',
    'Executive view': 'নির্বাহী দৃশ্য',
    'Pending leave': 'অপেক্ষমাণ ছুটি',
    'Open files': 'খোলা ফাইল',
    'Active projects': 'সক্রিয় প্রকল্প',
    'Open meeting actions': 'খোলা সভার কার্যক্রম',
    'Follow-up': 'ফলোআপ',
    'Matching the filters': 'ফিল্টার অনুযায়ী',
    'Total charged': 'মোট ধার্য',
    'Room charges, deposit and gateway': 'রুম চার্জ, জামানত ও গেটওয়ে',
    'Security deposits': 'নিরাপত্তা জামানত',
    'Held against the stay': 'অবস্থানের বিপরীতে সংরক্ষিত',
    'Gateway charges': 'গেটওয়ে চার্জ',
    'Sample charge where enabled': 'চালু থাকলে নমুনা চার্জ',
    'By status': 'অবস্থা অনুযায়ী',
    'By facility': 'সুবিধা অনুযায়ী',
    'Operational, financial and HR reports. Exports are logged in the report access log and the audit trail.': 'পরিচালন, আর্থিক ও এইচআর প্রতিবেদন। রপ্তানি প্রতিবেদন প্রবেশ লগ ও অডিট ট্রেইলে লিপিবদ্ধ হয়।',
    'Booking report': 'বুকিং প্রতিবেদন',
    'Access log': 'প্রবেশ লগ',
    'Bookings in register': 'রেজিস্টারে বুকিং',
    'Verified payments': 'যাচাইকৃত পেমেন্ট',
    'Signed gateway callbacks only': 'কেবল স্বাক্ষরিত গেটওয়ে কলব্যাক',
    'Audit entries': 'অডিট এন্ট্রি',
    'Every privileged action': 'প্রতিটি বিশেষ ক্ষমতার কার্যক্রম',
    'Export formats': 'রপ্তানি ফরম্যাট',
    'CSV · PDF': 'CSV · PDF',
    'Your role can export': 'আপনার ভূমিকা রপ্তানি করতে পারে',
    'Booking register': 'বুকিং রেজিস্টার',
    'Every application with status, dates, charges and payment totals.': 'অবস্থা, তারিখ, চার্জ ও পেমেন্ট মোটসহ প্রতিটি আবেদন।',
    'Revenue by month': 'মাস অনুযায়ী রাজস্ব',
    'Verified collections per month for the last 12 months.': 'গত ১২ মাসের মাসিক যাচাইকৃত আদায়।',
    'Workflow register': 'ওয়ার্কফ্লো রেজিস্টার',
    'Instances, current status and completion dates.': 'ইনস্ট্যান্স, বর্তমান অবস্থা ও সমাপ্তির তারিখ।',
    'Employee register': 'কর্মী রেজিস্টার',
    'Employee master list with department and designation.': 'বিভাগ ও পদবিসহ কর্মীর মূল তালিকা।',
    'Budget, expenditure and progress by project.': 'প্রকল্প অনুযায়ী বাজেট, ব্যয় ও অগ্রগতি।',
    'Recent report access': 'সাম্প্রতিক প্রতিবেদন প্রবেশ',
    'Report': 'প্রতিবেদন',
    'Parameters': 'প্যারামিটার',
    'IP': 'আইপি',
    'Employee register, attendance, leave, roster and training expiry. Sample records only.': 'কর্মী রেজিস্টার, উপস্থিতি, ছুটি, রোস্টার ও প্রশিক্ষণের মেয়াদ। কেবল নমুনা রেকর্ড।',
    'Approved leave currently active': 'বর্তমানে সক্রিয় অনুমোদিত ছুটি',
    'Departments': 'বিভাগসমূহ',
    'Sample organogram': 'নমুনা অর্গানোগ্রাম',
    'Expiring training': 'মেয়াদোত্তীর্ণ হচ্ছে এমন প্রশিক্ষণ',
    'Within the next 60 days': 'আগামী ৬০ দিনের মধ্যে',
    'Employee snapshot': 'কর্মীর সারসংক্ষেপ',
    'All employees': 'সব কর্মী',
    'No.': 'ক্রম',
    'Upcoming approved leave': 'আসন্ন অনুমোদিত ছুটি',
    'Training expiry': 'প্রশিক্ষণের মেয়াদ',
    'Employee register with department, designation and employment type.': 'বিভাগ, পদবি ও নিয়োগের ধরনসহ কর্মী রেজিস্টার।',
    'Employee no.': 'কর্মী নম্বর',
    'Service': 'চাকরিকাল',
    'Add employee': 'কর্মী যোগ করুন',
    'Name and employee number are required': 'নাম ও কর্মী নম্বর আবশ্যক',
    'Full name': 'পূর্ণ নাম',
    'Joining date': 'যোগদানের তারিখ',
    'Employment type': 'নিয়োগের ধরন',
    'Go': 'যান',
    'Late': 'বিলম্বে',
    'Holiday': 'ছুটি',
    'Recorded': 'লিপিবদ্ধ',
    'Mark': 'চিহ্নিত করুন',
    'Save attendance': 'উপস্থিতি সংরক্ষণ',
    'Leaving a row blank does not change it. Corrections are audited.': 'সারি ফাঁকা রাখলে তা অপরিবর্তিত থাকে। সংশোধন নিরীক্ষিত হয়।',
    'All leave applications with workflow status.': 'ওয়ার্কফ্লো অবস্থাসহ সব ছুটির আবেদন।',
    'Approval tasks': 'অনুমোদনের কাজ',
    'Leave register': 'ছুটি রেজিস্টার',
    'Tracking': 'ট্র্যাকিং',
    'Casual leave': 'নৈমিত্তিক ছুটি',
    'Annual leave': 'বার্ষিক ছুটি',
    'Sick leave': 'অসুস্থতাজনিত ছুটি',
    'Special leave': 'বিশেষ ছুটি',
    'Apply for leave': 'ছুটির আবেদন করুন',
    'Applying starts the leave workflow. Supervisor and HR decisions appear in My Tasks and update this status. Your employee record:': 'আবেদন করলে ছুটির ওয়ার্কফ্লো শুরু হয়। সুপারভাইজার ও এইচআরের সিদ্ধান্ত "আমার কাজ"-এ দেখা যায় এবং এই অবস্থা হালনাগাদ করে। আপনার কর্মী রেকর্ড:',
    'Leave type': 'ছুটির ধরন',
    'Start date': 'শুরুর তারিখ',
    'End date': 'শেষের তারিখ',
    'This week': 'এই সপ্তাহ',
    'Next week': 'আগামী সপ্তাহ',
    'Assign a shift': 'শিফট নির্ধারণ করুন',
    'Saving the same employee and date replaces the existing shift': 'একই কর্মী ও তারিখ সংরক্ষণ করলে বিদ্যমান শিফট প্রতিস্থাপিত হয়',
    'Shift': 'শিফট',
    'Note': 'নোট',
    'Save shift': 'শিফট সংরক্ষণ',
    'Certifications and training with expiry tracking. Expired records are flagged for HR follow-up.': 'মেয়াদ ট্র্যাকিংসহ সনদ ও প্রশিক্ষণ। মেয়াদোত্তীর্ণ রেকর্ড এইচআরের ফলোআপের জন্য চিহ্নিত হয়।',
    'Provider': 'প্রদানকারী',
    'Add training record': 'প্রশিক্ষণ রেকর্ড যোগ করুন',
    'Training title': 'প্রশিক্ষণের নাম',
    'Completed on': 'সম্পন্নের তারিখ',
    'Expires on': 'মেয়াদ শেষের তারিখ',
    'Add record': 'রেকর্ড যোগ করুন',
    'Registration, assignment, confidentiality and movement of Parishad files.': 'পরিষদ ফাইলের নিবন্ধন, বণ্টন, গোপনীয়তা ও স্থানান্তর।',
    'Awaiting action': 'ব্যবস্থা গ্রহণের অপেক্ষায়',
    'Assigned to an officer': 'কর্মকর্তাকে বরাদ্দকৃত',
    'Past the due date': 'নির্ধারিত তারিখ অতিক্রান্ত',
    'Closed / archived': 'বন্ধ / আর্কাইভকৃত',
    'Completed files': 'সম্পন্ন ফাইল',
    'General correspondence': 'সাধারণ পত্রালাপ',
    'Procurement': 'ক্রয়',
    'Legal / statutory': 'আইনি / বিধিবদ্ধ',
    'Project file': 'প্রকল্প ফাইল',
    'Finance': 'অর্থ',
    'Other': 'অন্যান্য',
    'File no.': 'ফাইল নম্বর',
    'Assigned': 'বরাদ্দকৃত',
    'Register entries with an uploaded attachment. Downloads are logged in the audit trail.': 'সংযুক্তিসহ রেজিস্টার এন্ট্রি। ডাউনলোড অডিট ট্রেইলে লিপিবদ্ধ হয়।',
    'Files past their due date that are not closed or archived. Follow up with the assigned officer.': 'নির্ধারিত তারিখ অতিক্রান্ত কিন্তু বন্ধ বা আর্কাইভ করা হয়নি এমন ফাইল। বরাদ্দকৃত কর্মকর্তার সঙ্গে ফলোআপ করুন।',
    'Days overdue': 'মেয়াদোত্তীর্ণ দিন',
    'Every movement and access action on the register. Read-only roles can view this log.': 'রেজিস্টারের প্রতিটি স্থানান্তর ও প্রবেশ কার্যক্রম। কেবল পঠনযোগ্য ভূমিকা এই লগ দেখতে পারে।',
    'File': 'ফাইল',
    'Project register with budget, progress and field inspection follow-up.': 'বাজেট, অগ্রগতি ও মাঠ পরিদর্শন ফলোআপসহ প্রকল্প রেজিস্টার।',
    'All registers': 'সব রেজিস্টার',
    'Active implementation': 'সক্রিয় বাস্তবায়ন',
    'Needs management attention': 'ব্যবস্থাপনার দৃষ্টি প্রয়োজন',
    'Budget / spent': 'বাজেট / ব্যয়িত',
    'Budget': 'বাজেট',
    'Field inspection records with findings, rating and follow-up date.': 'পর্যবেক্ষণ, রেটিং ও ফলোআপ তারিখসহ মাঠ পরিদর্শন রেকর্ড।',
    'Rating': 'রেটিং',
    'Finding': 'পর্যবেক্ষণ',
    'Meeting schedule, agendas, minutes and action follow-up.': 'সভার সময়সূচি, আলোচ্যসূচি, কার্যবিবরণী ও কার্যক্রম ফলোআপ।',
    'Matching the filter': 'ফিল্টার অনুযায়ী',
    'Open actions': 'খোলা কার্যক্রম',
    'Across all meetings': 'সব সভা মিলিয়ে',
    'Meeting': 'সভা',
    'Venue': 'স্থান',
    'Chair': 'সভাপতি',
    'Meeting decisions and their assigned actions. Overdue items are highlighted.': 'সভার সিদ্ধান্ত ও বরাদ্দকৃত কার্যক্রম। মেয়াদোত্তীর্ণ আইটেম চিহ্নিত।',
    'Open (all not done)': 'খোলা (সম্পন্ন নয়)',
    'Owner': 'দায়িত্বপ্রাপ্ত',
    'View only': 'কেবল দেখার',
    'Incidents and service requests with the sample support targets: Critical 2h, High 4h, Medium 8h, Low 16h (business hours).': 'নমুনা সহায়তা লক্ষ্যমাত্রাসহ ঘটনা ও সেবা অনুরোধ: অতি জরুরি ২ ঘণ্টা, উচ্চ ৪ ঘণ্টা, মধ্যম ৮ ঘণ্টা, নিম্ন ১৬ ঘণ্টা (কর্মঘণ্টায়)।',
    'Not resolved or closed': 'সমাধান বা বন্ধ হয়নি',
    'Critical open': 'অতি জরুরি খোলা',
    'Past target': 'লক্ষ্যমাত্রা অতিক্রান্ত',
    'Response target exceeded': 'সাড়া দেওয়ার লক্ষ্যমাত্রা অতিক্রান্ত',
    'Open (not resolved)': 'খোলা (সমাধান হয়নি)',
    'Ticket': 'টিকিট',
    'Response due': 'সাড়ার সময়সীমা',
    'Incident / fault': 'ঘটনা / ত্রুটি',
    'Access / account': 'প্রবেশ / অ্যাকাউন্ট',
    'Data correction': 'তথ্য সংশোধন',
    'Service request': 'সেবা অনুরোধ',
    'Log a ticket': 'টিকিট করুন',
    'Log ticket': 'টিকিট জমা দিন',
    'Discovery, data, configuration, UAT and go-live. The plan is editable by the support manager; dates are sample values confirmed during mobilisation.': 'ডিসকভারি, তথ্য, কনফিগারেশন, UAT ও গো-লাইভ। পরিকল্পনা সহায়তা ব্যবস্থাপক সম্পাদনা করতে পারেন; তারিখগুলো মোবিলাইজেশনে নিশ্চিতযোগ্য নমুনা মান।',
    'Plan progress': 'পরিকল্পনার অগ্রগতি',
    'Window': 'সময়সীমা',
    'Phase': 'পর্যায়',
    'Deliverable': 'অর্পণযোগ্য',
    'Acceptance checklist. UAT results are recorded by the UAT permission and logged with the actor and time.': 'গ্রহণ চেকলিস্ট। UAT ফলাফল UAT অনুমতিতে লিপিবদ্ধ হয় এবং কার্য সম্পাদনকারী ও সময়সহ লগ হয়।',
    'Checklist': 'চেকলিস্ট',
    'UAT test': 'UAT পরীক্ষা',
    'Area': 'ক্ষেত্র',
    'Item': 'আইটেম',
    'Checked': 'যাচাইকৃত',
    'Record result': 'ফলাফল লিপিবদ্ধ করুন',
    'Platform': 'প্ল্যাটফর্ম',
    'Security': 'নিরাপত্তা',
    'Documentation': 'ডকুমেন্টেশন',
    'Access': 'প্রবেশ',
    'Booking': 'বুকিং',
    'Reception': 'রিসেপশন',
    'Scope changes after sign-off. Each request records impact and the decision, with an audit trail.': 'চূড়ান্ত অনুমোদনের পর পরিধি পরিবর্তন। প্রতিটি অনুরোধ প্রভাব ও সিদ্ধান্ত অডিট ট্রেইলসহ লিপিবদ্ধ করে।',
    'Title': 'শিরোনাম',
    'Impact': 'প্রভাব',
    'Requested by': 'অনুরোধকারী',
    'Decision note': 'সিদ্ধান্তের নোট',
    'Decide': 'সিদ্ধান্ত দিন',
    'Release expired holds & payment windows': 'মেয়াদোত্তীর্ণ হোল্ড ও পেমেন্ট সময় ছাড়ুন',
    'Demand (approved bookings)': 'দাবি (অনুমোদিত বুকিং)',
    'Sample approved demand': 'নমুনা অনুমোদিত দাবি',
    'Collected (verified)': 'আদায় (যাচাইকৃত)',
    'Only signed callbacks count': 'কেবল স্বাক্ষরিত কলব্যাক গণনা হয়',
    'Outstanding': 'বকেয়া',
    'Demand less collected': 'দাবি থেকে আদায় বাদ',
    'Processed refunds': 'প্রক্রিয়াকৃত ফেরত',
    'Confirmed callbacks': 'নিশ্চিত কলব্যাক',
    'Duplicate callbacks ignored': 'পুনরাবৃত্ত কলব্যাক উপেক্ষিত',
    'Forged signatures rejected': 'জাল স্বাক্ষর প্রত্যাখ্যাত',
    'Amount / reference mismatches': 'পরিমাণ / রেফারেন্স অমিল',
    'Payment status': 'পেমেন্ট অবস্থা',
    'Initiated': 'সূচিত',
    'Success': 'সফল',
    'Exception': 'ব্যতিক্রম',
    'Duplicate callbacks': 'পুনরাবৃত্ত কলব্যাক',
    'Mismatch / forged': 'অমিল / জাল',
    'Failed / cancelled': 'ব্যর্থ / বাতিল',
    'Callbacks': 'কলব্যাক',
    'Manage': 'ব্যবস্থাপনা',
    'Public page': 'পাবলিক পৃষ্ঠা',
    'Next 14 days · room inventory': 'আগামী ১৪ দিন · রুম তালিকা',
    'Kind': 'ধরন',
    'Capacity': 'ধারণক্ষমতা',
    'Citizen rate': 'নাগরিক হার',
    'Next 7 days': 'আগামী ৭ দিন',
    'Green = free, red = held or booked. Holds expire automatically after the configured hold period.': 'সবুজ = খালি, লাল = সংরক্ষিত বা বুকড। নির্ধারিত হোল্ড সময়ের পর হোল্ড স্বয়ংক্রিয়ভাবে শেষ হয়।',
    'Units': 'ইউনিট',
    'Tariffs by applicant category': 'আবেদনকারীর শ্রেণি অনুযায়ী ভাড়া',
    'Standard': 'সাধারণ',
    'Remove': 'সরান',
    'Edit and configure': 'সম্পাদনা ও কনফিগার',
    'The main district guesthouse beside the Parishad office, used for official guests and citizens.': 'পরিষদ কার্যালয়ের পাশে প্রধান জেলা অতিথিশালা, সরকারি অতিথি ও নাগরিকদের জন্য ব্যবহৃত।',
    'Rules': 'নিয়ম',
    'Booking types': 'বুকিংয়ের ধরন',
    'Is active': 'সক্রিয়',
    'Save facility': 'সুবিধা সংরক্ষণ',
    'Add a unit': 'ইউনিট যোগ করুন',
    'Add unit': 'ইউনিট যোগ করুন',
    'Add or update a tariff': 'ভাড়া যোগ বা হালনাগাদ করুন',
    'Holiday amount': 'ছুটির দিনের পরিমাণ',
    'Saving an existing unit + category updates that tariff (one tariff per unit and category).': 'বিদ্যমান ইউনিট + শ্রেণি সংরক্ষণ করলে সেই ভাড়া হালনাগাদ হয় (প্রতি ইউনিট ও শ্রেণিতে একটি ভাড়া)।',
    'Save tariff': 'ভাড়া সংরক্ষণ',
    'Blackout dates': 'বন্ধের তারিখ',
    'Add blackout date': 'বন্ধের তারিখ যোগ করুন',
    'Facility record': 'সুবিধার রেকর্ড',
    'Inventories and holds': 'তালিকা ও হোল্ড',
    'Sample facility': 'নমুনা সুবিধা',
    'Permitted booking types:': 'অনুমোদিত বুকিংয়ের ধরন:',
    'Apply for this facility': 'এই সুবিধায় আবেদন করুন',
    'Rooms and facilities': 'রুম ও সুবিধা',
    'Tariffs are sample values': 'ভাড়াগুলো নমুনা মান',
    'Room / facility': 'রুম / সুবিধা',
    'Published terms and rules': 'প্রকাশিত শর্ত ও নিয়ম',
    'Friday and Saturday nights are charged at the holiday tariff. A security deposit may apply; the exact amount is shown before payment.': 'শুক্র ও শনিবার রাতে ছুটির দিনের ভাড়া প্রযোজ্য। নিরাপত্তা জামানত প্রযোজ্য হতে পারে; সঠিক পরিমাণ পেমেন্টের আগে দেখানো হয়।',
    'Room-level availability. Halls are booked per morning, afternoon or evening slot and are checked during application.': 'রুমভিত্তিক প্রাপ্যতা। হল সকাল, দুপুর বা সন্ধ্যার স্লট অনুযায়ী বুক হয় এবং আবেদনের সময় যাচাই করা হয়।',
    'Documents to prepare': 'প্রস্তুত করার নথি',
    'Government official:': 'সরকারি কর্মকর্তা:',
    'Public citizen:': 'সাধারণ নাগরিক:',
    'Organization:': 'সংস্থা:',
    'PDF, JPG, PNG or TXT up to 5 MB. Documents are stored locally in the demo.': 'PDF, JPG, PNG বা TXT, সর্বোচ্চ ৫ MB। ডেমোতে নথি স্থানীয়ভাবে সংরক্ষিত হয়।',
    'Attached bathroom': 'সংযুক্ত বাথরুম',
    'Air conditioning': 'শীতাতপ নিয়ন্ত্রণ',
    'Wi-Fi': 'ওয়াই-ফাই',
    'Generator backup': 'জেনারেটর ব্যাকআপ',
    'Parking': 'পার্কিং',
    'Module': 'মডিউল',
    'Object': 'অবজেক্ট',
    'Change': 'পরিবর্তন',
    'Create your account': 'আপনার অ্যাকাউন্ট তৈরি করুন',
    'Contact details': 'যোগাযোগের বিবরণ',
    'Secure your account': 'আপনার অ্যাকাউন্ট সুরক্ষিত করুন',
    'Use at least 8 characters. Sample password:': 'কমপক্ষে ৮ অক্ষর ব্যবহার করুন। নমুনা পাসওয়ার্ড:',
    'Enter a password.': 'একটি পাসওয়ার্ড দিন।',
    # User panel, catalogue and asset detail
    'User panel': 'ব্যবহারকারী প্যানেল',
    'User portal': 'ব্যবহারকারী পোর্টাল',
    'User sign-in': 'ব্যবহারকারী সাইন-ইন',
    'Citizen panel': 'নাগরিক প্যানেল',
    'Officials panel': 'কর্মকর্তা প্যানেল',
    'FIND YOUR SPACE': 'আপনার জায়গা খুঁজুন',
    'PLAN YOUR VISIT': 'আপনার সফর পরিকল্পনা করুন',
    'GAZIPUR ZILA PARISHAD': 'গাজীপুর জেলা পরিষদ',
    'Banglish': 'বাংলিশ',
    'Demo': 'ডেমো',
    'Government of Bangladesh': 'বাংলাদেশ সরকার',
    'Local spaces. A simpler service.': 'স্থানীয় জায়গা। সহজ একটি সেবা।',
    'Your next space. One simple place.': 'আপনার পরবর্তী জায়গা। এক সহজ ঠিকানা।',
    'Welcome to your next booking': 'আপনার পরবর্তী বুকিংয়ে স্বাগতম',
    'Explore, book and pay': 'দেখুন, বুক করুন ও পেমেন্ট করুন',
    'Explore six kinds of Parishad assets, manage your applications and follow every approval.':
        'পরিষদের ছয় ধরনের সম্পদ দেখুন, আপনার আবেদন পরিচালনা করুন এবং প্রতিটি অনুমোদন অনুসরণ করুন।',
    'Explore assets': 'সম্পদ দেখুন',
    'Asset categories': 'সম্পদের শ্রেণি',
    'All locations': 'সব অবস্থান',
    'Where in Gazipur?': 'গাজীপুরের কোথায়?',
    'Sort by': 'সাজানোর ক্রম',
    'Recommended': 'প্রস্তাবিত',
    'Price: low to high': 'মূল্য: কম থেকে বেশি',
    'Availability map': 'প্রাপ্যতার মানচিত্র',
    'Gazipur · sample layout': 'গাজীপুর · নমুনা বিন্যাস',
    'Illustrative locations, not a property survey. Select a pin to view availability.':
        'চিত্রগত অবস্থান, সম্পত্তি জরিপ নয়। প্রাপ্যতা দেখতে একটি পিন নির্বাচন করুন।',
    'Unavailable': 'অনুপলব্ধ',
    'Unavailable on these dates': 'এই তারিখগুলোতে অনুপলব্ধ',
    'Sample listings and rates. Availability updates with each reservation.':
        'নমুনা তালিকা ও হার। প্রতিটি বুকিংয়ের সঙ্গে প্রাপ্যতা হালনাগাদ হয়।',
    'No matching spaces': 'মিলে এমন কোনো জায়গা নেই',
    'Try another location, fewer guests or different dates.':
        'অন্য অবস্থান, কম অতিথি বা ভিন্ন তারিখ চেষ্টা করুন।',
    'Clear filters': 'ফিল্টার মুছুন',
    'Your recent bookings': 'আপনার সাম্প্রতিক বুকিং',
    'View all four Dakbungalows': 'চারটি ডাকবাংলো সব দেখুন',
    'Parishad managed': 'পরিষদ পরিচালিত',
    'capacity': 'জন',
    'Total for selected dates': 'নির্বাচিত তারিখের মোট',
    'Includes refundable deposit': 'ফেরতযোগ্য জামানতসহ',
    'Choose your space': 'আপনার জায়গা বেছে নিন',
    'About this space': 'এই জায়গা সম্পর্কে',
    'Illustrative sample photograph': 'নমুনা আলোকচিত্র',
    'Clear price breakdown': 'স্পষ্ট মূল্যের হিসাব',
    'Approval tracking': 'অনুমোদন ট্র্যাকিং',
    'Booking rules and important information': 'বুকিংয়ের নিয়ম ও গুরুত্বপূর্ণ তথ্য',
    'This is a sample short-term reservation, not a lease, ownership transfer or operating licence.':
        'এটি একটি নমুনা স্বল্পমেয়াদি বুকিং; ইজারা, মালিকানা হস্তান্তর বা পরিচালনা লাইসেন্স নয়।',
    'Use sample identity details only. No real payment is collected.':
        'শুধু নমুনা পরিচয়ের তথ্য ব্যবহার করুন। কোনো প্রকৃত পেমেন্ট নেওয়া হয় না।',
    'Room or asset': 'রুম বা সম্পদ',
    'Auditoriums are reserved for one slot on the start date.':
        'অডিটোরিয়াম শুরুর তারিখে একটি স্লটের জন্য সংরক্ষিত হয়।',
    'Event slot': 'অনুষ্ঠানের স্লট',
    'Check-in / start': 'চেক-ইন / শুরু',
    'Check-out / end': 'চেক-আউট / শেষ',
    'Guests / participants': 'অতিথি / অংশগ্রহণকারী',
    'Select a start date, then an end date': 'প্রথমে শুরুর তারিখ, তারপর শেষের তারিখ নির্বাচন করুন',
    'Choose dates and review the exact price before booking.':
        'তারিখ বেছে নিন এবং বুক করার আগে নির্ভুল মূল্য দেখুন।',
    'Make it yours': 'নিজের করে নিন',
    'One room or asset per booking.': 'প্রতি বুকিংয়ে একটি রুম বা সম্পদ।',
    'Reserve and try payment here. Follow officer reviews in the Citizen panel. A permit is issued only after approval.':
        'এখানে সংরক্ষণ করে পেমেন্ট চেষ্টা করুন। কর্মকর্তার পর্যালোচনা নাগরিক প্যানেলে অনুসরণ করুন। অনুমোদনের পরেই পারমিট ইস্যু হয়।',
    'Apply, follow each officer review, then pay after approval.':
        'আবেদন করুন, প্রতিটি কর্মকর্তার পর্যালোচনা অনুসরণ করুন, তারপর অনুমোদনের পর পেমেন্ট করুন।',
    'Review booking': 'বুকিং পর্যালোচনা করুন',
    'Book and continue to payment': 'বুক করে পেমেন্টে এগিয়ে যান',
    'No charge at this step': 'এই ধাপে কোনো চার্জ নেই',
    'Continue to simulated payment. Your application still needs officer approval before a permit is issued.':
        'অনুকরণকৃত পেমেন্টে এগিয়ে যান। পারমিট ইস্যুর আগে আপনার আবেদনে এখনো কর্মকর্তার অনুমোদন প্রয়োজন।',
    'Choose your dates': 'আপনার তারিখ বেছে নিন',
    'Applications and approval progress': 'আবেদন ও অনুমোদনের অগ্রগতি',
    'Your applications, payments and next officer review.':
        'আপনার আবেদন, পেমেন্ট ও পরবর্তী কর্মকর্তার পর্যালোচনা।',
    'Review, approve and manage': 'পর্যালোচনা, অনুমোদন ও ব্যবস্থাপনা',
    'Sign in to book': 'বুক করতে সাইন ইন করুন',
    'Use a citizen account from quick sign-in to try a reservation.':
        'সংরক্ষণ চেষ্টা করতে দ্রুত সাইন-ইন থেকে একটি নাগরিক অ্যাকাউন্ট ব্যবহার করুন।',
    # Asset catalogue copy (core/assets.py)
    'Lands': 'জমি',
    'Ponds': 'পুকুর',
    'Markets': 'বাজার',
    'Dakbungalows': 'ডাকবাংলো',
    'Room for your next idea.': 'আপনার পরের উদ্যোগের জন্য জায়গা।',
    'Find open spaces for your next community activity.':
        'আপনার পরবর্তী সম্প্রদায় কার্যক্রমের জন্য খোলা জায়গা খুঁজুন।',
    'A little closer to nature.': 'প্রকৃতির একটু কাছাকাছি।',
    'Explore peaceful waterside spaces across Gazipur.':
        'গাজীপুরজুড়ে পানির ধারের শান্ত জায়গা ঘুরে দেখুন।',
    'A place for local enterprise.': 'স্থানীয় উদ্যোগের একটি ঠিকানা।',
    'Discover market spaces and plan your next trading day.':
        'বাজারের জায়গা আবিষ্কার করুন এবং পরবর্তী বিক্রির দিন পরিকল্পনা করুন।',
    'Connect with the riverside.': 'নদীর ধারের সঙ্গে যুক্ত হোন।',
    'Browse ferry-ghat spaces and check available dates.':
        'ঘাটের জায়গা দেখুন ও খালি তারিখ যাচাই করুন।',
    'Bring everyone together.': 'সবাইকে একত্র করুন।',
    'Find a welcoming space for meetings, events and celebrations.':
        'সভা, অনুষ্ঠান ও উৎসবের জন্য আপ্যায়নপূর্ণ জায়গা খুঁজুন।',
    'A quieter stay in Gazipur.': 'গাজীপুরে একটু নীরব অবস্থান।',
    'Four dakbungalows. One simple way to find your stay.':
        'চারটি ডাকবাংলো। আপনার অবস্থান খোঁজার এক সহজ উপায়।',
    'Sample inventory': 'নমুনা তালিকা',
    # Sample asset units (seed_assets.py)
    'Community green': 'কমিউনিটি সবুজ মাঠ',
    'Riverside field': 'নদীর ধারের মাঠ',
    'Garden grounds': 'বাগান এলাকা',
    'Shapla pond': 'শাপলা পুকুর',
    'Greenbank pond': 'সবুজ পাড়ের পুকুর',
    'Lotus pond': 'পদ্ম পুকুর',
    'Morning bazaar stall': 'সকালের বাজারের দোকান',
    'Central market space': 'কেন্দ্রীয় বাজারের জায়গা',
    'Village market stall': 'গ্রামের বাজারের দোকান',
    'Turag landing': 'তুরাগ ঘাট',
    'Shitalakshya landing': 'শীতলক্ষ্যা ঘাট',
    'Balu river ghat': 'বালু নদীর ঘাট',
    'Parishad auditorium': 'পরিষদ অডিটোরিয়াম',
    'Community auditorium': 'কমিউনিটি অডিটোরিয়াম',
    'Garden auditorium': 'বাগান অডিটোরিয়াম',
    'Open lawn · 0.8 acre': 'খোলা মাঠ · ০.৮ একর',
    'Open plot · 1.2 acres': 'খোলা প্লট · ১.২ একর',
    'Garden plot · 0.6 acre': 'বাগানের প্লট · ০.৬ একর',
    'Waterside grounds · 0.5 acre': 'পানির ধারের জায়গা · ০.৫ একর',
    'Shaded bank · 0.8 acre': 'ছায়াঢাকা পাড় · ০.৮ একর',
    'Community pond · 0.4 acre': 'কমিউনিটি পুকুর · ০.৪ একর',
    'Covered stall · 120 sq ft': 'আবৃত দোকান · ১২০ বর্গফুট',
    'Trading space · 180 sq ft': 'ব্যবসার জায়গা · ১৮০ বর্গফুট',
    'Corner stall · 100 sq ft': 'কোণার দোকান · ১০০ বর্গফুট',
    'Riverside landing space': 'নদীর ধারের ঘাটের জায়গা',
    'Sheltered river landing': 'ছাউনিযুক্ত নদী ঘাট',
    'Small community landing': 'ছোট কমিউনিটি ঘাট',
    'Main hall · 400 seats': 'প্রধান হল · ৪০০ আসন',
    'Community hall · 200 seats': 'কমিউনিটি হল · ২০০ আসন',
    'Meeting hall · 100 seats': 'মিটিং হল · ১০০ আসন',
    'Managed access,Local assistance': 'পরিচালিত প্রবেশ,স্থানীয় সহায়তা',
    # Catalogue form validation (core/catalogue.py)
    'Choose today or a future date.': 'আজ বা ভবিষ্যতের একটি তারিখ বেছে নিন।',
    'Choose a date within the booking window.': 'বুকিং সময়সীমার মধ্যে একটি তারিখ বেছে নিন।',
    'Choose an end date after the start, within 14 days.':
        'শুরুর তারিখের পরে, ১৪ দিনের মধ্যে একটি শেষ তারিখ বেছে নিন।',
    # Booking journey extras (bookings/journey.py)
    'Reception check': 'রিসেপশন যাচাই',
    'Finance check': 'অর্থ যাচাই',
    'Payment received': 'পেমেন্ট গৃহীত',
    'Payment received. A correction was requested. Reply in the message section below.':
        'পেমেন্ট গৃহীত। সংশোধনের অনুরোধ করা হয়েছে। নিচের বার্তা অংশে উত্তর দিন।',
    'Payment received. Approval is pending; your permit will be available after final approval.':
        'পেমেন্ট গৃহীত। অনুমোদন অপেক্ষমাণ; চূড়ান্ত অনুমোদনের পর আপনার পারমিট পাওয়া যাবে।',
    'Payment received and approval complete. Please contact the booking desk to confirm your permit.':
        'পেমেন্ট গৃহীত এবং অনুমোদন সম্পন্ন। আপনার পারমিট নিশ্চিত করতে বুকিং ডেস্কের সঙ্গে যোগাযোগ করুন।',
    'You can pay now on the demo gateway. Your permit will be issued only after final approval.':
        'আপনি এখন ডেমো গেটওয়েতে পেমেন্ট করতে পারেন। চূড়ান্ত অনুমোদনের পরেই পারমিট ইস্যু হবে।',
    'Payment received. Your booking still requires approval. You can download your receipt now; the permit will be available after approval.':
        'পেমেন্ট গৃহীত। আপনার বুকিংয়ে এখনো অনুমোদন প্রয়োজন। আপনি এখনই রসিদ ডাউনলোড করতে পারেন; অনুমোদনের পর পারমিট পাওয়া যাবে।',
    # Demo payment gateway (templates/payments/gateway.html, payments/gateway.py)
    'Transaction ID': 'লেনদেন আইডি',
    'Scan to check booking status': 'বুকিংয়ের অবস্থা দেখতে স্ক্যান করুন',
    'This QR checks your booking. It does not make a payment or replace a permit.':
        'এই QR আপনার বুকিং যাচাই করে। এটি পেমেন্ট করে না বা পারমিটের বিকল্পও নয়।',
    'Choose how to pay': 'কীভাবে পেমেন্ট করবেন বেছে নিন',
    'No payment was completed. You can try another simulated payment.':
        'কোনো পেমেন্ট সম্পন্ন হয়নি। আপনি অন্য একটি অনুকরণকৃত পেমেন্ট চেষ্টা করতে পারেন।',
    'Payment checkout': 'পেমেন্ট চেকআউট',
    'Payment methods': 'পেমেন্ট পদ্ধতি',
    'Payment navigation': 'পেমেন্ট নেভিগেশন',
    'Choose a mobile wallet': 'একটি মোবাইল ওয়ালেট বেছে নিন',
    'Choose a bank payment method': 'একটি ব্যাংক পেমেন্ট পদ্ধতি বেছে নিন',
    'Mobile banking': 'মোবাইল ব্যাংকিং',
    'Simulated bank transfer': 'অনুকরণকৃত ব্যাংক ট্রান্সফার',
    'Simulated internet banking': 'অনুকরণকৃত ইন্টারনেট ব্যাংকিং',
    'Simulated payment': 'অনুকরণকৃত পেমেন্ট',
    'Simulated payment received': 'অনুকরণকৃত পেমেন্ট গৃহীত',
    'Simulated payment · No money is transferred': 'অনুকরণকৃত পেমেন্ট · কোনো টাকা লেনদেন হয় না',
    'Simulate payment': 'পেমেন্ট অনুকরণ করুন',
    'Demo card': 'ডেমো কার্ড',
    'Demo checkout': 'ডেমো চেকআউট',
    'Ready to simulate': 'অনুকরণের জন্য প্রস্তুত',
    'For simulation only': 'শুধু অনুকরণের জন্য',
    'A sample card is ready. No card details are needed.':
        'একটি নমুনা কার্ড প্রস্তুত। কার্ডের বিবরণের প্রয়োজন নেই।',
    'No wallet number, PIN or verification code is needed. This does not connect to your wallet.':
        'ওয়ালেট নম্বর, পিন বা যাচাই কোডের প্রয়োজন নেই। এটি আপনার ওয়ালেটের সঙ্গে সংযুক্ত হয় না।',
    'No bank account or login details are needed. This does not connect to your bank.':
        'ব্যাংক অ্যাকাউন্ট বা লগইন তথ্যের প্রয়োজন নেই। এটি আপনার ব্যাংকের সঙ্গে সংযুক্ত হয় না।',
    'Only the selected method is submitted. Do not enter real payment details.':
        'শুধু নির্বাচিত পদ্ধতিটি জমা হয়। প্রকৃত পেমেন্টের তথ্য দেবেন না।',
    'Selected method': 'নির্বাচিত পদ্ধতি',
    'Fewer guests': 'কম অতিথি',
    'More guests': 'বেশি অতিথি',
    'Next month': 'পরবর্তী মাস',
    'Previous month': 'পূর্ববর্তী মাস',
    'Amount paid': 'পরিশোধিত পরিমাণ',
    'Payment slip': 'পেমেন্ট স্লিপ',
    'Permit available': 'পারমিট উপলব্ধ',
    'Your permit is available as a separate document.':
        'আপনার পারমিটটি একটি পৃথক নথি হিসেবে উপলব্ধ।',
    'Callback history': 'কলব্যাকের ইতিহাস',
    'Booking verification QR code': 'বুকিং যাচাই QR কোড',
    'Check booking status': 'বুকিংয়ের অবস্থা দেখুন',
    'These controls test local simulated callbacks. Duplicate callbacks are ignored; forged callbacks are rejected.':
        'এই নিয়ন্ত্রণগুলো স্থানীয় অনুকরণকৃত কলব্যাক পরীক্ষা করে। ডুপ্লিকেট কলব্যাক উপেক্ষিত; জাল কলব্যাক প্রত্যাখ্যাত হয়।',
    'Unknown transaction reference.': 'অজানা লেনদেন রেফারেন্স।',
    'Invalid signature. The callback was rejected.':
        'অবৈধ স্বাক্ষর। কলব্যাক প্রত্যাখ্যাত হয়েছে।',
    'Amount or booking reference does not match the demand.':
        'পরিমাণ বা বুকিং রেফারেন্স দাবির সঙ্গে মেলেনি।',
    'Payment for this booking was already confirmed. Duplicate callback ignored.':
        'এই বুকিংয়ের পেমেন্ট ইতিমধ্যে নিশ্চিত হয়েছে। ডুপ্লিকেট কলব্যাক উপেক্ষিত।',
    'The booking is not eligible for payment or its inventory hold has expired or been released.':
        'বুকিংটি পেমেন্টের জন্য উপযোগী নয় অথবা এর ইনভেন্টরি হোল্ডের মেয়াদ শেষ হয়েছে বা ছেড়ে দেওয়া হয়েছে।',
    'Payment verified and booking confirmed.': 'পেমেন্ট যাচাইকৃত এবং বুকিং নিশ্চিত।',
    'Payment received. Approval is pending; the permit will be issued after final approval.':
        'পেমেন্ট গৃহীত। অনুমোদন অপেক্ষমাণ; চূড়ান্ত অনুমোদনের পর পারমিট ইস্যু হবে।',
    'The gateway reported that the payment did not complete.':
        'গেটওয়ে জানিয়েছে যে পেমেন্ট সম্পন্ন হয়নি।',
    'Unsupported gateway status.': 'অসমর্থিত গেটওয়ে অবস্থা।',
    'This refund has already been processed.': 'এই ফেরত ইতিমধ্যে প্রক্রিয়া করা হয়েছে।',
    'Refund request rejected.': 'ফেরতের অনুরোধ প্রত্যাখ্যাত।',
    'You can retry payment from your application page while the payment window is open.':
        'পেমেন্টের সময়সীমা খোলা থাকাকালীন আপনি আপনার আবেদনের পাতা থেকে পেমেন্ট আবার চেষ্টা করতে পারেন।',
    'The payment window closed and the hold was released. Please apply again if you still need the facility.':
        'পেমেন্টের সময়সীমা শেষ হয়েছে এবং হোল্ড ছেড়ে দেওয়া হয়েছে। সুবিধাটি এখনো প্রয়োজন হলে আবার আবেদন করুন।',
}


_NEW_TASK_SUBJECT = re.compile(r'^New task: (.+) \((GZP-[A-Z0-9-]+)\)$')
_UPDATE_SUBJECT = re.compile(r'^Update on (GZP-[A-Z0-9-]+)$')
_RECEIVED_SUBJECT = re.compile(r'^Application received - (GZP-[A-Z0-9-]+)$')
_MEETING_SUBJECT = re.compile(r'^Meeting today: (.+)$')
_BOOKING_UPDATE = re.compile(r'^Booking (GZP-[A-Z0-9-]+) at (.+?) is now (.+?)\.?$')
_PERSON_SUBJECT = re.compile(r'^([^-]+?) - ([^/]+?) / (.+)$')


def _pick(text):
    return BN.get(text) or BN_EXTRA.get(text) or text


def _dynamic(text):
    """Translate generated strings such as notification subjects and previews."""
    m = re.match(r'^Week of (.+?) to (.+?)\. One shift per employee per day\.$', text)
    if m:
        return f'সপ্তাহ {m.group(1)} থেকে {m.group(2)}। প্রতিদিন প্রতি কর্মচারীর জন্য একটি শিফট।'
    m = re.match(
        r'^Desk review, optional technical review, then approval within the delegated authority\.'
        r' Amounts above BDT ([\d,]+) go to the CEO\.$', text)
    if m:
        return ('ডেস্ক পর্যালোচনা, ঐচ্ছিক কারিগরি পর্যালোচনা, তারপর অর্পিত ক্ষমতার মধ্যে অনুমোদন। '
                f'{localize(m.group(1))} টাকার বেশি হলে সিইও-এর কাছে যায়।')
    m = re.match(r'^Release expired holds \((\d+)\)$', text)
    if m:
        return f'মেয়াদোত্তীর্ণ হোল্ড ছেড়ে দিন ({localize(m.group(1))})'
    m = re.match(r'^Payment window: open (.+?)\. Gateway charge paid by user: (.+)$', text)
    if m:
        return (f'পেমেন্ট সময়সীমা: খোলা {m.group(1)}। '
                f'ব্যবহারকারীর প্রদত্ত গেটওয়ে চার্জ: {_pick(m.group(2))}')
    m = re.match(r'^Receipt at (.+?)\. A permit has been issued\.$', text)
    if m:
        return f'রসিদ: {m.group(1)}। একটি পারমিট ইস্যু হয়েছে।'
    m = re.match(r'^Verification is read-only and available to anyone holding the QR code\.'
                 r' It shows no contact details\. Checked at (.+?)\.$', text)
    if m:
        return ('যাচাই কেবল পঠনযোগ্য এবং QR কোডধারীর জন্য উন্মুক্ত। এটি কোনো যোগাযোগের '
                f'বিবরণ দেখায় না। যাচাই হয়েছে {localize(m.group(1))}।')
    m = re.match(r'^(\d+ (?:days?|hours?|weeks?|months?|years?|minutes?)'
                 r'(?:, \d+ (?:days?|hours?|weeks?|months?|years?|minutes?))*) late$', text)
    if m:
        units = {'day': 'দিন', 'days': 'দিন', 'hour': 'ঘণ্টা', 'hours': 'ঘণ্টা',
                 'week': 'সপ্তাহ', 'weeks': 'সপ্তাহ', 'month': 'মাস', 'months': 'মাস',
                 'year': 'বছর', 'years': 'বছর', 'minute': 'মিনিট', 'minutes': 'মিনিট'}
        duration = re.sub(r'\b(days?|hours?|weeks?|months?|years?|minutes?)\b',
                          lambda x: units[x.group(1)], m.group(1))
        return f'{localize(duration)} দেরি'
    m = re.match(r'^(.+?); integrity check: ok$', text)
    if m:
        return f'{_pick(m.group(1))}; অখণ্ডতা যাচাই: ঠিক'
    m = re.match(r'^Delegated approval up to BDT ([\d,]+)$', text)
    if m:
        return f'{localize(m.group(1))} টাকা পর্যন্ত অর্পিত অনুমোদন'
    m = re.match(r'^(.+?) \(sample\)$', text)
    if m:
        return f'{_pick(m.group(1))} (নমুনা)'
    m = re.match(r'^Report viewed: (.+)$', text)
    if m:
        return f'প্রতিবেদন দেখা হয়েছে: {_pick(m.group(1))}'
    m = re.match(r'^This permit exists but is not in a confirmed state \(status: (.+?)\)\.$', text)
    if m:
        return f'এই পারমিটটি নিশ্চিত অবস্থায় নেই (অবস্থা: {_pick(m.group(1))})।'
    m = re.match(r'^This task is (.+?)\. Decisions can no longer be recorded on it\.$', text)
    if m:
        status = m.group(1)
        status = status[:1].upper() + status[1:]
        return f'এই কাজটি এখন {_pick(status)}। এতে আর সিদ্ধান্ত নথিভুক্ত করা যাবে না।'
    m = re.match(r'^Workflow (GZP-[A-Z0-9-]+) started at (.+)$', text)
    if m:
        return f'ওয়ার্কফ্লো {m.group(1)} শুরু হয়েছে: {_pick(m.group(2))}'
    m = _NEW_TASK_SUBJECT.match(text)
    if m:
        step = m.group(1)
        step = step[:1].upper() + step[1:]
        return f'নতুন কাজ: {_pick(step)} ({m.group(2)})'
    m = _UPDATE_SUBJECT.match(text)
    if m:
        return f'হালনাগাদ: {m.group(1)}'
    m = _RECEIVED_SUBJECT.match(text)
    if m:
        return f'আবেদন গৃহীত - {m.group(1)}'
    m = _MEETING_SUBJECT.match(text)
    if m:
        return f'আজকের সভা: {_pick(m.group(1))}'
    m = _BOOKING_UPDATE.match(text)
    if m:
        return f'বুকিং {m.group(1)} — {_pick(m.group(2))}: এখন {_pick(m.group(3))}।'

    changed = text
    subs = [
        (r'^Dear ([^,]+),', r'প্রিয় \1,'),
        (r'A new task is waiting for you at the "([^"]+)" step\.?',
         lambda x: f'"{_pick(x.group(1))}" ধাপে আপনার জন্য একটি নতুন কাজ অপেক্ষা করছে।'),
        (r'Reference: ', 'রেফারেন্স: '),
        (r'Subject: ', 'বিষয়: '),
        (r'Due: ', 'সময়সীমা: '),
        (r'Open My Tasks to review it\.?', 'পর্যালোচনা করতে "আমার কাজ" খুলুন।'),
        (r'We received your application (GZP-[A-Z0-9-]+)\.?', r'আপনার আবেদন \1 আমরা পেয়েছি।'),
        (r'Your application for (.+?) was received and is under review\.?',
         lambda x: f'{_pick(x.group(1))} — আপনার আবেদন গৃহীত হয়েছে এবং পর্যালোচনাধীন আছে।'),
        (r'You can track progress from your dashboard\.?',
         'ড্যাশবোর্ড থেকে অগ্রগতি দেখতে পারেন।'),
        (r'Gazipur Zila Parishad \(demo\)', 'গাজীপুর জেলা পরিষদ (নমুনা)'),
    ]
    for pattern, repl in subs:
        changed = re.sub(pattern, repl, changed)
    m = _PERSON_SUBJECT.match(changed)
    if m:
        changed = f'{m.group(1)} - {_pick(m.group(2))} / {_pick(m.group(3))}'
    if changed == text:
        return None
    tokens = []

    def _stash(match):
        tokens.append(match.group(0))
        return chr(0xE000 + len(tokens) - 1)

    changed = re.sub(r'GZP-[A-Z0-9-]+', _stash, changed)
    changed = localize(changed)
    for index, token in enumerate(tokens):
        changed = changed.replace(chr(0xE000 + index), token)
    return changed


_TRANSLIT_VOWELS = {
    'অ': 'o', 'আ': 'a', 'ই': 'i', 'ঈ': 'i', 'উ': 'u', 'ঊ': 'u',
    'ঋ': 'ri', 'এ': 'e', 'ঐ': 'oi', 'ও': 'o', 'ঔ': 'ou',
}
_TRANSLIT_SIGNS = {
    'া': 'a', 'ি': 'i', 'ী': 'i', 'ু': 'u', 'ূ': 'u', 'ৃ': 'ri',
    'ে': 'e', 'ৈ': 'oi', 'ো': 'o', 'ৌ': 'ou',
}
_TRANSLIT_CONSONANTS = {
    'ক': 'k', 'খ': 'kh', 'গ': 'g', 'ঘ': 'gh', 'ঙ': 'ng',
    'চ': 'ch', 'ছ': 'chh', 'জ': 'j', 'ঝ': 'jh', 'ঞ': 'n',
    'ট': 't', 'ঠ': 'th', 'ড': 'd', 'ঢ': 'dh', 'ণ': 'n',
    'ত': 't', 'থ': 'th', 'দ': 'd', 'ধ': 'dh', 'ন': 'n',
    'প': 'p', 'ফ': 'ph', 'ব': 'b', 'ভ': 'bh', 'ম': 'm',
    'য': 'j', 'র': 'r', 'ল': 'l', 'শ': 'sh', 'ষ': 'sh', 'স': 's',
    'হ': 'h', 'ৎ': 't',
}
_TRANSLIT_MARKS = {'ং': 'ng', 'ঃ': 'h', 'ঁ': 'n'}
_TRANSLIT_NUKTA = {'ড': 'r', 'ঢ': 'rh', 'য': 'y'}
_TRANSLIT_CLUSTERS = {
    'জ্ঞ': 'gy', 'ক্ষ': 'kkh', 'ঞ্চ': 'nch', 'ঙ্গ': 'ng', 'ন্ত': 'nt',
    'ন্দ': 'nd', 'ম্ব': 'mb', 'স্ট': 'st', 'ত্র': 'tr', 'প্র': 'pr',
    'গ্র': 'gr', 'ব্র': 'br', 'ক্র': 'kr', 'শ্র': 'shr', 'জ্জ': 'jj',
}
# Familiar English words stay English in Banglish.
_TRANSLIT_FIXES = {
    'djashobord': 'dashboard',
    'dyashbord': 'dashboard',
    'dakobanglo': 'dakbanglo',
    'dakobangla': 'dakbangla',
    'meil': 'mail',
    'autoboks': 'outbox',
    'inboks': 'inbox',
    'setings': 'settings',
    'protibedon': 'report',
    'siio': 'CEO',
    'iunit': 'unit',
    'sistem': 'system',
    'bjoboharokari': 'users',
    'byboharokari': 'users',
    'kormokkhetr': 'workspace',
    'eichar': 'HR',
    'prokolp': 'prokolpo',
    'somoyottirn': 'somoyottirno',
    'iueti': 'UAT',
    'diuti': 'Duty',
    'phail': 'file',
    'rajosb': 'rajoshsho',
    'bjakap': 'backup',
    'tikit': 'ticket',
}
# Whole words that read better in English (unit and facility names).
_TRANSLIT_WORDS = {
    'rum': 'room',
    'stjandard': 'standard',
    'phjamili': 'family',
    'bhiaipi': 'VIP',
    'suit': 'suite',
    'sjut': 'suite',
    'konopharens': 'conference',
    'miting': 'meeting',
    'hol': 'hall',
    'pljatophorm': 'platform',
    'dijital': 'digital',
    'jonj': 'jonno',
}
_TRANSLIT_WORDS_RE = re.compile(
    r'\b(' + '|'.join(sorted(_TRANSLIT_WORDS, key=len, reverse=True)) + r')\b',
    re.IGNORECASE)
# Office terms a Bangladeshi reader says in English; Banglish keeps them as they are.
_BANGLISH_KEEP = {
    'Assets', 'All assets', 'Land', 'Ponds', 'Markets', 'Kheyaghat',
    'Auditorium', 'Dak Bungalow', 'Dak Bungalow details', 'Approval status',
    'Booking status', 'Booking management', 'Booked', 'Pending approval',
    'Available', 'Dashboard', 'CEO dashboard', 'Settings', 'Mail', 'Inbox',
    'Outbox', 'Report', 'Reports', 'Payment', 'Payments', 'Total', 'Search',
    'Status', 'Export CSV', 'My tasks', 'Assets & tariffs',
    'Citizen', 'Officials', 'Citizen sign-in', 'Officials sign-in',
    'Citizen / user portal', 'Officials portal', 'Official sign-in',
    'Enter citizen portal', 'Secure payment', 'Card', 'Bank', 'Net banking',
    'Pay with cards', 'Card number', 'Card holder name', 'Mobile wallet',
    'bKash account number', 'Nagad account number', 'Rocket account number',
    'Account number', 'Internet banking', 'User ID', 'Direct debit',
    'Welcome back', 'Powered by', 'Secured by', 'Visa · Mastercard · Amex',
    'Recall', 'Pay',
}


def transliterate(text):
    """Write Bengali in Latin letters (Banglish), keeping digits and ASCII."""
    chars = list(str(text))
    out = []
    index = 0
    total = len(chars)
    while index < total:
        ch = chars[index]
        cluster = ''
        latin = ''
        for size in (3, 2):
            seq = ''.join(chars[index:index + size])
            if seq in _TRANSLIT_CLUSTERS:
                cluster, latin = seq, _TRANSLIT_CLUSTERS[seq]
                break
        if cluster:
            out.append(latin)
            nxt = chars[index + len(cluster)] if index + len(cluster) < total else ''
            if nxt and (nxt in _TRANSLIT_CONSONANTS or nxt in _TRANSLIT_MARKS):
                out.append('o')
            index += len(cluster)
            continue
        if ch in _TRANSLIT_VOWELS:
            out.append(_TRANSLIT_VOWELS[ch])
        elif ch in _TRANSLIT_CONSONANTS:
            out.append(_TRANSLIT_CONSONANTS[ch])
            nxt = chars[index + 1] if index + 1 < total else ''
            if nxt in _TRANSLIT_CONSONANTS or nxt in _TRANSLIT_MARKS:
                out.append('o')
        elif ch in _TRANSLIT_SIGNS:
            out.append(_TRANSLIT_SIGNS[ch])
        elif ch == '\u09bc' and index and chars[index - 1] in _TRANSLIT_NUKTA:
            if out:
                out.pop()
            out.append(_TRANSLIT_NUKTA[chars[index - 1]])
        elif ch in _TRANSLIT_MARKS:
            out.append(_TRANSLIT_MARKS[ch])
        elif ch == '\u09cd':
            pass
        else:
            out.append(ch)
        index += 1
    text = ''.join(out).translate(str.maketrans('০১২৩৪৫৬৭৮৯', '0123456789'))
    for wrong, right in _TRANSLIT_FIXES.items():
        text = text.replace(wrong, right)
    text = _TRANSLIT_WORDS_RE.sub(
        lambda m: _TRANSLIT_WORDS[m.group(0).lower()], text)
    return text


def banglish(text):
    """Bangla wording in Latin letters; untranslated strings stay English."""
    raw = str(text)
    if raw in _BANGLISH_KEEP:
        return raw
    found = BN.get(raw) or BN_EXTRA.get(raw) or _dynamic(raw)
    if not found:
        return raw
    out = transliterate(found)
    if raw[:1].isalpha() and raw[:1].islower():
        return out[:1].lower() + out[1:]
    if out[:1].isalpha():
        return out[:1].upper() + out[1:]
    return out


def translate(text, lang='en'):
    if lang == 'bn':
        found = BN.get(text) or BN_EXTRA.get(text)
        if found:
            return found
        dynamic = _dynamic(str(text))
        if dynamic:
            return dynamic
    if lang == 'bng':
        return banglish(text)
    return text


_OPAQUE_BLOCKS = re.compile(
    r'<script\b.*?</script>|<style\b.*?</style>|<textarea\b.*?</textarea>'
    r'|<pre\b.*?</pre>|<!--.*?-->',
    re.S | re.I,
)
_TEXT_NODE = re.compile(r'(?<=>)([^<]+)(?=<)')
_TEXT_ATTR = re.compile(r'\b(placeholder|title|aria-label)="([^"]*)"')


def translate_html(html):
    """Translate static text nodes and form hints for templates that are not
    individually tagged. Exact dictionary matches only, so data values and
    proper nouns are left untouched."""
    if 'bn' != CURRENT_LANG.get():
        return html

    def _lookup(raw):
        plain = ' '.join(unescape(raw).split())
        if not plain:
            return None
        found = BN.get(plain) or BN_EXTRA.get(plain)
        if found:
            return found if found != plain else None
        if re.search(r'[A-Za-z]', plain):
            dynamic = _dynamic(plain)
            if dynamic and dynamic != plain:
                return dynamic
        return None

    def _swap_attr(match):
        name, value = match.group(1), match.group(2)
        found = _lookup(value)
        if not found:
            return match.group(0)
        return f'{name}="{escape(found)}"'

    # Attributes first: masks replace whole <textarea>/<script> blocks, which
    # would otherwise hide the placeholder hints inside them.
    masked = _TEXT_ATTR.sub(_swap_attr, html)
    opaque = []

    def _mask(match):
        opaque.append(match.group(0))
        return chr(0x0001) + str(len(opaque) - 1) + chr(0x0002)

    masked = _OPAQUE_BLOCKS.sub(_mask, masked)

    def _swap_text(match):
        raw = match.group(1)
        found = _lookup(raw.strip())
        if not found:
            return raw
        lead = raw[:len(raw) - len(raw.lstrip())]
        trail = raw[len(raw.rstrip()):]
        return lead + escape(found) + trail

    masked = _TEXT_NODE.sub(_swap_text, masked)
    for index, block in enumerate(opaque):
        masked = masked.replace(chr(0x0001) + str(index) + chr(0x0002), block)
    return masked


def status_bn(label):
    return BN.get(label, label)


# Late additions for the secondary modules (accounts, workflow, support, health,
# security, payments, reception, HR, MIS). Merged without overriding earlier keys.
_BN_LATE = {
    # accounts
    'Access & verification': 'অ্যাক্সেস ও যাচাই',
    'Account details': 'অ্যাকাউন্টের বিবরণ',
    'Account active': 'অ্যাকাউন্ট সক্রিয়',
    'Accounts are created with a role; every role permission is enforced on the server.':
        'অ্যাকাউন্ট একটি ভূমিকা নিয়ে তৈরি হয়; প্রতিটি ভূমিকার অনুমতি সার্ভারে প্রয়োগ করা হয়।',
    'Assigned facility': 'নির্ধারিত ভবন',
    'Assigned facility (reception)': 'নির্ধারিত ভবন (রিসেপশন)',
    'Can act within permissions': 'অনুমোদিত সীমার মধ্যে কাজ করতে পারেন',
    'Change password': 'পাসওয়ার্ড পরিবর্তন',
    'Confirm new password': 'নতুন পাসওয়ার্ড নিশ্চিত করুন',
    'Confirm password': 'পাসওয়ার্ড নিশ্চিত করুন',
    'Current password': 'বর্তমান পাসওয়ার্ড',
    'Email verified': 'ইমেইল যাচাইকৃত',
    'First name': 'নামের প্রথম অংশ',
    'Last name': 'নামের শেষ অংশ',
    'New password': 'নতুন পাসওয়ার্ড',
    'No verification codes yet.': 'এখনও কোনো যাচাই কোড নেই।',
    'Unused': 'অব্যবহৃত',
    'Update password': 'পাসওয়ার্ড হালনাগাদ করুন',
    'Used': 'ব্যবহৃত',
    'Verification history': 'যাচাইয়ের ইতিহাস',
    'Your account details, role and verification status.':
        'আপনার অ্যাকাউন্টের বিবরণ, ভূমিকা ও যাচাইয়ের অবস্থা।',
    'code': 'কোড',
    '· attempt': '· চেষ্টা',
    'Email and mobile verified': 'ইমেইল ও মোবাইল যাচাইকৃত',
    'Least privilege': 'ন্যূনতম অনুমতি',
    'Back to accounts': 'অ্যাকাউন্টে ফিরে যান',
    'Management / Auditor accounts are read-only: write requests are blocked by middleware, not just hidden from the menu.':
        'ব্যবস্থাপনা / অডিটর অ্যাকাউন্ট কেবল পঠনযোগ্য: লেখার অনুরোধ মিডলওয়্যার দ্বারা ব্লক করা হয়, শুধু মেনু থেকে লুকানো নয়।',
    "Permissions come from the account's role. A System Administrator manages roles, master data, settings and audit access, but has no implicit booking approval power.":
        'অনুমতি আসে অ্যাকাউন্টের ভূমিকা থেকে। সিস্টেম প্রশাসক ভূমিকা, মাস্টার ডেটা, সেটিংস ও অডিট অ্যাক্সেস পরিচালনা করেন, তবে বুকিং অনুমোদনের অন্তর্নিহিত ক্ষমতা নেই।',
    'Already registered?': 'ইতিমধ্যে নিবন্ধিত?',
    'Citizen / applicant account. Email and mobile are verified with a one-time code.':
        'নাগরিক / আবেদনকারী অ্যাকাউন্ট। ইমেইল ও মোবাইল এককালীন কোডে যাচাই করা হয়।',
    'Use a sample number only. SMS delivery is simulated in the demo.':
        'শুধু নমুনা নম্বর ব্যবহার করুন। ডেমোতে এসএমএস পাঠানো অনুকরণ করা হয়।',
    'Codes expire after 10 minutes and allow five attempts. Login attempts and OTP attempts are rate limited on the server.':
        'কোডের মেয়াদ ১০ মিনিট এবং পাঁচবার চেষ্টা করা যায়। লগইন ও ওটিপি চেষ্টা সার্ভারে হার-সীমাবদ্ধ।',
    'Demo OTP:': 'ডেমো ওটিপি:',
    'One-time code': 'এককালীন কোড',
    'Send a new code': 'নতুন কোড পাঠান',
    'Shown on screen because SMS and email delivery are simulated. The same message is in the demo outbox.':
        'এসএমএস ও ইমেইল পাঠানো অনুকরণ করা হয় বলে এটি স্ক্রিনে দেখানো হচ্ছে। একই বার্তা ডেমো আউটবক্সে আছে।',
    'Verify your email and mobile': 'আপনার ইমেইল ও মোবাইল যাচাই করুন',
    'Scroll horizontally for all roles': 'সব ভূমিকা দেখতে অনুভূমিকভাবে স্ক্রল করুন',
    'No accounts found.': 'কোনো অ্যাকাউন্ট পাওয়া যায়নি।',
    'demo': 'ডেমো',
    '· Gazipur Zila Parishad': '· গাজীপুর জেলা পরিষদ',
    # workflow designer and performance
    'Active Inactive': 'সক্রিয় নিষ্ক্রিয়',
    'Acts as': 'ভূমিকা পালন করে',
    'Acts as role': 'যে ভূমিকা হিসেবে কাজ করে',
    'Add a step': 'একটি ধাপ যোগ করুন',
    'Add or update a row': 'সারি যোগ বা হালনাগাদ করুন',
    'All categories': 'সব বিভাগ',
    'Allow final approval': 'চূড়ান্ত অনুমোদন দিন',
    'Allowed decisions': 'অনুমোদিত সিদ্ধান্ত',
    'Always': 'সর্বদা',
    'Approval decisions are checked against the authority matrix. Correction decisions return the request to the requester.':
        'অনুমোদনের সিদ্ধান্ত ক্ষমতা ম্যাট্রিক্সের সঙ্গে যাচাই করা হয়। সংশোধনের সিদ্ধান্ত অনুরোধটি আবেদনকারীর কাছে ফেরত দেয়।',
    'Approving here completes the request.': 'এখানে অনুমোদন করলে অনুরোধটি সম্পন্ন হবে।',
    'Average turnaround': 'গড় নিষ্পত্তি সময়',
    'By template': 'টেমপ্লেট অনুযায়ী',
    'Can approve': 'অনুমোদন করতে পারেন',
    'Completed instances only': 'শুধু সম্পন্ন ইনস্ট্যান্স',
    'Condition': 'শর্ত',
    'Condition examples.': 'শর্তের উদাহরণ।',
    'Conditions': 'শর্তাবলি',
    'Configured authority': 'নির্ধারিত ক্ষমতা',
    'Configured route': 'নির্ধারিত পথ',
    'Current': 'বর্তমান',
    'Current step': 'বর্তমান ধাপ',
    'Decision authority for approvals is checked against the':
        'অনুমোদনের সিদ্ধান্ত-ক্ষমতা যাচাই করা হয়',
    'Decision history': 'সিদ্ধান্তের ইতিহাস',
    'Due · overdue': 'সময়সীমা · মেয়াদোত্তীর্ণ',
    'Edit step New step': 'ধাপ সম্পাদনা নতুন ধাপ',
    'Edit workflow template New workflow template':
        'কর্মপ্রবাহ টেমপ্লেট সম্পাদনা নতুন কর্মপ্রবাহ টেমপ্লেট',
    'Final step': 'চূড়ান্ত ধাপ',
    'Instances': 'ইনস্ট্যান্স',
    'Instances in view': 'দৃশ্যমান ইনস্ট্যান্স',
    'Max amount': 'সর্বোচ্চ পরিমাণ',
    'Max amount (৳)': 'সর্বোচ্চ পরিমাণ (৳)',
    'No authority rows configured. Approvals will be refused.':
        'কোনো ক্ষমতা সারি কনফিগার করা নেই। অনুমোদন প্রত্যাখ্যাত হবে।',
    'No decisions are configured for this step.':
        'এই ধাপের জন্য কোনো সিদ্ধান্ত কনফিগার করা নেই।',
    'No decisions recorded.': 'কোনো সিদ্ধান্ত নথিভুক্ত নেই।',
    'No instances match.': 'কোনো ইনস্ট্যান্স মেলেনি।',
    'No instances yet.': 'এখনও কোনো ইনস্ট্যান্স নেই।',
    'No pending tasks.': 'কোনো অপেক্ষমাণ কাজ নেই।',
    'No rejections recorded.': 'কোনো প্রত্যাখ্যান নথিভুক্ত নেই।',
    'No steps matched the request conditions.':
        'অনুরোধের শর্তের সঙ্গে কোনো ধাপ মেলেনি।',
    'No steps yet. Add the first step.': 'এখনও কোনো ধাপ নেই। প্রথম ধাপ যোগ করুন।',
    'No tasks.': 'কোনো কাজ নেই।',
    'No workflow instances recorded.': 'কোনো কর্মপ্রবাহ ইনস্ট্যান্স নথিভুক্ত নেই।',
    'No workflow templates yet.': 'এখনও কোনো কর্মপ্রবাহ টেমপ্লেট নেই।',
    'Note / reason': 'মন্তব্য / কারণ',
    'Open record': 'রেকর্ড খুলুন',
    'Open request': 'অনুরোধ খুলুন',
    'Order': 'ক্রম',
    'Past the step SLA': 'ধাপের এসএলএ অতিক্রান্ত',
    'Payload': 'পেলোড',
    'Pending across all roles': 'সব ভূমিকায় অপেক্ষমাণ',
    'Pending workload by step': 'ধাপ অনুযায়ী অপেক্ষমাণ কাজ',
    'Recent instances': 'সাম্প্রতিক ইনস্ট্যান্স',
    'Record a decision': 'সিদ্ধান্ত নথিভুক্ত করুন',
    'Record id': 'রেকর্ড আইডি',
    'Record type': 'রেকর্ডের ধরন',
    'Request data': 'অনুরোধের তথ্য',
    'Request details': 'অনুরোধের বিবরণ',
    'Route & history': 'পথ ও ইতিহাস',
    'Route and progress': 'পথ ও অগ্রগতি',
    'SLA hours': 'এসএলএ ঘণ্টা',
    'Sample route for bookings:': 'বুকিংয়ের নমুনা পথ:',
    'Sample values for the demo. The Parishad supplies and approves the real matrix. Leave the amount blank for unlimited authority within the category.':
        'ডেমোর জন্য নমুনা মান। প্রকৃত ম্যাট্রিক্স পরিষদ সরবরাহ ও অনুমোদন করবে। বিভাগের মধ্যে সীমাহীন ক্ষমতার জন্য পরিমাণ ফাঁকা রাখুন।',
    'Saving a row for the same role and category updates the existing row. Approval checks compare the request amount (for bookings, the total payable) with the max amount.':
        'একই ভূমিকা ও বিভাগের জন্য সারি সংরক্ষণ করলে বিদ্যমান সারি হালনাগাদ হয়। অনুমোদন যাচাইয়ে অনুরোধের পরিমাণ (বুকিংয়ে মোট প্রদেয়) সর্বোচ্চ পরিমাণের সঙ্গে তুলনা করা হয়।',
    'Status mix': 'অবস্থার মিশ্রণ',
    'Step name': 'ধাপের নাম',
    'Task priority': 'কাজের অগ্রাধিকার',
    'Templates group the steps used for one request category.':
        'টেমপ্লেট একটি অনুরোধ বিভাগের জন্য ব্যবহৃত ধাপগুলোকে একত্র করে।',
    'The exact sequence is data. Change the steps or conditions and the next application follows the new route. Authority to approve is separately controlled by the authority matrix.':
        'সঠিক ক্রমটাই ডেটা। ধাপ বা শর্ত পরিবর্তন করলে পরবর্তী আবেদন নতুন পথ অনুসরণ করবে। অনুমোদনের ক্ষমতা আলাদাভাবে ক্ষমতা ম্যাট্রিক্স দ্বারা নিয়ন্ত্রিত হয়।',
    'This task is': 'এই কাজটি',
    '. Decisions can no longer be recorded on it.':
        '. এর ওপর আর সিদ্ধান্ত নথিভুক্ত করা যাবে না।',
    'Top rejection reasons': 'প্রধান প্রত্যাখ্যানের কারণ',
    'Tracking ID': 'ট্র্যাকিং আইডি',
    'Turnaround, SLA exposure and rejection reasons. Computed from workflow instances and task records, not from a static spreadsheet.':
        'নিষ্পত্তি সময়, এসএলএ ঝুঁকি ও প্রত্যাখ্যানের কারণ। কর্মপ্রবাহ ইনস্ট্যান্স ও কাজের রেকর্ড থেকে গণনা করা হয়, কোনো স্থির স্প্রেডশিট থেকে নয়।',
    'Up to the last 1000 matching rows': 'সর্বশেষ ১০০০টি মিলে যাওয়া সারি পর্যন্ত',
    'authority matrix': 'ক্ষমতা ম্যাট্রিক্স',
    'decide whether a step is part of the route for a particular request. A step with no condition always runs.':
        'নির্দিষ্ট অনুরোধের জন্য কোনো ধাপ পথের অংশ হবে কি না তা নির্ধারণ করে। শর্তহীন ধাপ সবসময় চলে।',
    'final': 'চূড়ান্ত',
    '— awaiting your decision': '— আপনার সিদ্ধান্তের অপেক্ষায়',
    '· SLA h': '· এসএলএ ঘণ্টা',
    '· SLA h · conditional step': '· এসএলএ ঘণ্টা · শর্তসাপেক্ষ ধাপ',
    '· requested by on': '· অনুরোধকারী',
    'Conditional': 'শর্তসাপেক্ষ',
    'Returned for correction': 'সংশোধনের জন্য ফেরত',
    'Booking application': 'বুকিং আবেদন',
    'Leave application': 'ছুটির আবেদন',
    'Document file': 'নথি ফাইল',
    'Project action': 'প্রকল্প কার্যক্রম',
    'Document file decision': 'নথি ফাইলের সিদ্ধান্ত',
    'Employee leave approval': 'কর্মচারীর ছুটির অনুমোদন',
    'Project action approval': 'প্রকল্প কার্যক্রমের অনুমোদন',
    'Technical / facility review': 'কারিগরি / ভবন পর্যালোচনা',
    'Supervisor recommendation': 'সুপারভাইজার সুপারিশ',
    'Executive Officer decision': 'নির্বাহী কর্মকর্তার সিদ্ধান্ত',
    'Registry review and forward': 'রেজিস্ট্রি পর্যালোচনা ও ফরোয়ার্ড',
    'Registry forwards, Executive Officer approves.':
        'রেজিস্ট্রি ফরোয়ার্ড করে, নির্বাহী কর্মকর্তা অনুমোদন করেন।',
    'Executive Officer decision final': 'নির্বাহী কর্মকর্তার চূড়ান্ত সিদ্ধান্ত',
    'Project officer review': 'প্রকল্প কর্মকর্তার পর্যালোচনা',
    'Project officer forwards, Executive Officer approves.':
        'প্রকল্প কর্মকর্তা ফরোয়ার্ড করেন, নির্বাহী কর্মকর্তা অনুমোদন করেন।',
    'Desk review, optional technical review, then approval within the delegated authority. Amounts above BDT':
        'ডেস্ক পর্যালোচনা, ঐচ্ছিক কারিগরি পর্যালোচনা, তারপর অর্পিত ক্ষমতার মধ্যে অনুমোদন। এর বেশি পরিমাণ',
    'runs the step only for VIP suites and hall bookings.':
        'শুধু ভিআইপি স্যুট ও হল বুকিংয়ের জন্য এই ধাপ চলে।',
    'runs the step for stays of four nights or more, or for organizations.':
        'চার রাত বা বেশি অবস্থান, অথবা প্রতিষ্ঠানের ক্ষেত্রে এই ধাপ চলে।',
    'The payload keys come from the module that submits the request.':
        'পেলোডের কী-গুলো অনুরোধ জমা দেওয়া মডিউল থেকে আসে।',
    'forward, correct, reject': 'ফরোয়ার্ড, সংশোধন, প্রত্যাখ্যান',
    'recommend, correct, reject': 'সুপারিশ, সংশোধন, প্রত্যাখ্যান',
    'approve, recommend, reject, correct': 'অনুমোদন, সুপারিশ, প্রত্যাখ্যান, সংশোধন',
    'approve, reject, correct': 'অনুমোদন, প্রত্যাখ্যান, সংশোধন',
    'forward, return, reject': 'ফরোয়ার্ড, ফেরত, প্রত্যাখ্যান',
    'approve, reject, return': 'অনুমোদন, প্রত্যাখ্যান, ফেরত',
    'forward, reject': 'ফরোয়ার্ড, প্রত্যাখ্যান',
    'approve, reject': 'অনুমোদন, প্রত্যাখ্যান',
    '৳ Unlimited': '৳ সীমাহীন',
    'Booking Desk → Technical Reviewer (suite/hall only) → Executive Officer → CEO/Chairman (4+ nights or organization).':
        'বুকিং ডেস্ক → কারিগরি পর্যালোচক (শুধু স্যুট/হল) → নির্বাহী কর্মকর্তা → সিইও/চেয়ারম্যান (৪+ রাত বা প্রতিষ্ঠান)।',
    # support
    'Assignee': 'দায়িত্বপ্রাপ্ত',
    'Logged': 'নথিভুক্ত',
    'Only support managers can change the ticket. The requester is notified as the status changes in the real deployment.':
        'শুধু সহায়তা ব্যবস্থাপক টিকিট পরিবর্তন করতে পারেন। প্রকৃত বাস্তবায়নে অবস্থা পরিবর্তনের সঙ্গে আবেদনকারীকে জানানো হয়।',
    'Resolution': 'সমাধান',
    'Resolution / note': 'সমাধান / মন্তব্য',
    'Save ticket': 'টিকিট সংরক্ষণ',
    'Tickets': 'টিকিট',
    'Update ticket': 'টিকিট হালনাগাদ',
    'Deliverables & UAT': 'প্রদেয় ও ইউএটি',
    'No phases configured. Run the demo seed.': 'কোনো ধাপ কনফিগার করা নেই। ডেমো সিড চালান।',
    'No checklist items. Run the demo seed.': 'কোনো চেকলিস্ট আইটেম নেই। ডেমো সিড চালান।',
    'item(s) passed': 'আইটেম পাস হয়েছে',
    'No change requests.': 'কোনো পরিবর্তন অনুরোধ নেই।',
    'Submit a change request': 'পরিবর্তন অনুরোধ জমা দিন',
    'Submit request': 'অনুরোধ জমা দিন',
    '2 business-hour target': '২ কর্মঘণ্টার লক্ষ্যমাত্রা',
    'Incidents and service requests with the sample support targets:':
        'নমুনা সহায়তা লক্ষ্যমাত্রাসহ ঘটনা ও সেবার অনুরোধ:',
    'Critical': 'জরুরি',
    'High': 'উচ্চ',
    'Medium': 'মধ্যম',
    'Low': 'নিম্ন',
    'business hours': 'কর্মঘণ্টা',
    # meetings
    'Action items': 'কর্মপরিকল্পনা',
    'Add attendee': 'অংশগ্রহণকারী যোগ করুন',
    'Assign': 'নির্ধারণ করুন',
    'Attendees': 'অংশগ্রহণকারী',
    'Away': 'অনুপস্থিত',
    'Minutes and decisions': 'কার্যবিবরণী ও সিদ্ধান্ত',
    'New action': 'নতুন কর্মপরিকল্পনা',
    'No actions assigned.': 'কোনো কর্মপরিকল্পনা নির্ধারিত নেই।',
    'No actions in this view.': 'এই দৃশ্যে কোনো কর্মপরিকল্পনা নেই।',
    'No attendees recorded.': 'কোনো অংশগ্রহণকারী নথিভুক্ত নেই।',
    'Save minutes': 'কার্যবিবরণী সংরক্ষণ',
    'Secretary': 'সচিব',
    'Toggle': 'টগল করুন',
    'No meetings scheduled.': 'কোনো সভা নির্ধারিত নেই।',
    'Schedule a meeting': 'সভা নির্ধারণ করুন',
    'Schedule meeting': 'সভা নির্ধারণ',
    # documents
    'Allowed: pdf, png, jpg, csv, txt up to 5 MB':
        'অনুমোদিত: pdf, png, jpg, csv, txt সর্বোচ্চ ৫ MB',
    'Assign to': 'নির্ধারিত করুন',
    'No files match.': 'কোনো ফাইল মেলেনি।',
    'Register a new file': 'নতুন ফাইল নিবন্ধন করুন',
    'Register file': 'ফাইল নিবন্ধন',
    'Unassigned': 'অনির্ধারিত',
    'No files uploaded.': 'কোনো ফাইল আপলোড করা হয়নি।',
    'Add note': 'নোট যোগ করুন',
    'Close file': 'ফাইল বন্ধ করুন',
    'Confidential': 'গোপনীয়',
    'Due date': 'সময়সীমা',
    'Movement history': 'গতিবিধির ইতিহাস',
    'No movements recorded.': 'কোনো গতিবিধি নথিভুক্ত নেই।',
    'Open attachment': 'সংযুক্তি খুলুন',
    'Receive': 'গ্রহণ',
    'Received from': 'প্রাপ্তির উৎস',
    'Record a movement': 'গতিবিধি নথিভুক্ত করুন',
    'Registered by': 'নিবন্ধনকারী',
    'Return to creator': 'প্রেরকের কাছে ফেরত',
    'Save movement': 'গতিবিধি সংরক্ষণ',
    'To officer (forward)': 'কর্মকর্তার কাছে (ফরোয়ার্ড)',
    'No overdue files. Good.': 'কোনো মেয়াদোত্তীর্ণ ফাইল নেই। ভালো।',
    'late': 'দেরি',
    'No movements yet.': 'এখনও কোনো গতিবিধি নেই।',
    'No report access recorded.': 'কোনো প্রতিবেদন অ্যাক্সেস নথিভুক্ত নেই।',
    'Who viewed or exported which report, with parameters and IP address.':
        'কে কোন প্রতিবেদন দেখেছেন বা রপ্তানি করেছেন, প্যারামিটার ও আইপি ঠিকানাসহ।',
    # projects
    'Create project': 'প্রকল্প তৈরি করুন',
    'End': 'শেষ',
    'New project': 'নতুন প্রকল্প',
    'No projects match.': 'কোনো প্রকল্প মেলেনি।',
    'Project name': 'প্রকল্পের নাম',
    'Start': 'শুরু',
    'Approved allocation': 'অনুমোদিত বরাদ্দ',
    'Manager': 'ব্যবস্থাপক',
    'Milestone': 'মাইলফলক',
    'New milestone': 'নতুন মাইলফলক',
    'No inspections recorded.': 'কোনো পরিদর্শন নথিভুক্ত নেই।',
    'No milestones.': 'কোনো মাইলফলক নেই।',
    'Past the end date inspection(s)': 'শেষ তারিখ পার হওয়া পরিদর্শন',
    'Post progress update': 'অগ্রগতি হালনাগাদ পোস্ট করুন',
    'Progress (%)': 'অগ্রগতি (%)',
    'Recent inspections': 'সাম্প্রতিক পরিদর্শন',
    'Save update': 'হালনাগাদ সংরক্ষণ',
    'Scope': 'পরিধি',
    'Spent': 'ব্যয়িত',
    'Spent to date': 'এখন পর্যন্ত ব্যয়িত',
    'Findings': 'পর্যবেক্ষণ',
    'Record inspection': 'পরিদর্শন নথিভুক্ত করুন',
    'Save inspection': 'পরিদর্শন সংরক্ষণ',
    '% spent': '% ব্যয়িত',
    '% utilised': '% ব্যবহৃত',
    # facilities
    '35-day availability': '৩৫ দিনের প্রাপ্যতা',
    'No blackout dates.': 'কোনো বন্ধ তারিখ নেই।',
    'No tariffs published.': 'কোনো ট্যারিফ প্রকাশিত নেই।',
    'No units yet.': 'এখনও কোনো ইউনিট নেই।',
    'Rooms are locked per night and halls per date and slot. A database constraint prevents two active locks on the same inventory, so two applicants cannot book the same room. Expired holds are released by the scheduled command or the button on the facilities page.':
        'রুম রাতভিত্তিক এবং হল তারিখ ও স্লটভিত্তিক লক হয়। ডেটাবেস সীমাবদ্ধতা একই ইনভেন্টরিতে দুটি সক্রিয় লক আটকায়, তাই দুই আবেদনকারী একই রুম বুক করতে পারেন না। মেয়াদোত্তীর্ণ হোল্ড নির্ধারিত কমান্ড বা ভবন পৃষ্ঠার বোতামে ছেড়ে দেওয়া হয়।',
    '· unit(s) · Active Inactive': '· ইউনিট · সক্রিয় নিষ্ক্রিয়',
    'No units configured.': 'কোনো ইউনিট কনফিগার করা নেই।',
    'Release expired holds': 'মেয়াদোত্তীর্ণ হোল্ড ছেড়ে দিন',
    'unit(s)': 'ইউনিট',
    # health and security
    'System health': 'সিস্টেম স্বাস্থ্য',
    'Availability counters and recent platform events. Pages, uploads, payments and workflow decisions write here when something fails.':
        'প্রাপ্যতা কাউন্টার ও সাম্প্রতিক প্ল্যাটফর্ম ইভেন্ট। কোনো কিছু ব্যর্থ হলে পৃষ্ঠা, আপলোড, পেমেন্ট ও কর্মপ্রবাহ সিদ্ধান্ত এখানে লেখা হয়।',
    'Backup readiness': 'ব্যাকআপ প্রস্তুতি',
    'Backups and restore tests': 'ব্যাকআপ ও পুনরুদ্ধার পরীক্ষা',
    'Database': 'ডেটাবেস',
    'Errors': 'ত্রুটি',
    'Information events': 'তথ্য ইভেন্ট',
    'Investigate before the demo': 'ডেমোর আগে তদন্ত করুন',
    'Latest backup': 'সর্বশেষ ব্যাকআপ',
    'Message': 'বার্তা',
    'Needs review, not failing': 'পর্যালোচনা প্রয়োজন, ব্যর্থ নয়',
    'No backup has been created. Open': 'কোনো ব্যাকআপ তৈরি করা হয়নি। খুলুন',
    'No health events recorded.': 'কোনো স্বাস্থ্য ইভেন্ট নথিভুক্ত নেই।',
    'Path': 'পথ',
    'Recent events': 'সাম্প্রতিক ইভেন্ট',
    'Restore test not passed yet': 'পুনরুদ্ধার পরীক্ষা এখনও পাস হয়নি',
    'Restore test passed': 'পুনরুদ্ধার পরীক্ষা পাস',
    'Routine counters and notes': 'রুটিন কাউন্টার ও নোট',
    'Run or re-test': 'চালান বা পুনঃপরীক্ষা করুন',
    'Warnings': 'সতর্কতা',
    'Create backup now': 'এখন ব্যাকআপ তৈরি করুন',
    'Created': 'তৈরি হয়েছে',
    'No backups yet. Create one above.': 'এখনও কোনো ব্যাকআপ নেই। উপরে একটি তৈরি করুন।',
    'Not tested': 'পরীক্ষিত নয়',
    'Run restore test': 'পুনরুদ্ধার পরীক্ষা চালান',
    'SQLite online backup, stored under the project backups/ folder':
        'SQLite অনলাইন ব্যাকআপ, প্রকল্পের backups/ ফোল্ডারে সংরক্ষিত',
    'Size': 'আকার',
    'The restore test opens the backup file, runs': 'পুনরুদ্ধার পরীক্ষা ব্যাকআপ ফাইল খুলে চালায়',
    'What is enforced in code, what is a deployment commitment, and what is simulated in this offline demo. Labelled honestly.':
        'কোডে কী প্রয়োগ করা হয়, কী বাস্তবায়ন প্রতিশ্রুতি এবং এই অফলাইন ডেমোতে কী অনুকরণ করা হয়। সৎভাবে চিহ্নিত।',
    'and reads the table count. It does not overwrite the live database. A production deployment would restore into a rehearsal environment first, then promote.':
        'এবং টেবিল সংখ্যা পড়ে। এটি লাইভ ডেটাবেস ওভাররাইট করে না। প্রকৃত বাস্তবায়নে প্রথমে মহড়া পরিবেশে পুনরুদ্ধার করে পরে প্রমোট করা হবে।',
    'and create one before the demo.': 'এবং ডেমোর আগে একটি তৈরি করুন।',
    'Encryption': 'এনক্রিপশন',
    'HTTPS/TLS in production; demo runs on localhost':
        'প্রোডাকশনে HTTPS/TLS; ডেমো লোকালহোস্টে চলে',
    'Sensitive fields and backups are protected where the hosting architecture supports it. In this offline demo the transport is local HTTP, shown honestly as simulated.':
        'হোস্টিং আর্কিটেকচার যেখানে সমর্থন করে সেখানে সংবেদনশীল ফিল্ড ও ব্যাকআপ সুরক্ষিত থাকে। এই অফলাইন ডেমোতে পরিবহন স্থানীয় HTTP, যা সৎভাবে অনুকরণ হিসেবে দেখানো হয়েছে।',
    'Firewall and WAF': 'ফায়ারওয়াল ও WAF',
    'Configuration committed, not enforceable on a laptop':
        'কনফিগারেশন প্রতিশ্রুত, ল্যাপটপে প্রয়োগযোগ্য নয়',
    'Restrictive server firewall and web-layer rate limiting are part of the deployment baseline. The app enforces upload validation, CSRF and role checks in code.':
        'সীমাবদ্ধ সার্ভার ফায়ারওয়াল ও ওয়েব-স্তরের হার-সীমা বাস্তবায়নের ভিত্তির অংশ। অ্যাপ কোডে আপলোড যাচাই, CSRF ও ভূমিকা যাচাই প্রয়োগ করে।',
    'VPN / secure access': 'ভিপিএন / নিরাপদ অ্যাক্সেস',
    'Documented; demo has no VPN': 'নথিভুক্ত; ডেমোতে ভিপিএন নেই',
    'Management endpoints are separated by role and least privilege. VPN termination is a hosting control and is shown as a deployment commitment.':
        'ব্যবস্থাপনা এন্ডপয়েন্ট ভূমিকা ও ন্যূনতম অনুমতি দ্বারা পৃথক। ভিপিএন টার্মিনেশন একটি হোস্টিং নিয়ন্ত্রণ এবং বাস্তবায়ন প্রতিশ্রুতি হিসেবে দেখানো হয়েছে।',
    'Authentication': 'প্রমাণীকরণ',
    'Active': 'সক্রিয়',
    'Password hashing, session timeout, login rate limiting, email/OTP verification, role segregation and audit logs are implemented and testable.':
        'পাসওয়ার্ড হ্যাশিং, সেশন সময়সীমা, লগইন হার-সীমা, ইমেইল/ওটিপি যাচাই, ভূমিকা পৃথকীকরণ ও অডিট লগ প্রয়োগ করা হয়েছে এবং পরীক্ষাযোগ্য।',
    'Payment protection': 'পেমেন্ট সুরক্ষা',
    'Active (simulated gateway)': 'সক্রিয় (অনুকরণকৃত গেটওয়ে)',
    'Payments are confirmed only from HMAC-signed callbacks that the server verifies. Duplicate and mismatched callbacks are stored and rejected.':
        'সার্ভার যে HMAC-স্বাক্ষরিত কলব্যাক যাচাই করে সেটি থেকেই পেমেন্ট নিশ্চিত হয়। ডুপ্লিকেট ও অসামঞ্জস্যপূর্ণ কলব্যাক সংরক্ষণ করে প্রত্যাখ্যান করা হয়।',
    'Backup and recovery': 'ব্যাকআপ ও পুনরুদ্ধার',
    'SQLite is copied with the online backup API into a timestamped folder. The restore test opens the backup and runs an integrity check.':
        'SQLite অনলাইন ব্যাকআপ API দিয়ে টাইমস্ট্যাম্পযুক্ত ফোল্ডারে কপি করা হয়। পুনরুদ্ধার পরীক্ষা ব্যাকআপ খুলে অখণ্ডতা যাচাই চালায়।',
    'Monitoring and updates': 'মনিটরিং ও হালনাগাদ',
    'Active counters': 'সক্রিয় কাউন্টার',
    'Errors and availability counters are recorded. Patch and dependency management is a maintenance commitment under the 36-month support plan.':
        'ত্রুটি ও প্রাপ্যতা কাউন্টার নথিভুক্ত হয়। ৩৬ মাসের সহায়তা পরিকল্পনার অধীনে প্যাচ ও নির্ভরতা ব্যবস্থাপনা রক্ষণাবেক্ষণ প্রতিশ্রুতি।',
    'Simulated': 'অনুকরণকৃত',
    'Configuration': 'কনফিগারেশন',
    'Real': 'প্রকৃত',
    'Real logic': 'প্রকৃত লজিক',
    'Real counters': 'প্রকৃত কাউন্টার',
    'No settings have been changed yet.': 'এখনও কোনো সেটিংস পরিবর্তন করা হয়নি।',
    # error pages
    'Page not found (404)': 'পৃষ্ঠা পাওয়া যায়নি (৪০৪)',
    'The address may be wrong, or the record may have been removed. Try the public portal or your dashboard.':
        'ঠিকানাটি ভুল হতে পারে, অথবা রেকর্ডটি সরানো হয়েছে। পাবলিক পোর্টাল বা আপনার ড্যাশবোর্ড চেষ্টা করুন।',
    'Something went wrong (500)': 'কিছু একটা ভুল হয়েছে (৫০০)',
    'The server could not complete the request. The event is recorded on the system health page for the administrator.':
        'সার্ভার অনুরোধটি সম্পন্ন করতে পারেনি। ইভেন্টটি প্রশাসকের জন্য সিস্টেম স্বাস্থ্য পৃষ্ঠায় নথিভুক্ত হয়েছে।',
    # permits, tracking
    'Issued': 'ইস্যু হয়েছে',
    'Permit no.': 'পারমিট নং',
    'Permit not valid': 'পারমিট বৈধ নয়',
    'Permit valid': 'পারমিট বৈধ',
    'Stay': 'অবস্থান',
    'Back to the booking portal': 'বুকিং পোর্টালে ফিরে যান',
    'This permit exists but is not in a confirmed state (status:':
        'এই পারমিটটি আছে কিন্তু নিশ্চিত অবস্থায় নেই (অবস্থা:',
    '). No permit matches this QR code or token.':
        '). এই QR কোড বা টোকেনের সঙ্গে কোনো পারমিট মেলেনি।',
    'This permit was issued by the platform and the payment is verified by the server.':
        'এই পারমিট প্ল্যাটফর্ম ইস্যু করেছে এবং সার্ভার পেমেন্ট যাচাই করেছে।',
    'Verification is read-only and available to anyone holding the QR code. It shows no contact details. Checked at':
        'যাচাই কেবল পঠনযোগ্য এবং QR কোডধারীর জন্য উন্মুক্ত। এটি কোনো যোগাযোগের বিবরণ দেখায় না। যাচাই হয়েছে',
    'No booking found for': 'কোনো বুকিং পাওয়া যায়নি',
    '. Check the reference and try again.': '. রেফারেন্সটি যাচাই করে আবার চেষ্টা করুন।',
    'Payment is pending. Sign in and open your application to complete the simulated gateway payment before':
        'পেমেন্ট অপেক্ষমাণ। সাইন ইন করে আপনার আবেদন খুলে অনুকরণকৃত গেটওয়ে পেমেন্ট সম্পন্ন করুন',
    'The booking desk has requested clarification. Sign in to respond with the missing information.':
        'বুকিং ডেস্ক স্পষ্টীকরণ চেয়েছে। সাইন ইন করে অনুপস্থিত তথ্য দিন।',
    'Payment is verified and the permit is issued. Open the application to download the receipt and permit.':
        'পেমেন্ট যাচাই হয়েছে এবং পারমিট ইস্যু হয়েছে। রসিদ ও পারমিট ডাউনলোড করতে আবেদনটি খুলুন।',
    'Keep this reference for future tracking. You will be notified at each status change.':
        'ভবিষ্যতে ট্র্যাকিংয়ের জন্য এই রেফারেন্সটি রাখুন। প্রতিটি অবস্থা পরিবর্তনে আপনাকে জানানো হবে।',
    # payments
    'Amount to pay': 'প্রদেয় পরিমাণ',
    'Back to booking': 'বুকিংয়ে ফিরে যান',
    'Callback log for this transaction': 'এই লেনদেনের কলব্যাক লগ',
    'Demo version - sample data. This page is not a real payment gateway.':
        'ডেমো সংস্করণ - নমুনা ডেটা। এই পৃষ্ঠাটি প্রকৃত পেমেন্ট গেটওয়ে নয়।',
    'Demo:': 'ডেমো:',
    'Gateway status': 'গেটওয়ে অবস্থা',
    'Invalid': 'অবৈধ',
    'Merchant: Gazipur Zila Parishad (sample)': 'মার্চেন্ট: গাজীপুর জেলা পরিষদ (নমুনা)',
    'No callbacks yet. Choose an outcome above.': 'এখনও কোনো কলব্যাক নেই। উপরে একটি ফলাফল বেছে নিন।',
    'Payment protection:': 'পেমেন্ট সুরক্ষা:',
    'Payment verified.': 'পেমেন্ট যাচাইকৃত।',
    'Payment window: open': 'পেমেন্ট সময়সীমা: খোলা',
    'Gateway charge paid by user:': 'ব্যবহারকারীর প্রদত্ত গেটওয়ে চার্জ:',
    'Receipt at': 'রসিদ:',
    'A permit has been issued.': 'একটি পারমিট ইস্যু হয়েছে।',
    'Result': 'ফলাফল',
    'Sandbox': 'স্যান্ডবক্স',
    'Send forged callback': 'জাল কলব্যাক পাঠান',
    'Signature': 'স্বাক্ষর',
    'Simulate failure': 'ব্যর্থতা অনুকরণ করুন',
    'Simulated checkout in the style of a local aggregator. No real money moves.':
        'স্থানীয় অ্যাগ্রিগেটরের ধাঁচে অনুকরণকৃত চেকআউট। প্রকৃত অর্থ লেনদেন হয় না।',
    'Valid': 'বৈধ',
    'Yes No, absorbed': 'হ্যাঁ না, বহনকৃত',
    'this page imitates a hosted gateway. It produces HMAC-signed callbacks that the application verifies server-side. The buttons below let you exercise every outcome, including a duplicate and a forged callback.':
        'এই পৃষ্ঠাটি একটি হোস্টেড গেটওয়ে অনুকরণ করে। এটি HMAC-স্বাক্ষরিত কলব্যাক তৈরি করে যা অ্যাপ্লিকেশন সার্ভারে যাচাই করে। নিচের বোতামগুলো দিয়ে প্রতিটি ফলাফল পরীক্ষা করা যায়, ডুপ্লিকেট ও জাল কলব্যাকসহ।',
    'a payment is confirmed only when the server verifies the HMAC-SHA256 signature on the gateway callback. Callbacks with a wrong signature, wrong amount or duplicate transaction are stored and rejected.':
        'গেটওয়ে কলব্যাকের HMAC-SHA256 স্বাক্ষর সার্ভার যাচাই করলেই পেমেন্ট নিশ্চিত হয়। ভুল স্বাক্ষর, ভুল পরিমাণ বা ডুপ্লিকেট লেনদেনের কলব্যাক সংরক্ষণ করে প্রত্যাখ্যান করা হয়।',
    'Policy': 'নীতি',
    'Process refund': 'রিফান্ড প্রক্রিয়া করুন',
    'Refund': 'রিফান্ড',
    'Refund requests': 'রিফান্ড অনুরোধ',
    'of total': 'মোটের',
    'Release expired holds & payment windows':
        'মেয়াদোত্তীর্ণ হোল্ড ও পেমেন্ট সময়সীমা ছেড়ে দিন',
    'No transactions match the filters.': 'ফিল্টারে কোনো লেনদেন মেলেনি।',
    # reception
    'Arrivals in the next 3 days': 'আগামী ৩ দিনের আগমন',
    'Check-in opens one day before the booking date.':
        'চেক-ইন বুকিং তারিখের একদিন আগে খোলে।',
    'Check-out marks the booking completed and records the time.':
        'চেক-আউট বুকিং সম্পন্ন চিহ্নিত করে সময় নথিভুক্ত করে।',
    'Every verification and check-in/out is written to the audit log.':
        'প্রতিটি যাচাই এবং চেক-ইন/আউট অডিট লগে লেখা হয়।',
    'No arrivals for this facility.': 'এই ভবনের জন্য কোনো আগমন নেই।',
    'Only paid and confirmed bookings can be checked in.':
        'শুধু পরিশোধিত ও নিশ্চিত বুকিংয়ে চেক-ইন করা যায়।',
    'Open booking': 'বুকিং খুলুন',
    'Operator': 'অপারেটর',
    'QR scanning is simulated in this demo: point the phone camera at the permit, then type the reference shown under the QR code. The public verification page is available at':
        'এই ডেমোতে QR স্ক্যানিং অনুকরণ করা হয়: ফোনের ক্যামেরা পারমিটের দিকে ধরুন, তারপর QR কোডের নিচে দেখানো রেফারেন্স টাইপ করুন। পাবলিক যাচাই পৃষ্ঠা:',
    'Reception can only see bookings for the assigned facility.':
        'রিসেপশন শুধু নির্ধারিত ভবনের বুকিং দেখতে পারে।',
    'Reception rules': 'রিসেপশনের নিয়ম',
    'This booking is': 'এই বুকিংটি',
    'and cannot be checked in. Ask the applicant to complete payment.':
        'এবং চেক-ইন করা যাবে না। আবেদনকারীকে পেমেন্ট সম্পন্ন করতে বলুন।',
    'Valid booking': 'বৈধ বুকিং',
    'Verify': 'যাচাই করুন',
    'Verify a booking': 'বুকিং যাচাই করুন',
    'No bookings match the filters.': 'ফিল্টারে কোনো বুকিং মেলেনি।',
    'Create an account': 'অ্যাকাউন্ট তৈরি করুন',
    'Sign in to apply': 'আবেদন করতে সাইন ইন করুন',
    # HR
    'Emergency contact': 'জরুরি যোগাযোগ',
    'Joined': 'যোগদান',
    'Leave history': 'ছুটির ইতিহাস',
    'Linked account': 'সংযুক্ত অ্যাকাউন্ট',
    'No attendance recorded.': 'কোনো উপস্থিতি নথিভুক্ত নেই।',
    'No expiry': 'মেয়াদ নেই',
    'No leave applied.': 'কোনো ছুটি আবেদন করা হয়নি।',
    'No training records.': 'কোনো প্রশিক্ষণ রেকর্ড নেই।',
    'Out': 'বাইরে',
    'Recent attendance': 'সাম্প্রতিক উপস্থিতি',
    'Training and certification': 'প্রশিক্ষণ ও সনদ',
    'year(s)': 'বছর',
    'No employees match.': 'কোনো কর্মচারী মেলেনি।',
    'All leave applications with workflow status. Your leave applications and their approval status.':
        'কর্মপ্রবাহ অবস্থাসহ সব ছুটির আবেদন। আপনার ছুটির আবেদন ও তাদের অনুমোদনের অবস্থা।',
    'Leave register My applications': 'ছুটি নিবন্ধন আমার আবেদন',
    'No leave applications.': 'কোনো ছুটির আবেদন নেই।',
    'Your account is not linked to an employee record. Ask HR to link your account before applying for leave.':
        'আপনার অ্যাকাউন্ট কোনো কর্মচারী রেকর্ডের সঙ্গে সংযুক্ত নয়। ছুটির আবেদনের আগে এইচআর-কে অ্যাকাউন্ট সংযুক্ত করতে বলুন।',
    'Week of': 'সপ্তাহ',
    'to': 'থেকে',
    '. One shift per employee per day.': '. প্রতিদিন প্রতি কর্মচারীর জন্য একটি শিফট।',
    'No employees seeded yet.': 'এখনও কোনো কর্মচারী সিড করা হয়নি।',
    'No expiring training records.': 'মেয়াদ শেষ হওয়া কোনো প্রশিক্ষণ রেকর্ড নেই।',
    'No upcoming leave.': 'আসন্ন কোনো ছুটি নেই।',
    'No active employees.': 'কোনো সক্রিয় কর্মচারী নেই।',
    # MIS
    'No bookings match.': 'কোনো বুকিং মেলেনি।',
    'No data.': 'কোনো ডেটা নেই।',
    'No bookings.': 'কোনো বুকিং নেই।',
    'No facilities.': 'কোনো ভবন নেই।',
    'No projects.': 'কোনো প্রকল্প নেই।',
    'No departments configured.': 'কোনো বিভাগ কনফিগার করা নেই।',
    'No open actions.': 'কোনো খোলা কর্মপরিকল্পনা নেই।',
    '· due': '· সময়সীমা',
    'No export permission': 'রপ্তানির অনুমতি নেই',
    'Your role can export': 'আপনার ভূমিকা রপ্তানি করতে পারে',
    'Export permission not granted': 'রপ্তানির অনুমতি দেওয়া হয়নি',
    # notification outbox labels
    'Application approved': 'আবেদন অনুমোদিত',
    'Correction requested': 'সংশোধন অনুরোধ',
    'Task escalated': 'কাজ এস্কালেট',
    'Payment receipt': 'পেমেন্ট রসিদ',
    'Permit ready': 'পারমিট প্রস্তুত',
    'Refund update': 'রিফান্ড হালনাগাদ',
    'Application rejected': 'আবেদন প্রত্যাখ্যাত',
    'Task reminder': 'কাজের অনুস্মারক',
    'Application status update': 'আবেদনের অবস্থা হালনাগাদ',
    'New workflow task': 'নতুন কর্মপ্রবাহ কাজ',
    'Refund request awaiting action': 'রিফান্ড অনুরোধ পদক্ষেপের অপেক্ষায়',
    'A cancellation refund is awaiting finance processing.':
        'বাতিলের রিফান্ড অর্থ বিভাগের প্রক্রিয়ার অপেক্ষায়।',
}

for _late_key, _late_value in _BN_LATE.items():
    if _late_key not in BN and _late_key not in BN_EXTRA:
        BN[_late_key] = _late_value

_BN_LATE_2 = {
    'No audit entries match.': 'কোনো অডিট এন্ট্রি মেলেনি।',
    'No tickets.': 'কোনো টিকিট নেই।',
    'decision': 'সিদ্ধান্ত',
    'Release expired holds (': 'মেয়াদোত্তীর্ণ হোল্ড ছেড়ে দিন (',
    'Password must be at least 8 characters. For the demo,':
        'পাসওয়ার্ড কমপক্ষে ৮ অক্ষরের হতে হবে। ডেমোর জন্য,',
    'runs the step for stays of four nights or more, or for organizations. The payload keys come from the module that submits the request.':
        'চার রাত বা বেশি অবস্থান, অথবা প্রতিষ্ঠানের ক্ষেত্রে এই ধাপ চলে। পেলোডের কী-গুলো অনুরোধ জমা দেওয়া মডিউল থেকে আসে।',
    '. Gateway charge paid by user:': '. ব্যবহারকারীর প্রদত্ত গেটওয়ে চার্জ:',
}

for _late_key, _late_value in _BN_LATE_2.items():
    if _late_key not in BN and _late_key not in BN_EXTRA:
        BN[_late_key] = _late_value

_BN_LATE_3 = {
    'go to the CEO.': 'গেলে সিইও-এর কাছে যায়।',
    'Supervisor recommends, HR approves.':
        'সুপারভাইজার সুপারিশ করেন, এইচআর অনুমোদন করেন।',
    'HR approval': 'এইচআর অনুমোদন',
    'Review only': 'শুধু পর্যালোচনা',
    'Technical review only': 'শুধু কারিগরি পর্যালোচনা',
    'Delegated approval up to BDT': 'বিডিটি পর্যন্ত অর্পিত অনুমোদন',
    'Final approval above the Executive Officer delegation':
        'নির্বাহী কর্মকর্তার অর্পিত সীমার বেশি হলে চূড়ান্ত অনুমোদন',
    'Document decisions within the delegated limit':
        'অর্পিত সীমার মধ্যে নথির সিদ্ধান্ত',
    'Forwarding only': 'শুধু ফরোয়ার্ডিং',
    'All leave applications': 'সব ছুটির আবেদন',
    'Recommendation only': 'শুধু সুপারিশ',
    'Project approvals within the delegated limit':
        'অর্পিত সীমার মধ্যে প্রকল্প অনুমোদন',
    'Seed backup': 'সিড ব্যাকআপ',
    'integrity check:': 'অখণ্ডতা যাচাই:',
    'SELECT 1 returned a row': 'SELECT 1 একটি সারি ফিরিয়েছে',
    'returned a row': 'একটি সারি ফিরিয়েছে',
    'The facility is reserved for official duty during these dates.':
        'এই তারিখগুলোতে ভবনটি সরকারি দায়িত্বের জন্য সংরক্ষিত।',
    'Personal use of an official guesthouse is not permitted under the sample policy.':
        'নমুনা নীতির অধীনে সরকারি গেস্টহাউসের ব্যক্তিগত ব্যবহার অনুমোদিত নয়।',
    'The request exceeds the approved delegation for this period.':
        'অনুরোধটি এই সময়ের অনুমোদিত ক্ষমতার সীমা ছাড়িয়েছে।',
}

for _late_key, _late_value in _BN_LATE_3.items():
    if _late_key not in BN and _late_key not in BN_EXTRA:
        BN[_late_key] = _late_value

_BN_LATE_4 = {
    # staff designations and departments
    'Chief Executive Officer': 'প্রধান নির্বাহী কর্মকর্তা',
    'Executive Officer': 'নির্বাহী কর্মকর্তা',
    'Accounts Officer': 'হিসাব কর্মকর্তা',
    'Administrative Officer': 'প্রশাসনিক কর্মকর্তা',
    'Agriculture Officer': 'কৃষি কর্মকর্তা',
    'Assistant Engineer': 'সহকারী প্রকৌশলী',
    'Assistant Teacher': 'সহকারী শিক্ষক',
    'Data Entry Operator': 'ডেটা এন্ট্রি অপারেটর',
    'Education Officer': 'শিক্ষা কর্মকর্তা',
    'Facility Caretaker': 'ভবন তত্ত্বাবধায়ক',
    'HR Officer': 'এইচআর কর্মকর্তা',
    'Health Inspector': 'স্বাস্থ্য পরিদর্শক',
    'ICT Officer': 'আইসিটি কর্মকর্তা',
    'Medical Officer': 'মেডিকেল কর্মকর্তা',
    'Meeting Secretary': 'সভা সচিব',
    'Office Assistant': 'অফিস সহকারী',
    'Project Officer': 'প্রকল্প কর্মকর্তা',
    'Registry Officer': 'রেজিস্ট্রি কর্মকর্তা',
    'Sub-Assistant Engineer': 'উপ-সহকারী প্রকৌশলী',
    'Finance & Accounts': 'অর্থ ও হিসাব',
    'Health & Family Planning': 'স্বাস্থ্য ও পরিবার পরিকল্পনা',
    'Board Audit Cell': 'বোর্ড অডিট সেল',
    'System Administrator': 'সিস্টেম প্রশাসক',
    'ICT Division': 'আইসিটি বিভাগ',
    'Engineering unit': 'প্রকৌশল ইউনিট',
    'Civil Defence': 'সিভিল ডিফেন্স',
    'Red Crescent': 'রেড ক্রিসেন্ট',
    'Finance Division': 'অর্থ বিভাগ',
    'Parishad training unit': 'পরিষদ প্রশিক্ষণ ইউনিট',
    # training courses
    'Cyber hygiene': 'সাইবার স্বাস্থ্যবিধি',
    'Field inspection': 'মাঠ পরিদর্শন',
    'Fire safety and evacuation': 'অগ্নি নিরাপত্তা ও সরিয়ে নেওয়া',
    'Data protection': 'ডেটা সুরক্ষা',
    'First aid refresher': 'প্রাথমিক চিকিৎসা পুনঃপ্রশিক্ষণ',
    'Financial reporting': 'আর্থিক প্রতিবেদন',
    'Customer service': 'গ্রাহকসেবা',
    'Disaster response': 'দুর্যোগ মোকাবিলা',
    'Procurement rules': 'ক্রয় বিধিমালা',
    'Records management': 'নথি ব্যবস্থাপনা',
    'Dakbungalow operations': 'ডাকবাংলো পরিচালনা',
    'Team leadership': 'দলনেতৃত্ব',
    'On-demand backup': 'চাহিদামতো ব্যাকআপ',
}

for _late_key, _late_value in _BN_LATE_4.items():
    if _late_key not in BN and _late_key not in BN_EXTRA:
        BN[_late_key] = _late_value

_BN_LATE_5 = {
    # audit log descriptions
    'Administrator signed in': 'প্রশাসক সাইন ইন করেছেন',
    'Session ended': 'সেশন শেষ হয়েছে',
    'Expired holds released': 'মেয়াদোত্তীর্ণ হোল্ড ছাড়া হয়েছে',
    'Register entry': 'রেজিস্টার এন্ট্রি',
    'Register note added': 'রেজিস্টার নোট যোগ হয়েছে',
    'Workflow task': 'কর্মপ্রবাহ কাজ',
    'Task approved at the final step': 'চূড়ান্ত ধাপে কাজ অনুমোদিত',
    'Task approved at the Executive Officer step':
        'নির্বাহী কর্মকর্তার ধাপে কাজ অনুমোদিত',
    'Role matrix': 'ভূমিকা ম্যাট্রিক্স',
    'Permission matrix reviewed': 'অনুমতি ম্যাট্রিক্স পর্যালোচিত',
    'Notification template': 'নোটিফিকেশন টেমপ্লেট',
    'Template body reviewed': 'টেমপ্লেট বডি পর্যালোচিত',
    'Payment export': 'পেমেন্ট রপ্তানি',
    'Payment list exported': 'পেমেন্ট তালিকা রপ্তানি হয়েছে',
    'Booking export': 'বুকিং রপ্তানি',
    'Booking list exported': 'বুকিং তালিকা রপ্তানি হয়েছে',
    'On-demand backup created': 'চাহিদামতো ব্যাকআপ তৈরি হয়েছে',
    'Restore test passed with PRAGMA integrity':
        'PRAGMA অখণ্ডতা যাচাইসহ পুনরুদ্ধার পরীক্ষা পাস',
    'Read-only management session': 'কেবল পঠনযোগ্য ব্যবস্থাপনা সেশন',
    'Report export': 'প্রতিবেদন রপ্তানি',
    'Monthly report exported as CSV': 'মাসিক প্রতিবেদন CSV হিসেবে রপ্তানি হয়েছে',
    'Attendance sheet finalised': 'উপস্থিতি শীট চূড়ান্ত হয়েছে',
    'Minutes recorded': 'কার্যবিবরণী নথিভুক্ত',
    'Minutes and action items recorded': 'কার্যবিবরণী ও কর্মপরিকল্পনা নথিভুক্ত',
    'Meeting scheduled': 'সভা নির্ধারিত',
    'Meeting scheduled with agenda': 'আলোচ্যসূচিসহ সভা নির্ধারিত',
    'Field inspection': 'মাঠ পরিদর্শন',
    'Inspection recorded with a minor observation':
        'সামান্য পর্যবেক্ষণসহ পরিদর্শন নথিভুক্ত',
    'Progress update': 'অগ্রগতি হালনাগাদ',
    'File decision': 'ফাইলের সিদ্ধান্ত',
    'File closed after approval': 'অনুমোদনের পর ফাইল বন্ধ',
    'File received': 'ফাইল গৃহীত',
    'File received back with comments': 'মন্তব্যসহ ফাইল ফেরত পাওয়া গেছে',
    'File forwarded to the Executive Officer':
        'ফাইল নির্বাহী কর্মকর্তার কাছে ফরোয়ার্ড',
    'Leave approval': 'ছুটির অনুমোদন',
    'Leave approved': 'ছুটি অনুমোদিত',
    'Leave recommendation': 'ছুটির সুপারিশ',
    'Leave recommended to HR': 'এইচআর-এর কাছে ছুটির সুপারিশ',
    'Employee record': 'কর্মচারী রেকর্ড',
    'Employee record added': 'কর্মচারী রেকর্ড যোগ হয়েছে',
    'Booking marked completed at reception': 'রিসেপশনে বুকিং সম্পন্ন চিহ্নিত',
    'Guest checked in after reference verification':
        'রেফারেন্স যাচাইয়ের পর অতিথি চেক-ইন',
    'Callback rejected': 'কলব্যাক প্রত্যাখ্যাত',
    'Forged callback rejected and recorded': 'জাল কলব্যাক প্রত্যাখ্যাত ও নথিভুক্ত',
    'Refund processed': 'রিফান্ড প্রক্রিয়াকৃত',
    'Sample refund processed in the demo gateway':
        'ডেমো গেটওয়েতে নমুনা রিফান্ড প্রক্রিয়াকৃত',
    'Gateway payment': 'গেটওয়ে পেমেন্ট',
    'Payment verified from a signed callback': 'স্বাক্ষরিত কলব্যাক থেকে পেমেন্ট যাচাই',
    'Facility readiness confirmed': 'ভবন প্রস্তুতি নিশ্চিত',
    'Application review': 'আবেদন পর্যালোচনা',
    'Completeness check completed': 'সম্পূর্ণতা যাচাই সম্পন্ন',
    'Booking approval': 'বুকিং অনুমোদন',
    'Approved a booking within BDT': 'সীমার মধ্যে বুকিং অনুমোদিত',
    'Final approval recorded within delegation':
        'অর্পিত ক্ষমতার মধ্যে চূড়ান্ত অনুমোদন নথিভুক্ত',
    'management role': 'ব্যবস্থাপনা ভূমিকা',
    'Management role confirmed read-only': 'ব্যবস্থাপনা ভূমিকা কেবল পঠনযোগ্য নিশ্চিত',
    'Demo account created': 'ডেমো অ্যাকাউন্ট তৈরি',
    'Application name reviewed for the demo': 'ডেমোর জন্য আবেদনের নাম পর্যালোচিত',
    'Sample certificate reference': 'নমুনা সনদ রেফারেন্স',
}

for _late_key, _late_value in _BN_LATE_5.items():
    if _late_key not in BN and _late_key not in BN_EXTRA:
        BN[_late_key] = _late_value

# Input placeholders and accessibility labels, translated by translate_html().
_BN_LATE_6 = {
    'Actor, object, change or IP': 'ব্যবহারকারী, বস্তু, পরিবর্তন বা আইপি',
    'Blank = unlimited': 'খালি = সীমাহীন',
    'File no. or subject': 'নথি নম্বর বা বিষয়',
    'File no., subject or sender': 'নথি নম্বর, বিষয় বা প্রেরক',
    'Language': 'ভাষা',
    'Main navigation': 'প্রধান নেভিগেশন',
    'Name, code or location': 'নাম, কোড বা অবস্থান',
    'Name, employee no. or designation': 'নাম, কর্মচারী নম্বর বা পদবি',
    'Office order reference or note': 'অফিস আদেশের রেফারেন্স বা নোট',
    'Or type a name': 'অথবা একটি নাম লিখুন',
    'Pagination': 'পৃষ্ঠা বিভাজন',
    'Public navigation': 'সাধারণ নেভিগেশন',
    'Recorded in the audit trail and shared with the requester where appropriate.':
        'অডিট লগে রেকর্ড করা হয় এবং প্রযোজ্য ক্ষেত্রে আবেদনকারীর সঙ্গে শেয়ার করা হয়।',
    'Reference, applicant, purpose': 'রেফারেন্স, আবেদনকারী, উদ্দেশ্য',
    'System Administrator cannot hold approval power':
        'সিস্টেম প্রশাসক অনুমোদনের ক্ষমতা রাখতে পারেন না',
    'Toggle active': 'সক্রিয়/নিষ্ক্রিয় করুন',
    'Toggle navigation': 'নেভিগেশন খুলুন',
    'Transaction, booking reference or receipt': 'লেনদেন, বুকিং রেফারেন্স বা রসিদ',
    'Type the reference, e.g. GZP-DB-2026-000123': 'রেফারেন্স লিখুন, যেমন GZP-DB-2026-000123',
    'Username, name or email': 'ব্যবহারকারীর নাম, নাম বা ইমেইল',
    'e.g. GZP-DB-2026-000123': 'যেমন GZP-DB-2026-000123',
    'A six-digit one-time code was generated for': 'ছয় সংখ্যার এককালীন কোড তৈরি হয়েছে',
    'Check the reference and try again.': 'রেফারেন্স যাচাই করে আবার চেষ্টা করুন।',
    'Payment window:': 'পেমেন্ট সময়সীমা:',
    'payment windows': 'পেমেন্ট সময়সীমা',
    'This booking cannot be checked in.': 'এই বুকিং চেক-ইন করা যাবে না।',
    'Ask the applicant to complete payment.': 'আবেদনকারীকে পেমেন্ট সম্পন্ন করতে বলুন।',
    'No, absorbed': 'না, প্রতিষ্ঠান বহন করেছে',
    'open': 'খোলা',
    'No permit matches this QR code or token.': 'এই QR কোড বা টোকেনের সঙ্গে কোনো পারমিট মেলেনি।',
    'h': ' ঘণ্টা',
    'step': 'ধাপ',
    'awaiting your decision': 'আপনার সিদ্ধান্তের অপেক্ষায়',
    'Nights': 'রাত',
    'Suite': 'সুইট',
    'Citizen': 'সাধারণ নাগরিক',
    'Government': 'সরকারি',
    'Full day': 'সারাদিন',
    'Task detail': 'কাজের বিবরণ',
    'Dakbungalow booking': 'ডাকবাংলো বুকিং',
    'Verify your account': 'আপনার অ্যাকাউন্ট যাচাই করুন',
    'Dealing Assistant': 'ডিলিং অ্যাসিস্ট্যান্ট',
    'Booking Desk': 'বুকিং ডেস্ক',
    'Unit type': 'ইউনিটের ধরন',
    'Review and forward': 'পর্যালোচনা ও অগ্রসর',
    'Return for correction': 'সংশোধনের জন্য ফেরত',
}

for _late_key, _late_value in _BN_LATE_6.items():
    if _late_key not in BN and _late_key not in BN_EXTRA:
        BN[_late_key] = _late_value

# Asset register, booking-status tiles and the renamed approval card.
_BN_LATE_7 = {
    'Assets': 'সম্পদ',
    'All assets': 'সকল সম্পদ',
    'Assets & tariffs': 'সম্পদ ও শুল্ক',
    'Zila Parishad properties': 'জেলা পরিষদের সম্পত্তি',
    'Land': 'জমি',
    'Ponds': 'পুকুর',
    'Markets': 'বাজার',
    'Kheyaghat': 'খেয়াঘাট',
    'Auditorium': 'অডিটোরিয়াম',
    'Dak Bungalow': 'ডাকবাংলো',
    'Dak Bungalow details': 'ডাকবাংলোর বিবরণ',
    'Land, ponds, markets, kheyaghat, auditorium and the Dak Bungalow register in one place.':
        'জমি, পুকুর, বাজার, খেয়াঘাট, অডিটোরিয়াম ও ডাকবাংলো—সব এক জায়গায়।',
    'Room and hall inventory, tariffs and blackout dates.':
        'কক্ষ ও হলের তালিকা, শুল্ক এবং বন্ধের তারিখ।',
    'rest houses': 'বিশ্রামাগার',
    'units': 'ইউনিট',
    '12 plots · 4.6 acres': '১২টি দাগ · ৪.৬ একর',
    '8 ponds · 3.2 acres': '৮টি পুকুর · ৩.২ একর',
    '3 bazaars · 96 stalls': '৩টি বাজার · ৯৬টি দোকান',
    '2 ghats on the Turag': 'তুরাগ নদীর ২টি ঘাট',
    '1 hall · 400 seats': '১টি হল · ৪০০ আসন',
    'Approval status': 'অনুমোদনের অবস্থা',
    'Booking status': 'বুকিংয়ের অবস্থা',
    'Pending approval': 'অনুমোদনের অপেক্ষায়',
    'Units free today': 'আজ খালি ইউনিট',
    'Booked and available today': 'আজকের বুকিং ও খালি অবস্থা',
    'booked': 'বুকিং হয়েছে',
    'available': 'খালি',
    'Booked today': 'আজ বুকিং হয়েছে',
    'plots': 'দাগ',
    'ponds': 'পুকুর',
    'stalls': 'দোকান',
    'ghats': 'ঘাট',
    'halls': 'হল',
    'Waiting for the booking desk': 'বুকিং ডেস্কের অপেক্ষায়',
    'All Dakbungalow applications, filters, status and approval history.':
        'ডাকবাংলোর সব আবেদন, ফিল্টার, অবস্থা ও অনুমোদনের ইতিহাস।',
    'Every booking passes the same plain route: booking desk, engineering review, executive officer, then the CEO for amounts above the delegated limit. Each stage stays pending approval until that desk decides.':
        'প্রতিটি বুকিং একই সরল পথে যায়: বুকিং ডেস্ক, কারিগরি পর্যালোচনা, নির্বাহী কর্মকর্তা, '
        'তারপর অর্পিত সীমার বেশি টাকার ক্ষেত্রে সিইও। প্রতিটি ধাপ সেই ডেস্ক সিদ্ধান্ত না নেওয়া '
        'পর্যন্ত অনুমোদনের অপেক্ষায় থাকে।',
    'Everything an administrator needs in one place: users and roles, approval steps and limits, settings, assets and tariffs, the activity log, security and system status.':
        'প্রশাসকের প্রয়োজনীয় সবকিছু এক জায়গায়: ব্যবহারকারী ও ভূমিকা, অনুমোদন ধাপ ও সীমা, সেটিংস, '
        'সম্পদ ও শুল্ক, কার্যক্রম লগ, নিরাপত্তা ও সিস্টেম অবস্থা।',
}

for _late_key, _late_value in _BN_LATE_7.items():
    BN[_late_key] = _late_value

# Guided tour on the CEO and administrator dashboards.
_BN_TOUR = {
    'Skip': 'বাদ দিন',
    'Finish': 'শেষ করুন',
    'Skip the guide': 'নির্দেশিকা বাদ দিন',
    'How to use this dashboard': 'এই ড্যাশবোর্ড কীভাবে ব্যবহার করবেন',
    'Money collected from Dakbungalow bookings this month. The line below shows today\'s collection and the number of verified payments. Click the box to open the booking and revenue report.':
        'এই মাসে ডাকবাংলো বুকিং থেকে সংগৃহীত টাকা। নিচের লাইনে আজকের আদায় ও যাচাইকৃত পেমেন্টের সংখ্যা আছে। '
        'বুকিং ও রাজস্ব প্রতিবেদন খুলতে বক্সে ক্লিক করুন।',
    'Requests waiting for your signature, how many of them are past the response target, and how many are moving through the system. Click to open your task list.':
        'আপনার স্বাক্ষরের অপেক্ষায় থাকা আবেদন, এর মধ্যে কতগুলো সময়সীমা পেরিয়েছে এবং কতগুলো সিস্টেমে চলমান। '
        'কাজের তালিকা খুলতে ক্লিক করুন।',
    'How many employees came in, how many are absent or on leave, and how many are not marked yet. Click for the attendance register.':
        'কতজন কর্মী এসেছেন, কতজন অনুপস্থিত বা ছুটিতে এবং কতজনের উপস্থিতি এখনো চিহ্নিত হয়নি। '
        'উপস্থিতি খাতা দেখতে ক্লিক করুন।',
    'Unread internal notices and citizen requests. This number is what still needs your attention. Click to open the mail box.':
        'অপঠিত অভ্যন্তরীণ বিজ্ঞপ্তি ও নাগরিকের আবেদন। এই সংখ্যাটিই আপনার মনোযোগ প্রয়োজন। '
        'মেইল বক্স খুলতে ক্লিক করুন।',
    'Meetings scheduled for today with time, venue and chair. If nothing is scheduled, the next meetings are listed instead.':
        'আজকের নির্ধারিত সভা, সময়, স্থান ও সভাপতিসহ। আজ কিছু না থাকলে পরবর্তী সভাগুলো দেখানো হয়।',
    'Each row is one decision you can take now. Rows marked in red are past the response target. Open a row to read the application and record your decision.':
        'প্রতিটি সারি এখনই নেওয়ার মতো একটি সিদ্ধান্ত। লাল চিহ্নিত সারি সময়সীমা পেরিয়েছে। '
        'আবেদন পড়ে সিদ্ধান্ত নথিভুক্ত করতে সারিটি খুলুন।',
    'Unread notices and messages for the administration. The number is what still needs an answer.':
        'প্রশাসনের জন্য অপঠিত বিজ্ঞপ্তি ও বার্তা। এই সংখ্যাটিই উত্তর প্রয়োজন এমন বিষয়।',
    'Who came in, who is absent or on leave, and who is not marked yet. A warning appears until attendance is marked for the day.':
        'কে এসেছেন, কে অনুপস্থিত বা ছুটিতে এবং কে এখনো চিহ্নিত হননি। দিনের উপস্থিতি না ওঠানো পর্যন্ত '
        'একটি সতর্কতা দেখানো হয়।',
    'Every workflow approval currently open across all offices, with the overdue count. Use this to spot a desk where requests are piling up.':
        'সব দপ্তরে এখন চলমান প্রতিটি ওয়ার্কফ্লো অনুমোদন এবং মেয়াদোত্তীর্ণের সংখ্যা। '
        'কোথায় আবেদন জমছে তা বোঝার জন্য এটি ব্যবহার করুন।',
    'Dakbungalow money collected this month, today\'s collection and the number of payments.':
        'এই মাসে ডাকবাংলোর সংগৃহীত টাকা, আজকের আদায় ও পেমেন্টের সংখ্যা।',
    'Active users, roles, recent health notices and the last verified backup. Open the full page for database and backup detail.':
        'সক্রিয় ব্যবহারকারী, ভূমিকা, সাম্প্রতিক স্বাস্থ্য বিজ্ঞপ্তি ও সর্বশেষ যাচাইকৃত ব্যাকআপ। '
        'ডেটাবেজ ও ব্যাকআপের বিস্তারিত দেখতে সম্পূর্ণ পাতা খুলুন।',
    'The latest recorded actions: sign-ins, decisions, settings changes, payments and exports. Open the activity log to search the full trail.':
        'সর্বশেষ নথিভুক্ত কার্যক্রম: সাইন-ইন, সিদ্ধান্ত, সেটিংস পরিবর্তন, পেমেন্ট ও রপ্তানি। '
        'সম্পূর্ণ লগ দেখতে কার্যক্রম লগ খুলুন।',
}

for _late_key, _late_value in _BN_TOUR.items():
    if _late_key not in BN and _late_key not in BN_EXTRA:
        BN[_late_key] = _late_value

# Portal chooser, applicant IDs and the SSLCOMMERZ demo checkout.
_BN_LATE_8 = {
    'Official service': 'সরকারি সেবা',
    'Gazipur Zila Parishad': 'গাজীপুর জেলা পরিষদ',
    'Two portals, one platform. Citizens book services; officials review and approve.':
        'দুটি পোর্টাল, একটি প্ল্যাটফর্ম। নাগরিকরা সেবা বুক করেন; কর্মকর্তারা পর্যালোচনা ও অনুমোদন করেন।',
    'Citizen / user portal': 'নাগরিক / ব্যবহারকারী পোর্টাল',
    'Book a Dakbungalow, track your application, pay securely and download your permit.':
        'ডাকবাংলো বুক করুন, আবেদন ট্র্যাক করুন, নিরাপদে পেমেন্ট করুন এবং পারমিট ডাউনলোড করুন।',
    'Enter citizen portal': 'নাগরিক পোর্টালে যান',
    'Officials portal': 'কর্মকর্তা পোর্টাল',
    'Booking desk, technical review, approvals, finance, HR and system administration.':
        'বুকিং ডেস্ক, কারিগরি পর্যালোচনা, অনুমোদন, অর্থ, এইচআর ও সিস্টেম প্রশাসন।',
    'Official sign-in': 'কর্মকর্তা সাইন-ইন',
    'New here?': 'নতুন এসেছেন?',
    'Create a citizen account': 'নাগরিক অ্যাকাউন্ট খুলুন',
    'Citizen': 'নাগরিক',
    'Officials': 'কর্মকর্তা',
    'Citizen sign-in': 'নাগরিক সাইন-ইন',
    'Officials sign-in': 'কর্মকর্তা সাইন-ইন',
    'Citizens and applicants using Parishad services.':
        'পরিষদের সেবা নেওয়া নাগরিক ও আবেদনকারী।',
    'Booking desk, reviewers, approvers, finance, HR and administration.':
        'বুকিং ডেস্ক, পর্যালোচক, অনুমোদনকারী, অর্থ, এইচআর ও প্রশাসন।',
    'Citizen and staff access to the integrated platform.':
        'সমন্বিত প্ল্যাটফর্মে নাগরিক ও কর্মকর্তা প্রবেশ।',
    'Citizen applicants need a National ID (NID) when submitting a booking. Sample numbers only in this demo.':
        'আবেদন জমা দেওয়ার সময় নাগরিক আবেদনকারীর জাতীয় পরিচয়পত্র (এনআইডি) প্রয়োজন। '
        'এই ডেমোতে কেবল নমুনা নম্বর ব্যবহৃত হয়।',
    'Officials sign in with the account issued by the system administrator. Roles are enforced on the server.':
        'সিস্টেম প্রশাসকের দেওয়া অ্যাকাউন্ট দিয়ে কর্মকর্তারা সাইন-ইন করেন। ভূমিকা সার্ভারে প্রয়োগ হয়।',
    'No official account?': 'কর্মকর্তা অ্যাকাউন্ট নেই?',
    'Ask the system administrator.': 'সিস্টেম প্রশাসককে বলুন।',
    'National ID (NID) or use office ID': 'জাতীয় পরিচয়পত্র (এনআইডি) বা অফিস আইডি',
    'National ID (NID)': 'জাতীয় পরিচয়পত্র (এনআইডি)',
    'Government office / service ID': 'সরকারি অফিস / সার্ভিস আইডি',
    'e.g. GZP-OFF-1042': 'যেমন GZP-OFF-1042',
    'Government officials may verify with a NID or an office / service ID.':
        'সরকারি কর্মকর্তারা এনআইডি অথবা অফিস / সার্ভিস আইডি দিয়ে যাচাই করতে পারেন।',
    'A public citizen or organization applicant must give a National ID (NID). Only sample numbers are used in this demo.':
        'সাধারণ নাগরিক বা সংস্থার আবেদনকারীকে জাতীয় পরিচয়পত্র (এনআইডি) দিতে হবে। '
        'এই ডেমোতে কেবল নমুনা নম্বর ব্যবহৃত হয়।',
    "Government of the People's Republic of Bangladesh": 'গণপ্রজাতন্ত্রী বাংলাদেশ সরকার',
    'Office / service ID': 'অফিস / সার্ভিস আইডি',
    'Secure payment': 'নিরাপদ পেমেন্ট',
    'Secure': 'নিরাপদ',
    'You are paying': 'আপনি পরিশোধ করছেন',
    'Payable to': 'পরিশোধযোগ্য',
    'Booking charges': 'বুকিং চার্জ',
    'Total amount': 'মোট পরিমাণ',
    'Pay before': 'যার আগে পেমেন্ট',
    'Payment verified': 'পেমেন্ট যাচাই হয়েছে',
    'Back to application': 'আবেদনে ফিরুন',
    'Gateway test controls': 'গেটওয়ে পরীক্ষার নিয়ন্ত্রণ',
    'Every button below sends a real signed callback to the server. Duplicate and forged callbacks are recorded and rejected.':
        'নিচের প্রতিটি বোতাম সার্ভারে বাস্তব স্বাক্ষরযুক্ত কলব্যাক পাঠায়। '
        'ডুপ্লিকেট ও জাল কলব্যাক নথিভুক্ত হয়ে প্রত্যাখ্যাত হয়।',
    'Simulate failure': 'ব্যর্থতা অনুকরণ করুন',
    'Duplicate callback': 'ডুপ্লিকেট কলব্যাক',
    'Forged callback': 'জাল কলব্যাক',
    'Received': 'প্রাপ্তি',
    'Gateway': 'গেটওয়ে',
    'Welcome back': 'ফিরে আসায় স্বাগতম',
    'This transaction is complete': 'এই লেনদেন সম্পন্ন',
    'A permit has been issued. You can download it from the left panel.':
        'পারমিট ইস্যু হয়েছে। বাম প্যানেল থেকে ডাউনলোড করুন।',
    'Open permit': 'পারমিট খুলুন',
    'Card': 'কার্ড',
    'Bank': 'ব্যাংক',
    'Net banking': 'নেট ব্যাংকিং',
    'Pay with cards': 'কার্ড দিয়ে পেমেন্ট',
    'Visa · Mastercard · Amex': 'ভিসা · মাস্টারকার্ড · অ্যামেক্স',
    'Card number': 'কার্ড নম্বর',
    'Expiry (MM/YY)': 'মেয়াদ (মাস/বছর)',
    'Card holder name': 'কার্ডধারীর নাম',
    'Remember this card for next time': 'পরের বারের জন্য এই কার্ড মনে রাখুন',
    'Mobile wallet': 'মোবাইল ওয়ালেট',
    'bKash account number': 'বিকাশ অ্যাকাউন্ট নম্বর',
    'Verification code (demo)': 'যাচাই কোড (ডেমো)',
    'You will receive a confirmation SMS from bKash. Enter the code to approve the payment.':
        'বিকাশ থেকে নিশ্চিতকরণ এসএমএস পাবেন। পেমেন্ট অনুমোদনে কোডটি দিন।',
    'Nagad account number': 'নগদ অ্যাকাউন্ট নম্বর',
    'PIN (demo)': 'পিন (ডেমো)',
    'Confirm the payment in the Nagad app or with the PIN sent to your phone.':
        'নগদ অ্যাপে অথবা ফোনে পাঠানো পিন দিয়ে পেমেন্ট নিশ্চিত করুন।',
    'Rocket account number': 'রকেট অ্যাকাউন্ট নম্বর',
    'Pay from your bank account': 'আপনার ব্যাংক অ্যাকাউন্ট থেকে পরিশোধ করুন',
    'Direct debit': 'সরাসরি ডেবিট',
    'Select your bank': 'আপনার ব্যাংক নির্বাচন করুন',
    'Account number': 'অ্যাকাউন্ট নম্বর',
    "Bank payments are confirmed by the bank's signed callback in the demo.":
        'ডেমোতে ব্যাংকের স্বাক্ষরিত কলব্যাক দিয়ে ব্যাংক পেমেন্ট নিশ্চিত হয়।',
    'Internet banking': 'ইন্টারনেট ব্যাংকিং',
    'User ID': 'ব্যবহারকারী আইডি',
    'Password (demo)': 'পাসওয়ার্ড (ডেমো)',
    'By clicking Pay you agree to the SSLCOMMERZ terms of service. This is a sandbox: no real money moves.':
        'পে-তে ক্লিক করলে আপনি SSLCOMMERZ সেবার শর্তাবলীতে সম্মত হচ্ছেন। '
        'এটি স্যান্ডবক্স: বাস্তবে কোনো টাকা যায় না।',
    'Powered by': 'পরিচালিত',
    'Secured by': 'সুরক্ষিত',
    'Demo sandbox': 'ডেমো স্যান্ডবক্স',
}

for _late_key, _late_value in _BN_LATE_8.items():
    BN[_late_key] = _late_value

_BN_LATE_9 = {
    "A security deposit may apply and is shown before payment.":
        "ফেরতযোগ্য জামানত প্রযোজ্য হতে পারে এবং পেমেন্টের আগে তা দেখানো হয়।",
    "All demo accounts share the same password. Roles are enforced on the server, not only in the menu.":
        "সব ডেমো অ্যাকাউন্টের পাসওয়ার্ড একই। ভূমিকা সার্ভারে প্রয়োগ হয়, শুধু মেনুতে নয়।",
    "All four facilities": "সব চারটি সুবিধা",
    "All statuses": "সব অবস্থা",
    "Application and approval tracking": "আবেদন ও অনুমোদন ট্র্যাকিং",
    "Apply with documents": "কাগজপত্রসহ আবেদন করুন",
    "Approved Dakbungalows": "অনুমোদিত ডাকবাংলো",
    "Approved, payment window open": "অনুমোদিত, পেমেন্টের সময় খোলা",
    "Assigned to": "বরাদ্দ",
    "Availability for": "খালি আছে",
    "Available facilities": "খালি সুবিধাসমূহ",
    "Awaiting payment": "পেমেন্টের অপেক্ষায়",
    "Back to dashboard": "ড্যাশবোর্ডে ফিরে যান",
    "Before you apply": "আবেদনের আগে",
    "Body": "বার্তা",
    "Book a Gazipur Zila Parishad Dakbungalow":
        "গাজীপুর জেলা পরিষদ ডাকবাংলো বুক করুন",
    "Booking reference": "বুকিং রেফারেন্স",
    "Browse and choose": "দেখুন ও বেছে নিন",
    "Browse facilities": "সুবিধাসমূহ দেখুন",
    "Channel": "মাধ্যম",
    "Check availability": "খালি আছে কি না দেখুন",
    "Code": "কোড",
    "Complements D-Nothi/e-Nothi, e-GP and statutory approvals; does not replace or bypass them.":
        "ডি-নথি/ই-নথি, ই-জিপি ও আইনগত অনুমোদনের পরিপূরক; এগুলোর বিকল্প বা বাইপাস নয়।",
    "Configurable approval routes and an editable authority matrix":
        "কনফিগারযোগ্য অনুমোদন প্রবাহ ও সম্পাদনযোগ্য কর্তৃত্ব ম্যাট্রিক্স",
    "Confirmed / completed": "নিশ্চিত / সম্পন্ন",
    "Critical": "অত্যন্ত জরুরি",
    "Decisions recorded by your role": "আপনার ভূমিকার নেওয়া সিদ্ধান্ত",
    "Demo quick sign-in - password": "ডেমো দ্রুত সাইন-ইন - পাসওয়ার্ড",
    "Documents by category": "শ্রেণি অনুযায়ী কাগজপত্র",
    "Due time comes from the workflow step": "সময়সীমা ওয়ার্কফ্লো ধাপ থেকে আসে",
    "Editable templates. Placeholders like": "সম্পাদনযোগ্য টেমপ্লেট। প্লেসহোল্ডার যেমন",
    "Escalated": "ঊর্ধ্বতনে পাঠানো",
    "Escalated after the configured hours": "নির্ধারিত সময় পার হওয়ার পর ঊর্ধ্বতনে পাঠানো",
    "Every email and SMS the platform would send. Nothing leaves this machine; entries are labelled simulated.":
        "প্ল্যাটফর্মের পাঠানো প্রতিটি ইমেইল ও এসএমএস। কিছুই এই মেশিন থেকে বের হয় না; সবই সিমুলেটেড।",
    "Expired": "মেয়াদোত্তীর্ণ",
    "Follow every step from the booking desk to the authorised approver.":
        "বুকিং ডেস্ক থেকে অনুমোদিত অনুমোদনকারী পর্যন্ত প্রতিটি ধাপ অনুসরণ করুন।",
    "Four Parishad Dakbungalows with rooms, VIP suites and conference halls. Check live availability, apply online, track approval and pay securely.":
        "কক্ষ, ভিআইপি স্যুট ও কনফারেন্স হলসহ চারটি পরিষদ ডাকবাংলো। লাইভ খালি দেখুন, অনলাইনে আবেদন করুন, অনুমোদন ট্র্যাক করুন ও নিরাপদে পেমেন্ট করুন।",
    "Friday and Saturday nights use the holiday tariff.":
        "শুক্র ও শনিবার রাতে ছুটির দিনের ভাড়া প্রযোজ্য।",
    "From": "থেকে",
    "Government official: service ID or office order.":
        "সরকারি কর্মকর্তা: সার্ভিস আইডি বা অফিস আদেশ।",
    "High": "উচ্চ",
    "Holiday": "ছুটি",
    "If you believe this is wrong, ask an administrator to review your role in":
        "এটি ভুল মনে হলে একজন প্রশাসককে আপনার ভূমিকা পর্যালোচনা করতে বলুন",
    "In-app notifications for your account. Email and SMS copies are in the demo outbox.":
        "আপনার অ্যাকাউন্টের ইন-অ্যাপ নোটিফিকেশন। ইমেইল ও এসএমএস কপি ডেমো আউটবক্সে আছে।",
    "Integrated Digital Platform": "সমন্বিত ডিজিটাল প্ল্যাটফর্ম",
    "Integrated digital automation, management information and citizen-facing Dakbungalow e-booking with verified payment confirmation.":
        "যাচাইকৃত পেমেন্ট নিশ্চিতকরণসহ সমন্বিত ডিজিটাল অটোমেশন, ব্যবস্থাপনা তথ্য ও নাগরিক সেবার ডাকবাংলো ই-বুকিং।",
    "Low": "কম",
    "Mark all read": "সব পঠিত হিসেবে চিহ্নিত করুন",
    "Medium": "মাঝারি",
    "New citizen applicant?": "নতুন নাগরিক আবেদনকারী?",
    "No facilities are published yet.": "এখনো কোনো সুবিধা প্রকাশ করা হয়নি।",
    "No messages yet. Run a booking or workflow action.":
        "এখনো কোনো বার্তা নেই। একটি বুকিং বা ওয়ার্কফ্লো কার্যক্রম চালান।",
    "No notifications yet.": "এখনো কোনো নোটিফিকেশন নেই।",
    "No tasks in this view.": "এই ভিউতে কোনো কাজ নেই।",
    "No templates seeded.": "কোনো টেমপ্লেট সিড করা হয়নি।",
    "Normal": "স্বাভাবিক",
    "Not a statutory platform": "এটি আইনগত প্ল্যাটফর্ম নয়",
    "Notification templates in use": "ব্যবহৃত নোটিফিকেশন টেমপ্লেট",
    "Official booking service": "সরকারি বুকিং সেবা",
    "One platform for records, approvals, projects and Dakbungalow bookings.":
        "নথি, অনুমোদন, প্রকল্প ও ডাকবাংলো বুকিংয়ের এক প্ল্যাটফর্ম।",
    "Online": "অনলাইন",
    "Open tasks": "খোলা কাজ",
    "Organization: request letter on letterhead.":
        "সংস্থা: লেটারহেডে অনুরোধপত্র।",
    "Pay and get the permit": "পেমেন্ট করুন ও পারমিট নিন",
    "Pay through the gateway and download the permit with a verification QR code.":
        "গেটওয়ে দিয়ে পেমেন্ট করুন এবং যাচাইকরণ কিউআর কোডসহ পারমিট ডাউনলোড করুন।",
    "Pending, overdue and completed tasks for your role. Filters by date, priority and status.":
        "আপনার ভূমিকার অপেক্ষমাণ, সময়োত্তীর্ণ ও সম্পন্ন কাজ। তারিখ, অগ্রাধিকার ও অবস্থা অনুযায়ী ফিল্টার।",
    "Plan progress": "পরিকল্পনার অগ্রগতি",
    "Prepared by": "প্রস্তুত করেছে",
    "Public citizen: national ID and a contact number.":
        "সাধারণ নাগরিক: জাতীয় পরিচয়পত্র ও যোগাযোগ নম্বর।",
    "Public home": "পাবলিক হোম",
    "Register, choose dates and attach the documents for your category.":
        "নিবন্ধন করুন, তারিখ বেছে নিন এবং আপনার শ্রেণির কাগজপত্র সংযুক্ত করুন।",
    "Requester": "আবেদনকারী",
    "Returned": "ফেরত",
    "Role-based dashboards with least-privilege enforcement":
        "সর্বনিম্ন অধিকার নিশ্চিত করে ভূমিকা-ভিত্তিক ড্যাশবোর্ড",
    "SLA": "এসএলএ",
    "SMS": "এসএমএস",
    "Sample rules": "নমুনা নিয়ম",
    "Save template": "টেমপ্লেট সংরক্ষণ",
    "See facilities, rooms, photos, tariffs, blackout dates and live availability.":
        "সুবিধা, কক্ষ, ছবি, ভাড়া, বন্ধের তারিখ ও লাইভ খালি দেখুন।",
    "Seven modules sharing one identity, audit trail and workflow engine":
        "একটি পরিচয়, অডিট ট্রেইল ও ওয়ার্কফ্লো ইঞ্জিন ব্যবহারকারী সাতটি মডিউল",
    "Showing sample inventory of rooms and halls.":
        "কক্ষ ও হলের নমুনা তালিকা দেখানো হচ্ছে।",
    "Signed gateway callbacks, printable permits and QR verification":
        "স্বাক্ষরিত গেটওয়ে কলব্যাক, প্রিন্টযোগ্য পারমিট ও কিউআর যাচাই",
    "Signed payment confirmation": "স্বাক্ষরিত পেমেন্ট নিশ্চিতকরণ",
    "Tariff on request": "অনুরোধে ভাড়া",
    "Technical review for conference halls and VIP suites.":
        "কনফারেন্স হল ও ভিআইপি স্যুটের জন্য কারিগরি পর্যালোচনা।",
    "Template": "টেমপ্লেট",
    "Templates": "টেমপ্লেট",
    "This platform complements D-Nothi/e-Nothi, e-GP and statutory approvals; it does not replace or bypass them.":
        "এই প্ল্যাটফর্ম ডি-নথি/ই-নথি, ই-জিপি ও আইনগত অনুমোদনের পরিপূরক; এটি সেগুলোর বিকল্প বা বাইপাস নয়।",
    "This portal complements D-Nothi/e-Nothi, e-GP and statutory approvals. It does not replace or bypass them.":
        "এই পোর্টাল ডি-নথি/ই-নথি, ই-জিপি ও আইনগত অনুমোদনের পরিপূরক। এটি সেগুলোর বিকল্প বা বাইপাস নয়।",
    "This system complements D-Nothi/e-Nothi, e-GP and other mandatory government platforms. It does not replace or bypass statutory approval authority. Tariffs, rules and approval routes shown are sample values.":
        "এই সিস্টেম ডি-নথি/ই-নথি, ই-জিপি ও অন্যান্য বাধ্যতামূলক সরকারি প্ল্যাটফর্মের পরিপূরক। এটি আইনগত অনুমোদন কর্তৃত্বের বিকল্প বা বাইপাস নয়। এখানে দেখানো ভাড়া, নিয়ম ও অনুমোদন প্রবাহ নমুনা মান।",
    "To": "পর্যন্ত",
    "Track approval": "অনুমোদন ট্র্যাক করুন",
    "Under review / clarification": "পর্যালোচনাধীন / স্পষ্টীকরণ",
    "Unread": "অপঠিত",
    "Urgent": "জরুরি",
    "Username": "ব্যবহারকারীর নাম",
    "Users and roles": "ব্যবহারকারী ও ভূমিকা",
    "Your role does not include this permission. Access is enforced on the server, not only by hiding the menu link.":
        "আপনার ভূমিকায় এই অনুমতি নেই। মেনু লুকানোর বাইরেও সার্ভারে অ্যাক্সেস নিয়ন্ত্রিত হয়।",
    "a guest": "একজন অতিথি",
    "and": "এবং",
    "are filled when a message is generated.": "বার্তা তৈরি হওয়ার সময় পূরণ হয়।",
    "room(s) / hall(s)": "কক্ষ / হল",
    "Choose your portal": "আপনার পোর্টাল বেছে নিন",
    "Court Road, Gazipur Sadar, Gazipur": "কোর্ট রোড, গাজীপুর সদর, গাজীপুর",
    "Kaliakair Bus Stand Road, Gazipur": "কালিয়াকৈর বাস স্ট্যান্ড রোড, গাজীপুর",
    "Kapasia Bazar Road, Gazipur": "কাপাসিয়া বাজার রোড, গাজীপুর",
    "Sreepur Sadar, Gazipur": "শ্রীপুর সদর, গাজীপুর",
}

for _late_key, _late_value in _BN_LATE_9.items():
    BN[_late_key] = _late_value
