import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def create_pdf(filename, title, doc_type, patient, date, table_data, instructions, next_steps):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    story = []
    styles = getSampleStyleSheet()

    style_watermark = ParagraphStyle(
        'Watermark', parent=styles['Normal'], fontName='Helvetica-Bold',
        fontSize=10, textColor=colors.HexColor('#DC2626'), alignment=1, spaceAfter=15
    )
    style_header = ParagraphStyle(
        'HeaderTitle', parent=styles['Heading1'], fontName='Helvetica-Bold',
        fontSize=18, textColor=colors.HexColor('#0F172A'), alignment=0, spaceAfter=5
    )
    style_doctype = ParagraphStyle(
        'DocType', parent=styles['Normal'], fontName='Helvetica-Bold',
        fontSize=11, textColor=colors.HexColor('#2563EB'), spaceAfter=15
    )
    style_meta_label = ParagraphStyle(
        'MetaLabel', parent=styles['Normal'], fontName='Helvetica-Bold',
        fontSize=10, textColor=colors.HexColor('#475569')
    )
    style_meta_val = ParagraphStyle(
        'MetaVal', parent=styles['Normal'], fontName='Helvetica',
        fontSize=10, textColor=colors.HexColor('#0F172A')
    )
    style_section = ParagraphStyle(
        'SectionHeading', parent=styles['Heading2'], fontName='Helvetica-Bold',
        fontSize=12, textColor=colors.HexColor('#1E293B'), spaceBefore=15, spaceAfter=8
    )
    style_body = ParagraphStyle(
        'BodyText', parent=styles['Normal'], fontName='Helvetica',
        fontSize=10, textColor=colors.HexColor('#334155'), leading=14
    )

    story.append(Paragraph("SYNTHETIC TEST DATA — NOT A REAL MEDICAL REPORT / PRESCRIPTION", style_watermark))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=15))
    story.append(Paragraph(title, style_header))
    story.append(Paragraph(f"Document Type: {doc_type}", style_doctype))

    meta_table_data = [
        [Paragraph("Patient Name:", style_meta_label), Paragraph(patient, style_meta_val),
         Paragraph("Date:", style_meta_label), Paragraph(date, style_meta_val)],
        [Paragraph("Facility:", style_meta_label), Paragraph("Metro Diagnostic Center (Demo)", style_meta_val),
         Paragraph("Status:", style_meta_label), Paragraph("Verified Synthetic Test Case", style_meta_val)]
    ]
    meta_table = Table(meta_table_data, colWidths=[90, 180, 50, 200])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(meta_table)
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E2E8F0'), spaceBefore=10, spaceAfter=15))

    story.append(Paragraph("Clinical Measurements & Information", style_section))
    
    formatted_table_data = []
    for row_idx, row in enumerate(table_data):
        formatted_row = []
        for col in row:
            p_style = ParagraphStyle('TH' if row_idx == 0 else 'TD',
                                     fontName='Helvetica-Bold' if row_idx == 0 else 'Helvetica',
                                     fontSize=10 if row_idx == 0 else 9,
                                     textColor=colors.HexColor('#0F172A' if row_idx == 0 else '#334155'))
            formatted_row.append(Paragraph(str(col), p_style))
        formatted_table_data.append(formatted_row)

    col_widths = [160, 90, 140, 90] if len(table_data[0]) == 4 else [120, 80, 80, 80, 120]
    main_table = Table(formatted_table_data, colWidths=col_widths)
    main_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(main_table)

    story.append(Spacer(1, 10))
    story.append(Paragraph("Instructions", style_section))
    story.append(Paragraph(instructions, style_body))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Verified Next Step", style_section))
    story.append(Paragraph(next_steps, style_body))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E2E8F0'), spaceAfter=10))
    story.append(Paragraph("SYNTHETIC TEST DATA — FOR TESTING READBACK APPLICATION ONLY", style_watermark))

    doc.build(story)

output_dir = "public/demo-data"
if not os.path.exists(output_dir):
    output_dir = "demo-data"
os.makedirs(output_dir, exist_ok=True)

create_pdf(
    filename=os.path.join(output_dir, "01_CBC_Blood_Report.pdf"),
    title="COMPLETE BLOOD COUNT (CBC)",
    doc_type="Laboratory Report",
    patient="Demo Patient A",
    date="08-Oct-2026",
    table_data=[
        ["Test Name", "Result Value", "Reference Range", "Flag"],
        ["Hemoglobin", "10.2 g/dL", "12.0–16.0 g/dL", "LOW"],
        ["WBC Count", "7,800 cells/µL", "4,000–11,000 cells/µL", "NORMAL"],
        ["Platelet Count", "210,000 cells/µL", "150,000–450,000 cells/µL", "NORMAL"],
        ["RBC Count", "4.1 mil/µL", "3.8–5.2 mil/µL", "NORMAL"]
    ],
    instructions="Do not take the prescribed medicine on an empty stomach.",
    next_steps="Follow-up consultation after 2 weeks."
)

create_pdf(
    filename=os.path.join(output_dir, "02_Prescription_Demo.pdf"),
    title="OUTPATIENT PRESCRIPTION",
    doc_type="Outpatient Prescription",
    patient="Demo Patient B",
    date="08-Oct-2026",
    table_data=[
        ["Medicine", "Strength", "Frequency", "Route", "Duration"],
        ["Metformin", "500 mg", "Twice daily", "Oral", "7 days"]
    ],
    instructions="Take after meals.",
    next_steps="Review after 7 days."
)

create_pdf(
    filename=os.path.join(output_dir, "03_Followup_Lipid_Report.pdf"),
    title="LIPID PROFILE — FOLLOW-UP REPORT",
    doc_type="Laboratory Report (Follow-up)",
    patient="Demo Patient C",
    date="08-Oct-2026",
    table_data=[
        ["Test Name", "Result Value", "Reference Range", "Flag"],
        ["Total Cholesterol", "198 mg/dL", "< 200 mg/dL", "NORMAL"],
        ["LDL Cholesterol", "118 mg/dL", "< 130 mg/dL", "NORMAL"],
        ["HDL Cholesterol", "46 mg/dL", "> 40 mg/dL", "NORMAL"],
        ["Triglycerides", "168 mg/dL", "< 150 mg/dL", "HIGH"]
    ],
    instructions="Continue the instructions provided in the source document.",
    next_steps="Follow-up lipid profile after 3 months."
)

print(f"PDFs successfully generated in: {output_dir}")
