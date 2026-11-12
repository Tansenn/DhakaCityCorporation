"""PDF helpers built on reportlab, plus QR generation for permits."""
from __future__ import annotations

import io
import random
from datetime import datetime

from django.conf import settings
from django.contrib.staticfiles import finders
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

NAVY = colors.HexColor('#1A1B41')
LIME = colors.HexColor('#B9FF29')
GREEN = colors.HexColor('#147d54')
INK = colors.HexColor('#22243F')
MUTED = colors.HexColor('#6B7280')
LINE = colors.HexColor('#D8DBE6')


def _static_image(name, width, height):
    path = finders.find(name)
    if not path:
        return None
    try:
        return Image(path, width=width, height=height)
    except Exception:
        return None


def qr_png_bytes(data):
    import qrcode

    qr = qrcode.QRCode(version=None, box_size=8, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='#1A1B41', back_color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()


def _styles():
    sheet = getSampleStyleSheet()
    sheet.add(ParagraphStyle(
        'GzpTitle', parent=sheet['Title'], fontName='Helvetica-Bold',
        fontSize=17, textColor=NAVY, alignment=TA_CENTER, spaceAfter=2,
    ))
    sheet.add(ParagraphStyle(
        'GzpSub', parent=sheet['Normal'], fontSize=9, textColor=MUTED,
        alignment=TA_CENTER, spaceAfter=10,
    ))
    sheet.add(ParagraphStyle(
        'GzpH', parent=sheet['Normal'], fontName='Helvetica-Bold',
        fontSize=11, textColor=NAVY, spaceBefore=10, spaceAfter=4,
    ))
    sheet.add(ParagraphStyle(
        'GzpBody', parent=sheet['Normal'], fontSize=9, textColor=INK, leading=13,
    ))
    sheet.add(ParagraphStyle(
        'GzpSmall', parent=sheet['Normal'], fontSize=7.5, textColor=MUTED, leading=10,
    ))
    return sheet


def permit_approver(booking):
    """Officer whose approval signs the permit; falls back to the CEO then EO."""
    instance = getattr(booking, 'workflow_instance', None)
    if instance:
        record = instance.records.filter(decision='approve').select_related(
            'actor', 'actor__designation', 'actor__role').order_by(
            '-created_at').first()
        if record and record.actor:
            return record.actor
    from accounts.models import User

    base = User.objects.select_related('designation', 'role').filter(is_active=True)
    return base.filter(role__code='ceo').first() or base.filter(role__code='eo').first()


class SignatureBlock(Flowable):
    """Handwritten-style signature above a rule, with printed name and role."""

    def __init__(self, name, designation, width=86 * mm, height=30 * mm):
        super().__init__()
        self.name = name
        self.designation = designation
        self.width = width
        self.height = height

    def draw(self):
        canvas = self.canv
        rnd = random.Random(sum(ord(ch) for ch in self.name) or 11)
        baseline = 9 * mm

        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor('#1a2a6b'))
        canvas.setLineWidth(1.15)
        canvas.setLineJoin(1)
        canvas.setLineCap(1)
        path = canvas.beginPath()
        x = 4 * mm
        y = baseline + 6 * mm
        path.moveTo(x, y)
        for _ in range(6):
            x1, y1 = x + rnd.uniform(3, 7) * mm, y + rnd.uniform(-6, 7) * mm
            x2, y2 = x + rnd.uniform(8, 12) * mm, y + rnd.uniform(-7, 6) * mm
            x += rnd.uniform(12, 16) * mm
            y = baseline + rnd.uniform(3, 11) * mm
            path.curveTo(x1, y1, x2, y2, x, y)
        path.moveTo(4 * mm, baseline + 4 * mm)
        path.curveTo(self.width * 0.30, baseline + 16 * mm,
                     self.width * 0.62, baseline - 1 * mm,
                     self.width - 5 * mm, baseline + 12 * mm)
        canvas.drawPath(path)

        canvas.setStrokeColor(INK)
        canvas.setLineWidth(0.7)
        canvas.line(0, baseline, self.width, baseline)
        canvas.restoreState()

        canvas.setFillColor(INK)
        canvas.setFont('Helvetica-Bold', 8.5)
        canvas.drawCentredString(self.width / 2, 5.2 * mm, self.name[:40])
        canvas.setFillColor(MUTED)
        canvas.setFont('Helvetica', 7.2)
        canvas.drawCentredString(self.width / 2, 1.6 * mm, self.designation[:56])
        canvas.setFont('Helvetica-Oblique', 6)
        canvas.setFillColor(MUTED)
        canvas.drawCentredString(self.width / 2, -2.6 * mm, 'Authorised signature')


def _permit_header():
    """Three-column letterhead: Parishad emblem, state text, government seal."""
    zp = _static_image('img/zp_gazipur_logo.png', 22 * mm, 22 * mm)
    gov = _static_image('img/bd_govt_seal.png', 20 * mm, 20 * mm)
    title = Paragraph(
        '<font size="7.5" color="#147d54">Government of the People\'s Republic of Bangladesh</font><br/>'
        '<font size="14" color="#1A1B41"><b>Gazipur Zila Parishad</b></font><br/>'
        '<font size="8" color="#6B7280">Office of the Zila Parishad, Gazipur</font>',
        ParagraphStyle('head', alignment=TA_CENTER, leading=16),
    )
    cell_zp = zp or Paragraph('', ParagraphStyle('blank'))
    cell_gov = gov or Paragraph('', ParagraphStyle('blank'))
    table = Table([[cell_zp, title, cell_gov]],
                  colWidths=[26 * mm, 122 * mm, 26 * mm])
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    return table


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.line(18 * mm, 16 * mm, A4[0] - 18 * mm, 16 * mm)
    canvas.setFont('Helvetica', 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(
        18 * mm, 11 * mm,
        f'{settings.ORGANISATION} | Prepared by {settings.SUPPLIER}',
    )
    canvas.drawRightString(
        A4[0] - 18 * mm, 11 * mm,
        f'Sample data | Page {canvas.getPageNumber()}',
    )
    canvas.restoreState()


def simple_pdf(filename, title, subtitle='', meta=None, sections=None,
               table=None, footer_note=''):
    """meta: list of (label, value); sections: list of (heading, body)."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=22 * mm,
        title=title, author=settings.SUPPLIER,
    )
    sheet = _styles()
    story = [
        Paragraph(title, sheet['GzpTitle']),
        Paragraph(subtitle or settings.APP_NAME, sheet['GzpSub']),
        HRFlowable(width='100%', thickness=1, color=LINE, spaceAfter=10),
    ]

    if meta:
        data = [[Paragraph(f'<b>{k}</b>', sheet['GzpBody']),
                 Paragraph(str(v), sheet['GzpBody'])] for k, v in meta]
        t = Table(data, colWidths=[48 * mm, 122 * mm])
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TEXTCOLOR', (0, 0), (0, -1), MUTED),
            ('LINEBELOW', (0, 0), (-1, -1), 0.25, colors.HexColor('#EDEFF5')),
        ]))
        story.append(t)

    for heading, body in (sections or []):
        story.append(Paragraph(heading, sheet['GzpH']))
        story.append(Paragraph(str(body).replace('\n', '<br/>'), sheet['GzpBody']))

    if table:
        headers, rows, widths = table
        data = [[Paragraph(f'<b>{h}</b>', sheet['GzpBody']) for h in headers]]
        for row in rows:
            data.append([Paragraph(str(c), sheet['GzpBody']) for c in row])
        tbl = Table(data, colWidths=widths, repeatRows=1)
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F3F9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), NAVY),
            ('GRID', (0, 0), (-1, -1), 0.4, LINE),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(Spacer(1, 6))
        story.append(tbl)

    if footer_note:
        story.append(Spacer(1, 10))
        story.append(Paragraph(footer_note, sheet['GzpSmall']))

    story.append(Spacer(1, 14))
    story.append(Paragraph(
        'This document is generated by the demo platform. Sample values only. '
        'It complements and does not replace statutory registers or approvals.',
        sheet['GzpSmall'],
    ))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def table_pdf(filename, title, headers, rows, subtitle='', widths=None,
              footer_note=''):
    total = 174 * mm
    if not widths:
        widths = [total / max(1, len(headers))] * len(headers)
    else:
        factor = total / sum(widths)
        widths = [w * factor for w in widths]
    return simple_pdf(
        filename, title, subtitle,
        sections=[], table=(headers, rows, widths),
        footer_note=footer_note,
    )


def receipt_signer():
    """Accounts officer who signs receipts; role-only text when none is seeded."""
    from accounts.models import User

    base = User.objects.select_related('designation', 'role').filter(is_active=True)
    officer = base.filter(role__code='finance').order_by('pk').first()
    if officer:
        designation = (officer.designation.name if officer.designation
                       else officer.role_name)
        return officer.display_name, designation
    return 'Accounts Officer', 'Finance & Accounts, Gazipur Zila Parishad'


def receipt_pdf(booking, payment):
    """A payment record, deliberately distinct from the separately issued permit."""
    from xml.sax.saxutils import escape

    from django.utils import timezone
    from reportlab.lib.enums import TA_RIGHT

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=22 * mm,
        title=f'Payment receipt {booking.reference}', author=settings.SUPPLIER,
    )
    sheet = _styles()
    body = sheet['GzpBody']
    label = ParagraphStyle('ReceiptLabel', parent=body, textColor=MUTED, fontSize=8)
    amount_style = ParagraphStyle('ReceiptAmount', parent=body, alignment=TA_RIGHT)
    header_style = ParagraphStyle(
        'ReceiptHeader', parent=body, textColor=colors.white,
        fontSize=18, leading=22, fontName='Helvetica-Bold',
    )
    stamp_style = ParagraphStyle(
        'ReceiptStamp', parent=body, alignment=TA_CENTER, textColor=GREEN,
        fontSize=17, leading=17, fontName='Helvetica-Bold',
    )
    band_style = ParagraphStyle(
        'ReceiptBand', parent=body, textColor=colors.white, fontSize=7.5,
        leading=10, fontName='Helvetica-Bold',
    )
    band_right = ParagraphStyle('ReceiptBandRight', parent=band_style, alignment=TA_RIGHT)
    register_label = ParagraphStyle(
        'ReceiptRegisterLabel', parent=body, fontSize=6.8, leading=8,
        textColor=MUTED, fontName='Helvetica-Bold',
    )
    register_value = ParagraphStyle(
        'ReceiptRegisterValue', parent=body, fontSize=9.5, leading=12,
        textColor=INK, fontName='Helvetica-Bold',
    )
    seal_caption = ParagraphStyle(
        'ReceiptSealCaption', parent=body, fontSize=6.8, alignment=TA_CENTER,
        textColor=MUTED, leading=8,
    )

    def text(value, style=body):
        # Names and references are data, never ReportLab paragraph markup.
        return Paragraph(escape(str(value)), style)

    def amount(value):
        # The receipt's built-in PDF font supports BDT, not the taka glyph.
        return f'BDT {value or 0:,.2f}'

    zp = _static_image('img/zp_gazipur_logo.png', 18 * mm, 18 * mm)
    gov = _static_image('img/bd_govt_logo.png', 16 * mm, 16 * mm)
    seal = _static_image('img/bd_govt_seal.png', 21 * mm, 21 * mm)

    verified_at = payment.verified_at
    if verified_at and timezone.is_aware(verified_at):
        verified_at = timezone.localtime(verified_at)

    # Government masthead: solid navy band over a green rule.
    band = Table([[
        Paragraph("Government of the People's Republic of Bangladesh", band_style),
        Paragraph('Local Government Division · Gazipur Zila Parishad', band_right),
    ]], colWidths=[104 * mm, 70 * mm], style=TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), NAVY),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    letterhead = Table([[
        zp or text(''),
        [Paragraph('GAZIPUR ZILA PARISHAD', sheet['GzpTitle']),
         Paragraph('Office of the Zila Parishad, Gazipur<br/>'
                   'Dakbungalow E-Booking · Accounts Section', sheet['GzpSub'])],
        gov or text(''),
    ]], colWidths=[25 * mm, 124 * mm, 25 * mm], style=TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    # Register-style reference band, like a government money receipt.
    register = Table([[
        [Paragraph('RECEIPT NO.', register_label), text(payment.receipt_no or payment.txn_id, register_value)],
        [Paragraph('PAYMENT DATE', register_label),
         text(verified_at.strftime('%d %b %Y, %H:%M') if verified_at else 'Not recorded', register_value)],
        [Paragraph('STATUS', register_label),
         Paragraph('<font color="#147d54">PAID</font> · SIMULATED',
                   ParagraphStyle('ReceiptStatus', parent=register_value, fontSize=9))],
    ]], colWidths=[74 * mm, 60 * mm, 40 * mm], style=TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F7F8FC')),
        ('BOX', (0, 0), (-1, -1), 0.9, NAVY),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, LINE),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 9),
        ('RIGHTPADDING', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))

    stamp = Table([[Paragraph('PAID<br/><font size="8">SIMULATED</font>', stamp_style)]],
                  colWidths=[35 * mm], style=TableStyle([
                      ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                      ('BOX', (0, 0), (-1, -1), 1, GREEN),
                      ('TOPPADDING', (0, 0), (-1, -1), 5),
                      ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                  ]))
    heading = Table([[text('Payment receipt', header_style), stamp]],
                    colWidths=[127 * mm, 47 * mm], style=TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), GREEN),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 12),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ]))

    channel = (payment.raw or {}).get('channel') or ''
    channel_name = {
        'card': 'Card', 'bkash': 'bKash', 'nagad': 'Nagad', 'rocket': 'Rocket',
        'bank': 'Bank', 'netbanking': 'Net banking', 'ekpay': 'ekpay',
    }.get(channel, channel or 'Not recorded')
    metadata = [
        ('Receipt no.', payment.receipt_no or payment.txn_id),
        ('Transaction ID', payment.txn_id),
        ('Payment channel', channel_name),
        ('Verified at', verified_at.strftime('%d %b %Y %H:%M %Z') if verified_at else 'Not recorded'),
        ('Booking reference', booking.reference),
        ('Applicant', booking.applicant.get_full_name() or booking.applicant.username),
        ('Facility', booking.facility.name),
        ('Room / hall', booking.unit.name),
        ('Stay', f'{booking.check_in:%d %b %Y} to {booking.check_out:%d %b %Y}'),
    ]
    details = Table([[text(key, label), text(value)] for key, value in metadata],
                    colWidths=[43 * mm, 131 * mm], style=TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#FAFBFD')),
                        ('BOX', (0, 0), (-1, -1), 0.8, LINE),
                        ('INNERGRID', (0, 0), (-1, -1), 0.35, LINE),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 10),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                        ('TOPPADDING', (0, 0), (-1, -1), 3),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ]))
    totals = Table([
        [text('Payment summary'), text('Amount (BDT)', amount_style)],
        [text('Booking charges'), text(amount(booking.amount), amount_style)],
        [text('Security deposit'), text(amount(booking.deposit), amount_style)],
        [text('Gateway charge'), text(amount(booking.gateway_charge), amount_style)],
        [Paragraph('<b>Total paid</b>', body),
         Paragraph(f'<b>{amount(payment.amount)}</b>', amount_style)],
    ], colWidths=[116 * mm, 58 * mm], style=TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F3')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#EAF5EE')),
        ('LINEBELOW', (0, 0), (-1, -1), .4, LINE),
        ('LINEABOVE', (0, -1), (-1, -1), 1, GREEN),
        ('BOX', (0, 0), (-1, -1), 0.8, LINE),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))

    seal_box = Table([
        [seal or text('')],
        [Paragraph('Office seal<br/>(sample)', seal_caption)],
    ], colWidths=[46 * mm], rowHeights=[23 * mm, 8 * mm], style=TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 0.6, LINE),
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
    ]))
    signer_name, signer_role = receipt_signer()
    signature = Table(
        [[SignatureBlock(signer_name, signer_role, width=78 * mm, height=27 * mm),
          seal_box]],
        colWidths=[116 * mm, 58 * mm],
        style=TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]),
    )

    approval = ('Permit issued separately' if booking.permit_issued_at
                else 'Pending approval')
    note = ('Download the separately issued permit from your application.'
            if booking.permit_issued_at else
            'Payment received. Booking approval is still required before a permit can be issued.')
    story = [
        band, Spacer(1, 2), HRFlowable(width='100%', thickness=2.4, color=GREEN,
                                       spaceBefore=0, spaceAfter=0),
        letterhead, Spacer(1, 4), register, Spacer(1, 10), heading, Spacer(1, 10),
        details, Spacer(1, 10), totals, Spacer(1, 8),
        Paragraph(f'<b>{approval}</b>', body), text(note, sheet['GzpSmall']),
        Spacer(1, 8), signature, Spacer(1, 8),
        Paragraph('<b>This receipt is not a booking permit.</b>', body),
        Spacer(1, 3),
        text('Simulated payment. No money was transferred. '
             'This receipt records a demo payment only.', sheet['GzpSmall']),
    ]
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{booking.reference}-receipt.pdf"'
    return response


def permit_pdf(booking, verify_url):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=14 * mm, bottomMargin=22 * mm,
        title=f'Booking permit {booking.reference}',
    )
    sheet = _styles()
    approver = permit_approver(booking)
    signer_name = approver.display_name if approver else 'Authorised officer'
    signer_role = (
        approver.designation.name if approver and approver.designation
        else (approver.role_name if approver else settings.ORGANISATION))
    if booking.office_id:
        applicant_id = f'Office / service ID {booking.office_id}'
    elif booking.national_id:
        applicant_id = f'NID {booking.national_id}'
    else:
        applicant_id = '-'

    story = [
        _permit_header(),
        Spacer(1, 6),
        Paragraph('Booking Confirmation / Permit', sheet['GzpTitle']),
        Paragraph(f'{settings.ORGANISATION} - Dakbungalow E-Booking', sheet['GzpSub']),
        HRFlowable(width='100%', thickness=2, color=GREEN, spaceAfter=12),
    ]
    data = [
        ['Permit no.', booking.permit_no or booking.reference],
        ['Booking reference', booking.reference],
        ['Applicant', booking.applicant.get_full_name() or booking.applicant.username],
        ['Applicant category', booking.get_category_display()],
        ['Applicant ID', applicant_id],
        ['Facility', f'{booking.facility.name} ({booking.facility.location})'],
        ['Room / facility', booking.unit.name],
        ['Check-in', booking.check_in.strftime('%d %b %Y')],
        ['Check-out', booking.check_out.strftime('%d %b %Y')],
        ['Guests', booking.guests],
        ['Purpose', booking.purpose],
        ['Payment', f'Paid - {booking.payment_txn_id or "-"}'],
        ['Issued', booking.permit_issued_at.strftime('%d %b %Y %H:%M') if booking.permit_issued_at else '-'],
    ]
    table = Table(
        [[Paragraph(f'<b>{k}</b>', sheet['GzpBody']), Paragraph(str(v), sheet['GzpBody'])]
         for k, v in data],
        colWidths=[48 * mm, 122 * mm],
    )
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TEXTCOLOR', (0, 0), (0, -1), MUTED),
        ('LINEBELOW', (0, 0), (-1, -1), 0.25, colors.HexColor('#EDEFF5')),
    ]))
    story.append(table)
    story.append(Spacer(1, 10))

    qr = Image(io.BytesIO(qr_png_bytes(verify_url)), width=32 * mm, height=32 * mm)
    qr_note = Paragraph(
        'Present this permit at the facility reception. The QR code opens a '
        'public verification page. The reception desk can also type the '
        f'reference <b>{booking.reference}</b> to verify.', sheet['GzpBody'])
    story.append(Table(
        [[SignatureBlock(signer_name, signer_role, width=74 * mm),
          qr, qr_note]],
        colWidths=[78 * mm, 36 * mm, 60 * mm],
        style=TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]),
    ))
    story.append(Spacer(1, 12))
    story.append(Paragraph('Terms', sheet['GzpH']))
    story.append(Paragraph(
        'This permit is valid only for the dates and facility shown above and '
        'only with the verified payment. Please carry a photo ID. Cancellation '
        'and refund are subject to the published sample policy. The permit does '
        'not replace any statutory approval.', sheet['GzpBody']))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        f'Verify at: {verify_url}', sheet['GzpSmall']))
    story.append(Paragraph(
        f'Issued by {settings.ORGANISATION} through the Integrated Digital Platform. '
        f'Sample data.', sheet['GzpSmall']))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{booking.reference}-permit.pdf"'
    return response
