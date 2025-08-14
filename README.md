# JumpCloud CSV User Importer
Import **new** users and **update** existing JumpCloud users from CSV.

## Quick start

# 1) Clone
git clone https://github.com/shashisinghtiger/Jumpcloud_assignment.git
change direcotry to the project folder - cd Jumpcloud_assignment

# 2) Create venv
python -m venv venv

# Activate the venv (Windows)
.\venv\Scripts\activate 

# 3) Install deps 
pip install -r requirements.txt

> Requires **Python 3.11.4 or later and **Git**

# 4) Configure API Key - PUT YOUR API KEY
Update or create the **config.ini** in the project root with the following inputs:
[jumpcloud]
# REQUIRED
API_KEY = your_jumpcloud_api_key
# OPTIONAL (defaults shown)
BASE_URL = https://console.jumpcloud.com/api
TIMEOUT = 30
ORG_ID = none #update this if using a multi-tenant (NOTE: THIS IS NOT TESTED)

# 5) Run the script
Run the script with the CSV path. Example Usage:
python jumpcloud_import.py <users.csv>


## CSV format

At minimum include these headers (case‑insensitive):

- `firstname`, `lastname`, `email`

Optional columns that will be used when present: 

middle_name
department
job_title
manager
hris_id
cost_center
birth_date
coffee_or_tea_preference
hire_date
termination_date
employee_status
home_street_address
home_city
home_state
home_postal_code
home_country
work_country


## What the script does (high level):
- Reads `config.ini` and connects to JumpCloud Admin API.
- Parses the CSV and normalizes values.
- **If user exists** (by email/username): updates profile fields as mentioned in the csv.
- **If user does not exist**: creates the user and sets passwords, optional fields and custom attributes.


## Troubleshooting (quick)
- **401/403**: Check `API_KEY` 
- **Import hangs/fails**: Ensure the venv is active and dependencies installed.
