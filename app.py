"""
Flask Application for Data Cleaning Dashboard
Main application file with all routes and endpoints.
"""

from flask import Flask, render_template, request, jsonify
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import time
import uuid
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from src import DataCleaner, SupabaseManager, ReportGenerator, DataAnalytics, MostCommonNamesExporter, ComparisonAnalytics, DB_CONFIG

# Google Sheets setup
SERVICE_ACCOUNT_FILE = "service_account.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build("sheets", "v4", credentials=creds)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize Supabase manager
supabase_manager = None
report_generator= ReportGenerator

# Sheet configurations
SHEETS_CONFIG = {
    'sheet1': {
        'type': 'google_sheets',
        'spreadsheet_id': "1kKprUOWWZ8kFP2CkMhzdqiD0iHKBH7et7aOnuVF_miY",
        'range_name': "01_jan",
        'display_name': 'January 2025',
        'identifier': 'jan_2025'
    },
    'sheet2': {
        'type': 'google_sheets',
        'spreadsheet_id': "1V9MQrvQS8N4Di3exRvNwhrwgwfccNmK5TwF1mV_jHdk",
        'range_name': "04_apr",
        'display_name': 'April 2025',
        'identifier': 'apr_2025'
    }
}


def init_supabase():
    """Initialize Supabase manager"""
    global supabase_manager
    if supabase_manager is None:
        try:
            supabase_manager = SupabaseManager()
            logger.info("Supabase initialized successfully")
        except Exception as e:
            logger.error(f"Error: Supabase initialization failed: {e}")
            raise


def get_sheet_data(spreadsheet_id, range_name):
    """Fetch data from Google Sheets with retry logic"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            return result.get("values", [])
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Retry {attempt + 1}/{max_retries} for sheet data: {e}")
                time.sleep(1)
            else:
                logger.error(f"Failed to fetch sheet data after {max_retries} attempts: {e}")
                raise


def process_and_clean_sheet_data(sheet_key, batch_size=100000):
    """
    Process Google Sheets data directly with row_id generation and cleaning
    
    Args:
        sheet_key: Sheet configuration key
        batch_size: Number of rows to process per batch
        store_original: Whether to store original data
    
    Returns:
        Tuple of (total_original, total_included, total_excluded)
    """
    config = SHEETS_CONFIG[sheet_key]
    
    # Step 1: Fetch ALL data from Google Sheets
    logger.info(f"Fetching data from Google Sheets: {config['display_name']}...")
    fetch_start = time.time()
    raw_data = get_sheet_data(config['spreadsheet_id'], config['range_name'])
    fetch_time = time.time() - fetch_start
    
    if not raw_data or len(raw_data) < 2:
        raise ValueError("No data found in sheet")
    
    headers = raw_data[0]
    total_rows = len(raw_data) - 1
    logger.info(f"✓ Fetched {total_rows:,} rows from Google Sheets in {fetch_time:.1f}s")
    
    # Step 2: Create tables
    init_supabase()
    supabase_manager.create_original_table('clients_2025', config['identifier'])
    
    # Step 3: Clear existing data
    safe_table_name = 'clients_2025'.lower().replace(' ', '_').replace('-', '_')
    original_table = f"{safe_table_name}_{config['identifier']}_original"
    supabase_manager.clear_table(original_table)
    
    # Step 4: Process in batches
    total_included = 0
    total_excluded = 0
    num_batches = (total_rows + batch_size - 1) // batch_size
    
    logger.info(f"Processing {total_rows:,} rows in {num_batches} batches of {batch_size:,}...")
    overall_start = time.time()
    
    for batch_num in range(num_batches):
        batch_start_time = time.time()
        batch_start = batch_num * batch_size + 1  # +1 to skip header
        batch_end = min(batch_start + batch_size, len(raw_data))
        
        logger.info(f"\nProcessing batch {batch_num + 1}/{num_batches} (rows {batch_start} to {batch_end - 1})...")
        
        # Parse batch with row_id generation
        batch_with_ids = []

        
        for idx in range(batch_start, batch_end):
            row_data = raw_data[idx]
            row_id = str(uuid.uuid4())
            original_row_number = idx
            
            # Parse row data
            parsed_row = {
                'row_id': row_id,
                'original_row_number': original_row_number,
                'firstname': row_data[0] if len(row_data) > 0 else '',
                'birthday': row_data[1] if len(row_data) > 1 else '',
                'birthmonth': row_data[2] if len(row_data) > 2 else '',
                'birthyear': row_data[3] if len(row_data) > 3 else ''
            }
            batch_with_ids.append(parsed_row)
            
        
        # Clean this batch
        clean_start = time.time()
        cleaner = DataCleaner()
        all_data = cleaner.clean_dataset(batch_with_ids)
        clean_time = time.time() - clean_start
        
        included_count = sum(1 for row in all_data if row['status'] == 'included')
        excluded_count = sum(1 for row in all_data if row['status'] == 'excluded')
        logger.info(f"Batch {batch_num + 1}: Cleaned in {clean_time:.1f}s - {included_count} included, {excluded_count} excluded")
        
        # Parallel inserts
        insert_start = time.time()
        
        supabase_manager.append_data(original_table, all_data)
        insert_time = time.time() - insert_start
        
        
        # Update totals
        total_included += included_count
        total_excluded += excluded_count
        
        # Batch summary
        batch_total = time.time() - batch_start_time
        logger.info(f"Batch {batch_num + 1}: Inserted in {insert_time:.1f}s (parallel)")
        logger.info(f"Batch {batch_num + 1} total time: {batch_total:.1f}s")
    
    # Final summary
    total_time = time.time() - overall_start
    logger.info(f"\n✓ Processing complete!")
    logger.info(f"Total: {total_rows:,} rows")
    logger.info(f"Included: {total_included:,} rows")
    logger.info(f"Excluded: {total_excluded:,} rows")
    logger.info(f"Total processing time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    logger.info(f"Average rate: {total_rows/total_time:.0f} rows/sec")
    
    return total_rows, total_included, total_excluded


@app.route('/')
def index():
    """Serve main page"""
    return render_template('index.html', sheets=SHEETS_CONFIG)


@app.route("/process/<sheet_key>", methods=['POST'])
def process(sheet_key):
    """Process a sheet and clean the data"""
    sheet = SHEETS_CONFIG.get(sheet_key)
    if not sheet:
        return jsonify({"error": "Invalid sheet key"}), 400
    
    try:
        total, included, excluded = process_and_clean_sheet_data(sheet_key)
        return jsonify({
            "success": True,
            "sheet": sheet_key,
            "total_rows": total,
            "included_count": included,
            "excluded_count": excluded
        })
    except Exception as e:
        logger.error(f"Error processing sheet {sheet_key}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/data/<sheet_key>/<table_type>")
def get_table_data(sheet_key, table_type):
    """Get data from a specific table"""
    sheet = SHEETS_CONFIG.get(sheet_key)
    if not sheet:
        return jsonify({"error": "Invalid sheet key"}), 400
    
    if table_type not in ['included', 'excluded', 'original']:
        return jsonify({"error": "Invalid table type"}), 400
    
    try:
        init_supabase()
        safe_table_name = 'clients_2025'.lower().replace(' ', '_').replace('-', '_')
        table_name = f"{safe_table_name}_{sheet['identifier']}_original"
        
        # Add status filter
        status_filter = ""
        if table_type in ['included', 'excluded']:
            status_filter = f"WHERE status = '{table_type}'"
        
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 100))
        sort_by = request.args.get('sort_by', 'original_row_number')
        sort_order = request.args.get('sort_order', 'asc')
        
        # Get data
        data, total_count = supabase_manager.get_table_data(
            table_name, 
            page, 
            per_page, 
            sort_by, 
            sort_order, 
            table_type if table_type in ['included', 'excluded'] else None
        )
        
        return jsonify({
            "success": True,
            "data": data,
            "total_count": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": (total_count + per_page - 1) // per_page
        })
    except Exception as e:
        logger.error(f"Error getting table data: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route("/check_tables/<sheet_key>")
def check_tables(sheet_key):
    """Check if tables exist for a sheet"""
    sheet = SHEETS_CONFIG.get(sheet_key)
    if not sheet:
        return jsonify({"error": "Invalid sheet key"}), 400
    
    try:
        init_supabase()
        result = supabase_manager.check_tables_exist('clients_2025', sheet['identifier'])
        
        # Check if analytics table exists
        safe_table_name = 'clients_2025'.lower().replace(' ', '_').replace('-', '_')
        analytics_table = f"{safe_table_name}_{sheet['identifier']}_analytics"
        
        analytics_exists = False
        with supabase_manager.conn.cursor() as cur:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                )
            """, (analytics_table,))
            analytics_exists = cur.fetchone()[0]
        
        return jsonify({
            "success": True,
            "sheet_key": sheet_key,
            "exists": result['exists'],
            "counts": result['counts'],
            "analytics_exists": analytics_exists
        })
    except Exception as e:
        logger.error(f"Error checking tables for {sheet_key}: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route("/download/<sheet_key>/<table_type>/<format>")
def download_table(sheet_key, table_type, format):
    sheet = SHEETS_CONFIG.get(sheet_key)
    if not sheet:
        return jsonify({"error": "Invalid sheet key"}), 400

    if table_type not in {"included", "excluded", "original"}:
        return jsonify({"error": "Invalid table type"}), 400

    if format not in {"csv", "pdf"}:
        return jsonify({"error": "Invalid format"}), 400

    try:
        init_supabase()

        safe_table_name = 'clients_2025'.lower().replace(' ', '_').replace('-', '_')
        original_table = f"{safe_table_name}_{sheet['identifier']}_original"

        if table_type == 'included':
            columns_select = "original_row_number, row_id, firstname, birthday, birthmonth, birthyear"
            where_clause = "WHERE status = 'included'"
        elif table_type == 'excluded':
            columns_select = "original_row_number, row_id, firstname, birthday, birthmonth, birthyear, exclusion_reason"
            where_clause = "WHERE status = 'excluded'"
        else:
            columns_select = "*"
            where_clause = ""

        sql = f"""
            SELECT {columns_select}
            FROM {original_table}
            {where_clause}
            ORDER BY original_row_number ASC
        """

        # Fetch column names ONLY (cheap)
        with supabase_manager.conn.cursor() as cur:
            cur.execute(sql + " LIMIT 0")
            columns = [desc[0] for desc in cur.description]

        if format == "csv":
            return report_generator.generate_csv(
                sheet=sheet,
                table_type=table_type,
                columns=columns,
                sql=sql,
                conn=supabase_manager.conn
            )

        return report_generator.generate_pdf(
            sheet=sheet,
            table_type=table_type,
            columns=columns,
            sql=sql,
            conn=supabase_manager.conn
        )

    except Exception as e:
        logger.exception("Error downloading table")
        return jsonify({"error": str(e)}), 500

    
    
#Analytics section 
@app.route('/analytics/<sheet_key>/create', methods=['POST'])
def create_analytics(sheet_key):
    """Create analytics tables for a sheet"""
    try:
        sheet = SHEETS_CONFIG.get(sheet_key)
        if not sheet:
            return jsonify({'error': 'Invalid sheet key'}), 404
        
        logger.info(f"Creating analytics for sheet: {sheet_key}")
        
        analytics = DataAnalytics(DB_CONFIG)
        analytics.connect()
        
        try:
            # Create indexes FIRST (before creating views)
            analytics.create_duplicate_indexes('clients_2025', sheet['identifier'])
            
            # Create analytics tables
            analytics.create_analytics_table('clients_2025', sheet['identifier'])
            analytics.create_duplicate_groups_view('clients_2025', sheet['identifier'])
            analytics.create_duplicate_table_indexes('clients_2025', sheet['identifier'])  # ← Indexes on DUPLICATE tables AFTER they're created
            analytics.create_visualization_tables('clients_2025', sheet['identifier'])
            analytics.create_common_names_table('clients_2025', sheet['identifier'])  # Add this line
            
            logger.info(f"✅ Analytics created successfully for {sheet_key}")
            return jsonify({'success': True, 'message': 'Analytics created successfully'})
            
        finally:
            analytics.disconnect()
            
    except Exception as e:
        logger.error(f"Error creating analytics: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
@app.route('/analytics/<sheet_key>/summary')
def get_analytics_summary(sheet_key):
    """Get summary statistics for a sheet"""
    try:
        sheet = SHEETS_CONFIG.get(sheet_key)
        if not sheet:
            return jsonify({'error': 'Invalid sheet key'}), 404
        
        logger.info(f"Getting analytics for sheet: {sheet_key}")
        
        analytics = DataAnalytics(DB_CONFIG)
        analytics.connect()
        
        try:
            # Use the existing method from DataAnalytics class
            data = analytics.get_analytics_data('clients_2025', sheet['identifier'])
            
            if not data:
                return jsonify({'error': 'No analytics data found'}), 404
            
            # Map database columns to frontend fields
            summary = {
                'unique_names': int(data.get('unique_names', 0)) if data.get('unique_names') is not None else 0,
                'unique_birthdays': int(data.get('unique_full_birthdays', 0)) if data.get('unique_full_birthdays') is not None else 0,
                'unique_name_year': int(data.get('unique_name_year_combinations', 0)) if data.get('unique_name_year_combinations') is not None else 0,
                'unique_name_month': int(data.get('unique_name_month_combinations', 0)) if data.get('unique_name_month_combinations') is not None else 0,
                'unique_name_day': int(data.get('unique_name_day_combinations', 0)) if data.get('unique_name_day_combinations') is not None else 0
            }
            
            logger.info(f"Analytics summary: {summary}")
            return jsonify(summary)
            
        finally:
            analytics.disconnect()
            
    except Exception as e:
        logger.error(f"Error generating analytics summary: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
@app.route('/analytics/<sheet_key>/duplicates/<group_type>')
def get_duplicate_groups(sheet_key, group_type):
    """Get duplicate groups by type (name_year, name_month, name_day)"""
    try:
        sheet = SHEETS_CONFIG.get(sheet_key)
        if not sheet:
            return jsonify({'error': 'Invalid sheet key'}), 404
        
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        # Validate group_type
        if group_type not in ['name_year', 'name_month', 'name_day', 'year_month', 'year_day', 'month_day']:
            return jsonify({'error': 'Invalid group type'}), 400
        
        logger.info(f"Getting {group_type} duplicates for sheet: {sheet_key}")
        
        analytics = DataAnalytics(DB_CONFIG)
        analytics.connect()
        
        try:
            duplicates, total_count = analytics.get_duplicate_groups(
                'clients_2025', 
                sheet['identifier'], 
                group_type, 
                page, 
                per_page
            )
            
            total_pages = (total_count + per_page - 1) // per_page
            
            return jsonify({
                'data': duplicates,
                'page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': total_pages,
                'group_type': group_type
            })
            
        finally:
            analytics.disconnect()
            
    except Exception as e:
        logger.error(f"Error getting duplicate groups: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/analytics/<sheet_key>/charts/<chart_type>')
def get_chart_data(sheet_key, chart_type):
    """Get chart data (birthyear or birthmonth distributions)"""
    try:
        sheet = SHEETS_CONFIG.get(sheet_key)
        if not sheet:
            return jsonify({'error': 'Invalid sheet key'}), 404
        
        # Validate chart_type
        if chart_type not in ['birthyear', 'birthmonth']:
            return jsonify({'error': 'Invalid chart type'}), 400
        
        logger.info(f"Getting {chart_type} chart data for sheet: {sheet_key}")
        
        analytics = DataAnalytics(DB_CONFIG)
        analytics.connect()
        
        try:
            chart_data = analytics.get_chart_data(
                'clients_2025', 
                sheet['identifier'], 
                chart_type
            )
            
            return jsonify({'data': chart_data, 'chart_type': chart_type})
            
        finally:
            analytics.disconnect()
            
    except Exception as e:
        logger.error(f"Error getting chart data: {str(e)}")
        return jsonify({'error': str(e)}), 500
 
@app.route('/analytics/<sheet_key>/common_names')    
def get_common_names(sheet_key):
    """Get top 80% most common names with frequencies"""
    try:
        sheet = SHEETS_CONFIG.get(sheet_key)
        if not sheet:
            return jsonify({'error': 'Invalid sheet key'}), 404
        
        logger.info(f"Getting common names for sheet: {sheet_key}")
        
        analytics = DataAnalytics(DB_CONFIG)
        analytics.connect()
        
        try:
            data = analytics.get_common_names_data('clients_2025', sheet['identifier'])
            
            if not data:
                return jsonify({'error': 'No common names data found'}), 404
            
            # Calculate summary stats
            total_names = len(data)
            total_records = data[0].get('total_records', 0) if data else 0
            coverage_count = data[-1].get('cumulative_count', 0) if data else 0
            
            return jsonify({
                'names': data,
                'summary': {
                    'total_names': total_names,
                    'total_records': total_records,
                    'coverage_count': coverage_count,
                    'coverage_percentage': 80.0
                }
            })
            
        finally:
            analytics.disconnect()
            
    except Exception as e:
        logger.error(f"Error getting common names: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/analytics/<sheet_key>/common_names/download/<format>')
def download_common_names(sheet_key, format):
    """Download common names as CSV or JSON"""
    try:
        sheet = SHEETS_CONFIG.get(sheet_key)
        if not sheet:
            return jsonify({'error': 'Invalid sheet key'}), 404
        
        if format not in ['csv', 'json']:
            return jsonify({'error': 'Invalid format. Use csv or json'}), 400
        
        logger.info(f"Downloading common names as {format} for sheet: {sheet_key}")
        
        analytics = DataAnalytics(DB_CONFIG)
        analytics.connect()
        
        try:
            data = analytics.get_common_names_data('clients_2025', sheet['identifier'])
            
            if not data:
                return jsonify({'error': 'No common names data found'}), 404
            
            exporter = MostCommonNamesExporter()
            
            if format == 'csv':
                return exporter.generate_csv(data, sheet)
            else:
                return exporter.generate_json(data, sheet)
            
        finally:
            analytics.disconnect()
            
    except Exception as e:
        logger.error(f"Error downloading common names: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
@app.route('/comparison/create', methods=['POST'])
def create_comparison():
    """Create comparison analytics between JAN and APR"""
    try:
        logger.info("Creating comparison analytics between JAN and APR")
        
        comparison = ComparisonAnalytics(DB_CONFIG)
        comparison.connect()
        
        try:
            # Create all comparison tables
            comparison.create_comparison_analytics(
                table_name='clients_2025',
                jan_identifier='jan_2025',
                apr_identifier='apr_2025'
            )
            
            logger.info("✅ Comparison analytics created successfully")
            return jsonify({'success': True, 'message': 'Comparison analytics created successfully'})
            
        finally:
            comparison.disconnect()
            
    except Exception as e:
        logger.error(f"Error creating comparison analytics: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/comparison/summary')
def get_comparison_summary():
    """Get comparison summary statistics"""
    try:
        logger.info("Getting comparison summary")
        
        comparison = ComparisonAnalytics(DB_CONFIG)
        comparison.connect()
        
        try:
            summary = comparison.get_comparison_summary('clients_2025')
            
            if not summary:
                return jsonify({'error': 'No comparison data found. Please create comparison analytics first.'}), 404
            
            return jsonify(summary)
            
        finally:
            comparison.disconnect()
            
    except Exception as e:
        logger.error(f"Error getting comparison summary: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/comparison/common_names')
def get_comparison_common_names():
    """Get common names between JAN and APR"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        filter_top80 = request.args.get('filter_top80', None)
        
        logger.info(f"Getting common names (page={page}, filter={filter_top80})")
        
        comparison = ComparisonAnalytics(DB_CONFIG)
        comparison.connect()
        
        try:
            data, total_count = comparison.get_common_names(
                'clients_2025',
                page=page,
                per_page=per_page,
                filter_top80_only=filter_top80
            )
            
            total_pages = (total_count + per_page - 1) // per_page
            
            return jsonify({
                'data': data,
                'page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': total_pages
            })
            
        finally:
            comparison.disconnect()
            
    except Exception as e:
        logger.error(f"Error getting common names: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/comparison/unique_jan')
def get_comparison_unique_jan():
    """Get names unique to JAN"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        top80_only = request.args.get('top80_only', 'false').lower() == 'true'
        
        logger.info(f"Getting unique JAN names (page={page}, top80_only={top80_only})")
        
        comparison = ComparisonAnalytics(DB_CONFIG)
        comparison.connect()
        
        try:
            data, total_count = comparison.get_unique_jan_names(
                'clients_2025',
                page=page,
                per_page=per_page,
                top80_only=top80_only
            )
            
            total_pages = (total_count + per_page - 1) // per_page
            
            return jsonify({
                'data': data,
                'page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': total_pages
            })
            
        finally:
            comparison.disconnect()
            
    except Exception as e:
        logger.error(f"Error getting unique JAN names: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/comparison/unique_apr')
def get_comparison_unique_apr():
    """Get names unique to APR"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        top80_only = request.args.get('top80_only', 'false').lower() == 'true'
        
        logger.info(f"Getting unique APR names (page={page}, top80_only={top80_only})")
        
        comparison = ComparisonAnalytics(DB_CONFIG)
        comparison.connect()
        
        try:
            data, total_count = comparison.get_unique_apr_names(
                'clients_2025',
                page=page,
                per_page=per_page,
                top80_only=top80_only
            )
            
            total_pages = (total_count + per_page - 1) // per_page
            
            return jsonify({
                'data': data,
                'page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': total_pages
            })
            
        finally:
            comparison.disconnect()
            
    except Exception as e:
        logger.error(f"Error getting unique APR names: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/comparison/download/<dataset>/<format>')
def download_comparison(dataset, format):
    """Download comparison data as CSV"""
    try:
        if dataset not in ['common_names', 'unique_jan', 'unique_apr']:
            return jsonify({'error': 'Invalid dataset'}), 400
        
        if format != 'csv':
            return jsonify({'error': 'Only CSV format is supported'}), 400
        
        logger.info(f"Downloading {dataset} as {format}")
        
        comparison = ComparisonAnalytics(DB_CONFIG)
        comparison.connect()
        
        try:
            import tempfile
            import os
            from flask import send_file
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='')
            
            if dataset == 'common_names':
                filter_top80 = request.args.get('filter_top80', None)
                comparison.export_common_names_to_csv('clients_2025', temp_file.name, filter_top80)
                filename = 'common_names.csv'
            elif dataset == 'unique_jan':
                top80_only = request.args.get('top80_only', 'false').lower() == 'true'
                comparison.export_unique_jan_to_csv('clients_2025', temp_file.name, top80_only)
                filename = 'unique_jan.csv'
            else:  # unique_apr
                top80_only = request.args.get('top80_only', 'false').lower() == 'true'
                comparison.export_unique_apr_to_csv('clients_2025', temp_file.name, top80_only)
                filename = 'unique_apr.csv'
            
            temp_file.close()
            
            return send_file(
                temp_file.name,
                mimetype='text/csv',
                as_attachment=True,
                download_name=filename
            )
            
        finally:
            comparison.disconnect()
            
    except Exception as e:
        logger.error(f"Error downloading comparison data: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
@app.route('/comparison/check')
def check_comparison_tables():
    """Check if comparison tables exist"""
    try:
        init_supabase()
        
        safe_table_name = 'clients_2025'.lower().replace(' ', '_').replace('-', '_')
        comparison_summary_table = f"{safe_table_name}_comparison_summary"
        
        with supabase_manager.conn.cursor() as cur:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                )
            """, (comparison_summary_table,))
            exists = cur.fetchone()[0]
        
        return jsonify({
            'success': True,
            'exists': exists
        })
    except Exception as e:
        logger.error(f"Error checking comparison tables: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)