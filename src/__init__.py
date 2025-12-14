"""
Data Cleaning Application Modules

This package contains all the core functionality for:
- Data cleaning
- Database interactions (Supabase)
- Reporting
- Analytics
- Comparison of datasets
"""

from .supabase_data import SupabaseManager
from .datacleaning import DataCleaner
from .reports import ReportGenerator
from .analytics import DataAnalytics, DB_CONFIG
from .most_common_names import MostCommonNamesExporter
from .comparison import ComparisonAnalytics


__all__ = ['SupabaseManager', 'DataCleaner', 'ReportGenerator', 'DataAnalytics', 'MostCommonNamesExporter', 'ComparisonAnalytics']
