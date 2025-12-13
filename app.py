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

from src import DataCleaner, SupabaseManager, ReportGenerator, DataAnalytics, DB_CONFIG

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


def process_and_clean_sheet_data(sheet_key, batch_size=100000, store_original=True):
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
    supabase_manager.create_table_if_not_exists('clients_2025', config['identifier'])
    if store_original:
        supabase_manager.create_original_table('clients_2025', config['identifier'])
    
    # Step 3: Clear existing data
    safe_table_name = 'clients_2025'.lower().replace(' ', '_').replace('-', '_')
    included_table = f"{safe_table_name}_{config['identifier']}_included"
    excluded_table = f"{safe_table_name}_{config['identifier']}_excluded"
    
    logger.info("Clearing existing data...")
    supabase_manager.clear_table(included_table)
    supabase_manager.clear_table(excluded_table)
    
    if store_original:
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
        original_batch = []
        
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
            
            # Store for original table if needed
            if store_original:
                original_batch.append({
                    'row_id': row_id,
                    'original_row_number': original_row_number,
                    'firstname': parsed_row['firstname'],
                    'birthday': parsed_row['birthday'],
                    'birthmonth': parsed_row['birthmonth'],
                    'birthyear': parsed_row['birthyear']
                })
        
        # Clean this batch
        clean_start = time.time()
        cleaner = DataCleaner()
        included_data, excluded_data = cleaner.clean_dataset(batch_with_ids)
        clean_time = time.time() - clean_start
        
        logger.info(f"Batch {batch_num + 1}: Cleaned in {clean_time:.1f}s - {len(included_data)} included, {len(excluded_data)} excluded")
        
        # Parallel inserts
        insert_start = time.time()
        
        with ThreadPoolExecutor(max_workers=1) as executor:
            futures = []
            
            # Submit included insert job
            if included_data:
                futures.append(
                    executor.submit(
                        supabase_manager.append_data,
                        included_table,
                        included_data
                    )
                )
            
            # Submit excluded insert job
            if excluded_data:
                futures.append(
                    executor.submit(
                        supabase_manager.append_data,
                        excluded_table,
                        excluded_data
                    )
                )
            
            # Submit original insert job (if enabled)
            if store_original and original_batch:
                futures.append(
                    executor.submit(
                        supabase_manager.append_data,
                        original_table,
                        original_batch
                    )
                )
            
            # Wait for all inserts to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Error in parallel insert: {e}")
                    raise
        
        insert_time = time.time() - insert_start
        
        # Update totals
        total_included += len(included_data)
        total_excluded += len(excluded_data)
        
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
    
    if table_type not in ['original', 'included', 'excluded']:
        return jsonify({"error": "Invalid table type"}), 400
    
    try:
        init_supabase()
        safe_table_name = 'clients_2025'.lower().replace(' ', '_').replace('-', '_')
        table_name = f"{safe_table_name}_{sheet['identifier']}_{table_type}"
        
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
            sort_order
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
        return jsonify({
            "success": True,
            "sheet_key": sheet_key,
            "exists": result['exists'],
            "counts": result['counts']
        })
    except Exception as e:
        logger.error(f"Error checking tables for {sheet_key}: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route("/download/<sheet_key>/<table_type>/<format>")
def download_table(sheet_key, table_type, format):
    """Download table data as CSV or PDF"""
    sheet = SHEETS_CONFIG.get(sheet_key)
    if not sheet:
        return jsonify({"error": "Invalid sheet key"}), 400
    
    if table_type not in ['included', 'excluded', 'original']:
        return jsonify({"error": "Invalid table type"}), 400
    
    if format not in ['csv', 'pdf']:
        return jsonify({"error": "Invalid format"}), 400
    
    try:
        init_supabase()
        safe_table_name = 'clients_2025'.lower().replace(' ', '_').replace('-', '_')
        table_name = f"{safe_table_name}_{sheet['identifier']}_{table_type}"
        
        # Fetch ALL data (no pagination)
        with supabase_manager.conn.cursor() as cur:
            cur.execute(f"SELECT * FROM {table_name} ORDER BY original_row_number ASC")
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
        
        if format == 'csv':
            return report_generator.generate_csv(sheet, table_type, columns, rows)
        else:
            return report_generator.generate_pdf(sheet, table_type, columns, rows)
            
    except Exception as e:
        logger.error(f"Error downloading table: {e}")
        return jsonify({"error": str(e)}), 500
    
    
#Analytics section 
@app.route('/analytics/<sheet_key>/summary')
def get_analytics_summary(sheet_key):
    """Get summary statistics for a sheet"""
    try:
        # Get the sheet configuration
        sheet = SHEETS_CONFIG.get(sheet_key)
        if not sheet:
            return jsonify({'error': 'Invalid sheet key'}), 404
        
        # Construct the table name
        safe_table_name = 'clients_2025'.lower().replace(' ', '_').replace('-', '_')
        included_table = f"{safe_table_name}_{sheet['identifier']}_included"
        
        logger.info(f"Getting analytics for table: {included_table}")
        
        # Initialize analytics
        analytics = DataAnalytics(DB_CONFIG)
        analytics.connect()
        
        try:
            # Get all summary statistics - pass the table name instead of sheet_id
            summary_data = {
                'unique_names': analytics.get_total_unique_names(included_table),
                'unique_birthdays': analytics.get_unique_birthday_combinations(included_table),
                'unique_name_year': analytics.get_unique_name_year_combinations(included_table),
                'unique_name_month': analytics.get_unique_name_month_combinations(included_table),
                'unique_name_day': analytics.get_unique_name_day_combinations(included_table)
            }
            
            logger.info(f"Analytics summary generated for {sheet_key}: {summary_data}")
            return jsonify(summary_data)
            
        finally:
            analytics.disconnect()
            
    except Exception as e:
        logger.error(f"Error generating analytics summary: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)