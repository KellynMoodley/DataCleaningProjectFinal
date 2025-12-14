import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from dotenv import load_dotenv
import os
import logging
from typing import List, Dict, Any, Tuple, Optional
import csv

# ---------------------------
# Logging setup
# ---------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

DB_CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT', '6543'),
    'dbname': os.getenv('DB_NAME', 'postgres'),
    'sslmode': 'require'
}


class ComparisonAnalytics:
    """
    Analytics class for comparing JAN and APR birth data datasets.
    Creates comparison tables and provides methods to retrieve comparison data.
    """
    
    def __init__(self, db_config):
        """
        Initialize comparison analytics with database configuration.
        
        Args:
            db_config: Dictionary with keys: host, database, user, password, port
        """
        self.db_config = db_config
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            logger.info("✓ Database connection established")
        except Exception as e:
            logger.error(f"✗ Database connection failed: {e}")
            raise
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            logger.info("✓ Database connection closed")
    
    def execute_sql(self, query, params=None):
        """Execute SQL query with error handling"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"SQL execution failed: {e}")
            raise
    
    def _verify_tables_exist(self, table_names: List[str]):
        """Verify all required tables exist before comparison"""
        for table in table_names:
            query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                )
            """
            with self.connection.cursor() as cur:
                cur.execute(query, (table,))
                exists = cur.fetchone()[0]
                if not exists:
                    raise ValueError(f"Required table not found: {table}")
                logger.info(f"✓ Verified table exists: {table}")
    
    def create_comparison_analytics(self, 
                                   table_name: str,
                                   jan_identifier: str = "jan",
                                   apr_identifier: str = "apr"):
        """
        Create all comparison analytics tables for JAN vs APR comparison
        
        Args:
            table_name: Base table name (e.g., "birth_data")
            jan_identifier: Sheet identifier for JAN data (default: "jan")
            apr_identifier: Sheet identifier for APR data (default: "apr")
        """
        safe_table = table_name.lower().replace(' ', '_').replace('-', '_')
        
        # Source tables
        jan_original = f"{safe_table}_{jan_identifier}_original"
        jan_common = f"{safe_table}_{jan_identifier}_common_names"
        
        apr_original = f"{safe_table}_{apr_identifier}_original"
        apr_common = f"{safe_table}_{apr_identifier}_common_names"
        
        logger.info("=" * 80)
        logger.info("CREATING COMPARISON ANALYTICS")
        logger.info("=" * 80)
        
        # Increase statement timeout for large datasets (10 minutes)
        logger.info("Setting statement timeout to 10 minutes...")
        self.execute_sql("SET statement_timeout = '600000'")  # 10 minutes in milliseconds
        
        # Verify tables exist
        logger.info("Verifying required tables exist...")
        self._verify_tables_exist([jan_original, jan_common, apr_original, apr_common])
        
        # Create comparison tables
        self._create_common_names_table(safe_table, jan_original, apr_original, 
                                       jan_common, apr_common)
        self._create_unique_jan_table(safe_table, jan_original, apr_original, jan_common)
        self._create_unique_apr_table(safe_table, jan_original, apr_original, apr_common)
        self._create_comparison_summary_table(safe_table, jan_original, apr_original,
                                             jan_common, apr_common)
        
        # Create indexes
        self._create_comparison_indexes(safe_table)
        
        # Reset statement timeout to default
        self.execute_sql("SET statement_timeout = DEFAULT")
        
        logger.info("=" * 80)
        logger.info("✅ COMPARISON ANALYTICS COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
    
    def _create_common_names_table(self, safe_table: str, 
                                   jan_original: str, apr_original: str,
                                   jan_common: str, apr_common: str):
        """Create table of names appearing in both JAN and APR"""
        comparison_table = f"{safe_table}_comparison_common_names"
        
        logger.info(f"Creating common names comparison table: {comparison_table}")
        
        # Drop existing table
        self.execute_sql(f"DROP TABLE IF EXISTS {comparison_table}")
        
        # Step 1: Create temp tables for distinct names from each dataset
        logger.info("Step 1/5: Creating temp tables for distinct names...")
        self.execute_sql(f"""
            CREATE TEMP TABLE temp_jan_distinct AS
            SELECT DISTINCT 
                LOWER(TRIM(firstname)) as firstname_normalized,
                firstname as firstname_original
            FROM {jan_original}
            WHERE status = 'included'
            AND firstname IS NOT NULL 
            AND firstname != ''
        """)
        self.execute_sql("CREATE INDEX idx_temp_jan_distinct ON temp_jan_distinct(firstname_normalized)")
        
        self.execute_sql(f"""
            CREATE TEMP TABLE temp_apr_distinct AS
            SELECT DISTINCT 
                LOWER(TRIM(firstname)) as firstname_normalized,
                firstname as firstname_original
            FROM {apr_original}
            WHERE status = 'included'
            AND firstname IS NOT NULL 
            AND firstname != ''
        """)
        self.execute_sql("CREATE INDEX idx_temp_apr_distinct ON temp_apr_distinct(firstname_normalized)")
        
        # Step 2: Find common names
        logger.info("Step 2/5: Finding common names...")
        self.execute_sql("""
            CREATE TEMP TABLE temp_common_names AS
            SELECT DISTINCT j.firstname_normalized
            FROM temp_jan_distinct j
            INNER JOIN temp_apr_distinct a ON j.firstname_normalized = a.firstname_normalized
        """)
        self.execute_sql("CREATE INDEX idx_temp_common ON temp_common_names(firstname_normalized)")
        
        # Step 3: Calculate frequencies for each dataset
        logger.info("Step 3/5: Calculating frequencies...")
        self.execute_sql(f"""
            CREATE TEMP TABLE temp_jan_freq AS
            SELECT 
                LOWER(TRIM(firstname)) as firstname_normalized,
                COUNT(*) as jan_frequency
            FROM {jan_original}
            WHERE status = 'included'
            AND firstname IS NOT NULL 
            AND firstname != ''
            GROUP BY LOWER(TRIM(firstname))
        """)
        self.execute_sql("CREATE INDEX idx_temp_jan_freq ON temp_jan_freq(firstname_normalized)")
        
        self.execute_sql(f"""
            CREATE TEMP TABLE temp_apr_freq AS
            SELECT 
                LOWER(TRIM(firstname)) as firstname_normalized,
                COUNT(*) as apr_frequency
            FROM {apr_original}
            WHERE status = 'included'
            AND firstname IS NOT NULL 
            AND firstname != ''
            GROUP BY LOWER(TRIM(firstname))
        """)
        self.execute_sql("CREATE INDEX idx_temp_apr_freq ON temp_apr_freq(firstname_normalized)")
        
        # Step 4: Get top 80% info from both datasets
        logger.info("Step 4/5: Getting top 80% information...")
        self.execute_sql(f"""
            CREATE TEMP TABLE temp_jan_top80 AS
            SELECT 
                LOWER(TRIM(firstname)) as firstname_normalized,
                rank as jan_rank,
                frequency as jan_top80_frequency
            FROM {jan_common}
        """)
        self.execute_sql("CREATE INDEX idx_temp_jan_top80 ON temp_jan_top80(firstname_normalized)")
        
        self.execute_sql(f"""
            CREATE TEMP TABLE temp_apr_top80 AS
            SELECT 
                LOWER(TRIM(firstname)) as firstname_normalized,
                rank as apr_rank,
                frequency as apr_top80_frequency
            FROM {apr_common}
        """)
        self.execute_sql("CREATE INDEX idx_temp_apr_top80 ON temp_apr_top80(firstname_normalized)")
        
        # Step 5: Create final comparison table
        logger.info("Step 5/5: Creating final comparison table...")
        self.execute_sql(f"""
            CREATE TABLE {comparison_table} AS
            SELECT 
                cn.firstname_normalized as firstname,
                COALESCE(jf.jan_frequency, 0) as jan_frequency,
                COALESCE(af.apr_frequency, 0) as apr_frequency,
                COALESCE(jf.jan_frequency, 0) + COALESCE(af.apr_frequency, 0) as total_frequency,
                CASE WHEN jt.jan_rank IS NOT NULL THEN true ELSE false END as in_jan_top80,
                CASE WHEN at.apr_rank IS NOT NULL THEN true ELSE false END as in_apr_top80,
                jt.jan_rank,
                at.apr_rank,
                NOW() as calculated_at
            FROM temp_common_names cn
            LEFT JOIN temp_jan_freq jf ON cn.firstname_normalized = jf.firstname_normalized
            LEFT JOIN temp_apr_freq af ON cn.firstname_normalized = af.firstname_normalized
            LEFT JOIN temp_jan_top80 jt ON cn.firstname_normalized = jt.firstname_normalized
            LEFT JOIN temp_apr_top80 at ON cn.firstname_normalized = at.firstname_normalized
            ORDER BY total_frequency DESC, firstname
        """)
        
        # Clean up temp tables
        logger.info("Cleaning up temporary tables...")
        self.execute_sql("DROP TABLE IF EXISTS temp_jan_distinct")
        self.execute_sql("DROP TABLE IF EXISTS temp_apr_distinct")
        self.execute_sql("DROP TABLE IF EXISTS temp_common_names")
        self.execute_sql("DROP TABLE IF EXISTS temp_jan_freq")
        self.execute_sql("DROP TABLE IF EXISTS temp_apr_freq")
        self.execute_sql("DROP TABLE IF EXISTS temp_jan_top80")
        self.execute_sql("DROP TABLE IF EXISTS temp_apr_top80")
        
        logger.info(f"✅ Created common names table: {comparison_table}")
    
    def _create_unique_jan_table(self, safe_table: str, 
                                jan_original: str, apr_original: str,
                                jan_common: str):
        """Create table of names unique to JAN (not in APR)"""
        comparison_table = f"{safe_table}_comparison_unique_jan"
        
        logger.info(f"Creating unique JAN names table: {comparison_table}")
        
        # Drop existing table
        self.execute_sql(f"DROP TABLE IF EXISTS {comparison_table}")
        
        # Step 1: Create temp table with distinct JAN names
        logger.info("Step 1/4: Creating temp table with distinct JAN names...")
        self.execute_sql(f"""
            CREATE TEMP TABLE temp_jan_names AS
            SELECT DISTINCT LOWER(TRIM(firstname)) as firstname_normalized
            FROM {jan_original}
            WHERE status = 'included'
            AND firstname IS NOT NULL 
            AND firstname != ''
        """)
        self.execute_sql("CREATE INDEX idx_temp_jan_names ON temp_jan_names(firstname_normalized)")
        
        # Step 2: Create temp table with distinct APR names
        logger.info("Step 2/4: Creating temp table with distinct APR names...")
        self.execute_sql(f"""
            CREATE TEMP TABLE temp_apr_names AS
            SELECT DISTINCT LOWER(TRIM(firstname)) as firstname_normalized
            FROM {apr_original}
            WHERE status = 'included'
            AND firstname IS NOT NULL 
            AND firstname != ''
        """)
        self.execute_sql("CREATE INDEX idx_temp_apr_names ON temp_apr_names(firstname_normalized)")
        
        # Step 3: Create temp table with unique JAN names (not in APR)
        logger.info("Step 3/4: Finding names unique to JAN...")
        self.execute_sql("""
            CREATE TEMP TABLE temp_unique_jan_names AS
            SELECT j.firstname_normalized
            FROM temp_jan_names j
            LEFT JOIN temp_apr_names a ON j.firstname_normalized = a.firstname_normalized
            WHERE a.firstname_normalized IS NULL
        """)
        self.execute_sql("CREATE INDEX idx_temp_unique_jan ON temp_unique_jan_names(firstname_normalized)")
        
        # Step 4: Create final table with all JAN records for unique names
        logger.info("Step 4/4: Creating final unique JAN table with all records...")
        self.execute_sql(f"""
            CREATE TABLE {comparison_table} AS
            SELECT 
                jo.row_id,
                jo.original_row_number,
                jo.firstname,
                jo.birthyear,
                jo.birthmonth,
                jo.birthday,
                LOWER(TRIM(jo.firstname)) as firstname_normalized,
                CASE WHEN jc.rank IS NOT NULL THEN true ELSE false END as in_jan_top80,
                jc.rank as jan_rank,
                NOW() as calculated_at
            FROM {jan_original} jo
            INNER JOIN temp_unique_jan_names ujn 
                ON LOWER(TRIM(jo.firstname)) = ujn.firstname_normalized
            LEFT JOIN {jan_common} jc 
                ON LOWER(TRIM(jc.firstname)) = LOWER(TRIM(jo.firstname))
            WHERE jo.status = 'included'
            AND jo.firstname IS NOT NULL 
            AND jo.firstname != ''
            ORDER BY jo.original_row_number
        """)
        
        # Clean up temp tables
        self.execute_sql("DROP TABLE IF EXISTS temp_jan_names")
        self.execute_sql("DROP TABLE IF EXISTS temp_apr_names")
        self.execute_sql("DROP TABLE IF EXISTS temp_unique_jan_names")
        
        logger.info(f"✅ Created unique JAN names table: {comparison_table}")
    
    def _create_unique_apr_table(self, safe_table: str, 
                                jan_original: str, apr_original: str,
                                apr_common: str):
        """Create table of names unique to APR (not in JAN)"""
        comparison_table = f"{safe_table}_comparison_unique_apr"
        
        logger.info(f"Creating unique APR names table: {comparison_table}")
        
        # Drop existing table
        self.execute_sql(f"DROP TABLE IF EXISTS {comparison_table}")
        
        # Step 1: Create temp table with distinct JAN names (reuse if exists)
        logger.info("Step 1/4: Creating temp table with distinct JAN names...")
        self.execute_sql("DROP TABLE IF EXISTS temp_jan_names_apr")
        self.execute_sql(f"""
            CREATE TEMP TABLE temp_jan_names_apr AS
            SELECT DISTINCT LOWER(TRIM(firstname)) as firstname_normalized
            FROM {jan_original}
            WHERE status = 'included'
            AND firstname IS NOT NULL 
            AND firstname != ''
        """)
        self.execute_sql("CREATE INDEX idx_temp_jan_names_apr ON temp_jan_names_apr(firstname_normalized)")
        
        # Step 2: Create temp table with distinct APR names
        logger.info("Step 2/4: Creating temp table with distinct APR names...")
        self.execute_sql("DROP TABLE IF EXISTS temp_apr_names_unique")
        self.execute_sql(f"""
            CREATE TEMP TABLE temp_apr_names_unique AS
            SELECT DISTINCT LOWER(TRIM(firstname)) as firstname_normalized
            FROM {apr_original}
            WHERE status = 'included'
            AND firstname IS NOT NULL 
            AND firstname != ''
        """)
        self.execute_sql("CREATE INDEX idx_temp_apr_names_unique ON temp_apr_names_unique(firstname_normalized)")
        
        # Step 3: Create temp table with unique APR names (not in JAN)
        logger.info("Step 3/4: Finding names unique to APR...")
        self.execute_sql("""
            CREATE TEMP TABLE temp_unique_apr_names AS
            SELECT a.firstname_normalized
            FROM temp_apr_names_unique a
            LEFT JOIN temp_jan_names_apr j ON a.firstname_normalized = j.firstname_normalized
            WHERE j.firstname_normalized IS NULL
        """)
        self.execute_sql("CREATE INDEX idx_temp_unique_apr ON temp_unique_apr_names(firstname_normalized)")
        
        # Step 4: Create final table with all APR records for unique names
        logger.info("Step 4/4: Creating final unique APR table with all records...")
        self.execute_sql(f"""
            CREATE TABLE {comparison_table} AS
            SELECT 
                ao.row_id,
                ao.original_row_number,
                ao.firstname,
                ao.birthyear,
                ao.birthmonth,
                ao.birthday,
                LOWER(TRIM(ao.firstname)) as firstname_normalized,
                CASE WHEN ac.rank IS NOT NULL THEN true ELSE false END as in_apr_top80,
                ac.rank as apr_rank,
                NOW() as calculated_at
            FROM {apr_original} ao
            INNER JOIN temp_unique_apr_names uan 
                ON LOWER(TRIM(ao.firstname)) = uan.firstname_normalized
            LEFT JOIN {apr_common} ac 
                ON LOWER(TRIM(ac.firstname)) = LOWER(TRIM(ao.firstname))
            WHERE ao.status = 'included'
            AND ao.firstname IS NOT NULL 
            AND ao.firstname != ''
            ORDER BY ao.original_row_number
        """)
        
        # Clean up temp tables
        self.execute_sql("DROP TABLE IF EXISTS temp_jan_names_apr")
        self.execute_sql("DROP TABLE IF EXISTS temp_apr_names_unique")
        self.execute_sql("DROP TABLE IF EXISTS temp_unique_apr_names")
        
        logger.info(f"✅ Created unique APR names table: {comparison_table}")
    
    def _create_comparison_summary_table(self, safe_table: str,
                                        jan_original: str, apr_original: str,
                                        jan_common: str, apr_common: str):
        """Create summary table with all comparison metrics"""
        summary_table = f"{safe_table}_comparison_summary"
        
        logger.info(f"Creating comparison summary table: {summary_table}")
        
        # Drop existing table
        self.execute_sql(f"DROP TABLE IF EXISTS {summary_table}")
        
    
        """ Create comprehensive summary table
        Includes:
          - JAN/APR total records and unique names
          - Top 80% frequent names
          - Unique names in each month
          - Overlaps between months and top 80%"""
          
        create_query = f"""
        CREATE TABLE {summary_table} AS
        WITH jan_included AS (
            SELECT DISTINCT LOWER(TRIM(firstname)) as firstname_normalized
            FROM {jan_original}
            WHERE status = 'included'
            AND firstname IS NOT NULL 
            AND firstname != ''
        ),
        apr_included AS (
            SELECT DISTINCT LOWER(TRIM(firstname)) as firstname_normalized
            FROM {apr_original}
            WHERE status = 'included'
            AND firstname IS NOT NULL 
            AND firstname != ''
        ),
        jan_top80 AS (
            SELECT DISTINCT LOWER(TRIM(firstname)) as firstname_normalized
            FROM {jan_common}
        ),
        apr_top80 AS (
            SELECT DISTINCT LOWER(TRIM(firstname)) as firstname_normalized
            FROM {apr_common}
        ),
        common_names AS (
            SELECT j.firstname_normalized
            FROM jan_included j
            INNER JOIN apr_included a ON j.firstname_normalized = a.firstname_normalized
        ),
        unique_jan AS (
            SELECT j.firstname_normalized
            FROM jan_included j
            LEFT JOIN apr_included a ON j.firstname_normalized = a.firstname_normalized
            WHERE a.firstname_normalized IS NULL
        ),
        unique_apr AS (
            SELECT a.firstname_normalized
            FROM apr_included a
            LEFT JOIN jan_included j ON a.firstname_normalized = j.firstname_normalized
            WHERE j.firstname_normalized IS NULL
        ),
        jan_top80_in_apr AS (
            SELECT jt.firstname_normalized
            FROM jan_top80 jt
            INNER JOIN apr_included a ON jt.firstname_normalized = a.firstname_normalized
        ),
        apr_top80_in_jan AS (
            SELECT at.firstname_normalized
            FROM apr_top80 at
            INNER JOIN jan_included j ON at.firstname_normalized = j.firstname_normalized
        ),
        both_top80 AS (
            SELECT jt.firstname_normalized
            FROM jan_top80 jt
            INNER JOIN apr_top80 at ON jt.firstname_normalized = at.firstname_normalized
        ),
        jan_stats AS (
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT LOWER(TRIM(firstname))) as unique_names
            FROM {jan_original}
            WHERE status = 'included'
            AND firstname IS NOT NULL 
            AND firstname != ''
        ),
        apr_stats AS (
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT LOWER(TRIM(firstname))) as unique_names
            FROM {apr_original}
            WHERE status = 'included'
            AND firstname IS NOT NULL 
            AND firstname != ''
        )
        SELECT 
            -- JAN statistics
            (SELECT total_records FROM jan_stats) as jan_total_records,
            (SELECT unique_names FROM jan_stats) as jan_unique_names,
            (SELECT COUNT(*) FROM jan_top80) as jan_top80_count,
            
            -- APR statistics
            (SELECT total_records FROM apr_stats) as apr_total_records,
            (SELECT unique_names FROM apr_stats) as apr_unique_names,
            (SELECT COUNT(*) FROM apr_top80) as apr_top80_count,
            
            -- Common names (in both datasets)
            (SELECT COUNT(*) FROM common_names) as common_names_count,
            
            -- Unique names
            (SELECT COUNT(*) FROM unique_jan) as unique_jan_names_count,
            (SELECT COUNT(*) FROM unique_apr) as unique_apr_names_count,
            
            -- Top 80% overlaps
            (SELECT COUNT(*) FROM jan_top80_in_apr) as jan_top80_in_apr_count,
            (SELECT COUNT(*) FROM apr_top80_in_jan) as apr_top80_in_jan_count,
            (SELECT COUNT(*) FROM both_top80) as both_top80_count,
            
            -- Percentages
            ROUND((SELECT COUNT(*)::numeric FROM common_names) / NULLIF((SELECT unique_names FROM jan_stats), 0) * 100, 2) as common_names_pct_of_jan,
            ROUND((SELECT COUNT(*)::numeric FROM common_names) / NULLIF((SELECT unique_names FROM apr_stats), 0) * 100, 2) as common_names_pct_of_apr,
            ROUND((SELECT COUNT(*)::numeric FROM jan_top80_in_apr) / NULLIF((SELECT COUNT(*) FROM jan_top80), 0) * 100, 2) as jan_top80_in_apr_pct,
            ROUND((SELECT COUNT(*)::numeric FROM apr_top80_in_jan) / NULLIF((SELECT COUNT(*) FROM apr_top80), 0) * 100, 2) as apr_top80_in_jan_pct,
            
            -- Metadata
            NOW() as calculated_at;
        """
        
        self.execute_sql(create_query)
        logger.info(f"✅ Created comparison summary table: {summary_table}")
    
    def _create_comparison_indexes(self, safe_table: str):
        """Create indexes on comparison tables for faster queries"""
        logger.info("Creating indexes on comparison tables...")
        
        indexes = [
            # Common names indexes
            f"CREATE INDEX IF NOT EXISTS idx_{safe_table}_comparison_common_firstname ON {safe_table}_comparison_common_names(firstname)",
            f"CREATE INDEX IF NOT EXISTS idx_{safe_table}_comparison_common_jan_freq ON {safe_table}_comparison_common_names(jan_frequency DESC)",
            f"CREATE INDEX IF NOT EXISTS idx_{safe_table}_comparison_common_apr_freq ON {safe_table}_comparison_common_names(apr_frequency DESC)",
            f"CREATE INDEX IF NOT EXISTS idx_{safe_table}_comparison_common_total_freq ON {safe_table}_comparison_common_names(total_frequency DESC)",
            f"CREATE INDEX IF NOT EXISTS idx_{safe_table}_comparison_common_jan_top80 ON {safe_table}_comparison_common_names(in_jan_top80)",
            f"CREATE INDEX IF NOT EXISTS idx_{safe_table}_comparison_common_apr_top80 ON {safe_table}_comparison_common_names(in_apr_top80)",
            
            # Unique JAN indexes
            f"CREATE INDEX IF NOT EXISTS idx_{safe_table}_comparison_unique_jan_firstname ON {safe_table}_comparison_unique_jan(firstname_normalized)",
            f"CREATE INDEX IF NOT EXISTS idx_{safe_table}_comparison_unique_jan_top80 ON {safe_table}_comparison_unique_jan(in_jan_top80)",
            f"CREATE INDEX IF NOT EXISTS idx_{safe_table}_comparison_unique_jan_row ON {safe_table}_comparison_unique_jan(original_row_number)",
            
            # Unique APR indexes
            f"CREATE INDEX IF NOT EXISTS idx_{safe_table}_comparison_unique_apr_firstname ON {safe_table}_comparison_unique_apr(firstname_normalized)",
            f"CREATE INDEX IF NOT EXISTS idx_{safe_table}_comparison_unique_apr_top80 ON {safe_table}_comparison_unique_apr(in_apr_top80)",
            f"CREATE INDEX IF NOT EXISTS idx_{safe_table}_comparison_unique_apr_row ON {safe_table}_comparison_unique_apr(original_row_number)",
        ]
        
        for idx_query in indexes:
            try:
                self.execute_sql(idx_query)
            except Exception as e:
                logger.warning(f"Index creation skipped or failed: {e}")
        
        logger.info("✅ All comparison indexes created successfully")
    
    # ==================== RETRIEVAL METHODS ====================
    
    def get_comparison_summary(self, table_name: str) -> Dict[str, Any]:
        """Get high-level comparison summary metrics"""
        safe_table = table_name.lower().replace(' ', '_').replace('-', '_')
        summary_table = f"{safe_table}_comparison_summary"
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"SELECT * FROM {summary_table}")
                result = cur.fetchone()
                
                if result:
                    data = dict(result)
                    # Convert datetime to ISO string
                    if 'calculated_at' in data and data['calculated_at']:
                        data['calculated_at'] = data['calculated_at'].isoformat()
                    return data
                return {}
        except Exception as e:
            logger.error(f"❌ Error retrieving comparison summary: {e}")
            raise
    
    def get_common_names(self, table_name: str, 
                        page: int = 1, 
                        per_page: int = 50,
                        filter_top80_only: Optional[str] = None) -> Tuple[List[Dict], int]:
        """
        Get common names (appearing in both JAN and APR)
        
        Args:
            table_name: Base table name
            page: Page number (1-indexed)
            per_page: Records per page
            filter_top80_only: Filter by top 80% - 'jan', 'apr', 'both', or None
        """
        safe_table = table_name.lower().replace(' ', '_').replace('-', '_')
        common_table = f"{safe_table}_comparison_common_names"
        
        try:
            offset = (page - 1) * per_page
            
            # Build WHERE clause
            where_clause = ""
            if filter_top80_only == 'jan':
                where_clause = "WHERE in_jan_top80 = true"
            elif filter_top80_only == 'apr':
                where_clause = "WHERE in_apr_top80 = true"
            elif filter_top80_only == 'both':
                where_clause = "WHERE in_jan_top80 = true AND in_apr_top80 = true"
            
            # Get total count
            with self.connection.cursor() as cur:
                count_query = f"SELECT COUNT(*) FROM {common_table} {where_clause}"
                cur.execute(count_query)
                total_count = cur.fetchone()[0]
            
            # Get paginated data
            with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
                query = f"""
                    SELECT * FROM {common_table}
                    {where_clause}
                    ORDER BY total_frequency DESC, firstname
                    LIMIT %s OFFSET %s
                """
                cur.execute(query, (per_page, offset))
                rows = cur.fetchall()
                
            # Convert datetime fields
            results = []
            for row in rows:
                data = dict(row)
                if 'calculated_at' in data and data['calculated_at']:
                    data['calculated_at'] = data['calculated_at'].isoformat()
                results.append(data)
            
            return results, total_count
        except Exception as e:
            logger.error(f"❌ Error retrieving common names: {e}")
            raise
    
    def get_unique_jan_names(self, table_name: str,
                            page: int = 1,
                            per_page: int = 50,
                            top80_only: bool = False) -> Tuple[List[Dict], int]:
        """
        Get names unique to JAN (not in APR)
        
        Args:
            table_name: Base table name
            page: Page number (1-indexed)
            per_page: Records per page
            top80_only: If True, only return names in JAN's top 80%
        """
        safe_table = table_name.lower().replace(' ', '_').replace('-', '_')
        unique_table = f"{safe_table}_comparison_unique_jan"
        
        try:
            offset = (page - 1) * per_page
            
            where_clause = "WHERE in_jan_top80 = true" if top80_only else ""
            
            # Get total count
            with self.connection.cursor() as cur:
                count_query = f"SELECT COUNT(*) FROM {unique_table} {where_clause}"
                cur.execute(count_query)
                total_count = cur.fetchone()[0]
            
            # Get paginated data
            with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
                query = f"""
                    SELECT * FROM {unique_table}
                    {where_clause}
                    ORDER BY original_row_number
                    LIMIT %s OFFSET %s
                """
                cur.execute(query, (per_page, offset))
                rows = cur.fetchall()
            
            # Convert datetime and UUID fields
            results = []
            for row in rows:
                data = dict(row)
                if 'calculated_at' in data and data['calculated_at']:
                    data['calculated_at'] = data['calculated_at'].isoformat()
                if 'row_id' in data and data['row_id']:
                    data['row_id'] = str(data['row_id'])
                results.append(data)
            
            return results, total_count
        except Exception as e:
            logger.error(f"❌ Error retrieving unique JAN names: {e}")
            raise
    
    def get_unique_apr_names(self, table_name: str,
                            page: int = 1,
                            per_page: int = 50,
                            top80_only: bool = False) -> Tuple[List[Dict], int]:
        """
        Get names unique to APR (not in JAN)
        
        Args:
            table_name: Base table name
            page: Page number (1-indexed)
            per_page: Records per page
            top80_only: If True, only return names in APR's top 80%
        """
        safe_table = table_name.lower().replace(' ', '_').replace('-', '_')
        unique_table = f"{safe_table}_comparison_unique_apr"
        
        try:
            offset = (page - 1) * per_page
            
            where_clause = "WHERE in_apr_top80 = true" if top80_only else ""
            
            # Get total count
            with self.connection.cursor() as cur:
                count_query = f"SELECT COUNT(*) FROM {unique_table} {where_clause}"
                cur.execute(count_query)
                total_count = cur.fetchone()[0]
            
            # Get paginated data
            with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
                query = f"""
                    SELECT * FROM {unique_table}
                    {where_clause}
                    ORDER BY original_row_number
                    LIMIT %s OFFSET %s
                """
                cur.execute(query, (per_page, offset))
                rows = cur.fetchall()
            
            # Convert datetime and UUID fields
            results = []
            for row in rows:
                data = dict(row)
                if 'calculated_at' in data and data['calculated_at']:
                    data['calculated_at'] = data['calculated_at'].isoformat()
                if 'row_id' in data and data['row_id']:
                    data['row_id'] = str(data['row_id'])
                results.append(data)
            
            return results, total_count
        except Exception as e:
            logger.error(f"❌ Error retrieving unique APR names: {e}")
            raise
    
    # ==================== EXPORT METHODS ====================
    
    def export_common_names_to_csv(self, table_name: str, output_path: str,
                                   filter_top80_only: Optional[str] = None) -> str:
        """
        Export common names to CSV file
        
        Args:
            table_name: Base table name
            output_path: Path where CSV file will be saved
            filter_top80_only: Filter by top 80% - 'jan', 'apr', 'both', or None
        
        Returns:
            Path to the created CSV file
        """
        safe_table = table_name.lower().replace(' ', '_').replace('-', '_')
        common_table = f"{safe_table}_comparison_common_names"
        
        try:
            # Build WHERE clause
            where_clause = ""
            if filter_top80_only == 'jan':
                where_clause = "WHERE in_jan_top80 = true"
            elif filter_top80_only == 'apr':
                where_clause = "WHERE in_apr_top80 = true"
            elif filter_top80_only == 'both':
                where_clause = "WHERE in_jan_top80 = true AND in_apr_top80 = true"
            
            with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
                query = f"""
                    SELECT 
                        firstname,
                        jan_frequency,
                        apr_frequency,
                        total_frequency,
                        in_jan_top80,
                        in_apr_top80,
                        jan_rank,
                        apr_rank
                    FROM {common_table}
                    {where_clause}
                    ORDER BY total_frequency DESC, firstname
                """
                cur.execute(query)
                rows = cur.fetchall()
            
            # Write to CSV
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                if rows:
                    fieldnames = rows[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for row in rows:
                        writer.writerow(dict(row))
            
            logger.info(f"✅ Exported {len(rows)} common names to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"❌ Error exporting common names to CSV: {e}")
            raise
    
    def export_unique_jan_to_csv(self, table_name: str, output_path: str,
                                top80_only: bool = False) -> str:
        """
        Export unique JAN names to CSV file
        
        Args:
            table_name: Base table name
            output_path: Path where CSV file will be saved
            top80_only: If True, only export names in JAN's top 80%
        
        Returns:
            Path to the created CSV file
        """
        safe_table = table_name.lower().replace(' ', '_').replace('-', '_')
        unique_table = f"{safe_table}_comparison_unique_jan"
        
        try:
            where_clause = "WHERE in_jan_top80 = true" if top80_only else ""
            
            with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
                query = f"""
                    SELECT 
                        original_row_number,
                        firstname,
                        birthyear,
                        birthmonth,
                        birthday,
                        in_jan_top80,
                        jan_rank
                    FROM {unique_table}
                    {where_clause}
                    ORDER BY original_row_number
                """
                cur.execute(query)
                rows = cur.fetchall()
            
            # Write to CSV
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                if rows:
                    fieldnames = rows[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for row in rows:
                        writer.writerow(dict(row))
            
            logger.info(f"✅ Exported {len(rows)} unique JAN names to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"❌ Error exporting unique JAN names to CSV: {e}")
            raise
    
    def export_unique_apr_to_csv(self, table_name: str, output_path: str,
                                top80_only: bool = False) -> str:
        """
        Export unique APR names to CSV file
        
        Args:
            table_name: Base table name
            output_path: Path where CSV file will be saved
            top80_only: If True, only export names in APR's top 80%
        
        Returns:
            Path to the created CSV file
        """
        safe_table = table_name.lower().replace(' ', '_').replace('-', '_')
        unique_table = f"{safe_table}_comparison_unique_apr"
        
        try:
            where_clause = "WHERE in_apr_top80 = true" if top80_only else ""
            
            with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
                query = f"""
                    SELECT 
                        original_row_number,
                        firstname,
                        birthyear,
                        birthmonth,
                        birthday,
                        in_apr_top80,
                        apr_rank
                    FROM {unique_table}
                    {where_clause}
                    ORDER BY original_row_number
                """
                cur.execute(query)
                rows = cur.fetchall()
            
            # Write to CSV
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                if rows:
                    fieldnames = rows[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for row in rows:
                        writer.writerow(dict(row))
            
            logger.info(f"✅ Exported {len(rows)} unique APR names to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"❌ Error exporting unique APR names to CSV: {e}")
            raise
    
    def get_unique_jan_names_list(self, table_name: str, top80_only: bool = False) -> List[str]:
        """Get list of unique JAN names (for display purposes)"""
        safe_table = table_name.lower().replace(' ', '_').replace('-', '_')
        unique_table = f"{safe_table}_comparison_unique_jan"
        
        try:
            where_clause = "WHERE in_jan_top80 = true" if top80_only else ""
            
            with self.connection.cursor() as cur:
                query = f"""
                    SELECT DISTINCT firstname_normalized
                    FROM {unique_table}
                    {where_clause}
                    ORDER BY firstname_normalized
                """
                cur.execute(query)
                rows = cur.fetchall()
                return [row[0] for row in rows]
        except Exception as e:
            logger.error(f"❌ Error retrieving unique JAN names list: {e}")
            raise
    
    def get_unique_apr_names_list(self, table_name: str, top80_only: bool = False) -> List[str]:
        """Get list of unique APR names (for display purposes)"""
        safe_table = table_name.lower().replace(' ', '_').replace('-', '_')
        unique_table = f"{safe_table}_comparison_unique_apr"
        
        try:
            where_clause = "WHERE in_apr_top80 = true" if top80_only else ""
            
            with self.connection.cursor() as cur:
                query = f"""
                    SELECT DISTINCT firstname_normalized
                    FROM {unique_table}
                    {where_clause}
                    ORDER BY firstname_normalized
                """
                cur.execute(query)
                rows = cur.fetchall()
                return [row[0] for row in rows]
        except Exception as e:
            logger.error(f"❌ Error retrieving unique APR names list: {e}")
            raise
    
    def get_common_names_list(self, table_name: str, filter_top80_only: Optional[str] = None) -> List[str]:
        """Get list of common names (for display purposes)"""
        safe_table = table_name.lower().replace(' ', '_').replace('-', '_')
        common_table = f"{safe_table}_comparison_common_names"
        
        try:
            where_clause = ""
            if filter_top80_only == 'jan':
                where_clause = "WHERE in_jan_top80 = true"
            elif filter_top80_only == 'apr':
                where_clause = "WHERE in_apr_top80 = true"
            elif filter_top80_only == 'both':
                where_clause = "WHERE in_jan_top80 = true AND in_apr_top80 = true"
            
            with self.connection.cursor() as cur:
                query = f"""
                    SELECT firstname
                    FROM {common_table}
                    {where_clause}
                    ORDER BY total_frequency DESC, firstname
                """
                cur.execute(query)
                rows = cur.fetchall()
                return [row[0] for row in rows]
        except Exception as e:
            logger.error(f"❌ Error retrieving common names list: {e}")
            raise
