import os
import logging
import time
import uuid
from typing import List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from dotenv import load_dotenv
import csv
import io

# ---------------------------
# Logging setup
# ---------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ---------------------------
# Load environment variables
# ---------------------------
load_dotenv()

DB_CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT', '6543'),
    'dbname': os.getenv('DB_NAME', 'postgres'),
    'sslmode': 'require'
}

print(f"🔍 DEBUG: Connecting to {os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}")

# ---------------------------
# PostgreSQL Helper Class
# ---------------------------
class SupabaseManager:
    def __init__(self):
        self.conn = None
        self.connect()

    def connect(self):
        """Establish a PostgreSQL connection."""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.conn.autocommit = True
            logger.info("✅ Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            raise

    def execute_sql(self, sql: str, params=None):
        """Execute raw SQL."""
        try:
            with self.conn.cursor() as cur:
                if params:
                    cur.execute(sql, params)
                else:
                    cur.execute(sql)
            logger.info("✅ Executed SQL successfully")
        except Exception as e:
            logger.error(f"❌ Error executing SQL: {e}\nSQL: {sql}")
            raise

    # ---------------------------
    # Table Creation
    # ---------------------------

    def create_original_table(self, table_name: str, sheet_identifier: str):
        """Create table for data."""
        safe_table_name = table_name.lower().replace(' ', '_').replace('-', '_')
        original_table = f"{safe_table_name}_{sheet_identifier}_original"

        original_sql = f"""
        CREATE TABLE IF NOT EXISTS {original_table} (
            row_id UUID PRIMARY KEY,
            original_row_number INTEGER NOT NULL,
            firstname TEXT,
            birthday TEXT,
            birthmonth TEXT,
            birthyear TEXT,
            exclusion_reason TEXT,
            status TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_{original_table}_row_number ON {original_table}(row_id);
        CREATE INDEX IF NOT EXISTS idx_{original_table}_original_row_number ON {original_table}(original_row_number);
        CREATE INDEX IF NOT EXISTS idx_{original_table}_firstname ON {original_table}(firstname);
        CREATE INDEX IF NOT EXISTS idx_{original_table}_birthday ON {original_table}(birthday);
        CREATE INDEX IF NOT EXISTS idx_{original_table}_birthmonth ON {original_table}(birthmonth);
        CREATE INDEX IF NOT EXISTS idx_{original_table}_birthyear ON {original_table}(birthyear);
        CREATE INDEX IF NOT EXISTS idx_{original_table}_status ON {original_table}(status);
        """

        logger.info(f"Creating original table: {original_table}")
        self.execute_sql(original_sql)

    # ---------------------------
    # Table Operations
    # ---------------------------
    def clear_table(self, table_name: str):
        """Clear all data from a table."""
        try:
            sql = f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE"
            self.execute_sql(sql)
            logger.info(f"✅ Cleared table: {table_name}")
        except Exception as e:
            logger.error(f"❌ Error clearing table {table_name}: {e}")
            raise

    # ---------------------------
    # Batch Insert Helpers
    # ---------------------------
    def append_data(self, table_name: str, rows: List[Dict[str, Any]]):
        """Insert data into a table using batch insert."""
        if not rows:
            logger.info(f"No rows to insert into {table_name}")
            return

        try:
            keys = rows[0].keys()
            columns = ', '.join(keys)
            
            buffer = io.StringIO()
            writer = csv.writer(buffer, quoting=csv.QUOTE_ALL)
            
            for row in rows:
               writer.writerow([row[k] for k in keys])
               
            buffer.seek(0)

            # Use COPY command with proper encoding
            with self.conn.cursor() as cur:
                cur.copy_expert(
                    f"COPY {table_name} ({columns}) FROM STDIN WITH (FORMAT CSV, ENCODING 'UTF8', QUOTE '\"')",
                    buffer
                )
                
            logger.info(f"✅ Inserted {len(rows)} rows into {table_name}")
                
        except Exception as e:
            logger.error(f"❌ Error inserting into {table_name}: {e}")
            raise

    # ---------------------------
    # Data Retrieval
    # ---------------------------
    def get_table_data(self, table_name: str, page: int = 1, per_page: int = 100, 
                       sort_by: str = 'original_row_number', sort_order: str = 'asc', status_filter: str = None) -> Tuple[List[Dict], int]:
        """
        Get paginated data from a table with sorting.
        
        Args:
            table_name: Name of the table
            page: Page number (1-indexed)
            per_page: Number of records per page
            sort_by: Column to sort by
            sort_order: 'asc' or 'desc'
        
        Returns:
            Tuple of (data_list, total_count)
        """
        try:
            # Validate sort order
            if sort_order.lower() not in ['asc', 'desc']:
                sort_order = 'asc'
            
            # Calculate offset
            offset = (page - 1) * per_page
            
            # Get total count
            with self.conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                total_count = cur.fetchone()[0]
            
            # Get paginated data
            sql = f"""
                SELECT * FROM {table_name}
                ORDER BY {sort_by} {sort_order}
                LIMIT %s OFFSET %s
            """
            
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (per_page, offset))
                rows = cur.fetchall()
                
                # Convert to list of dicts and handle any datetime serialization
                data = []
                for row in rows:
                    row_dict = dict(row)
                    # Convert UUID to string if present
                    if 'row_id' in row_dict and row_dict['row_id']:
                        row_dict['row_id'] = str(row_dict['row_id'])
                    # Convert datetime to ISO string if present
                    if 'created_at' in row_dict and row_dict['created_at']:
                        row_dict['created_at'] = row_dict['created_at'].isoformat()
                    data.append(row_dict)
            
            logger.info(f"Retrieved {len(data)} rows from {table_name} (page {page})")
            return data, total_count
            
        except Exception as e:
            logger.error(f"❌ Error retrieving data from {table_name}: {e}")
            raise


    # =========================
    # COUNT METHODS
    # =========================
    def count_records(self, table_name: str) -> int:
        """Count total records in a table"""
        try:
            with self.conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cur.fetchone()[0]
                return count
        except Exception as e:
            logger.error(f"Error counting records in {table_name}: {e}")
            return 0
        
        
    def check_tables_exist(self, table_name: str, sheet_identifier: str) -> Dict[str, Any]:
        """Check if tables exist and return row counts"""
        try:
            safe_table_name = table_name.lower().replace(' ', '_').replace('-', '_')
            original_table = f"{safe_table_name}_{sheet_identifier}_original"
        
            result = {
                'exists': False,
                'counts': {
                    'original': 0,
                    'included': 0,   
                    'excluded': 0
                }
            }
            
            # Check if tables exist and get counts
            with self.conn.cursor() as cur:
            
                # Check original table
                cur.execute(f"""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name = '{original_table}'
                """)
                
                table_exists = cur.fetchone()[0]
                logger.info(f"🔍 Table exists query returned: {table_exists}")
                
                if table_exists > 0:  # ✅ CORRECT - use the variable
                    result['exists'] = True  # ADD THIS LINE TOO!
                    
                    cur.execute(f"SELECT COUNT(*) FROM {original_table}")
                    result['counts']['original'] = cur.fetchone()[0]
                    
                    # Get included count
                    cur.execute(f"SELECT COUNT(*) FROM {original_table} WHERE status = 'included'")
                    result['counts']['included'] = cur.fetchone()[0]
                    
                    # Get excluded count
                    cur.execute(f"SELECT COUNT(*) FROM {original_table} WHERE status = 'excluded'")
                    result['counts']['excluded'] = cur.fetchone()[0]
        
            return result
        
        except Exception as e:
            logger.error(f"Error checking tables: {e}")
            return {'exists': False, 'counts': {'original': 0, 'included': 0, 'excluded': 0}}