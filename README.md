# DineIQ Analytics

Big Data + Data Science restaurant intelligence platform.
Aptech - Data Science Intelligence Arena.
Reference: DineIQ Analytics SRS v1.0.

## Repository Layout
- app/, run.py, seed.py: backend source (Student 4A)
- tests/: pytest suite
- migrations/: DB migrations
- spark_jobs/, data_generator/: data engineering (Student 1)
- docs/: documentation

## Backend Quick Start
1. py -3.11 -m venv venv
2. venv\Scripts\activate
3. pip install -r requirements.txt
4. flask --app run db upgrade
5. python seed.py
6. python run.py

Server: http://localhost:5000

Default admin:
- email: admin@dineiq.local
- password: Admin@12345

## Tests
pytest -q
Expected: 21 passed.

## Docs
- docs/INFRASTRUCTURE_REPORT.md
- docs/PERMISSIONS_MATRIX.md
- docs/ERROR_CODES.md
- docs/API_CONTRACT.md
- docs/TEST_PLAN.md

## AI Usage
See AI_USAGE.md.
