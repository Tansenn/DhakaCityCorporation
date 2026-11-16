"""Generate demonstration application forms in a Bangladesh government
form layout (masthead, letterhead, numbered fields, declaration, office use).

The output is a sample document only: no real authority is conferred and
the forms are not valid for statutory submission.
"""
from __future__ import annotations

import io
from xml.sax.saxutils import escape

from django.contrib.staticfiles import finders
from django.http import HttpResponse
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

NAVY = colors.HexColor('#0d2a4a')
GREEN = colors.HexColor('#147d54')
BD_GREEN = colors.HexColor('#006a4e')
BD_RED = colors.HexColor('#f42a41')
INK = colors.HexColor('#16362e')
MUTED = colors.HexColor('#5c7268')
LINE = colors.HexColor('#cfdad3')
FILL = colors.HexColor('#f7f8fc')


def _image(name, width, height):
    path = finders.find(name)
    if not path:
        return ''
    try:
        return Image(path, width=width, height=height)
    except Exception:
        return ''


def _styles():
    sheet = getSampleStyleSheet()
    sheet.add(ParagraphStyle('GzpFormTitle', parent=sheet['Title'],
                             fontName='Helvetica-Bold', fontSize=13, leading=16,
                             textColor=NAVY, alignment=TA_CENTER, spaceAfter=0))
    sheet.add(ParagraphStyle('GzpFormSmall', parent=sheet['Normal'], fontSize=7.5,
                             leading=10, textColor=MUTED))
    sheet.add(ParagraphStyle('GzpFormBody', parent=sheet['Normal'], fontSize=8.5,
                             leading=12, textColor=INK))
    sheet.add(ParagraphStyle('GzpFormLabel', parent=sheet['Normal'], fontSize=8,
                             leading=10, textColor=MUTED))
    sheet.add(ParagraphStyle('GzpFormValue', parent=sheet['Normal'], fontSize=9,
                             leading=11, textColor=INK))
    sheet.add(ParagraphStyle('GzpFormCell', parent=sheet['Normal'], fontSize=8,
                             leading=10, textColor=INK))
    return sheet


_SAMPLE_RULES = [
    ('applicant', 'Md. Rakib Hasan'),
    ('owner', 'Md. Rakib Hasan'),
    ('contractor', 'Md. Rakib Hasan'),
    ('patient', 'Md. Rakib Hasan'),
    ('employee', 'Md. Rakib Hasan'),
    ('licence holder', 'Md. Rakib Hasan'),
    ('deceased', 'Md. Abdul Malek'),
    ('child', 'Ayesha Siddika'),
    ('father', 'Md. Abdul Karim'),
    ('mother', 'Mst. Rahima Begum'),
    ('guardian', 'Md. Abdul Karim'),
    ('informant', 'Md. Rakib Hasan'),
    ('address', 'House 12, Court Road, Gazipur Sadar, Gazipur'),
    ('national id', '1990 1234 5678901'),
    ('mobile', '01711-000001'),
    ('ward', 'Ward 12'),
    ('district', 'Gazipur'),
    ('market', 'Gazipur Sadar Market'),
    ('shop', 'Block A, Shop 14'),
    ('trade name', 'Rahim Traders'),
    ('business address', 'Court Road, Gazipur Sadar'),
    ('nature of business', 'General store'),
    ('business capital', 'BDT 5,00,000'),
    ('number of employees', '4'),
    ('vehicle type', 'Three-wheeler (CNG)'),
    ('registration number', 'Dhaka Metro-Ha 11-2233'),
    ('engine number', 'ENG-2026-778812'),
    ('chassis number', 'CHS-2026-445510'),
    ('licence number', 'TRAD-2026-00145'),
    ('tax identification', '123456789012'),
    ('holding', 'Holding 42, Ward 12'),
    ('khatian', 'Khatian 1187'),
    ('plot', 'Plot 42, Block C'),
    ('land area', '3.5 decimal'),
    ('area in square', '900'),
    ('amount', 'BDT 50,000'),
    ('income', 'BDT 18,000'),
    ('cost', 'BDT 1,20,000'),
    ('wage', 'BDT 800'),
    ('deposit', 'BDT 25,000'),
    ('receipt', 'GZP-RCPT-2026-0192'),
    ('date of death', '10 October 2026'),
    ('date of birth', '2 February 2019'),
    ('place of death', 'Gazipur Sadar Hospital'),
    ('place of birth', 'Gazipur Sadar'),
    ('date of joining', '12 March 2021'),
    ('leave', '10 days'),
    ('designation', 'Administrative Officer'),
    ('employee id', 'GZP-EMP-0114'),
    ('department', 'Revenue Department'),
    ('reason', 'Demonstration application for the digital portal preview'),
    ('purpose', 'Community programme'),
    ('cause of distress', 'Loss of income after illness'),
    ('disease', 'Chronic kidney disease'),
    ('attachments', 'NID copy and supporting documents'),
    ('category', 'General'),
    ('duration', '30 days'),
    ('size', '12 ft x 6 ft'),
    ('length', '40'),
    ('width', '3'),
    ('road', 'Court Road, in front of Holding 42'),
    ('location', 'Court Road, Gazipur Sadar'),
    ('hospital', 'Gazipur Sadar Hospital'),
    ('post applied', 'Office Assistant'),
    ('educational', 'Bachelor of Arts'),
    ('work experience', '3 years in office support'),
    ('work category', 'Skilled maintenance worker'),
    ('days available', '6 days'),
    ('route', 'Gazipur - Dhaka'),
    ('company', 'Rahim Traders'),
    ('category applied', 'General category'),
    ('business description', 'Stationery and general goods'),
    ('assessment year', '2026-2027'),
    ('objection', 'The assessed area is higher than the measured area'),
    ('grounds', 'The assessed area is higher than the measured area'),
    ('renewal year', '2026'),
    ('deposit type', 'Security deposit'),
    ('heirs', '4'),
    ('plan type', 'Residential building plan'),
    ('premises type', 'Commercial premises'),
    ('leave balance', '18 days earned leave'),
    ('leave period', '20 to 30 November 2026'),
]


def sample_value(label):
    lowered = label.lower()
    for keyword, value in _SAMPLE_RULES:
        if keyword in lowered:
            return value
    return 'Sample entry'


def _text_badge(text, sheet, size=18 * mm):
    cell = Table([[Paragraph(
        f'<b><font size="9" color="#006a4e">{text}</font></b>',
        ParagraphStyle('badge', parent=sheet['Normal'], alignment=TA_CENTER))]],
        colWidths=[size], rowHeights=[size])
    cell.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, BD_GREEN),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e8f3ee')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return cell


def build_form_pdf(form, variant='blank', organization=None, values=None, application=None):
    """Return an HttpResponse holding the application form as a PDF."""
    org = organization or form.organization
    is_city = bool(org and org.is_city)
    org_name = org.name if org else 'Gazipur Zila Parishad'
    sheet = _styles()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=14 * mm, rightMargin=14 * mm,
        topMargin=12 * mm, bottomMargin=12 * mm,
        title=f'{form.title} - {org_name}', author=org_name,
    )
    width = doc.width
    sample = variant == 'sample'
    filled = variant == 'filled'
    story = []

    band = Table([[Paragraph(
        "<font size=\"9\">Government of the People's Republic of Bangladesh</font><br/>"
        f'<font size="7.5" color="#c8d6e8">Local Government Division - {escape(org_name)}</font>',
        ParagraphStyle('band', parent=sheet['Normal'], alignment=TA_CENTER,
                       textColor=colors.white, leading=11))]], colWidths=[width])
    band.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BD_GREEN if is_city else NAVY),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(band)
    story.append(HRFlowable(width='100%', thickness=1.6,
                            color=BD_RED if is_city else GREEN, spaceAfter=6))

    if is_city:
        head = Table([[
            _text_badge('DSCC', sheet),
            Paragraph(
                f'<b><font size="14" color="#006a4e">{escape(org_name.upper())}</font></b><br/>'
                f'<font size="8" color="#5c7268">{escape(org.address or "Corporation office")}'
                '<br/>Service counter - Application form</font>',
                ParagraphStyle('hq', parent=sheet['Normal'], alignment=TA_CENTER, leading=13)),
            _text_badge('BD', sheet),
        ]], colWidths=[22 * mm, width - 44 * mm, 22 * mm])
    else:
        head = Table([[
            _image('img/zp_gazipur_logo.png', 17 * mm, 17 * mm),
            Paragraph(
                '<b><font size="14" color="#0d2a4a">GAZIPUR ZILA PARISHAD</font></b><br/>'
                '<font size="8" color="#5c7268">Office of the Zila Parishad, Gazipur<br/>'
                'Service counter - Application form</font>',
                ParagraphStyle('hq', parent=sheet['Normal'], alignment=TA_CENTER, leading=13)),
            _image('img/bd_govt_logo.png', 15 * mm, 15 * mm),
        ]], colWidths=[22 * mm, width - 44 * mm, 22 * mm])
    head.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(head)
    story.append(Spacer(1, 5))

    if filled:
        copy_label = 'SUBMITTED COPY'
    elif sample:
        copy_label = 'SAMPLE COPY'
    else:
        copy_label = 'BLANK FORM'
    default_no = f'{org.code.upper()}/FRM/2026/{form.sl:03d}' if org else 'GZP/SVC/2026/000'
    strip = Table([[
        Paragraph(f'FORM NO. {form.form_no or default_no}', sheet['GzpFormLabel']),
        Paragraph(f'ISSUE DATE {timezone.localdate():%d %b %Y}', sheet['GzpFormLabel']),
        Paragraph(f'<b>{copy_label}</b>', sheet['GzpFormLabel']),
    ]], colWidths=[width * 0.42, width * 0.33, width * 0.25])
    strip.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), FILL),
        ('BOX', (0, 0), (-1, -1), 0.8, NAVY),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, LINE),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(strip)
    story.append(Spacer(1, 6))

    title = Table([[Paragraph(form.title, sheet['GzpFormTitle'])]], colWidths=[width])
    title.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#eaf5ee')),
        ('BOX', (0, 0), (-1, -1), 0.6, GREEN),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(title)
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        'Please write in block letters. Fields left blank will be treated as incomplete. '
        'Attach copies of the documents listed for this service.', sheet['GzpFormSmall']))
    story.append(Spacer(1, 4))

    rows = []
    section_rows = []
    values = values or {}
    section_style = ParagraphStyle('GzpFormSection', parent=sheet['GzpFormCell'],
                                   fontName='Helvetica-Bold', fontSize=8,
                                   textColor=colors.white)
    for spec in form.field_specs():
        if spec['kind'] == 'section':
            rows.append([Paragraph(escape(spec['label']).upper(), section_style), ''])
            section_rows.append(len(rows) - 1)
            continue
        label = spec['label']
        if filled:
            text = escape(str(values.get(label, ''))) or '&nbsp;'
        elif sample:
            text = escape(sample_value(label))
        else:
            text = '&nbsp;'
        if spec['options'] and not filled:
            text = escape(' / '.join(spec['options']))
        rows.append([
            Paragraph(f'<b>{spec["index"]}.</b> {escape(label)}', sheet['GzpFormCell']),
            Paragraph(text, sheet['GzpFormValue']),
        ])
    fields = Table(rows, colWidths=[72 * mm, width - 72 * mm])
    style = [
        ('BOX', (0, 0), (-1, -1), 0.7, LINE),
        ('INNERGRID', (0, 0), (-1, -1), 0.35, LINE),
        ('BACKGROUND', (0, 0), (0, -1), FILL),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]
    for row_index in section_rows:
        style.extend([
            ('SPAN', (0, row_index), (1, row_index)),
            ('BACKGROUND', (0, row_index), (-1, row_index), BD_GREEN),
            ('TOPPADDING', (0, row_index), (-1, row_index), 7),
        ])
    fields.setStyle(TableStyle(style))
    story.append(fields)
    story.append(Spacer(1, 6))

    declaration = Table([[Paragraph(
        '<b>Declaration.</b> I declare that the information given above is true and correct '
        f'to the best of my knowledge. This is a demonstration form generated by the '
        f'{escape(org_name)} digital service platform prototype and no statutory '
        'application is created by downloading it.', sheet['GzpFormBody'])]], colWidths=[width])
    declaration.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.6, LINE),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fbfcfd')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(declaration)
    if application is not None:
        story.append(Spacer(1, 8))
        story.append(Paragraph(
            f'<b>Reference {escape(application.reference)}</b> - verification record',
            sheet['GzpFormBody']))
        cells = ['Stage', 'Decision', 'Verified by', 'Date', 'Remarks']
        action_rows = [[Paragraph(f'<b>{cell}</b>', sheet['GzpFormSmall']) for cell in cells]]
        for action in application.actions.select_related('actor'):
            action_rows.append([
                Paragraph(escape(action.label), sheet['GzpFormCell']),
                Paragraph(escape(action.get_decision_display()), sheet['GzpFormCell']),
                Paragraph(escape(action.actor.display_name if action.actor else 'System'),
                          sheet['GzpFormCell']),
                Paragraph(f'{timezone.localtime(action.created_at):%d %b %Y}',
                          sheet['GzpFormCell']),
                Paragraph(escape(action.comments) or '-', sheet['GzpFormCell']),
            ])
        action_table = Table(
            action_rows,
            colWidths=[width * 0.22, width * 0.2, width * 0.18, width * 0.14, width * 0.26])
        action_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.7, LINE),
            ('INNERGRID', (0, 0), (-1, -1), 0.35, LINE),
            ('BACKGROUND', (0, 0), (-1, 0), FILL),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(action_table)
    story.append(Spacer(1, 10))

    signature_box = Table([
        [Paragraph('Signature of applicant', sheet['GzpFormLabel'])],
        [Paragraph('Date: ____________________', sheet['GzpFormValue'])],
    ], colWidths=[width * 0.5], rowHeights=[16 * mm, 9 * mm])
    signature_box.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, 0), 0.7, INK),
        ('VALIGN', (0, 1), (-1, 1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 1), (-1, 1), 4),
    ]))
    office_box = Table([
        [Paragraph('<b>For office use only</b>', sheet['GzpFormSmall'])],
        [Paragraph('Received by: ______________________', sheet['GzpFormSmall'])],
        [Paragraph('Date: ___________  Reference: ____________', sheet['GzpFormSmall'])],
        [Paragraph('Fee received: _____________________', sheet['GzpFormSmall'])],
    ], colWidths=[width * 0.42], rowHeights=[9 * mm, 9 * mm, 9 * mm, 9 * mm])
    office_box.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.6, LINE),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fbfcfd')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    bottom = Table([[signature_box, '', office_box]],
                   colWidths=[width * 0.5, width * 0.08, width * 0.42])
    bottom.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(bottom)
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width='100%', thickness=0.5, color=LINE, spaceAfter=3))
    story.append(Paragraph(
        f'Demonstration document - {escape(org_name)} digital service platform prototype - '
        'Not a valid government form. Do not submit real personal data.',
        ParagraphStyle('foot', parent=sheet['GzpFormSmall'], alignment=TA_CENTER)))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    response = HttpResponse(pdf, content_type='application/pdf')
    suffix = {'sample': '-sample', 'filled': '-submitted'}.get(variant, '')
    prefix = org.code if org else 'gzp'
    response['Content-Disposition'] = (
        f'attachment; filename="{prefix}-form-{form.sl:02d}{suffix}.pdf"')
    return response


def build_certificate_pdf(application):
    """Return an approval certificate for an approved online application."""
    org = application.organization
    sheet = _styles()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=14 * mm, bottomMargin=14 * mm,
        title=f'Certificate {application.reference}', author=org.name,
    )
    width = doc.width
    story = []
    band = Table([[Paragraph(
        "<font size=\"9\">Government of the People's Republic of Bangladesh</font><br/>"
        f'<font size="7.5" color="#c8d6e8">Local Government Division - {escape(org.name)}</font>',
        ParagraphStyle('band', parent=sheet['Normal'], alignment=TA_CENTER,
                       textColor=colors.white, leading=11))]], colWidths=[width])
    band.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BD_GREEN),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(band)
    story.append(HRFlowable(width='100%', thickness=2, color=BD_RED, spaceAfter=10))
    story.append(Paragraph(
        f'<b><font size="13" color="#006a4e">{escape(org.name.upper())}</font></b><br/>'
        f'<font size="8" color="#5c7268">{escape(org.address)}</font>',
        ParagraphStyle('cert-head', parent=sheet['Normal'], alignment=TA_CENTER, leading=14)))
    story.append(Spacer(1, 10))
    story.append(Table([[Paragraph('APPROVAL CERTIFICATE', sheet['GzpFormTitle'])]],
                       colWidths=[width], style=TableStyle([
                           ('BOX', (0, 0), (-1, -1), 0.8, BD_GREEN),
                           ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e6f2ec')),
                           ('TOPPADDING', (0, 0), (-1, -1), 8),
                           ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                       ])))
    story.append(Spacer(1, 12))
    lines = [
        ('Reference', application.reference),
        ('Service', application.service.name if application.service else application.form.title),
        ('Form', application.form.title),
        ('Applicant', application.applicant.display_name),
        ('Ward', f'Ward {application.ward.number}' if application.ward else 'Not specified'),
        ('Status', application.get_status_display()),
        ('Approved on', f'{timezone.localtime(application.decided_at or timezone.now()):%d %B %Y}'),
    ]
    rows = [[Paragraph(f'<b>{label}</b>', sheet['GzpFormCell']),
             Paragraph(escape(str(value)), sheet['GzpFormValue'])] for label, value in lines]
    info = Table(rows, colWidths=[45 * mm, width - 45 * mm])
    info.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.7, LINE),
        ('INNERGRID', (0, 0), (-1, -1), 0.35, LINE),
        ('BACKGROUND', (0, 0), (0, -1), FILL),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(info)
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        'This certificate confirms that the demonstration application above completed all '
        'configured verification stages of the digital platform prototype. It carries no '
        'statutory authority.', sheet['GzpFormBody']))
    story.append(Spacer(1, 26))
    sign = Table([[
        Paragraph(f'{escape(org.head_title)}<br/><b>{escape(org.head_name or "Authorised officer")}</b><br/>'
                  f'{escape(org.name)}', sheet['GzpFormCell']),
        Paragraph(f'Issued {timezone.localdate():%d %b %Y}', sheet['GzpFormSmall']),
    ]], colWidths=[width * 0.6, width * 0.4])
    sign.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (0, 0), 0.7, INK),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(sign)
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        'Demonstration document - not a valid government certificate.',
        ParagraphStyle('cert-foot', parent=sheet['GzpFormSmall'], alignment=TA_CENTER)))
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="certificate-{application.reference}.pdf"')
    return response
