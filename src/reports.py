from flask import Response, send_file
import csv
from io import StringIO, BytesIO
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from html import escape


class ReportGenerator:

    def generate_csv(sheet, table_type, columns, sql, conn):
        from io import StringIO
        
        buffer = StringIO()
        
        # BOM for Excel
        buffer.write('\ufeff')
        
        # Write header
        writer = csv.writer(buffer, quoting=csv.QUOTE_ALL)
        writer.writerow(columns)
        
        # Use COPY to export data directly
        copy_sql = f"COPY ({sql}) TO STDOUT WITH (FORMAT CSV, ENCODING 'UTF8', QUOTE '\"')"
        
        with conn.cursor() as cur:
            # Write data using COPY - this appends to buffer
            cur.copy_expert(copy_sql, buffer)
        
        buffer.seek(0)
        
        filename = f"{sheet['display_name']}_{table_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return Response(
            buffer.getvalue(),
            mimetype="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    def generate_pdf(sheet, table_type, columns, sql, conn):
        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            leftMargin=5 * mm,
            rightMargin=5 * mm,
            topMargin=5 * mm,
            bottomMargin=5 * mm
        )

        elements = []
        styles = getSampleStyleSheet()

        # Title
        title_map = {
            "included": "DATA INCLUDED REPORT",
            "excluded": "DATA EXCLUSION REPORT",
            "original": "ORIGINAL DATA REPORT"
        }

        title = f"{title_map.get(table_type, 'DATA REPORT')} - {sheet['display_name']}"
        elements.append(Paragraph(f"<b>{title}</b>", styles['Title']))
        elements.append(Spacer(1, 5 * mm))
        elements.append(
            Paragraph(
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                styles['Normal']
            )
        )
        elements.append(Spacer(1, 5 * mm))

        # Columns to exclude entirely
        exclude_columns = {'id', 'created_at'}
        filtered_columns = [c for c in columns if c not in exclude_columns]
        column_indices = [columns.index(c) for c in filtered_columns]

        # Columns that need wrapping
        wrap_columns = {'row_id', 'exclusion_reason'}

        # Header row
        header_row = [
            col[:20] + '...' if len(col) > 20 else col
            for col in filtered_columns
        ]

        # Column widths
        available_width = 280 * mm - 10 * mm
        col_width = max(25 * mm, available_width / len(filtered_columns))
        col_widths = [col_width] * len(filtered_columns)

        # Paragraph style for wrapped cells
        cell_style = ParagraphStyle(
            'CellStyle',
            fontName='Helvetica',
            fontSize=8,
            leading=10,
            wordWrap='CJK'  # allows breaking long strings without spaces
        )

        # Table style
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#404040')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
            [colors.white, colors.HexColor('#F5F5F5')]),
        ])

        max_rows = 1000

        # Fetch data
        with conn.cursor() as cur:
            cur.execute(sql)
            all_rows = cur.fetchmany(max_rows)

        # Build table data
        table_data = [header_row]

        for row in all_rows:
            formatted_row = []
            for col, idx in zip(filtered_columns, column_indices):
                value = '' if row[idx] is None else str(row[idx])[:150]

                if col in wrap_columns:
                    formatted_row.append(Paragraph(value, cell_style))
                else:
                    formatted_row.append(value)

            table_data.append(formatted_row)

        # Create table
        if table_data:
            table = Table(table_data, colWidths=col_widths, repeatRows=1)
            table.setStyle(table_style)
            elements.append(table)

        doc.build(elements)
        buffer.seek(0)

        filename = (
            f"{sheet['display_name']}_"
            f"{table_type}_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )

        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename
        )
