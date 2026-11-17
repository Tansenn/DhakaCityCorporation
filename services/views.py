import os
import re
from uuid import uuid4

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from accounts.models import User
from audit.models import log
from notifications.models import Notification
from organizations.models import Organization, Ward

from .models import (
    ApplicationAttachment,
    ApplicationAction,
    Service,
    ServiceApplication,
    ServiceForm,
    ServicePayment,
    VerificationRoute,
)
from .pdfs import build_certificate_pdf, build_form_pdf


@require_GET
def form_download(request, pk, variant):
    form = get_object_or_404(ServiceForm.objects.select_related('service'), pk=pk)
    if variant == 'blank':
        return build_form_pdf(form, 'blank', organization=form.organization)
    if variant == 'sample' and form.has_sample:
        return build_form_pdf(form, 'sample', organization=form.organization)
    raise Http404('No such form variant.')


# --------------------------------------------------------------- city corporation
def _city():
    return get_object_or_404(Organization, code='dscc', is_active=True)


def _city_forms(org):
    return ServiceForm.objects.filter(organization=org).select_related('service')


def _new_reference(org):
    year = timezone.localdate().year
    prefix = f'{org.code.upper()}-{year}-'
    for _ in range(50):
        last = ServiceApplication.objects.filter(
            organization=org, reference__startswith=prefix).order_by('-id').first()
        sequence = 1
        if last:
            try:
                sequence = int(last.reference.rsplit('-', 1)[1]) + 1
            except ValueError:
                sequence = last.pk + 1
        reference = f'{prefix}{sequence:04d}'
        if not ServiceApplication.objects.filter(reference=reference).exists():
            return reference
    return f'{prefix}{timezone.now():%H%M%S}'


def _notify(user, application, subject):
    if user is None:
        return
    Notification.objects.create(
        user=user, subject=subject,
        body=f'Application {application.reference} - {application.form.title}. '
             f'Current status: {application.get_status_display()}.',
        url=f'/dscc/applications/{application.reference}/',
        template_code='city_application',
    )


APPLICATION_STATUS_FILTERS = {
    'pending': ('submitted', 'in_review'),
    'approved': ('approved',),
    'returned': ('returned',),
    'rejected': ('rejected',),
}

UPLOAD_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.webp'}
UPLOAD_LIMIT_BYTES = 5 * 1024 * 1024
UPLOAD_LIMIT_COUNT = 8

PAYMENT_OPTIONS = [
    {'code': 'bkash', 'label': 'bKash', 'logo': 'img/pay/bkash.png',
     'hint': 'Mobile account', 'field_label': 'bKash account number',
     'placeholder': '01XXXXXXXXX', 'pattern': '[0-9]{11}', 'maxlength': 11},
    {'code': 'nagad', 'label': 'Nagad', 'logo': 'img/pay/nagad.png',
     'hint': 'Mobile account', 'field_label': 'Nagad account number',
     'placeholder': '01XXXXXXXXX', 'pattern': '[0-9]{11}', 'maxlength': 11},
    {'code': 'bank', 'label': 'Bank transfer', 'logo': 'img/pay/bank.svg',
     'hint': 'Any scheduled bank', 'field_label': 'Bank account number',
     'placeholder': 'Account number', 'pattern': '[0-9 -]{6,20}', 'maxlength': 20},
    {'code': 'sslcommerz', 'label': 'SSLCommerz', 'logo': 'img/pay/sslcommerz.svg',
     'hint': 'Card or internet banking', 'field_label': 'Card number',
     'placeholder': 'Card number', 'pattern': '[0-9 ]{12,19}', 'maxlength': 19},
]


def _collect_uploads(request, fields):
    uploads, errors = [], []
    for row in fields:
        if row['type'] != 'attach':
            continue
        for upload in request.FILES.getlist(row['key']):
            uploads.append((row['label'], upload))
    for upload in request.FILES.getlist('extra_files'):
        uploads.append(('Supporting document', upload))
    if len(uploads) > UPLOAD_LIMIT_COUNT:
        return [], [f'Attach at most {UPLOAD_LIMIT_COUNT} files.']
    for _label, upload in uploads:
        ext = os.path.splitext(upload.name)[1].lower()
        if ext not in UPLOAD_EXTENSIONS:
            errors.append(f'{upload.name}: use a PDF, JPG, PNG or WEBP file.')
        elif upload.size > UPLOAD_LIMIT_BYTES:
            errors.append(f'{upload.name}: the file is larger than 5 MB.')
    return uploads, errors


def _status_counts(applications):
    counts = {
        key: applications.filter(status__in=statuses).count()
        for key, statuses in APPLICATION_STATUS_FILTERS.items()
    }
    counts['all'] = applications.count()
    return counts


def city_home(request):
    org = _city()
    request.session['gzp_org'] = org.code
    services = Service.objects.filter(organization=org, is_active=True)
    forms = _city_forms(org)
    return render(request, 'services/city_home.html', {
        'page_title': org.name,
        'org': org,
        'services': services,
        'form_count': forms.count(),
        'sample_forms': forms.filter(has_sample=True)[:4],
        'zones': org.zones.all(),
        'ward_count': org.wards.count(),
        'head_title': org.head_title,
        'head_name': org.head_name,
    })



@login_required
def city_dashboard(request):
    _city_permission(request)
    if request.user.is_citizen:
        return redirect('/dscc/applications/')
    org = _city()
    request.session['gzp_org'] = org.code
    base = ServiceApplication.objects.filter(organization=org).select_related(
        'form', 'service', 'ward', 'applicant')
    open_apps = base.filter(status__in=['submitted', 'in_review'])
    desk = open_apps
    if not request.user.can('city.manage') and request.user.role_id:
        orders = list(VerificationRoute.objects.filter(
            organization=org, role=request.user.role).values_list('order', flat=True))
        desk = open_apps.filter(current_order__in=orders or [-1])
    pending = [{'application': row, 'can_act': row.can_act(request.user)}
               for row in desk.order_by('created_at')[:8]]
    return render(request, 'services/city_dashboard.html', {
        'page_title': 'City dashboard',
        'org': org,
        'pending': pending,
        'at_desk_count': desk.count(),
        'open_count': open_apps.count(),
        'approved_count': base.filter(status='approved').count(),
        'returned_count': base.filter(status='returned').count(),
        'decided': base.exclude(status__in=['submitted', 'in_review'])
                   .order_by('-updated_at')[:6],
        'my_stages': VerificationRoute.objects.filter(
            organization=org, role=request.user.role).order_by('order'),
        'is_final_desk': bool(request.user.role and VerificationRoute.objects.filter(
            organization=org, role=request.user.role, is_final=True).exists()),
        'stage_count': VerificationRoute.objects.filter(organization=org).count(),
    })


def city_service(request, code):
    org = _city()
    request.session['gzp_org'] = org.code
    service = get_object_or_404(Service, organization=org, code=code, is_active=True)
    return render(request, 'services/city_service.html', {
        'page_title': service.name,
        'org': org,
        'service': service,
        'forms': service.forms.filter(organization=org),
        'requirement_list': service.requirement_list(),
    })


def city_forms(request):
    org = _city()
    request.session['gzp_org'] = org.code
    forms = _city_forms(org)
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    service_code = request.GET.get('service', '')
    if query:
        forms = forms.filter(Q(title__icontains=query) | Q(title_bn__icontains=query))
    if category:
        forms = forms.filter(category=category)
    if service_code:
        forms = forms.filter(service__code=service_code)
    return render(request, 'services/city_forms.html', {
        'page_title': 'City corporation forms',
        'org': org,
        'forms': forms,
        'q': query,
        'category': category,
        'service_code': service_code,
        'categories': ServiceForm.CATEGORIES,
        'services': Service.objects.filter(organization=org, is_active=True),
        'form_count': forms.count(),
    })


def city_offices(request):
    from django.db.models import Count

    from organizations.data import CITY_DEPARTMENTS, CITY_OFFICE_GROUPS

    org = _city()
    request.session['gzp_org'] = org.code
    known = {department.name: department for department in org.departments.all()}
    by_department = {}
    service_total = 0
    active_services = (Service.objects.filter(organization=org, is_active=True)
                       .annotate(form_total=Count('forms')))
    for service in active_services:
        service_total += 1
        by_department.setdefault(service.department, []).append({
            'name': service.name,
            'name_bn': service.name_bn,
            'code': service.code,
            'url': f'/dscc/services/{service.code}/',
            'forms': service.form_total,
        })
    groups = []
    for group in CITY_OFFICE_GROUPS:
        rows = []
        for number, row in enumerate(CITY_DEPARTMENTS, start=1):
            if row['group'] != group:
                continue
            department = known.get(row['name'])
            rows.append({
                **row,
                'number': f'{number:02d}',
                'code': department.code if department else '',
                'services': by_department.get(row['name'], []),
            })
        groups.append({'label': group, 'rows': rows})
    return render(request, 'services/city_offices.html', {
        'page_title': 'Offices and departments',
        'org': org,
        'groups': groups,
        'office_count': len(CITY_DEPARTMENTS),
        'service_total': service_total,
    })


def city_office_detail(request, code):
    from django.db.models import Count

    from hr.models import Department
    from organizations.data import CITY_DEPARTMENTS

    org = _city()
    request.session['gzp_org'] = org.code
    department = get_object_or_404(Department, organization=org, code=code)
    position = next(
        (index for index, row in enumerate(CITY_DEPARTMENTS, start=1)
         if row['name'] == department.name),
        None)
    if position is None:
        raise Http404
    row = CITY_DEPARTMENTS[position - 1]
    services = list(
        Service.objects.filter(organization=org, is_active=True,
                               department=department.name)
        .annotate(form_total=Count('forms')))
    forms = list(
        ServiceForm.objects.filter(organization=org,
                                   service__department=department.name)
        .select_related('service').order_by('sort', 'sl'))
    return render(request, 'services/city_office_detail.html', {
        'page_title': row['name'],
        'org': org,
        'office': {**row, 'number': f'{position:02d}', 'code': department.code},
        'group': row['group'],
        'services': services,
        'forms': forms,
        'form_total': len(forms),
        'head_user': department.head,
        'head_title': org.head_title,
    })


def city_acts(request):
    from organizations.data import CITY_LEGAL_CATEGORIES, CITY_LEGAL_DOCUMENTS

    org = _city()
    request.session['gzp_org'] = org.code
    active = request.GET.get('type', '')
    if active not in dict(CITY_LEGAL_CATEGORIES):
        active = ''
    documents = [doc for doc in CITY_LEGAL_DOCUMENTS if not active or doc['category'] == active]
    documents.sort(key=lambda doc: doc['year'], reverse=True)
    counts = {}
    for doc in CITY_LEGAL_DOCUMENTS:
        counts[doc['category']] = counts.get(doc['category'], 0) + 1
    tabs = [{'code': code, 'label': label, 'count': counts.get(code, 0)}
            for code, label in CITY_LEGAL_CATEGORIES]
    return render(request, 'services/city_acts.html', {
        'page_title': 'Acts, rules and gazettes',
        'org': org,
        'documents': documents,
        'tabs': tabs,
        'active': active,
        'total': len(CITY_LEGAL_DOCUMENTS),
    })


def city_form(request, pk):
    org = _city()
    request.session['gzp_org'] = org.code
    form = get_object_or_404(_city_forms(org), pk=pk)
    specs = form.field_specs()
    return render(request, 'services/city_form.html', {
        'page_title': form.title,
        'org': org,
        'form': form,
        'fields': specs,
        'field_count': len([row for row in specs if row['kind'] == 'field']),
        'my_applications': request.user.service_applications.filter(
            form=form).select_related('form')[:3]
        if request.user.is_authenticated else [],
    })


@login_required
def city_form_fill(request, pk):
    org = _city()
    form = get_object_or_404(_city_forms(org), pk=pk)
    specs = form.field_specs()
    fields = [row for row in specs if row['kind'] == 'field']
    wards = Ward.objects.filter(organization=org)
    values = {}
    uploads = []
    if request.method == 'POST':
        values = {row['label']: (request.POST.get(row['key']) or '').strip()
                  for row in fields}
        for row in fields:
            row['value'] = values[row['label']]
        uploads, upload_errors = _collect_uploads(request, fields)
        missing = [row['label'] for row in fields
                   if not row['value'] and not row['optional']]
        invalid = [row['label'] for row in fields
                   if row['options'] and row['value'] and row['value'] not in row['options']]
        if missing:
            messages.error(
                request,
                'Please complete: ' + ', '.join(missing[:3])
                + (' and %d more field(s).' % (len(missing) - 3) if len(missing) > 3 else '.'),
            )
        elif invalid:
            messages.error(request, 'Choose a listed option for: ' + ', '.join(invalid[:3]) + '.')
        elif upload_errors:
            messages.error(request, ' '.join(upload_errors[:3]))
        else:
            counts = {}
            for label, _upload in uploads:
                counts[label] = counts.get(label, 0) + 1
            for row in fields:
                if row['type'] == 'attach':
                    count = counts.get(row['label'], 0)
                    values[row['label']] = f'{count} file(s) attached' if count else ''
                    row['value'] = values[row['label']]
            ward = wards.filter(pk=request.POST.get('ward') or 0).first()
            application = ServiceApplication.objects.create(
                reference=_new_reference(org), organization=org, form=form,
                service=form.service, applicant=request.user, ward=ward, data=values,
            )
            for label, upload in uploads:
                original_name = re.sub(
                    r'[\r\n\t]+', ' ', os.path.basename(upload.name))[:255]
                ApplicationAttachment.objects.create(
                    application=application, field_label=label, file=upload,
                    original_name=original_name, size=upload.size,
                )
            ApplicationAction.objects.create(
                application=application, order=0, label='Application submitted',
                role_code=request.user.role.code if request.user.role else '',
                actor=request.user, decision='verify',
                comments='Submitted through the online form',
            )
            _notify(request.user, application, 'Application received')
            log(request.user, 'create', application,
                f'City application {application.reference} submitted', module='services')
            messages.success(
                request,
                f'Application {application.reference} submitted. '
                'It is now with the ward councillor for verification.')
            if uploads:
                messages.info(
                    request, f'{len(uploads)} document(s) attached to the file.')
            if settings.DEMO_MODE and application.fee_amount:
                messages.info(
                    request,
                    'Walkthrough mode: the fee can be paid now without approval, '
                    'or you can open the application to follow the normal flow.')
                return redirect(
                    f'/dscc/applications/{application.reference}/pay/'
                    '?demo=1&method=sslcommerz')
            return redirect('city_application', ref=application.reference)
    return render(request, 'services/city_fill.html', {
        'page_title': f'Fill: {form.title}',
        'org': org,
        'form': form,
        'fields': specs,
        'values': values,
        'wards': wards,
        'selected_ward': request.POST.get('ward', ''),
        'has_attach': any(row['type'] == 'attach' for row in fields),
        'requirements': form.service.requirement_list() if form.service else [],
    })


def _visible_or_403(request, application):
    if application.applicant_id == request.user.id:
        return
    if request.user.is_superuser or request.user.is_staff_portal_user:
        return
    raise PermissionDenied('This application belongs to another applicant.')


@login_required
def city_application(request, ref):
    application = get_object_or_404(
        ServiceApplication.objects.select_related('form', 'service', 'ward', 'organization'),
        reference=ref)
    _visible_or_403(request, application)
    return render(request, 'services/city_application.html', {
        'page_title': f'Application {application.reference}',
        'org': application.organization,
        'application': application,
        'stages': application.stages(),
        'actions': application.actions.select_related('actor'),
        'field_values': application.field_values(),
        'can_act': application.can_act(request.user),
    })


@login_required
def city_attachment(request, ref, pk):
    application = get_object_or_404(ServiceApplication, reference=ref)
    _visible_or_403(request, application)
    attachment = get_object_or_404(
        ApplicationAttachment, pk=pk, application=application)
    return FileResponse(
        attachment.file.open('rb'), as_attachment=True,
        filename=attachment.original_name or os.path.basename(attachment.file.name))


@login_required
def city_payment(request, ref):
    application = get_object_or_404(
        ServiceApplication.objects.select_related('form', 'service', 'organization'),
        reference=ref)
    if application.applicant_id != request.user.id:
        raise PermissionDenied('Only the applicant can pay this fee.')
    amount = application.fee_amount
    if not amount:
        messages.info(request, 'This service has no fee.')
        return redirect('city_application', ref=ref)
    if application.payment:
        messages.info(request, 'This application fee is already paid.')
        return redirect('city_application', ref=ref)
    # The live flow collects the fee only after final approval. The walkthrough
    # path (`?demo=1`) skips that gate so the payment portal can be shown
    # without running the whole verification chain first.
    direct = settings.DEMO_MODE and (
        request.GET.get('demo') == '1' or request.POST.get('demo') == '1')
    if application.status != 'approved' and not direct:
        messages.info(
            request,
            'Payment opens after final approval. '
            'The fee is collected once verification is complete.')
        return redirect('city_application', ref=ref)
    if request.method == 'POST':
        method = request.POST.get('method', '')
        option = next((row for row in PAYMENT_OPTIONS if row['code'] == method), None)
        if option is None:
            messages.error(request, 'Choose a payment method.')
        else:
            raw = (request.POST.get(f'payer_ref_{method}') or '').strip()
            digits = re.sub(r'\D', '', raw)
            if method in ('bkash', 'nagad'):
                valid = len(digits) == 11 and digits.startswith('01')
            elif method == 'bank':
                valid = 6 <= len(digits) <= 20
            else:
                valid = 12 <= len(digits) <= 19
            if not valid:
                messages.error(
                    request, f'Enter a valid {option["field_label"].lower()}.')
            else:
                transaction_id = f'PAY-{timezone.now():%y%m%d}-{uuid4().hex[:6].upper()}'
                payment = ServicePayment.objects.create(
                    application=application, method=method, amount=amount,
                    transaction_id=transaction_id, payer_ref=digits[-4:],
                )
                Notification.objects.create(
                    user=request.user, subject='Payment received',
                    body=f'Payment of BDT {amount} for application '
                         f'{application.reference} was received via {option["label"]}. '
                         f'Transaction {transaction_id}.',
                    url=f'/dscc/applications/{application.reference}/',
                    template_code='city_application',
                )
                log(request.user, 'payment', payment,
                    f'{application.reference}: BDT {amount} via {option["label"]}',
                    module='services')
                messages.success(
                    request,
                    f'Payment of BDT {amount} received via {option["label"]}. '
                    f'Transaction {transaction_id}.')
                if direct and application.status != 'approved':
                    messages.info(
                        request,
                        'Direct payment completed. The application is still '
                        'in the verification chain.')
                return redirect('city_application', ref=ref)
    codes = [row['code'] for row in PAYMENT_OPTIONS]
    requested = (request.POST.get('method') if request.method == 'POST'
                 else request.GET.get('method')) or ''
    selected_method = requested if requested in codes else codes[0]
    return render(request, 'services/city_payment.html', {
        'page_title': f'Pay fee: {application.reference}',
        'org': application.organization,
        'application': application,
        'amount': amount,
        'payment_options': PAYMENT_OPTIONS,
        'selected_method': selected_method,
        'direct': direct,
    })


@login_required
def city_applications(request):
    org = _city()
    mine = request.user.service_applications.filter(
        organization=org).select_related('form', 'service').order_by('-created_at')
    active = request.GET.get('status', 'all')
    if active in APPLICATION_STATUS_FILTERS:
        applications = mine.filter(status__in=APPLICATION_STATUS_FILTERS[active])
    else:
        active = 'all'
        applications = mine
    return render(request, 'services/city_applications.html', {
        'page_title': 'My city applications',
        'org': org,
        'applications': applications,
        'active_status': active,
        'status_counts': _status_counts(mine),
    })


@login_required
def city_application_pdf(request, ref):
    application = get_object_or_404(
        ServiceApplication.objects.select_related('form', 'organization'), reference=ref)
    _visible_or_403(request, application)
    return build_form_pdf(
        application.form, 'filled', organization=application.organization,
        values=application.data, application=application)


@login_required
def city_certificate(request, ref):
    application = get_object_or_404(
        ServiceApplication.objects.select_related('form', 'organization'), reference=ref)
    _visible_or_403(request, application)
    if application.status != 'approved':
        raise Http404('The certificate is issued after final approval.')
    return build_certificate_pdf(application)


def _city_permission(request):
    if request.user.is_superuser or request.user.can('city.view'):
        return
    raise PermissionDenied('You do not have access to city service applications.')


@login_required
def city_queue(request):
    _city_permission(request)
    org = _city()
    base = ServiceApplication.objects.filter(organization=org).select_related(
        'form', 'service', 'ward', 'applicant')
    open_apps = base.filter(status__in=['submitted', 'in_review'])
    if not request.user.can('city.manage') and request.user.role_id:
        orders = list(VerificationRoute.objects.filter(
            organization=org, role=request.user.role).values_list('order', flat=True))
        open_apps = open_apps.filter(current_order__in=orders or [0])
    pending = [{'application': row, 'can_act': row.can_act(request.user)}
               for row in open_apps.order_by('created_at')]
    decided = [row for row in base.exclude(status__in=['submitted', 'in_review'])
               .order_by('-updated_at')[:10]]
    return render(request, 'services/city_queue.html', {
        'page_title': 'City verification queue',
        'org': org,
        'pending': pending,
        'decided': decided,
        'stages': VerificationRoute.objects.filter(organization=org).order_by('order'),
    })


@login_required
@require_POST
def city_action(request, ref):
    application = get_object_or_404(
        ServiceApplication.objects.select_related('form', 'organization'), reference=ref)
    if not application.can_act(request.user):
        raise PermissionDenied('This application is not waiting for your role.')
    decision = request.POST.get('decision')
    if decision not in ('verify', 'approve', 'reject', 'return'):
        messages.error(request, 'Choose a valid action.')
        return redirect('city_queue')
    stage = application.current_stage
    order = stage.order if stage else application.current_order
    label = stage.label if stage else 'Verification'
    comments = (request.POST.get('comments') or '').strip()
    ApplicationAction.objects.create(
        application=application, order=order, label=label,
        role_code=request.user.role.code if request.user.role else '',
        actor=request.user, decision=decision, comments=comments,
    )
    following = None
    if decision == 'reject':
        application.status = 'rejected'
        application.decided_at = timezone.now()
    elif decision == 'return':
        application.status = 'returned'
    else:
        following = application.next_stage()
        if following:
            application.current_order = following.order
            application.status = 'in_review'
        else:
            application.status = 'approved'
            application.decided_at = timezone.now()
    application.note = comments[:255]
    application.save()
    _notify(application.applicant, application,
            f'Application {application.reference}: {application.get_status_display()}')
    if following:
        desk = User.objects.filter(
            organization=application.organization, role=following.role, is_active=True,
        ).exclude(pk=request.user.pk)
        for recipient in desk:
            _notify(recipient, application,
                    f'Application {application.reference} is waiting at {following.label}')
    log(request.user, 'decision', application,
        f'{application.reference}: {application.get_status_display()}', module='services')
    messages.success(
        request,
        f'{application.reference} moved to: {application.get_status_display()}.')
    return redirect(request.POST.get('next') or 'city_queue')


@login_required
@require_POST
def city_resubmit(request, ref):
    application = get_object_or_404(ServiceApplication, reference=ref)
    if application.applicant_id != request.user.id or not application.can_resubmit:
        raise PermissionDenied('This application cannot be resubmitted.')
    stages = application.stages()
    application.status = 'submitted'
    application.current_order = stages[0].order if stages else 1
    application.decided_at = None
    application.save()
    ApplicationAction.objects.create(
        application=application, order=0, label='Resubmitted',
        role_code=request.user.role.code if request.user.role else '',
        actor=request.user, decision='resubmit',
        comments=(request.POST.get('comments') or '').strip(),
    )
    _notify(application.applicant, application, 'Application resubmitted')
    messages.success(request, f'{application.reference} resubmitted for verification.')
    return redirect('city_application', ref=application.reference)


@login_required
def city_setup(request):
    if not (request.user.is_superuser or request.user.can('city.manage')):
        raise PermissionDenied('Only an administrator can change the city setup.')
    organizations = list(Organization.objects.filter(is_active=True))
    org = _city()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'org':
            org.head_title = (request.POST.get('head_title') or '').strip() or org.head_title
            org.head_name = (request.POST.get('head_name') or '').strip()
            org.address = (request.POST.get('address') or '').strip()
            org.phone = (request.POST.get('phone') or '').strip()
            org.save()
            messages.success(request, 'Organisation details saved.')
        elif action == 'zone':
            number = int(request.POST.get('number') or 0)
            if number:
                org.zones.update_or_create(number=number, defaults={
                    'name': (request.POST.get('name') or f'Zone {number}').strip(),
                    'name_bn': (request.POST.get('name_bn') or '').strip(),
                })
                messages.success(request, f'Zone {number} saved.')
        elif action == 'ward':
            number = int(request.POST.get('number') or 0)
            zone = org.zones.filter(pk=request.POST.get('zone') or 0).first()
            if number and zone:
                org.wards.update_or_create(number=number, defaults={
                    'zone': zone,
                    'name': (request.POST.get('name') or f'Ward {number}').strip(),
                    'name_bn': (request.POST.get('name_bn') or '').strip(),
                    'councillor_name': (request.POST.get('councillor_name') or '').strip(),
                })
                messages.success(request, f'Ward {number} saved.')
            else:
                messages.error(request, 'Choose a zone and a ward number.')
        return redirect('city_setup')
    zones = org.zones.prefetch_related('wards').all()
    next_ward = (org.wards.order_by('-number').values_list('number', flat=True).first() or 0) + 1
    next_zone = (org.zones.order_by('-number').values_list('number', flat=True).first() or 0) + 1
    return render(request, 'services/city_setup.html', {
        'page_title': 'City corporation setup',
        'org': org,
        'organizations': organizations,
        'zones': zones,
        'next_ward': next_ward,
        'next_zone': next_zone,
        'ward_total': org.wards.count(),
    })
