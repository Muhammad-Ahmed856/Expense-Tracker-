# Expense Tracker

A simple command-line Expense Tracker built in Python. It lets users register, login, add/edit/delete expenses, set budgets, view spending summaries, and get financial insights. User data is stored locally per-user in `user_data/`.

## Features

- User registration and login with hashed passwords
- Add, edit, delete expenses with categories and dates
- Set budgets (daily/weekly/monthly) and view budget status
- Spending summary and financial insights
- Exports data as JSON in `user_data/<username>/expenses.json`

## Requirements

- Python 3.8+
- No external libraries required (uses Python standard library only)

## Quick start (Windows)

1. (Optional) Create and activate a virtual environment:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1   # PowerShell
# or
venv\Scripts\activate.bat    # cmd.exe
```

2. Install requirements (none for this project, but keep the step if you add dependencies later):

```powershell
pip install -r requirements.txt
```

3. Run the app:

```powershell
python Expense_Tracker.py
```

## Project layout

- `Expense_Tracker.py` - main application
- `user_data/` - per-user data directory (created at runtime)
- `users.json` - registered users (created at runtime)

Note: `user_data/` and `users.json` are excluded from version control via `.gitignore` to avoid committing sensitive data.

