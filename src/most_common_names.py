"""
Most Common Names Export Module
Handles CSV and JSON export of top 80% most common names
"""

import csv
import json
import logging
from io import StringIO, BytesIO
from flask import Response, send_file
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class MostCommonNamesExporter:
    """Export most common names data to CSV and JSON formats"""
    
    @staticmethod
    def generate_csv(data: List[Dict[str, Any]], sheet_info: Dict[str, str]) -> Response:
        """
        Generate CSV file for most common names
        
        Args:
            data: List of common names with frequencies
            sheet_info: Sheet metadata (display_name, identifier)
        
        Returns:
            Flask Response with CSV file
        """
        try:
            # Create CSV in memory
            output = StringIO()
            
            if not data or len(data) == 0:
                # Empty file with headers only
                writer = csv.writer(output)
                writer.writerow(['Rank', 'Name', 'Frequency', 'Percentage', 'Cumulative Count', 'Cumulative Percentage', 'Total Records'])
                csv_data = output.getvalue()
                output.close()
                
                return Response(
                    csv_data,
                    mimetype='text/csv',
                    headers={
                        'Content-Disposition': f'attachment; filename=common_names_{sheet_info["identifier"]}.csv'
                    }
                )
            
            # Write headers
            writer = csv.writer(output)
            writer.writerow(['Rank', 'Name', 'Frequency', 'Percentage (%)', 'Cumulative Count', 'Cumulative Percentage (%)', 'Total Records'])
            
            # Write data rows
            for row in data:
                writer.writerow([
                    row.get('rank', ''),
                    row.get('firstname', ''),
                    row.get('frequency', 0),
                    row.get('percentage_of_total', 0),
                    row.get('cumulative_count', 0),
                    row.get('cumulative_percentage', 0),
                    row.get('total_records', 0)
                ])
            
            # Get CSV content
            csv_data = output.getvalue()
            output.close()
            
            logger.info(f"✅ Generated CSV with {len(data)} common names")
            
            return Response(
                csv_data,
                mimetype='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename=common_names_{sheet_info["identifier"]}.csv'
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Error generating CSV: {e}")
            raise
    
    @staticmethod
    def generate_json(data: List[Dict[str, Any]], sheet_info: Dict[str, str]) -> Response:
        """
        Generate JSON file for most common names
        
        Args:
            data: List of common names with frequencies
            sheet_info: Sheet metadata (display_name, identifier)
        
        Returns:
            Flask Response with JSON file
        """
        try:
            # Prepare JSON structure
            json_output = {
                'metadata': {
                    'sheet_name': sheet_info.get('display_name', 'Unknown'),
                    'sheet_identifier': sheet_info.get('identifier', 'unknown'),
                    'total_names': len(data),
                    'total_records': data[0].get('total_records', 0) if data else 0,
                    'coverage': '80% of included records'
                },
                'common_names': []
            }
            
            # Add data
            for row in data:
                json_output['common_names'].append({
                    'rank': row.get('rank'),
                    'name': row.get('firstname'),
                    'frequency': row.get('frequency'),
                    'percentage_of_total': float(row.get('percentage_of_total', 0)),
                    'cumulative_count': row.get('cumulative_count'),
                    'cumulative_percentage': float(row.get('cumulative_percentage', 0))
                })
            
            # Convert to JSON string
            json_data = json.dumps(json_output, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Generated JSON with {len(data)} common names")
            
            return Response(
                json_data,
                mimetype='application/json',
                headers={
                    'Content-Disposition': f'attachment; filename=common_names_{sheet_info["identifier"]}.json'
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Error generating JSON: {e}")
            raise