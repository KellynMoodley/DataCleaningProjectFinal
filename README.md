# Data Cleaning Project

## IMPORTANT NOTES

There are additional README files to help explain the code in more detail:

* **ProjectREADME** – Explains the code in detail.
* **Assessment_checklistREADME** – Checklist of what was implemented in this task based on the question.
* **ProcessREADME** – The current website does not allow for processing (explained in Assessment_checklistREADME), as processing has already been completed. This README shows examples of the logs after the "Process Sheet" button was pressed.

**Note:** Loading tables and downloading CSVs and PDFs may take some time due to the large datasets and formatting. Please avoid changing operations until the files have finished downloading.


## How to Run the Project (Using a Virtual Environment – Windows)

Follow the steps below to set up and run the application locally.

## Prerequisites

Make sure you have the following installed on your PC:

* **Python 3.x**
* **Git**


## Setup Instructions

### 1. Open Command Prompt

* Press **Windows + R**
* Type `cmd`
* Press **Enter**


### 2. Clone the Repository

Run the command below **exactly as shown**:

```bash
git clone https://github.com/KellynMoodley/DataCleaningProjectFinal.git
```


### 3. Navigate to the Project Folder

```bash
cd DataCleaningProjectFinal
```


### 4. Add Environment Files

1. Open the `DataCleaningProjectFinal` folder on your **Desktop**.
2. Copy and paste the following files into the **main project directory**:

   * `.env`
   *  `service_account.json` 


### 5. Create a Virtual Environment

Run:

```bash
py -m venv venv
```

**If this does not work**, try:

```bash
python -m venv venv
```

(This depends on how Python is installed on your PC.)


### 6. Activate the Virtual Environment

```bash
.\venv\Scripts\activate
```

If successful, you should see `(venv)` at the beginning of the command line.


### 7. Upgrade pip

```bash
pip install --upgrade pip
```


### 8. Install Required Dependencies

```bash
pip install -r requirements.txt
```


### 9. Run the Application

```bash
py app.py
```


### 10. Open the Application in Your Browser

Navigate to:

```
http://127.0.0.1:5000
```


## Project Structure

```
DataCleaningProjectFinal/
├── app.py                      # Main Flask application entry point
├── requirements.txt            # Python dependencies
├── service_account.json        # Google Sheets API credentials
├── .env                        # Environment variables (DB credentials)
├── README.md
├── Extra README
│   ├── Assessment_checklistREADME.md
│   ├── ProcessREADME.md
│   └── ProjectREADME.md
    ├── images                     # images for ProcessREADME.md
        ├── image3.png
        ├── images1.png
        └── images2.png
├── templates/
│   └── index.html             # Main dashboard template
├── static/
│   └── main.js                # Frontend JavaScript logic
└── src/                       # Core modules
    ├── __init__.py            # Package initializer
    ├── supabase_data.py       # Database connection & operations
    ├── datacleaning.py        # Data validation & cleaning logic
    ├── analytics.py           # Analytics table creation & queries
    ├── comparison.py          # JAN vs APR comparison analytics
    ├── reports.py             # CSV/PDF report generation
    └── most_common_names.py   # Top 80% names export
```


## Notes

* Ensure the `.env` file contains all required environment variables before running the app.
* The service_account.json must be added to the project folder as well.
* The virtual environment must be activated every time before running the application.


Tools and Languages: 

Backend- 
•	Python
•	Flask
•	PostgreSQL (Supabase)
•	psycopg2

Frontend- 
•	HTML
•	CSS
•	JavaScript
•	Chart.js

Additional Tools- 
•	Google Sheets API
•	ReportLab (PDF generation)
•	dotenv (environment variables)
•	Jinja2 (templating)
•	Supabase

