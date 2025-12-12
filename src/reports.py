from flask import send_file
import csv
import io
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
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
        """Generate PDF file with proper text wrapping, special character support, and formatting"""
        from html import escape
        
        buffer = io.BytesIO()
        # Use landscape orientation with smaller margins for more space
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), 
                            leftMargin=5*mm, rightMargin=5*mm,
                            topMargin=5*mm, bottomMargin=5*mm)
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
        elements.append(Spacer(1, 5*mm))
        
        # Metadata
        date_para = Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal'])
        elements.append(date_para)
        count_para = Paragraph(f"Total Records: {len(rows):,}", styles['Normal'])
        elements.append(count_para)
        elements.append(Spacer(1, 5*mm))
        
        # Limit rows for PDF (too many rows = huge file)
        max_rows = 1000
        original_row_count = len(rows)
        if len(rows) > max_rows:
            rows = rows[:max_rows]
            note = Paragraph(f"<i>Note: Showing first {max_rows:,} of {original_row_count:,} records. Download CSV for complete data.</i>", styles['Normal'])
            elements.append(note)
            elements.append(Spacer(1, 5*mm))
        
        # Create custom styles for table cells with larger fonts
        cell_style = ParagraphStyle(
            'CellStyle',
            parent=styles['Normal'],
            fontSize=8,
            leading=10,
            wordWrap='CJK',
            alignment=0  # Left align
        )
        
        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=styles['Normal'],
            fontSize=9,
            leading=11,
            fontName='Helvetica-Bold',
            textColor=colors.whitesmoke,
            wordWrap='CJK',
            alignment=0
        )
        
        # Shorten column headers if they're too long
        shortened_columns = []
        for col in columns:
            if len(col) > 20:
                # Truncate long column names
                shortened_columns.append(col[:17] + '...')
            else:
                shortened_columns.append(col)
        
        # Prepare table data with Paragraph objects for text wrapping
        table_data = []
        
        # Header row with wrapping
        header_row = [Paragraph(f"<b>{escape(str(col))}</b>", header_style) for col in shortened_columns]
        table_data.append(header_row)
        
        # Data rows with wrapping and special character support
        for row in rows:
            row_data = []
            for val in row:
                if val is None:
                    row_data.append(Paragraph('', cell_style))
                else:
                    val_str = str(val)
                    # Truncate extremely long values
                    if len(val_str) > 150:
                        val_str = val_str[:147] + '...'
                    # Escape HTML special characters but preserve unicode
                    val_str = escape(val_str)
                    row_data.append(Paragraph(val_str, cell_style))
            table_data.append(row_data)
        
        # Calculate available width 
        available_width = 350*mm - 10*mm
        num_cols = len(columns)
        
        # Smart column width calculation
        if num_cols <= 5:
            col_width = available_width / num_cols
            col_widths = [col_width] * num_cols
        else:
            # For many columns, set minimum width
            min_col_width =  25*mm  
            if num_cols * min_col_width <= available_width:
                col_width = available_width / num_cols
                col_widths = [col_width] * num_cols
            else:
                # Use minimum width, table will be wide
                col_widths = [min_col_width] * num_cols
        
        # Create table
        pdf_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        # Style table with larger padding
        pdf_table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#404040')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            # Alternating row colors for readability
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
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