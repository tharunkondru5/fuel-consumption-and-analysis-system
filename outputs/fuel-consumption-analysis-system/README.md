# Fuel Consumption Analysis System

A beginner-friendly Flask application for managing vehicles and fuel fills, calculating fuel efficiency, and comparing vehicles. MySQL stores the data; pandas and NumPy calculate summaries; Matplotlib creates the monthly mileage chart.

## Project layout

```text
fuel-consumption-analysis-system/
├── app.py                 # Flask routes, validation and analysis
├── schema.sql             # MySQL tables
├── data/sample_data.sql   # Example vehicles and fills
├── templates/dashboard.html
├── static/style.css
├── requirements.txt
├── .env.example           # Database settings template
├── .gitignore
└── README.md
```

## Requirements

- Python 3.10 or newer
- MySQL Server 8.0 or newer and a MySQL user
- Git (only needed to publish the project)

## Run on Windows PowerShell

1. Open PowerShell in this project folder.
2. Create and activate a virtual environment:

   ```powershell
   py -3 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that PowerShell window, then activate again.

3. Install libraries:

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Create the MySQL database and tables. Replace `root` with your MySQL user if needed:

   ```powershell
   mysql -u root -p < schema.sql
   mysql -u root -p fuel_analysis < data/sample_data.sql
   ```

   The second command inserts two sample vehicles and dated fuel fills. Sample records include both full and partial fills.

5. Copy `.env.example` to `.env` and edit `DB_USER` and `DB_PASSWORD` to match your local MySQL account. Keep `.env` private; Git ignores it.

   ```powershell
   Copy-Item .env.example .env
   notepad .env
   ```

6. Start the web app:

   ```powershell
   python app.py
   ```

7. Open the local address printed in PowerShell (usually `http://127.0.0.1:5000`). Press `Ctrl+C` to stop it.

## Using the app

- Add a vehicle with a unique code, type, and fuel type.
- Record each fill with date, odometer, litres, total cost, and whether the tank was filled completely.
- The app rejects zero/negative litres, negative cost or odometer, dates earlier than the latest vehicle record, and odometer readings that do not increase.
- Full-tank mileage is calculated between successive full-tank records. It divides odometer distance by all litres purchased in that interval, including partial fills. This is the preferred comparison because the tank starts and ends full.
- For a partial fill, displayed distance divided by that fill's litres is only an approximate indicator; the amount of fuel remaining in the tank is unknown. The dashboard labels it approximate and excludes it from vehicle comparisons and the monthly mileage chart.
- Fuel expense totals include all saved fills. The first record for each vehicle is a baseline and has no distance/mileage result.

## Git: save and push the project

Initialize and make your first local commit:

```powershell
git init
git add .
git commit -m "Build fuel consumption analysis app"
```

Create an empty repository on GitHub (do not add a README/license there), then copy its HTTPS or SSH URL. Connect it and push:

```powershell
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/fuel-consumption-analysis.git
git push -u origin main
```

Replace the example URL with your repository's actual URL. GitHub may ask you to authenticate through a browser or SSH key. If `origin` already exists, check it with `git remote -v` and use `git remote set-url origin <your-repository-url>` instead of adding it again.

## Notes

This is a local learning project. Before hosting it publicly, set a strong secret key, turn off Flask debug mode, and use a database account with only the permissions the application needs.
