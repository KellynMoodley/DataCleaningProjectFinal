import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from dotenv import load_dotenv
import os
import logging
from typing import List, Dict, Any, Tuple

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

class DataAnalytics:
    """
    Analytics class for analyzing included birth data from PostgreSQL database.
    Focuses on unique combinations, duplicates, and statistical insights.
    """
    
    def __init__(self, db_config):
        """
        Initialize analytics with database configuration.
        
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
            print("✓ Database connection established")
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            raise
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            print("✓ Database connection closed")
            
    def execute_sql(self, query):
        try:
            self.cursor.execute(query)
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"SQL execution failed: {e}")
            raise

    def create_analytics_table(self, table_name: str, sheet_identifier: str):
        """Create a comprehensive analytics table for data analysis"""
        safe_table_name = table_name.lower().replace(' ', '_').replace('-', '_')
        original_table = f"{safe_table_name}_{sheet_identifier}_original"
        analytics_table = f"{safe_table_name}_{sheet_identifier}_analytics"
        
        # Drop existing analytics table if it exists
        drop_query = f"DROP TABLE IF EXISTS {analytics_table}"
        self.execute_sql(drop_query)
        
        # Create comprehensive analytics table
        create_query = f"""
        CREATE TABLE {analytics_table} AS
        WITH included_data AS (
            SELECT * FROM {original_table}
            WHERE status = 'included'
        ),
        name_frequencies AS (
            SELECT 
                firstname,
                COUNT(*) as frequency,
                SUM(COUNT(*)) OVER () as total_records
            FROM included_data
            WHERE firstname IS NOT NULL AND firstname != ''
            GROUP BY firstname
            ORDER BY COUNT(*) DESC
        ),
        cumulative_names AS (
            SELECT 
                firstname,
                frequency,
                total_records,
                SUM(frequency) OVER (ORDER BY frequency DESC, firstname) as cumulative_count,
                (SUM(frequency) OVER (ORDER BY frequency DESC, firstname))::float / total_records as cumulative_percentage
            FROM name_frequencies
        ),
        top_80_names AS (
            SELECT 
                COUNT(*) as count_of_top_names,
                SUM(frequency) as count_covered_by_top_names,
                ARRAY_AGG(firstname ORDER BY frequency DESC) as top_names_list
            FROM cumulative_names
            WHERE cumulative_percentage <= 0.80
        ),
        duplicate_analysis AS (
            SELECT
                -- Name + Year duplicates
                COUNT(*) FILTER (
                    WHERE (firstname, birthyear) IN (
                        SELECT firstname, birthyear
                        FROM included_data
                        WHERE firstname IS NOT NULL AND firstname != '' 
                        AND birthyear IS NOT NULL
                        GROUP BY firstname, birthyear
                        HAVING COUNT(*) > 1
                    )
                ) as duplicates_name_year,
                
                -- Name + Month duplicates
                COUNT(*) FILTER (
                    WHERE (firstname, birthmonth) IN (
                        SELECT firstname, birthmonth
                        FROM included_data
                        WHERE firstname IS NOT NULL AND firstname != '' 
                        AND birthmonth IS NOT NULL
                        GROUP BY firstname, birthmonth
                        HAVING COUNT(*) > 1
                    )
                ) as duplicates_name_month,
                
                -- Name + Day duplicates
                COUNT(*) FILTER (
                    WHERE (firstname, birthday) IN (
                        SELECT firstname, birthday
                        FROM included_data
                        WHERE firstname IS NOT NULL AND firstname != '' 
                        AND birthday IS NOT NULL
                        GROUP BY firstname, birthday
                        HAVING COUNT(*) > 1
                    )
                ) as duplicates_name_day,
                
                -- Year + Month duplicates
                COUNT(*) FILTER (
                    WHERE (birthyear, birthmonth) IN (
                        SELECT birthyear, birthmonth
                        FROM included_data
                        WHERE birthyear IS NOT NULL 
                        AND birthmonth IS NOT NULL
                        GROUP BY birthyear, birthmonth
                        HAVING COUNT(*) > 1
                    )
                ) as duplicates_year_month,
                
                -- Year + Day duplicates
                COUNT(*) FILTER (
                    WHERE (birthyear, birthday) IN (
                        SELECT birthyear, birthday
                        FROM included_data
                        WHERE birthyear IS NOT NULL 
                        AND birthday IS NOT NULL
                        GROUP BY birthyear, birthday
                        HAVING COUNT(*) > 1
                    )
                ) as duplicates_year_day,
                
                -- Month + Day duplicates
                COUNT(*) FILTER (
                    WHERE (birthmonth, birthday) IN (
                        SELECT birthmonth, birthday
                        FROM included_data
                        WHERE birthmonth IS NOT NULL 
                        AND birthday IS NOT NULL
                        GROUP BY birthmonth, birthday
                        HAVING COUNT(*) > 1
                    )
                ) as duplicates_month_day,
                
                -- Total records with ANY 2-field duplicate
                COUNT(DISTINCT row_id) FILTER (
                    WHERE 
                        -- Name + Year match
                        (firstname, birthyear) IN (
                            SELECT firstname, birthyear
                            FROM included_data
                            WHERE firstname IS NOT NULL AND firstname != '' 
                            AND birthyear IS NOT NULL
                            GROUP BY firstname, birthyear
                            HAVING COUNT(*) > 1
                        )
                        OR
                        -- Name + Month match
                        (firstname, birthmonth) IN (
                            SELECT firstname, birthmonth
                            FROM included_data
                            WHERE firstname IS NOT NULL AND firstname != '' 
                            AND birthmonth IS NOT NULL
                            GROUP BY firstname, birthmonth
                            HAVING COUNT(*) > 1
                        )
                        OR
                        -- Name + Day match
                        (firstname, birthday) IN (
                            SELECT firstname, birthday
                            FROM included_data
                            WHERE firstname IS NOT NULL AND firstname != '' 
                            AND birthday IS NOT NULL
                            GROUP BY firstname, birthday
                            HAVING COUNT(*) > 1
                        )
                        OR
                        -- Year + Month match
                        (birthyear, birthmonth) IN (
                            SELECT birthyear, birthmonth
                            FROM included_data
                            WHERE birthyear IS NOT NULL 
                            AND birthmonth IS NOT NULL
                            GROUP BY birthyear, birthmonth
                            HAVING COUNT(*) > 1
                        )
                        OR
                        -- Year + Day match
                        (birthyear, birthday) IN (
                            SELECT birthyear, birthday
                            FROM included_data
                            WHERE birthyear IS NOT NULL 
                            AND birthday IS NOT NULL
                            GROUP BY birthyear, birthday
                            HAVING COUNT(*) > 1
                        )
                        OR
                        -- Month + Day match
                        (birthmonth, birthday) IN (
                            SELECT birthmonth, birthday
                            FROM included_data
                            WHERE birthmonth IS NOT NULL 
                            AND birthday IS NOT NULL
                            GROUP BY birthmonth, birthday
                            HAVING COUNT(*) > 1
                        )
                ) as total_records_with_any_duplicate
            FROM included_data
        )
        SELECT 
            -- Basic counts
            (SELECT COUNT(*) FROM included_data) as total_included_records,
            
            -- Uniqueness metrics
            COUNT(DISTINCT firstname) as unique_names,
            COUNT(DISTINCT (birthyear, birthmonth, birthday)) FILTER (
                WHERE birthyear IS NOT NULL 
                AND birthmonth IS NOT NULL 
                AND birthday IS NOT NULL
            ) as unique_full_birthdays,
            
            -- Unique combinations
            COUNT(DISTINCT (firstname, birthyear)) FILTER (
                WHERE firstname IS NOT NULL AND firstname != '' 
                AND birthyear IS NOT NULL
            ) as unique_name_year_combinations,
            COUNT(DISTINCT (firstname, birthmonth)) FILTER (
                WHERE firstname IS NOT NULL AND firstname != '' 
                AND birthmonth IS NOT NULL
            ) as unique_name_month_combinations,
            COUNT(DISTINCT (firstname, birthday)) FILTER (
                WHERE firstname IS NOT NULL AND firstname != '' 
                AND birthday IS NOT NULL
            ) as unique_name_day_combinations,
            
            -- Duplicate counts (records involved in duplicates)
            (SELECT duplicates_name_year FROM duplicate_analysis) as duplicate_count_name_year,
            (SELECT duplicates_name_month FROM duplicate_analysis) as duplicate_count_name_month,
            (SELECT duplicates_name_day FROM duplicate_analysis) as duplicate_count_name_day,
            (SELECT duplicates_year_month FROM duplicate_analysis) as duplicate_count_year_month,
            (SELECT duplicates_year_day FROM duplicate_analysis) as duplicate_count_year_day,
            (SELECT duplicates_month_day FROM duplicate_analysis) as duplicate_count_month_day,
            (SELECT total_records_with_any_duplicate FROM duplicate_analysis) as total_duplicate_records,
            
            -- Top 80% name analysis
            (SELECT count_of_top_names FROM top_80_names) as top_80_percent_name_count,
            (SELECT count_covered_by_top_names FROM top_80_names) as top_80_percent_record_count,
            (SELECT top_names_list FROM top_80_names) as top_80_percent_names,
            
            -- Metadata
            NOW() as calculated_at
        FROM included_data;
        """
        
        logger.info(f"Creating analytics table: {analytics_table}")
        self.execute_sql(create_query)
        logger.info(f"✅ Analytics table created successfully")


    def create_duplicate_groups_view(self, table_name: str, sheet_identifier: str):
        """Create views to show duplicate record groups"""
        safe_table_name = table_name.lower().replace(' ', '_').replace('-', '_')
        original_table = f"{safe_table_name}_{sheet_identifier}_original"
        
        # Create view for name + year duplicates
        view_name_year = f"{safe_table_name}_{sheet_identifier}_duplicates_name_year"
        self.execute_sql(f"DROP TABLE IF EXISTS {view_name_year}")
        
        create_view_query = f"""
        CREATE TABLE {view_name_year} AS
        SELECT 
            firstname,
            birthyear,
            COUNT(*) as duplicate_count,
            ARRAY_AGG(row_id::text ORDER BY original_row_number) as row_ids,
            ARRAY_AGG(original_row_number ORDER BY original_row_number) as original_row_numbers,
            ARRAY_AGG(birthday ORDER BY original_row_number) as birthdays,
            ARRAY_AGG(birthmonth ORDER BY original_row_number) as birthmonths
        FROM {original_table}
        WHERE status = 'included'
        AND firstname IS NOT NULL AND firstname != ''
        AND birthyear IS NOT NULL
        GROUP BY firstname, birthyear
        HAVING COUNT(*) > 1
        ORDER BY duplicate_count DESC, firstname, birthyear;
        """
        self.execute_sql(create_view_query)
        logger.info(f"✅ Created duplicate group view: {view_name_year}")
        
        # Create view for name + month duplicates
        view_name_month = f"{safe_table_name}_{sheet_identifier}_duplicates_name_month"
        self.execute_sql(f"DROP TABLE IF EXISTS {view_name_month}")
        
        create_view_query = f"""
        CREATE TABLE {view_name_month} AS
        SELECT 
            firstname,
            birthmonth,
            COUNT(*) as duplicate_count,
            ARRAY_AGG(row_id::text ORDER BY original_row_number) as row_ids,
            ARRAY_AGG(original_row_number ORDER BY original_row_number) as original_row_numbers,
            ARRAY_AGG(birthday ORDER BY original_row_number) as birthdays,
            ARRAY_AGG(birthyear ORDER BY original_row_number) as birthyears
        FROM {original_table}
        WHERE status = 'included'
        AND firstname IS NOT NULL AND firstname != ''
        AND birthmonth IS NOT NULL
        GROUP BY firstname, birthmonth
        HAVING COUNT(*) > 1
        ORDER BY duplicate_count DESC, firstname, birthmonth;
        """
        self.execute_sql(create_view_query)
        logger.info(f"✅ Created duplicate group view: {view_name_month}")
        
        # Create view for name + day duplicates
        view_name_day = f"{safe_table_name}_{sheet_identifier}_duplicates_name_day"
        self.execute_sql(f"DROP TABLE IF EXISTS {view_name_day}")
        
        create_view_query = f"""
        CREATE TABLE {view_name_day} AS
        SELECT 
            firstname,
            birthday,
            COUNT(*) as duplicate_count,
            ARRAY_AGG(row_id::text ORDER BY original_row_number) as row_ids,
            ARRAY_AGG(original_row_number ORDER BY original_row_number) as original_row_numbers,
            ARRAY_AGG(birthmonth ORDER BY original_row_number) as birthmonths,
            ARRAY_AGG(birthyear ORDER BY original_row_number) as birthyears
        FROM {original_table}
        WHERE status = 'included'
        AND firstname IS NOT NULL AND firstname != ''
        AND birthday IS NOT NULL
        GROUP BY firstname, birthday
        HAVING COUNT(*) > 1
        ORDER BY duplicate_count DESC, firstname, birthday;
        """
        self.execute_sql(create_view_query)
        logger.info(f"✅ Created duplicate group view: {view_name_day}")
        
        # ==================== ADD THESE THREE NEW VIEWS ====================
        
        # Create view for year + month duplicates
        view_year_month = f"{safe_table_name}_{sheet_identifier}_duplicates_year_month"
        self.execute_sql(f"DROP TABLE IF EXISTS {view_year_month}")
        
        create_view_query = f"""
        CREATE TABLE {view_year_month} AS
        SELECT 
            birthyear,
            birthmonth,
            COUNT(*) as duplicate_count,
            ARRAY_AGG(row_id::text ORDER BY original_row_number) as row_ids,
            ARRAY_AGG(original_row_number ORDER BY original_row_number) as original_row_numbers,
            ARRAY_AGG(firstname ORDER BY original_row_number) as firstnames,
            ARRAY_AGG(birthday ORDER BY original_row_number) as birthdays
        FROM {original_table}
        WHERE status = 'included'
        AND birthyear IS NOT NULL
        AND birthmonth IS NOT NULL
        GROUP BY birthyear, birthmonth
        HAVING COUNT(*) > 1
        ORDER BY duplicate_count DESC, birthyear, birthmonth;
        """
        self.execute_sql(create_view_query)
        logger.info(f"✅ Created duplicate group view: {view_year_month}")
        
        # Create view for year + day duplicates
        view_year_day = f"{safe_table_name}_{sheet_identifier}_duplicates_year_day"
        self.execute_sql(f"DROP TABLE IF EXISTS {view_year_day}")
        
        create_view_query = f"""
        CREATE TABLE {view_year_day} AS
        SELECT 
            birthyear,
            birthday,
            COUNT(*) as duplicate_count,
            ARRAY_AGG(row_id::text ORDER BY original_row_number) as row_ids,
            ARRAY_AGG(original_row_number ORDER BY original_row_number) as original_row_numbers,
            ARRAY_AGG(firstname ORDER BY original_row_number) as firstnames,
            ARRAY_AGG(birthmonth ORDER BY original_row_number) as birthmonths
        FROM {original_table}
        WHERE status = 'included'
        AND birthyear IS NOT NULL
        AND birthday IS NOT NULL
        GROUP BY birthyear, birthday
        HAVING COUNT(*) > 1
        ORDER BY duplicate_count DESC, birthyear, birthday;
        """
        self.execute_sql(create_view_query)
        logger.info(f"✅ Created duplicate group view: {view_year_day}")
        
        # Create view for month + day duplicates
        view_month_day = f"{safe_table_name}_{sheet_identifier}_duplicates_month_day"
        self.execute_sql(f"DROP TABLE IF EXISTS {view_month_day}")
        
        create_view_query = f"""
        CREATE TABLE {view_month_day} AS
        SELECT 
            birthmonth,
            birthday,
            COUNT(*) as duplicate_count,
            ARRAY_AGG(row_id::text ORDER BY original_row_number) as row_ids,
            ARRAY_AGG(original_row_number ORDER BY original_row_number) as original_row_numbers,
            ARRAY_AGG(firstname ORDER BY original_row_number) as firstnames,
            ARRAY_AGG(birthyear ORDER BY original_row_number) as birthyears
        FROM {original_table}
        WHERE status = 'included'
        AND birthmonth IS NOT NULL
        AND birthday IS NOT NULL
        GROUP BY birthmonth, birthday
        HAVING COUNT(*) > 1
        ORDER BY duplicate_count DESC, birthmonth, birthday;
        """
        
        self.execute_sql(create_view_query)
        logger.info(f"✅ Created duplicate group view: {view_month_day}")


    def create_visualization_tables(self, table_name: str, sheet_identifier: str):
        """Create tables for visualization data (birth year and birth month distributions)"""
        safe_table_name = table_name.lower().replace(' ', '_').replace('-', '_')
        original_table = f"{safe_table_name}_{sheet_identifier}_original"
        
        # Birth year distribution
        birthyear_chart_table = f"{safe_table_name}_{sheet_identifier}_chart_birthyear"
        self.execute_sql(f"DROP TABLE IF EXISTS {birthyear_chart_table}")
        
        birthyear_query = f"""
        CREATE TABLE {birthyear_chart_table} AS
        SELECT 
            birthyear,
            COUNT(*) as count
        FROM {original_table}
        WHERE status = 'included'
        AND birthyear IS NOT NULL
        GROUP BY birthyear
        ORDER BY birthyear;
        """
        self.execute_sql(birthyear_query)
        logger.info(f"✅ Created birth year chart table: {birthyear_chart_table}")
        
        # Birth month distribution
        birthmonth_chart_table = f"{safe_table_name}_{sheet_identifier}_chart_birthmonth"
        self.execute_sql(f"DROP TABLE IF EXISTS {birthmonth_chart_table}")
        
        birthmonth_query = f"""
        CREATE TABLE {birthmonth_chart_table} AS
        SELECT 
            birthmonth,
            COUNT(*) as count
        FROM {original_table}
        WHERE status = 'included'
        AND birthmonth IS NOT NULL
        GROUP BY birthmonth
        ORDER BY birthmonth;
        """
        self.execute_sql(birthmonth_query)
        logger.info(f"✅ Created birth month chart table: {birthmonth_chart_table}")


    def get_analytics_data(self, table_name: str, sheet_identifier: str) -> Dict[str, Any]:
        """Retrieve analytics data"""
        safe_table_name = table_name.lower().replace(' ', '_').replace('-', '_')
        analytics_table = f"{safe_table_name}_{sheet_identifier}_analytics"
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"SELECT * FROM {analytics_table}")
                result = cur.fetchone()
                
                if result:
                    data = dict(result)
                    # Convert datetime to ISO string
                    if 'calculated_at' in data and data['calculated_at']:
                        data['calculated_at'] = data['calculated_at'].isoformat()
                    return data
                return {}
        except Exception as e:
            logger.error(f"❌ Error retrieving analytics data: {e}")
            raise


    def get_chart_data(self, table_name: str, sheet_identifier: str, chart_type: str) -> List[Dict[str, Any]]:
        """Retrieve chart data for visualizations"""
        safe_table_name = table_name.lower().replace(' ', '_').replace('-', '_')
        
        if chart_type == 'birthyear':
            chart_table = f"{safe_table_name}_{sheet_identifier}_chart_birthyear"
        elif chart_type == 'birthmonth':
            chart_table = f"{safe_table_name}_{sheet_identifier}_chart_birthmonth"
        else:
            raise ValueError(f"Invalid chart type: {chart_type}")
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"SELECT * FROM {chart_table}")
                rows = cur.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ Error retrieving chart data: {e}")
            raise


    def get_duplicate_groups(self, table_name: str, sheet_identifier: str, 
                            group_type: str, page: int = 1, per_page: int = 50) -> Tuple[List[Dict], int]:
        """Retrieve duplicate group data with pagination"""
        safe_table_name = table_name.lower().replace(' ', '_').replace('-', '_')
        
        valid_types = {
            'name_year': f"{safe_table_name}_{sheet_identifier}_duplicates_name_year",
            'name_month': f"{safe_table_name}_{sheet_identifier}_duplicates_name_month",
            'name_day': f"{safe_table_name}_{sheet_identifier}_duplicates_name_day",
            'year_month': f"{safe_table_name}_{sheet_identifier}_duplicates_year_month",
            'year_day': f"{safe_table_name}_{sheet_identifier}_duplicates_year_day",
            'month_day': f"{safe_table_name}_{sheet_identifier}_duplicates_month_day"
        }
        
        if group_type not in valid_types:
            raise ValueError(f"Invalid group type: {group_type}")
        
        view_name = valid_types[group_type]
        
        try:
            offset = (page - 1) * per_page
            
            # Get total count
            with self.connection.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {view_name}")
                total_count = cur.fetchone()[0]
            
            # Get paginated data
            with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"""
                    SELECT * FROM {view_name}
                    LIMIT %s OFFSET %s
                """, (per_page, offset))
                rows = cur.fetchall()
                
            return [dict(row) for row in rows], total_count
        except Exception as e:
            logger.error(f"❌ Error retrieving duplicate groups: {e}")
            raise

    def create_duplicate_indexes(self, table_name: str, sheet_identifier: str):
        """Create indexes on ORIGINAL table for faster duplicate detection"""
        safe_table_name = table_name.lower().replace(' ', '_').replace('-', '_')
        original_table = f"{safe_table_name}_{sheet_identifier}_original"
        
        logger.info(f"Creating indexes on {original_table}...")
        
        #create indexes for rows with status=included
        indexes = [
            f"CREATE INDEX IF NOT EXISTS idx_{original_table}_name_year ON {original_table}(firstname, birthyear) WHERE status = 'included'",
            f"CREATE INDEX IF NOT EXISTS idx_{original_table}_name_month ON {original_table}(firstname, birthmonth) WHERE status = 'included'",
            f"CREATE INDEX IF NOT EXISTS idx_{original_table}_name_day ON {original_table}(firstname, birthday) WHERE status = 'included'",
            f"CREATE INDEX IF NOT EXISTS idx_{original_table}_year_month ON {original_table}(birthyear, birthmonth) WHERE status = 'included'",
            f"CREATE INDEX IF NOT EXISTS idx_{original_table}_year_day ON {original_table}(birthyear, birthday) WHERE status = 'included'",
            f"CREATE INDEX IF NOT EXISTS idx_{original_table}_month_day ON {original_table}(birthmonth, birthday) WHERE status = 'included'",
            f"CREATE INDEX IF NOT EXISTS idx_{original_table}_original_row ON {original_table}(original_row_number)",
            f"CREATE INDEX IF NOT EXISTS idx_{original_table}_status ON {original_table}(status)"
        ]
        
        for idx_query in indexes:
            try:
                self.execute_sql(idx_query)
                logger.info(f"✅ Index created")
            except Exception as e:
                logger.warning(f"Index creation skipped or failed: {e}")
        
        logger.info(f"✅ All original table indexes created successfully")


    def create_duplicate_table_indexes(self, table_name: str, sheet_identifier: str):
        """Create indexes ON duplicate tables for fast queries"""
        safe_table_name = table_name.lower().replace(' ', '_').replace('-', '_')
        
        logger.info("Creating indexes on duplicate tables...")
        
        indexes = [
            f"CREATE INDEX IF NOT EXISTS idx_{safe_table_name}_{sheet_identifier}_duplicates_name_year_count ON {safe_table_name}_{sheet_identifier}_duplicates_name_year(duplicate_count DESC)",
            f"CREATE INDEX IF NOT EXISTS idx_{safe_table_name}_{sheet_identifier}_duplicates_name_month_count ON {safe_table_name}_{sheet_identifier}_duplicates_name_month(duplicate_count DESC)",
            f"CREATE INDEX IF NOT EXISTS idx_{safe_table_name}_{sheet_identifier}_duplicates_name_day_count ON {safe_table_name}_{sheet_identifier}_duplicates_name_day(duplicate_count DESC)",
            f"CREATE INDEX IF NOT EXISTS idx_{safe_table_name}_{sheet_identifier}_duplicates_year_month_count ON {safe_table_name}_{sheet_identifier}_duplicates_year_month(duplicate_count DESC)",
            f"CREATE INDEX IF NOT EXISTS idx_{safe_table_name}_{sheet_identifier}_duplicates_year_day_count ON {safe_table_name}_{sheet_identifier}_duplicates_year_day(duplicate_count DESC)",
            f"CREATE INDEX IF NOT EXISTS idx_{safe_table_name}_{sheet_identifier}_duplicates_month_day_count ON {safe_table_name}_{sheet_identifier}_duplicates_month_day(duplicate_count DESC)"
        ]
        
        for idx_query in indexes:
            try:
                self.execute_sql(idx_query)
                logger.info(f"✅ Index created")
            except Exception as e:
                logger.warning(f"Index creation failed: {e}")
        
        logger.info(f"✅ All duplicate table indexes created successfully")
        
        
    def create_common_names_table(self, table_name: str, sheet_identifier: str):
        """Create a table with the top 80% most common names with their frequencies"""
        safe_table_name = table_name.lower().replace(' ', '_').replace('-', '_')
        original_table = f"{safe_table_name}_{sheet_identifier}_original"
        common_names_table = f"{safe_table_name}_{sheet_identifier}_common_names"
        
        # Drop existing table if it exists
        drop_query = f"DROP TABLE IF EXISTS {common_names_table}"
        self.execute_sql(drop_query)
        
        # Create common names table with frequencies
        create_query = f"""
        CREATE TABLE {common_names_table} AS
        WITH included_data AS (
            SELECT * FROM {original_table}
            WHERE status = 'included'
        ),
        name_frequencies AS (
            SELECT 
                firstname,
                COUNT(*) as frequency,
                SUM(COUNT(*)) OVER () as total_records
            FROM included_data
            WHERE firstname IS NOT NULL AND firstname != ''
            GROUP BY firstname
        ),
        cumulative_names AS (
            SELECT 
                firstname,
                frequency,
                total_records,
                SUM(frequency) OVER (ORDER BY frequency DESC, firstname) as cumulative_count,
                (SUM(frequency) OVER (ORDER BY frequency DESC, firstname))::float / total_records as cumulative_percentage,
                (frequency::float / total_records * 100) as percentage_of_total
            FROM name_frequencies
        ),
        top_80_names AS (
            SELECT 
                firstname,
                frequency,
                total_records,
                cumulative_count,
                cumulative_percentage,
                percentage_of_total,
                ROW_NUMBER() OVER (ORDER BY frequency DESC, firstname) as rank
            FROM cumulative_names
            WHERE cumulative_percentage <= 0.80
        )
        SELECT 
            rank,
            firstname,
            frequency,
            ROUND(percentage_of_total::numeric, 2) as percentage_of_total,
            cumulative_count,
            ROUND((cumulative_percentage * 100)::numeric, 2) as cumulative_percentage,
            total_records
        FROM top_80_names
        ORDER BY rank;
        """
        
        logger.info(f"Creating common names table: {common_names_table}")
        self.execute_sql(create_query)
        
        # Create indexes for fast queries
        logger.info(f"Creating indexes on {common_names_table}...")
        indexes = [
            f"CREATE INDEX IF NOT EXISTS idx_{common_names_table}_rank ON {common_names_table}(rank)",
            f"CREATE INDEX IF NOT EXISTS idx_{common_names_table}_frequency ON {common_names_table}(frequency DESC)",
            f"CREATE INDEX IF NOT EXISTS idx_{common_names_table}_firstname ON {common_names_table}(firstname)"
        ]
        
        for idx_query in indexes:
            try:
                self.execute_sql(idx_query)
            except Exception as e:
                logger.warning(f"Index creation skipped or failed: {e}")
        
        logger.info(f"✅ Common names table created successfully")


    def get_common_names_data(self, table_name: str, sheet_identifier: str) -> List[Dict[str, Any]]:
        """Retrieve common names data"""
        safe_table_name = table_name.lower().replace(' ', '_').replace('-', '_')
        common_names_table = f"{safe_table_name}_{sheet_identifier}_common_names"
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"""
                    SELECT 
                        rank,
                        firstname,
                        frequency,
                        percentage_of_total,
                        cumulative_count,
                        cumulative_percentage,
                        total_records
                    FROM {common_names_table}
                    ORDER BY rank
                """)
                rows = cur.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ Error retrieving common names data: {e}")
            raise
