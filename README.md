# Data Cleaning Project

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
   * `service_account.py` or `service_account.json` (depending on your setup)


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
├── .env
├── README.md
├── app.py
├── requirements.txt
├── service_account.json
├── src/
│   ├── __init__.py
│   ├── analytics.py
│   ├── comparison.py
│   ├── datacleaning.py
│   ├── most_common_names.py
│   ├── reports.py
│   └── supabase_data.py
├── static/
│   └── main.js
├── templates/
│   └── index.html
```


## Notes

* Ensure the `.env` file contains all required environment variables before running the app.
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



