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
    
    def get_total_unique_names(self, table_name):
        """
        Get total count of unique names in included data.
        
        Args:
            table_name: Name of the included table to analyze
            
        Returns:
            int: Count of unique names
        """
        query = f"""
            SELECT COUNT(DISTINCT UPPER(REGEXP_REPLACE(TRIM(name), '\s+', ' ', 'g'))) as unique_names
            FROM {table_name}
            WHERE name IS NOT NULL
            AND name != ''
        """
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        return result['unique_names']

    def get_unique_birthday_combinations(self, table_name):
        """
        Get count of unique birthday combinations (birth_day, birth_month, birth_year).
        
        Args:
            table_name: Name of the included table to analyze
            
        Returns:
            int: Count of unique birthday triplets
        """
        query = f"""
            SELECT COUNT(*) as unique_birthdays
            FROM (
                SELECT DISTINCT birth_day, birth_month, birth_year
                FROM {table_name}
                WHERE birth_day IS NOT NULL
                AND birth_month IS NOT NULL
                AND birth_year IS NOT NULL
            ) as unique_combos
        """
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        return result['unique_birthdays']

    def get_unique_name_year_combinations(self, table_name):
        """
        Get count of unique name + birth_year combinations.
        
        Args:
            table_name: Name of the included table to analyze
            
        Returns:
            int: Count of unique name+year combinations
        """
        query = f"""
            SELECT COUNT(*) as unique_combos
            FROM (
                SELECT DISTINCT LOWER(TRIM(name)) as name, birth_year
                FROM {table_name}
                WHERE name IS NOT NULL
                AND name != ''
                AND birth_year IS NOT NULL
            ) as unique_combos
        """
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        return result['unique_combos']

    def get_unique_name_month_combinations(self, table_name):
        """
        Get count of unique name + birth_month combinations.
        
        Args:
            table_name: Name of the included table to analyze
            
        Returns:
            int: Count of unique name+month combinations
        """
        query = f"""
            SELECT COUNT(*) as unique_combos
            FROM (
                SELECT DISTINCT LOWER(TRIM(name)) as name, birth_month
                FROM {table_name}
                WHERE name IS NOT NULL
                AND name != ''
                AND birth_month IS NOT NULL
            ) as unique_combos
        """
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        return result['unique_combos']

    def get_unique_name_day_combinations(self, table_name):
        """
        Get count of unique name + birth_day combinations.
        
        Args:
            table_name: Name of the included table to analyze
            
        Returns:
            int: Count of unique name+day combinations
        """
        query = f"""
            SELECT COUNT(*) as unique_combos
            FROM (
                SELECT DISTINCT LOWER(TRIM(name)) as name, birth_day
                FROM {table_name}
                WHERE name IS NOT NULL
                AND name != ''
                AND birth_day IS NOT NULL
            ) as unique_combos
        """
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        return result['unique_combos']
