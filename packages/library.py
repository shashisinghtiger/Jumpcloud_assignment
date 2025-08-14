from configparser import ConfigParser
import csv
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import secrets
import string, os
import csv
from datetime import datetime
import requests

try:
    import jcapiv1
    from jcapiv1.rest import ApiException
except Exception as e:
    raise SystemExit(
        "The JumpCloud SDK (jcapiv1) is not installed. "
        "Install it with:\n"
        "  pip install git+https://github.com/TheJumpCloud/jcapi-python.git#subdirectory=jcapiv1"
    ) from e


def map_manager_UID(userlist):
    data = {}
    for user in userlist:
        hris_id = (user.get("employeeIdentifier") or "").strip()
        email = (user.get("email") or "").strip()
        if hris_id and email:
            data[hris_id] = email
    for user in userlist:
        manager_hris = (user.get("manager") or "").strip()
        user["assigned_manager"] = data.get(manager_hris)
    return userlist

def load_sdk_configuration(config_path: str | Path = "config.ini") -> Tuple[jcapiv1.Configuration, Optional[str]]:
    api_key = os.getenv("API_KEY")
    org_id = os.getenv("ORG_ID") 
    if not api_key:
        cp = ConfigParser()
        read_ok = cp.read(config_path)
        if not read_ok:
            raise FileNotFoundError(f"Config file not found at: {config_path}")
        if not cp.has_section("jumpcloud"):
            raise ValueError("Missing [jumpcloud] section in config.ini")
        api_key = cp.get("jumpcloud", "api_key", fallback="").strip()
        org_id = cp.get("jumpcloud", "org_id", fallback="").strip() or None
    if not api_key:
        raise ValueError(
            "JumpCloud API key missing.Set under [jumpcloud] api_key in config.ini"
        )

    configuration = jcapiv1.Configuration()
    configuration.api_key["x-api-key"] = api_key
    return configuration, org_id

def generate_password(length=16):
    lowers  = string.ascii_lowercase
    uppers  = string.ascii_uppercase
    digits  = string.digits
    symbols = "!@#$%^&*"
    mandatoryKeys = [
            secrets.choice(lowers),
            secrets.choice(uppers),
            secrets.choice(digits),
            secrets.choice(symbols),
        ]
    allKeys = lowers + uppers + digits + symbols
    restKeys = []
    for i in range(length-4):
        restKeys.append(secrets.choice(allKeys))
    password = mandatoryKeys + restKeys
    secrets.SystemRandom().shuffle(password)
    return "".join(password)

def generate_username(firstName:str = "",lastName:str = ""):
    if not firstName.strip() or not lastName.strip():
        return "firstname or lastname is an empty string"
    username = "{}.{}".format(firstName.strip(),lastName.strip())
    return username

def read_users_csv(path):
    users, errors = [], []
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                return [], ["CSV has no header row."]
            for i, row in enumerate(reader, start=2): 
                try:
                    first_name = (row.get("first_name") or "").strip()
                    last_name  = (row.get("last_name") or "").strip()
                    email = (row.get("email") or "").strip()    
                    if not (first_name and last_name and email and "@" in email):
                        raise ValueError("need first_name, last_name, valid email")
                    username = generate_username(first_name,last_name)

                    user = {
                        "firstname": first_name,
                        "lastname":  last_name,
                        "middlename": (row.get("middle_name") or "").strip() or None,
                        "email": email,
                        "username": username,
                        "department": (row.get("department") or "").strip() or None,
                        "jobTitle": (row.get("job_title") or row.get("job_title") or "").strip() or None,
                        "manager": (row.get("manager") or "").strip() or None,
                        "employeeIdentifier": (row.get("hris_id") or "").strip() or None,
                        "costCenter": (row.get("cost_center") or "").strip() or None,
                        "coffeeOrTeaPreference":(row.get("coffee_or_tea_preference") or "").strip() or None,
                        "birthdate":(row.get("birth_date") or "").strip() or None,
                        "hireDate":(row.get("hire_date") or "").strip() or None,
                        "terminationDate": (row.get("termination_date") or "").strip() or None,
                    }
                    work_country= (row.get("work_country") or "").strip() or None

                    home = {
                        "type": "home",
                        "streetAddress":(row.get("home_street_address") or "").strip(),
                        "locality":(row.get("home_city") or "").strip(),
                        "region":(row.get("home_state") or "").strip(),
                        "postalCode":(row.get("home_postal_code") or "").strip(),
                        "country":(row.get("home_country") or "").strip(),
                    }
                    if any(v for k, v in home.items() if k != "type"):
                        user["addresses"] = [home,{"type": "work", "country": work_country}]

                    status = (row.get("employee_status") or "").strip().lower()
                    if status == "active":
                        user["state"] = "ACTIVATED"
                    elif status == "inactive":
                        user["state"] = "SUSPENDED"
                    users.append(user)
                except Exception as e:
                    errors.append(f"Row {i}: {e}")

    except FileNotFoundError:
        return [], [f"File not found: {path}"]
    except UnicodeDecodeError:
        return [], [f"Could not decode '{path}'. Save as UTF-8 or UTF-8-SIG."]
    except Exception as e:
        return [], [f"Unexpected error: {e}"]
    userlist = map_manager_UID(users)
    return userlist, errors

def user_exists(api, email=None, username=None, org_id=None):
    for field, value in (("email", email), ("username", username)):
        if value:
            params = {
                "content_type": "application/json",
                "accept": "application/json",
                "filter": f"{field}:$eq:{value}",
                "limit": 1
            }
            if org_id:  
                params["x_org_id"] = org_id

            resp = api.systemusers_list(**params)
            if resp and getattr(resp, "results", []):
                return resp.results[0].id
    return None

def update_user(api, user_id, body, org_id=None):
    params = {
        "content_type": "application/json",
        "accept": "application/json",
        "id": user_id,
        "body": body
    }
    if org_id:
        params["x_org_id"] = org_id
    try:
        resp = api.systemusers_put(**params)
        return resp, None
    except Exception as e:
        return None, str(e)
    
def create_user(api, body, org_id=None):
    try:
        if org_id is None or org_id == "none":
            created = api.systemusers_post("application/json", "application/json", body=body)
        else:
            created = api.systemusers_post("application/json", "application/json",  body=body, x_org_id=org_id)
        uid = getattr(created,"id")
        if uid:
            return created, None
        else:
            return None, "No user ID in created response."
    except Exception as e:
        return None, str(e)

def load_config(path="config.ini"):
    cp = ConfigParser()
    cp.read(path)
    sec = cp["jumpcloud"]
    api_key  = sec.get("API_KEY")                               
    base_url = sec.get("BASE_URL")
    org_raw = sec.get("ORG_ID", fallback="").strip().lower()
    org_id = None if org_raw in ("", "none", "null") else sec.get("ORG_ID")
    return api_key, base_url, org_id
    
def setAccountStatus(userid: str, state: str):
    if state not in ("ACTIVATED", "SUSPENDED"):
        return False, "state must be 'ACTIVATED' or 'SUSPENDED'"
    API_KEY, API_URL = load_config()[0], load_config()[1]
    url = f"{API_URL}/systemusers/{userid}"
    headers = {"x-api-key": API_KEY, "Accept": "application/json", "Content-Type": "application/json"}
    try:
        r = requests.put(url, headers=headers, json={"state": state}, timeout=30)
        r.raise_for_status()
        return True, None
    except requests.HTTPError:
        try:
            msg = r.json()
        except Exception:
            msg = r.text
        return False, f"{r.status_code} {r.reason} - {msg}"
    except Exception as e:
        return False, str(e) 



def write_log_to_csv(rows):
    filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".csv" 
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print("Log generated: {}".format(filename))    
    return filename


def set_manager(api, user_id: str, manager_uid: str, org_id: str | None = None):
    params = {
        "id": user_id,
        "content_type": "application/json",
        "accept": "application/json",
        "body": {"manager": manager_uid}
    }
    if org_id:
        params["x_org_id"] = org_id

    try:
        resp = api.systemusers_put(**params)
        return resp, None
    except Exception as e:
        return None, str(e)