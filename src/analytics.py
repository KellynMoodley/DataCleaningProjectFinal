import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json
from dotenv import load_dotenv
import os

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
    
    def get_total_unique_names(self, sheet_id):
        """
        Get total count of unique names in included data.
        
        Args:
            sheet_id: UUID of the sheet to analyze
            
        Returns:
            int: Count of unique names
        """
        query = """
            SELECT COUNT(DISTINCT LOWER(TRIM(general_name))) as unique_names
            FROM included_data
            WHERE sheet_id = %s
            AND general_name IS NOT NULL
            AND general_name != ''
        """
        self.cursor.execute(query, (sheet_id,))
        result = self.cursor.fetchone()
        return result['unique_names']
    
    def get_unique_birthday_combinations(self, sheet_id):
        """
        Get count of unique birthday combinations (birth_day, birth_month, birth_year).
        
        Args:
            sheet_id: UUID of the sheet to analyze
            
        Returns:
            int: Count of unique birthday triplets
        """
        query = """
            SELECT COUNT(*) as unique_birthdays
            FROM (
                SELECT DISTINCT birth_day, birth_month, birth_year
                FROM included_data
                WHERE sheet_id = %s
                AND birth_day IS NOT NULL
                AND birth_month IS NOT NULL
                AND birth_year IS NOT NULL
            ) as unique_combos
        """
        self.cursor.execute(query, (sheet_id,))
        result = self.cursor.fetchone()
        return result['unique_birthdays']
    
    def get_unique_name_year_combinations(self, sheet_id):
        """
        Get count of unique name + birth_year combinations.
        
        Args:
            sheet_id: UUID of the sheet to analyze
            
        Returns:
            int: Count of unique name+year combinations
        """
        query = """
            SELECT COUNT(*) as unique_combos
            FROM (
                SELECT DISTINCT LOWER(TRIM(general_name)) as name, birth_year
                FROM included_data
                WHERE sheet_id = %s
                AND general_name IS NOT NULL
                AND general_name != ''
                AND birth_year IS NOT NULL
            ) as unique_combos
        """
        self.cursor.execute(query, (sheet_id,))
        result = self.cursor.fetchone()
        return result['unique_combos']
    
    def get_unique_name_month_combinations(self, sheet_id):
        """
        Get count of unique name + birth_month combinations.
        
        Args:
            sheet_id: UUID of the sheet to analyze
            
        Returns:
            int: Count of unique name+month combinations
        """
        query = """
            SELECT COUNT(*) as unique_combos
            FROM (
                SELECT DISTINCT LOWER(TRIM(general_name)) as name, birth_month
                FROM included_data
                WHERE sheet_id = %s
                AND general_name IS NOT NULL
                AND general_name != ''
                AND birth_month IS NOT NULL
            ) as unique_combos
        """
        self.cursor.execute(query, (sheet_id,))
        result = self.cursor.fetchone()
        return result['unique_combos']
    
    def get_unique_name_day_combinations(self, sheet_id):
        """
        Get count of unique name + birth_day combinations.
        
        Args:
            sheet_id: UUID of the sheet to analyze
            
        Returns:
            int: Count of unique name+day combinations
        """
        query = """
            SELECT COUNT(*) as unique_combos
            FROM (
                SELECT DISTINCT LOWER(TRIM(general_name)) as name, birth_day
                FROM included_data
                WHERE sheet_id = %s
                AND general_name IS NOT NULL
                AND general_name != ''
                AND birth_day IS NOT NULL
            ) as unique_combos
        """
        self.cursor.execute(query, (sheet_id,))
        result = self.cursor.fetchone()
        return result['unique_combos']
    
    def get_duplicate_records_2_field_match(self, sheet_id):
        """
        Find all duplicate records where at least 2 of the 4 fields match.
        Groups records by their matching field combinations.
        
        Args:
            sheet_id: UUID of the sheet to analyze
            
        Returns:
            dict: Dictionary with duplicate categories and their records
        """
        duplicates = {
            'name_year': [],
            'name_month': [],
            'name_day': [],
            'year_month': [],
            'year_day': [],
            'month_day': [],
            'total_duplicate_records': 0
        }
        
        # Name + Year duplicates
        query = """
            WITH duplicates AS (
                SELECT 
                    LOWER(TRIM(general_name)) as name,
                    birth_year,
                    COUNT(*) as count
                FROM included_data
                WHERE sheet_id = %s
                AND general_name IS NOT NULL
                AND general_name != ''
                AND birth_year IS NOT NULL
                GROUP BY LOWER(TRIM(general_name)), birth_year
                HAVING COUNT(*) > 1
            )
            SELECT 
                d.name,
                d.birth_year,
                d.count,
                json_agg(json_build_object(
                    'id', i.id,
                    'row_id', i.row_id,
                    'name', i.general_name,
                    'birth_day', i.birth_day,
                    'birth_month', i.birth_month,
                    'birth_year', i.birth_year
                )) as records
            FROM duplicates d
            JOIN included_data i ON 
                LOWER(TRIM(i.general_name)) = d.name 
                AND i.birth_year = d.birth_year
                AND i.sheet_id = %s
            GROUP BY d.name, d.birth_year, d.count
            ORDER BY d.count DESC
        """
        self.cursor.execute(query, (sheet_id, sheet_id))
        duplicates['name_year'] = self.cursor.fetchall()
        
        # Name + Month duplicates
        query = """
            WITH duplicates AS (
                SELECT 
                    LOWER(TRIM(general_name)) as name,
                    birth_month,
                    COUNT(*) as count
                FROM included_data
                WHERE sheet_id = %s
                AND general_name IS NOT NULL
                AND general_name != ''
                AND birth_month IS NOT NULL
                GROUP BY LOWER(TRIM(general_name)), birth_month
                HAVING COUNT(*) > 1
            )
            SELECT 
                d.name,
                d.birth_month,
                d.count,
                json_agg(json_build_object(
                    'id', i.id,
                    'row_id', i.row_id,
                    'name', i.general_name,
                    'birth_day', i.birth_day,
                    'birth_month', i.birth_month,
                    'birth_year', i.birth_year
                )) as records
            FROM duplicates d
            JOIN included_data i ON 
                LOWER(TRIM(i.general_name)) = d.name 
                AND i.birth_month = d.birth_month
                AND i.sheet_id = %s
            GROUP BY d.name, d.birth_month, d.count
            ORDER BY d.count DESC
        """
        self.cursor.execute(query, (sheet_id, sheet_id))
        duplicates['name_month'] = self.cursor.fetchall()
        
        # Name + Day duplicates
        query = """
            WITH duplicates AS (
                SELECT 
                    LOWER(TRIM(general_name)) as name,
                    birth_day,
                    COUNT(*) as count
                FROM included_data
                WHERE sheet_id = %s
                AND general_name IS NOT NULL
                AND general_name != ''
                AND birth_day IS NOT NULL
                GROUP BY LOWER(TRIM(general_name)), birth_day
                HAVING COUNT(*) > 1
            )
            SELECT 
                d.name,
                d.birth_day,
                d.count,
                json_agg(json_build_object(
                    'id', i.id,
                    'row_id', i.row_id,
                    'name', i.general_name,
                    'birth_day', i.birth_day,
                    'birth_month', i.birth_month,
                    'birth_year', i.birth_year
                )) as records
            FROM duplicates d
            JOIN included_data i ON 
                LOWER(TRIM(i.general_name)) = d.name 
                AND i.birth_day = d.birth_day
                AND i.sheet_id = %s
            GROUP BY d.name, d.birth_day, d.count
            ORDER BY d.count DESC
        """
        self.cursor.execute(query, (sheet_id, sheet_id))
        duplicates['name_day'] = self.cursor.fetchall()
        
        # Year + Month duplicates
        query = """
            WITH duplicates AS (
                SELECT 
                    birth_year,
                    birth_month,
                    COUNT(*) as count
                FROM included_data
                WHERE sheet_id = %s
                AND birth_year IS NOT NULL
                AND birth_month IS NOT NULL
                GROUP BY birth_year, birth_month
                HAVING COUNT(*) > 1
            )
            SELECT 
                d.birth_year,
                d.birth_month,
                d.count,
                json_agg(json_build_object(
                    'id', i.id,
                    'row_id', i.row_id,
                    'name', i.general_name,
                    'birth_day', i.birth_day,
                    'birth_month', i.birth_month,
                    'birth_year', i.birth_year
                )) as records
            FROM duplicates d
            JOIN included_data i ON 
                i.birth_year = d.birth_year 
                AND i.birth_month = d.birth_month
                AND i.sheet_id = %s
            GROUP BY d.birth_year, d.birth_month, d.count
            ORDER BY d.count DESC
        """
        self.cursor.execute(query, (sheet_id, sheet_id))
        duplicates['year_month'] = self.cursor.fetchall()
        
        # Year + Day duplicates
        query = """
            WITH duplicates AS (
                SELECT 
                    birth_year,
                    birth_day,
                    COUNT(*) as count
                FROM included_data
                WHERE sheet_id = %s
                AND birth_year IS NOT NULL
                AND birth_day IS NOT NULL
                GROUP BY birth_year, birth_day
                HAVING COUNT(*) > 1
            )
            SELECT 
                d.birth_year,
                d.birth_day,
                d.count,
                json_agg(json_build_object(
                    'id', i.id,
                    'row_id', i.row_id,
                    'name', i.general_name,
                    'birth_day', i.birth_day,
                    'birth_month', i.birth_month,
                    'birth_year', i.birth_year
                )) as records
            FROM duplicates d
            JOIN included_data i ON 
                i.birth_year = d.birth_year 
                AND i.birth_day = d.birth_day
                AND i.sheet_id = %s
            GROUP BY d.birth_year, d.birth_day, d.count
            ORDER BY d.count DESC
        """
        self.cursor.execute(query, (sheet_id, sheet_id))
        duplicates['year_day'] = self.cursor.fetchall()
        
        # Month + Day duplicates
        query = """
            WITH duplicates AS (
                SELECT 
                    birth_month,
                    birth_day,
                    COUNT(*) as count
                FROM included_data
                WHERE sheet_id = %s
                AND birth_month IS NOT NULL
                AND birth_day IS NOT NULL
                GROUP BY birth_month, birth_day
                HAVING COUNT(*) > 1
            )
            SELECT 
                d.birth_month,
                d.birth_day,
                d.count,
                json_agg(json_build_object(
                    'id', i.id,
                    'row_id', i.row_id,
                    'name', i.general_name,
                    'birth_day', i.birth_day,
                    'birth_month', i.birth_month,
                    'birth_year', i.birth_year
                )) as records
            FROM duplicates d
            JOIN included_data i ON 
                i.birth_month = d.birth_month 
                AND i.birth_day = d.birth_day
                AND i.sheet_id = %s
            GROUP BY d.birth_month, d.birth_day, d.count
            ORDER BY d.count DESC
        """
        self.cursor.execute(query, (sheet_id, sheet_id))
        duplicates['month_day'] = self.cursor.fetchall()
        
        # Calculate total duplicate records (unique records that appear in any duplicate group)
        query = """
            SELECT COUNT(DISTINCT id) as total_duplicates
            FROM included_data
            WHERE sheet_id = %s
            AND (
                -- Records with name+year duplicates
                (general_name, birth_year) IN (
                    SELECT LOWER(TRIM(general_name)), birth_year
                    FROM included_data
                    WHERE sheet_id = %s
                    AND general_name IS NOT NULL AND birth_year IS NOT NULL
                    GROUP BY LOWER(TRIM(general_name)), birth_year
                    HAVING COUNT(*) > 1
                )
                OR
                -- Records with name+month duplicates
                (general_name, birth_month) IN (
                    SELECT LOWER(TRIM(general_name)), birth_month
                    FROM included_data
                    WHERE sheet_id = %s
                    AND general_name IS NOT NULL AND birth_month IS NOT NULL
                    GROUP BY LOWER(TRIM(general_name)), birth_month
                    HAVING COUNT(*) > 1
                )
                OR
                -- Records with name+day duplicates
                (general_name, birth_day) IN (
                    SELECT LOWER(TRIM(general_name)), birth_day
                    FROM included_data
                    WHERE sheet_id = %s
                    AND general_name IS NOT NULL AND birth_day IS NOT NULL
                    GROUP BY LOWER(TRIM(general_name)), birth_day
                    HAVING COUNT(*) > 1
                )
                OR
                -- Records with year+month duplicates
                (birth_year, birth_month) IN (
                    SELECT birth_year, birth_month
                    FROM included_data
                    WHERE sheet_id = %s
                    AND birth_year IS NOT NULL AND birth_month IS NOT NULL
                    GROUP BY birth_year, birth_month
                    HAVING COUNT(*) > 1
                )
                OR
                -- Records with year+day duplicates
                (birth_year, birth_day) IN (
                    SELECT birth_year, birth_day
                    FROM included_data
                    WHERE sheet_id = %s
                    AND birth_year IS NOT NULL AND birth_day IS NOT NULL
                    GROUP BY birth_year, birth_day
                    HAVING COUNT(*) > 1
                )
                OR
                -- Records with month+day duplicates
                (birth_month, birth_day) IN (
                    SELECT birth_month, birth_day
                    FROM included_data
                    WHERE sheet_id = %s
                    AND birth_month IS NOT NULL AND birth_day IS NOT NULL
                    GROUP BY birth_month, birth_day
                    HAVING COUNT(*) > 1
                )
            )
        """
        self.cursor.execute(query, (sheet_id, sheet_id, sheet_id, sheet_id, sheet_id, sheet_id, sheet_id))
        result = self.cursor.fetchone()
        duplicates['total_duplicate_records'] = result['total_duplicates']
        
        return duplicates
    
    def get_birth_year_distribution(self, sheet_id):
        """
        Get count of people per birth year for visualization.
        
        Args:
            sheet_id: UUID of the sheet to analyze
            
        Returns:
            list: List of dicts with birth_year and count
        """
        query = """
            SELECT 
                birth_year,
                COUNT(*) as count
            FROM included_data
            WHERE sheet_id = %s
            AND birth_year IS NOT NULL
            GROUP BY birth_year
            ORDER BY birth_year
        """
        self.cursor.execute(query, (sheet_id,))
        return self.cursor.fetchall()
    
    def get_birth_month_distribution(self, sheet_id):
        """
        Get count of people per birth month for visualization.
        
        Args:
            sheet_id: UUID of the sheet to analyze
            
        Returns:
            list: List of dicts with birth_month and count
        """
        query = """
            SELECT 
                birth_month,
                COUNT(*) as count
            FROM included_data
            WHERE sheet_id = %s
            AND birth_month IS NOT NULL
            GROUP BY birth_month
            ORDER BY birth_month
        """
        self.cursor.execute(query, (sheet_id,))
        return self.cursor.fetchall()
    
    def generate_full_report(self, sheet_id):
        """
        Generate a comprehensive analytics report for a sheet.
        
        Args:
            sheet_id: UUID of the sheet to analyze
            
        Returns:
            dict: Complete analytics report
        """
        print(f"\n{'='*60}")
        print(f"ANALYTICS REPORT - Sheet ID: {sheet_id}")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        report = {}
        
        # Basic statistics
        print("📊 UNIQUE COMBINATIONS")
        print("-" * 60)
        
        report['unique_names'] = self.get_total_unique_names(sheet_id)
        print(f"Total Unique Names: {report['unique_names']:,}")
        
        report['unique_birthdays'] = self.get_unique_birthday_combinations(sheet_id)
        print(f"Unique Birthday Combinations: {report['unique_birthdays']:,}")
        
        report['unique_name_year'] = self.get_unique_name_year_combinations(sheet_id)
        print(f"Unique Name + Year: {report['unique_name_year']:,}")
        
        report['unique_name_month'] = self.get_unique_name_month_combinations(sheet_id)
        print(f"Unique Name + Month: {report['unique_name_month']:,}")
        
        report['unique_name_day'] = self.get_unique_name_day_combinations(sheet_id)
        print(f"Unique Name + Day: {report['unique_name_day']:,}")
        
        # Duplicate analysis
        print(f"\n🔍 DUPLICATE ANALYSIS (2+ Field Matches)")
        print("-" * 60)
        
        report['duplicates'] = self.get_duplicate_records_2_field_match(sheet_id)
        print(f"Total Duplicate Records: {report['duplicates']['total_duplicate_records']:,}")
        
        print(f"\nName + Year duplicates: {len(report['duplicates']['name_year'])} groups")
        if report['duplicates']['name_year']:
            print("  Top 3:")
            for dup in report['duplicates']['name_year'][:3]:
                print(f"    • {dup['name']} + {dup['birth_year']}: {dup['count']} records")
        
        print(f"\nName + Month duplicates: {len(report['duplicates']['name_month'])} groups")
        if report['duplicates']['name_month']:
            print("  Top 3:")
            for dup in report['duplicates']['name_month'][:3]:
                print(f"    • {dup['name']} + Month {dup['birth_month']}: {dup['count']} records")
        
        print(f"\nName + Day duplicates: {len(report['duplicates']['name_day'])} groups")
        if report['duplicates']['name_day']:
            print("  Top 3:")
            for dup in report['duplicates']['name_day'][:3]:
                print(f"    • {dup['name']} + Day {dup['birth_day']}: {dup['count']} records")
        
        print(f"\nYear + Month duplicates: {len(report['duplicates']['year_month'])} groups")
        print(f"Year + Day duplicates: {len(report['duplicates']['year_day'])} groups")
        print(f"Month + Day duplicates: {len(report['duplicates']['month_day'])} groups")
        
        # Distribution data
        print(f"\n📈 DISTRIBUTION DATA")
        print("-" * 60)
        
        report['birth_year_distribution'] = self.get_birth_year_distribution(sheet_id)
        print(f"Birth Year Distribution: {len(report['birth_year_distribution'])} unique years")
        
        report['birth_month_distribution'] = self.get_birth_month_distribution(sheet_id)
        print(f"Birth Month Distribution: {len(report['birth_month_distribution'])} months with data")
        
        print(f"\n{'='*60}\n")
        
        return report

