# Database Runbook

## Local Setup Commands

Run these from the repository root.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
python scripts/check_connection.py
python scripts/run_migrations.py
```

The migration runner applies table migrations and then the review view in
`db/views/v_glossary_flat.sql`.
