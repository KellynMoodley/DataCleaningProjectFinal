# 📊 Google Sheets Data Cleaning & Analytics Dashboard

A comprehensive Python-based web application for cleaning, validating, and analyzing birth data from Google Sheets with advanced comparison analytics between datasets.

---

## 🎯 Overview

This application processes raw birth data from Google Sheets, applies validation rules, generates inclusion/exclusion reports, performs duplicate analysis, and compares datasets (JAN vs APR). Built with Flask, PostgreSQL, and JavaScript.

---

## 🚀 Installation & Setup

### **Configure Environment Variables**

Create a `.env` file:
```env
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=6543
DB_NAME=postgres
```

### **Configure Google Sheets API**

1. Create a Google Cloud Project
2. Enable Google Sheets API
3. Create Service Account credentials
4. Download JSON key as `service_account.json`
5. Share your Google Sheets with the service account email


## 📋 Features

### **1. Data Processing Pipeline**

```
Google Sheets → Fetch Data → Generate UUIDs → Validate & Clean → Store in PostgreSQL → Generate Analytics
```

| Step | Description |
|------|-------------|
| **Fetch** | Retrieves data from Google Sheets via API |
| **UUID Generation** | Assigns unique `row_id` to each record |
| **Validation** | Applies 6 business rules (see below) |
| **Storage** | Bulk insert using PostgreSQL COPY command |
| **Analytics** | Creates 10+ derived tables for analysis |

### **2. Validation Rules**

| Rule | Description | Example Exclusion |
|------|-------------|-------------------|
| **Name Characters** | Only A-Z letters and spaces allowed | `"John123"` → "special character in name" |
| **Name Length** | Minimum 3 characters | `"Jo"` → "name too short" |
| **Birth Day** | Must be numeric, 1-31 | `"32"` → "invalid day (not 1-31)" |
| **Birth Month** | Must be numeric, 1-12 | `"13"` → "invalid month (not 1-12)" |
| **Birth Year** | Must be numeric, ≥1940 | `"1939"` → "birth_year older than 1940" |
| **Missing Data** | All fields required | `""` → "missing birth_year" |

### **3. Dashboard Views**

#### **Main Interface**
| View | Description |
|------|-------------|
| **Sheets Grid** | Process and view multiple Google Sheets |
| **Original Data** | All rows (included + excluded) with filtering |
| **Included Data** | Valid records that passed validation |
| **Excluded Data** | Invalid records with exclusion reasons |
| **Summary Statistics** | Aggregate metrics and uniqueness analysis |
| **Duplicate Analysis** | 6 types of duplicate detection |
| **Charts** | Birth year/month distribution visualizations |
| **Common Names** | Top 80% most frequent names (Pareto analysis) |
| **Comparison (JAN vs APR)** | Dataset overlap and unique names |

#### **Interactive Features**
- ✅ **Pagination**: 50/100/200/500 records per page
- ✅ **Filtering**: By name, birth month, birth year
- ✅ **Sorting**: Click column headers to toggle asc/desc
- ✅ **Downloads**: CSV and PDF exports

---

## 📊 Analytics & Metrics

### **Summary Statistics**

| Metric | Description |
|--------|-------------|
| **Total Rows** | Original dataset size |
| **Included Count** | Valid records |
| **Excluded Count** | Invalid records |
| **Unique Names** | Distinct names in dataset |
| **Unique Birthdays** | Distinct birth date combinations |
| **Unique Combinations** | Name+Year, Name+Month, Name+Day |

### **Duplicate Detection (6 Types)**

| Type | Fields Analyzed | Use Case |
|------|----------------|----------|
| **Name + Year** | `firstname`, `birthyear` | Same person, different months |
| **Name + Month** | `firstname`, `birthmonth` | Same name, same birth month |
| **Name + Day** | `firstname`, `birthday` | Same name, same day of month |
| **Year + Month** | `birthyear`, `birthmonth` | Cohort analysis |
| **Year + Day** | `birthyear`, `birthday` | Date pattern analysis |
| **Month + Day** | `birthmonth`, `birthday` | Seasonal pattern analysis |

### **Top 80% Most Common Names**

Implements Pareto Principle (80/20 rule):
- Identifies smallest set of names covering 80% of records
- Provides cumulative frequency analysis
- Exports as CSV/JSON

**Example Output:**
| Rank | Name | Frequency | % of Total | Cumulative % |
|------|------|-----------|------------|--------------|
| 1 | John | 1,250 | 2.5% | 2.5% |
| 2 | Mary | 980 | 2.0% | 4.5% |
| ... | ... | ... | ... | ... |
| 150 | Sarah | 120 | 0.24% | 80.0% |

---

## 🔄 JAN vs APR Comparison

### **Comparison Metrics**

| Category | Metrics Provided |
|----------|------------------|
| **Dataset Overview** | Total records, unique names, top 80% names (both datasets) |
| **Common Names** | Count and list of names in both JAN and APR |
| **Unique to JAN** | Names appearing only in January dataset |
| **Unique to APR** | Names appearing only in April dataset |
| **Top 80% Overlap** | How many JAN top 80% appear in APR (and vice versa) |
| **Both Top 80%** | Names in top 80% of BOTH datasets |

### **Comparison Views**

1. **Summary Dashboard**: High-level statistics with percentages
2. **Common Names Table**: Paginated list with frequencies from both months
3. **Unique JAN Table**: All records with JAN-only names
4. **Unique APR Table**: All records with APR-only names

### **Download Options**
- ✅ Common names CSV
- ✅ Unique JAN CSV
- ✅ Unique APR CSV

---

## 🗄️ Database Schema

### **Core Tables**

#### **1. Original Data Table**
```sql
{table_name}_{identifier}_original
├── row_id (UUID, PRIMARY KEY)
├── original_row_number (INTEGER)
├── firstname (TEXT)
├── birthday (INTEGER)
├── birthmonth (INTEGER)
├── birthyear (INTEGER)
├── exclusion_reason (TEXT)
└── status (TEXT) -- 'included' or 'excluded'
```

#### **2. Analytics Table**
```sql
{table_name}_{identifier}_analytics
├── total_included_records (INTEGER)
├── unique_names (INTEGER)
├── unique_full_birthdays (INTEGER)
├── unique_name_year_combinations (INTEGER)
├── unique_name_month_combinations (INTEGER)
├── unique_name_day_combinations (INTEGER)
├── duplicate_count_name_year (INTEGER)
├── duplicate_count_name_month (INTEGER)
├── duplicate_count_name_day (INTEGER)
├── duplicate_count_year_month (INTEGER)
├── duplicate_count_year_day (INTEGER)
├── duplicate_count_month_day (INTEGER)
├── total_duplicate_records (INTEGER)
├── top_80_percent_name_count (INTEGER)
├── top_80_percent_record_count (INTEGER)
├── top_80_percent_names (TEXT[])
└── calculated_at (TIMESTAMP)
```

#### **3. Duplicate Group Tables (6 tables)**
```sql
{table_name}_{identifier}_duplicates_{type}
├── {grouping_field_1} (e.g., firstname)
├── {grouping_field_2} (e.g., birthyear)
├── duplicate_count (INTEGER)
├── row_ids (TEXT[])
├── original_row_numbers (INTEGER[])
└── {other_fields} (arrays of related data)
```

#### **4. Visualization Tables**
```sql
{table_name}_{identifier}_chart_birthyear
├── birthyear (INTEGER)
└── count (INTEGER)

{table_name}_{identifier}_chart_birthmonth
├── birthmonth (INTEGER)
└── count (INTEGER)
```

#### **5. Common Names Table**
```sql
{table_name}_{identifier}_common_names
├── rank (INTEGER)
├── firstname (TEXT)
├── frequency (INTEGER)
├── percentage_of_total (NUMERIC)
├── cumulative_count (INTEGER)
├── cumulative_percentage (NUMERIC)
└── total_records (INTEGER)
```

#### **6. Comparison Tables**

**Summary Table:**
```sql
{table_name}_comparison_summary
├── jan_total_records, jan_unique_names, jan_top80_count
├── apr_total_records, apr_unique_names, apr_top80_count
├── common_names_count, common_names_pct_of_jan, common_names_pct_of_apr
├── unique_jan_names_count, unique_apr_names_count
├── jan_top80_in_apr_count, jan_top80_in_apr_pct
├── apr_top80_in_jan_count, apr_top80_in_jan_pct
├── both_top80_count
└── calculated_at
```

**Common Names Table:**
```sql
{table_name}_comparison_common_names
├── firstname
├── jan_frequency, apr_frequency, total_frequency
├── in_jan_top80, in_apr_top80
├── jan_rank, apr_rank
└── calculated_at
```

**Unique Tables (JAN/APR):**
```sql
{table_name}_comparison_unique_{jan|apr}
├── row_id, original_row_number
├── firstname, birthyear, birthmonth, birthday
├── firstname_normalized
├── in_{jan|apr}_top80
├── {jan|apr}_rank
└── calculated_at
```

---

## 🔌 API Endpoints

### **Main Routes**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serve main dashboard |
| `POST` | `/process/<sheet_key>` | Process Google Sheet data |
| `GET` | `/check_tables/<sheet_key>` | Check if tables exist |

### **Data Retrieval**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/data/<sheet_key>/<table_type>` | Get paginated table data (original/included/excluded) |
| `GET` | `/download/<sheet_key>/<table_type>/<format>` | Download as CSV or PDF |

### **Analytics**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/analytics/<sheet_key>/create` | Create analytics tables |
| `GET` | `/analytics/<sheet_key>/summary` | Get summary statistics |
| `GET` | `/analytics/<sheet_key>/duplicates/<group_type>` | Get duplicate groups |
| `GET` | `/analytics/<sheet_key>/charts/<chart_type>` | Get chart data (birthyear/birthmonth) |
| `GET` | `/analytics/<sheet_key>/common_names` | Get top 80% names |
| `GET` | `/analytics/<sheet_key>/common_names/download/<format>` | Download common names (CSV/JSON) |

### **Comparison**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/comparison/create` | Create JAN vs APR comparison |
| `GET` | `/comparison/summary` | Get comparison summary |
| `GET` | `/comparison/common_names` | Get common names (paginated) |
| `GET` | `/comparison/unique_jan` | Get JAN-only names |
| `GET` | `/comparison/unique_apr` | Get APR-only names |
| `GET` | `/comparison/download/<dataset>/<format>` | Download comparison data |
| `GET` | `/comparison/check` | Check if comparison tables exist |

---

## 🎨 Frontend Components

### **JavaScript Modules (main.js)**

#### **Global State Management**
```javascript
currentSheet              // Active sheet selection
currentTableStates        // Pagination & sorting per table
currentFilters           // Active filters per table
chartInstance            // Chart.js instance
currentDuplicatesState   // Duplicate analysis state
currentComparisonState   // Comparison view state
```

#### **Key Functions by Category**

| Category | Functions |
|----------|-----------|
| **Sheet Processing** | `processSheet()`, `viewSheetData()` |
| **Tab Navigation** | `switchTab()` |
| **Table Operations** | `loadTableData()`, `renderTable()`, `renderPagination()` |
| **Sorting & Filtering** | `sortTable()`, `applyFilters()`, `clearFilters()` |
| **Analytics** | `loadanalytics()`, `loadAnalyticsSummary()`, `loadDuplicates()` |
| **Charts** | `loadChart()`, `renderChart()` |
| **Comparison** | `loadComparisonAnalytics()`, `loadComparisonSummary()`, `fetchComparisonData()` |
| **Downloads** | `downloadTable()`, `downloadCommonNames()`, `downloadComparisonData()` |

---

## 📦 Python Modules

### **src/ Package Structure**

| Module | Class | Purpose |
|--------|-------|---------|
| `supabase_data.py` | `SupabaseManager` | Database connection, CRUD operations, bulk inserts |
| `datacleaning.py` | `DataCleaner` | Validation rules, data cleaning, error tracking |
| `analytics.py` | `DataAnalytics` | Analytics table creation, duplicate detection |
| `comparison.py` | `ComparisonAnalytics` | JAN vs APR comparison logic |
| `reports.py` | `ReportGenerator` | CSV/PDF export generation |
| `most_common_names.py` | `MostCommonNamesExporter` | Top 80% names CSV/JSON export |
| `__init__.py` | - | Package initializer, exports public API |

### **Key Module Methods**

#### **SupabaseManager**
```python
connect()                        # Establish DB connection
create_original_table()          # Create main data table
append_data()                    # Bulk insert with COPY
get_table_data()                 # Paginated, filtered queries
check_tables_exist()             # Verify table existence
```

#### **DataCleaner**
```python
clean_dataset()                  # Process all rows
clean_row()                      # Validate single row
is_valid_name()                  # Name validation
is_valid_numeric()               # Numeric field validation
get_cleaning_summary()           # Summary statistics
```

#### **DataAnalytics**
```python
create_analytics_table()         # Main analytics
create_duplicate_groups_view()   # 6 duplicate tables
create_visualization_tables()    # Chart data
create_common_names_table()      # Top 80% analysis
create_duplicate_indexes()       # Performance indexes
get_analytics_data()             # Retrieve metrics
get_duplicate_groups()           # Paginated duplicates
```

#### **ComparisonAnalytics**
```python
create_comparison_analytics()    # Create all comparison tables
get_comparison_summary()         # Summary metrics
get_common_names()               # Names in both datasets
get_unique_jan_names()           # JAN-only names
get_unique_apr_names()           # APR-only names
export_*_to_csv()               # CSV exports
```

---

## 🔒 Security & Performance

### **Security Measures**
- ✅ Environment variables for sensitive credentials
- ✅ SQL injection prevention (parameterized queries)
- ✅ XSS protection (HTML escaping)
- ✅ Service account authentication for Google Sheets

### **Performance Optimizations**
- ✅ PostgreSQL COPY command for bulk inserts (10x faster than INSERT)
- ✅ Batch processing (100,000 rows per batch)
- ✅ Comprehensive indexing on all query fields
- ✅ Connection pooling with autocommit
- ✅ Paginated API responses (prevents memory overflow)
- ✅ Chart data pre-aggregation (no runtime calculations)
- ✅ CTE-based analytics (efficient SQL execution)

### **Scalability Features**
- ✅ Handles 1M+ row datasets
- ✅ Concurrent request handling
- ✅ Temp table cleanup in comparison analytics
- ✅ Statement timeout management (10 min for large operations)

---

## 📈 Usage Workflow

### **Standard Workflow**

```
1. Load Dashboard → http://localhost:5000

2. Process Sheet
   └─> Click "Process Sheet" on desired sheet card
   └─> Wait for completion (status box shows progress)
   └─> View counts: Total, Included, Excluded

3. View Data
   └─> Click "View Data" button
   └─> Browse tabs: Original, Included, Excluded
   └─> Apply filters, sorting, pagination
   └─> Download CSV/PDF reports

4. Load Analytics
   └─> Switch to "Summary Statistics" tab
   └─> Click "Load Analytics"
   └─> View metrics: uniqueness, duplicates
   └─> Explore duplicate groups (6 types)
   └─> View charts (birth year/month)
   └─> Check top 80% common names

5. Compare Datasets (JAN vs APR)
   └─> Process both JAN and APR sheets first
   └─> Load analytics for both
   └─> Switch to "Comparison" tab
   └─> Click "Load Comparison"
   └─> View summary statistics
   └─> Explore common/unique names
   └─> Download comparison reports
```

---

## 🐛 Troubleshooting

### **Common Issues**

| Issue | Solution |
|-------|----------|
| **Database connection fails** | Check `.env` credentials, verify PostgreSQL is running |
| **Google Sheets API error** | Verify `service_account.json` exists, check sheet sharing permissions |
| **"No data available"** | Process sheet first before viewing data |
| **Analytics button greyed out** | Tables already created; refresh to reload |
| **Comparison fails** | Ensure both JAN and APR sheets are processed and analytics loaded |
| **PDF download empty** | Check console for errors, verify ReportLab installation |
| **Slow performance** | Create indexes (`create_duplicate_indexes()`), reduce batch size |

### **Debug Mode**

Enable detailed logging in `app.py`:
```python
logging.basicConfig(level=logging.DEBUG)
```

Check logs for:
- SQL query execution times
- API response times
- Error stack traces

---
