# Assessment Completion Checklist & Requirements Mapping

## Purpose of This Document

This document maps the **assessment requirements** to their **actual implementation in the codebase**. It demonstrates compliance with all required features, highlights partial implementations, and explains any intentional design deviations.

---

## Part A – Data Cleaning Rules (01 JAN Dataset)

| Requirement                       | Status     | Implementation                                                   |
| --------------------------------- | ---------- | ---------------------------------------------------------------- |
| Load dataset                      | ✅ Complete | `app.py` – `get_sheet_data()` fetches data via Google Sheets API |
| Generate unique `row_id` (UUID)   | ✅ Complete | `process_and_clean_sheet_data()` assigns UUID per row            |
| Reject non A–Z characters in name | ✅ Complete | `DataCleaner.is_valid_name()` using regex `^[A-Za-z\s]+$`        |
| Allow spaces in names             | ✅ Complete | Regex includes whitespace (`\s`)                                 |
| Validate numeric columns (B–D)    | ✅ Complete | `is_valid_numeric()`                                             |
| Name length ≥ 3 characters        | ✅ Complete | `is_valid_name()`                                                |
| Birth year ≥ 1940                 | ✅ Complete | `is_valid_year()`                                                |
| Day between 1–31                  | ✅ Complete | `is_valid_day()`                                                 |
| Month between 1–12                | ✅ Complete | `is_valid_month()`                                               |
| Track exclusion reasons           | ✅ Complete | `clean_row()` collects all errors                                |
| Store multiple exclusion reasons  | ✅ Complete | Errors appended and joined with `;`                              |
| Included data report              | ✅ Complete | Dashboard view + CSV/PDF downloads                               |
| Excluded data report              | ✅ Complete | Dashboard view + CSV/PDF downloads                               |

---

## Part B – Dashboard Requirements (01 JAN Dataset)

### 1. Final (Included) Data View

| Requirement                          | Status     | Implementation                       |
| ------------------------------------ | ---------- | ------------------------------------ |
| Table/grid display                   | ✅ Complete | `index.html` – Included Data section |
| Column filtering (name, month, year) | ✅ Complete | `main.js` – `applyFilters()`         |
| Column sorting                       | ✅ Complete | `sortTable()`                        |
| CSV download                         | ✅ Complete | `/download/<sheet>/<type>/csv`       |
| PDF download                         | ✅ Complete | `/download/<sheet>/<type>/pdf`-only displays first 1000 rows due to size of pdf |

---

### 2. Excluded Data View

| Requirement                  | Status     | Implementation            |
| ---------------------------- | ---------- | ------------------------- |
| Table with exclusion reasons | ✅ Complete | Excluded Data section     |
| CSV download                 | ✅ Complete | `/download/<sheet>/<type>/csv`|
| PDF download                 | ✅ Complete | `/download/<sheet>/<type>/pdf`- only displays first 1000 rows due to size of pdf  |

---

### 3. Summary Analytics

| Metric                                | Status     | Implementation             |
| ------------------------------------- | ---------- | -------------------------- |
| Original / Included / Excluded counts | ✅ Complete | Displayed after processing |
| Percentage calculations               | ✅ Complete | Calculated in backend      |
| Total unique names                    | ✅ Complete | `analytics.py`             |
| Unique birthday combinations          | ✅ Complete | `unique_full_birthdays`    |
| Unique name + year/month/day          | ✅ Complete | Analytics tables           |
| Duplicate detection (6 types)         | ✅ Complete | Duplicate Analysis section |
| Duplicate group filtering             | ✅ Complete | 6-tab UI                   |
| Visualizations                        | ✅ Complete | Chart.js bar charts        |

---

## Part C – Top 80% Most Common Names (01 JAN Dataset)

| Requirement                | Status     | Implementation                           |
| -------------------------- | ---------- | ---------------------------------------- |
| Compute name frequencies   | ✅ Complete | `create_common_names_table()`            |
| Sort by frequency          | ✅ Complete | DESC ordering                            |
| Select top 80% cumulative  | ✅ Complete | CTE with `cumulative_percentage <= 0.80` |
| Dashboard view             | ✅ Complete | “Top 80% Most Common Names” tab          |
| CSV download               | ✅ Complete | `/common_names/download/csv`             |
| JSON download              | ✅ Complete | `/common_names/download/json`            |
| Frequency statistics shown | ✅ Complete | Rank, frequency, percentage, cumulative  |

---

## Part D – Generic Upload & Processing (04 APR Dataset)

| Requirement                        | Status            | Notes                          |
| ---------------------------------- | ----------------- | ------------------------------ |
| Upload CSV via UI                  | ❌ Not Implemented | Google Sheets API used instead |
| Apply same cleaning rules          | ✅ Complete        | Shared `DataCleaner`           |
| Generate included/excluded reports | ✅ Complete        | Both datasets fully supported  |
| Generate analytics                 | ✅ Complete        | Analytics created per sheet    |
| Top 80% names                      | ✅ Complete        | Supported for both datasets    |
| Render in dashboard                | ✅ Complete        | Sheets selectable via UI       |

**Design Decision Note:**  
Google Sheets API integration was used instead of CSV uploads to avoid formatting issues caused by spreadsheet software and to bypass Microsoft Excel’s row display limit of 1,048,576 rows. This approach ensures accurate data ingestion and better supports large datasets.

---

## Part E – Comparison Between JAN and APR

### 1. Common Names

| Requirement        | Status            | Implementation       |
| ------------------ | ----------------- | -------------------- |
| Count common names | ✅ Complete        | Comparison analytics |
| Display count      | ✅ Complete        | Summary dashboard    |
| Display table      | ✅ Complete        | Paginated table      |
| CSV download       | ✅ Complete        | Endpoint provided    |
| PDF download       | ❌ Not Implemented | CSV only             |

---

### 2. Names Unique to JAN

| Requirement           | Status            |
| --------------------- | ----------------- |
| Identify unique names | ✅ Complete        |
| Count displayed       | ✅ Complete        |
| Table view            | ✅ Complete        |
| CSV download          | ✅ Complete        |
| PDF download          | ❌ Not Implemented |

---

### 3. Names Unique to APR

| Requirement           | Status            |
| --------------------- | ----------------- |
| Identify unique names | ✅ Complete        |
| Count displayed       | ✅ Complete        |
| Table view            | ✅ Complete        |
| CSV download          | ✅ Complete        |
| PDF download          | ❌ Not Implemented |

---

### 4. Top 80% Overlap Analysis

| Metric               | Status     |
| -------------------- | ---------- |
| JAN top 80% in APR   | ✅ Complete |
| APR top 80% in JAN   | ✅ Complete |
| Both in top 80%      | ✅ Complete |
| Counts & percentages | ✅ Complete |
| Table views          | ✅ Complete |

---