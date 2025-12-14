DataCleaningProjectFinal/
├── .env
├── README.md
├── app.py
├── requirements.txt
├── service_account.json
├── src
│   ├── __init__.py
│   ├── analytics.py
│   ├── comparison.py
│   ├── datacleaning.py
│   ├── most_common_names.py
│   ├── reports.py
│   └── supabase_data.py
├── static
│   └── main.js
├── templates
│   └── index.html



## ✅ Assessment Completion Checklist


## 📦 Repository & Application Setup

* ✔ Public GitHub repository with full source code
* ✔ Python 3.x backend application
* ✔ `requirements.txt` provided
* ✔ Application runs locally without modification
* ✔ Clear, modular project structure
* ✔ Single entry point (`app.py`)
* ✔ Reusable data-processing logic shared across datasets
* ✔ Upload-based workflow (no hardcoded file paths)

---

## 🧹 Data Cleaning & Validation (JAN Dataset)

* ✔ Loaded `clients_2025_01_JAN.csv`
* ✔ Generated a UUID-based `row_id` for every record
* ✔ Preserved `row_id` across included and excluded datasets

### Validation Rules Implemented

* ✔ Name validation:

  * ✔ Only English A–Z characters allowed
  * ✔ Spaces allowed
  * ✔ Digits, punctuation, accents, and emojis excluded
* ✔ Name length validation:

  * ✔ Excluded names shorter than 3 characters
* ✔ Numeric validation:

  * ✔ `birth_day`, `birth_month`, `birth_year` required and numeric
* ✔ Range validation:

  * ✔ `birth_day` must be 1–31
  * ✔ `birth_month` must be 1–12
* ✔ Birth year validation:

  * ✔ Excluded records with `birth_year < 1940`
* ✔ All invalid rows routed to exclusion report with clear reasons
* ✔ Multiple validation failures handled and documented

---

## 📑 Included & Excluded Reports

* ✔ **Data Included Report**

  * ✔ Validated and cleaned records only
  * ✔ Columns: `row_id, name, birth_day, birth_month, birth_year`
* ✔ **Data Exclusion Report**

  * ✔ Original raw values preserved
  * ✔ `exclusion_reason` included
  * ✔ `row_id` maintained for traceability
* ✔ Both reports accessible from the web dashboard



## 📊 Dashboard Features (JAN Dataset)

### Included Data View

* ✔ Interactive table with sorting
* ✔ Column filtering and search
* ✔ Download included data as:

  * ✔ CSV
  * ✔ PDF (full row_id visible)

### Excluded Data View

* ✔ Separate table for excluded rows
* ✔ Displays exclusion reasons per row
* ✔ Download excluded data as:

  * ✔ CSV
  * ✔ PDF


## 📈 Summary Analytics

* ✔ Original dataset row count
* ✔ Included row count
* ✔ Excluded row count
* ✔ Percentage included vs original
* ✔ Percentage excluded vs original
* ✔ Total unique names
* ✔ Unique birthday combinations (`day + month + year`)
* ✔ Unique combinations:

  * ✔ Name + birth_year
  * ✔ Name + birth_month
  * ✔ Name + birth_day
* ✔ Detection of duplicate records where ≥2 fields match
* ✔ Grouped views of duplicate combinations


## 📉 Visualisations

* ✔ At least one chart displaying dataset distribution
  *(e.g. count of records per birth year or birth month)*


## 🔝 Top 80% Most Common Names (JAN Dataset)

* ✔ Name frequencies calculated from final included data
* ✔ Names sorted by descending frequency
* ✔ Top group selected to cover 80% of included records
* ✔ Dedicated dashboard view for top 80% names
* ✔ Downloadable outputs provided:

  * ✔ CSV
  * ✔ JSON



## 📤 Generic Upload & APR Dataset Processing

* ✔ CSV upload supported via web UI
* ✔ Schema validation enforced (`name, birth_day, birth_month, birth_year`)
* ✔ Same cleaning rules reused for all uploads
* ✔ Automatic generation of:

  * ✔ Included report
  * ✔ Excluded report
  * ✔ Summary analytics
  * ✔ Top 80% most common names
* ✔ Successfully tested with `clients_2025_04_APR.csv`


## 🔍 JAN vs APR Dataset Comparison

* ✔ Count of names appearing in both JAN and APR datasets
* ✔ Identification of names unique to JAN
* ✔ Identification of names unique to APR
* ✔ Dashboard views for:

  * ✔ Common names
  * ✔ Unique-to-JAN names
  * ✔ Unique-to-APR names
* ✔ Downloadable reports:

  * ✔ Unique-to-JAN (CSV, optional PDF)
  * ✔ Unique-to-APR (CSV, optional PDF)

### Top 80% Overlap Analysis

* ✔ JAN top-80% names compared against APR dataset
* ✔ APR top-80% names compared against JAN dataset
* ✔ Overlap counts displayed
* ✔ Lists/tables available for inspection


🧠 Code Quality & UX

* ✔ Modular Python design (cleaning, analytics, reporting, comparison)
* ✔ Clear function and variable naming
* ✔ Centralised validation logic
* ✔ Error handling for invalid uploads and missing columns
* ✔ All records traceable via `row_id`
* ✔ Simple, usable dashboard UI


