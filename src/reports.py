from flask import send_file
import csv
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime

class ReportGenerator:

    def generate_csv(sheet, table_type, columns, rows):
        """Generate CSV file"""
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        
        # Write header
        writer.writerow(columns)
        
        # Write data
        for row in rows:
            writer.writerow(row)
        
        # Convert to bytes
        output.seek(0)
        bytes_output = io.BytesIO()
        bytes_output.write('\ufeff'.encode('utf-8')) 
        bytes_output.write(output.getvalue().encode('utf-8'))
        bytes_output.seek(0)
        
        filename = f"{sheet['display_name']}_{table_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return send_file(
            bytes_output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )


    def generate_pdf(sheet, table_type, columns, rows):
        """Generate PDF file"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        
        # Title
        if table_type == 'included':
            title = f"DATA INCLUDED REPORT - {sheet['display_name']}"
        elif table_type == 'excluded':
            title = f"DATA EXCLUSION REPORT - {sheet['display_name']}"
        else:
            title = f"ORIGINAL DATA REPORT - {sheet['display_name']}"
        
        title_para = Paragraph(f"<b>{title}</b>", styles['Title'])
        elements.append(title_para)
        elements.append(Spacer(1, 0.3*inch))
        
        # Metadata
        date_para = Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal'])
        elements.append(date_para)
        count_para = Paragraph(f"Total Records: {len(rows):,}", styles['Normal'])
        elements.append(count_para)
        elements.append(Spacer(1, 0.3*inch))
        
        # Limit rows for PDF (too many rows = huge file)
        max_rows = 1000
        if len(rows) > max_rows:
            rows = rows[:max_rows]
            note = Paragraph(f"<i>Note: Showing first {max_rows:,} of {len(rows):,} records. Download CSV for complete data.</i>", styles['Normal'])
            elements.append(note)
            elements.append(Spacer(1, 0.2*inch))
        
        # Table data
        table_data = [columns]  # Header row
        for row in rows:
            # Convert all values to strings and truncate long text
            row_data = []
            for val in row:
                if val is None:
                    row_data.append('')
                else:
                    val_str = str(val)
                    # Truncate long values
                    if len(val_str) > 50:
                        val_str = val_str[:47] + '...'
                    row_data.append(val_str)
            table_data.append(row_data)
        
        # Create table
        # Adjust column widths based on number of columns
        num_cols = len(columns)
        col_width = 7.5 * inch / num_cols  # Fit within page width
        
        pdf_table = Table(table_data, colWidths=[col_width] * num_cols)
        
        # Style table
        pdf_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(pdf_table)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        filename = f"{sheet['display_name']}_{table_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )