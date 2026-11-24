# P17 PropNest — Real Estate Listing and Price Estimator

Academic SEPM demonstration. Flask + SQLite + HTML/CSS + pytest. Synthetic property information only.

## Features
- Property listing, detail view, city/type/search filters
- Rule-based property price estimator (not trained machine learning)
- Buyer enquiry saved locally (no email sent)
- Dashboard with listings, enquiries and average asking price
- Health and metrics JSON endpoints
- 25 automated pytest cases; actual results depend on running the tests

## Windows PowerShell
```powershell
cd "C:\path\to\PropNest"
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```
Open http://127.0.0.1:5000

In a **second terminal**:
```powershell
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=html --cov-report=term-missing
start htmlcov\index.html
```

Do not activate PowerShell scripts if execution policy blocks them; use the Python executable directly.

## SEPM mapping
Requirements and SRS: property listing, discovery, price estimation, enquiries, dashboard. Agile example: Sprint 1 listings/search, Sprint 2 estimator/testing. SDLC: requirements → design → implementation → testing → deployment. Quality: validation, automated tests, CI. Suggested future work: trained regression model with validated market data, login/roles, PostgreSQL, cloud deployment, Docker, Selenium, SonarQube and monitoring. Do not report these as completed unless actually implemented.
