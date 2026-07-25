Write-Host "Bootstrapping Python Repository (Native Windows Mode)..." -ForegroundColor Green

# 1. Environment template initialization
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env -ErrorAction Ignore
}

# 2. Virtual environment provisioning
if (-not (Test-Path .venv)) {
    python -m venv .venv
}

# 3. Core dependency installation
& .venv\Scripts\pip install --upgrade pip
& .venv\Scripts\pip install -r requirements.txt

# 4. Git hook registration
& .venv\Scripts\pre-commit install

# 5. Core smoke test validation
& .venv\Scripts\python smoke_test.py

Write-Host "Bootstrap Complete." -ForegroundColor Green
