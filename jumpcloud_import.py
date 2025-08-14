import json
from packages.library import write_log_to_csv , generate_password, load_sdk_configuration , read_users_csv, setAccountStatus , user_exists , update_user ,set_manager,  create_user
import jcapiv1 , datetime

import sys

if len(sys.argv) <= 1:
    print("Error: Please provide a CSV path.\nUsage: python create_user.py <users.csv>")
    sys.exit(2)

csv_path = sys.argv[1]

configuration,org_id = load_sdk_configuration()


userlist, errorList = read_users_csv(path=csv_path)
employee_manager_pair = [{"emp": user["email"], "manager": user.get("assigned_manager")} for user in userlist]

api = jcapiv1.SystemusersApi(jcapiv1.ApiClient(configuration))
execution_result = []

for user in userlist:
    _result = {
        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "username" : user.get("username"),
        "Status" : "",
        "Action" : "",
        "API_Response": ""
    }
    try:
        raw_data = {
            "firstname": user.get("firstname"),
            "lastname": user.get("lastname"),
            "middlename": user.get("middlename"),
            "email": user.get("email"),
            "username": user.get("username"),
            "department": user.get("department"),
            "job_title": user.get("jobTitle"),
            "employee_identifier": user.get("employeeIdentifier"),
            "cost_center": user.get("costCenter"),
            "addresses": user.get("addresses"),
            "password": generate_password(),
            
        }
        attributes_list = []
        if user.get("coffeeOrTeaPreference") is not None:
            attributes_list.append({"name": "coffeeOrTeaPreference", "value": user.get("coffeeOrTeaPreference")})
        if user.get("birthdate") is not None:
            attributes_list.append({"name": "birthdate", "value": user.get("birthdate")})    
        if user.get("hireDate") is not None:
            attributes_list.append({"name": "hireDate", "value": user.get("hireDate")})  
        if user.get("terminationDate") is not None:
            attributes_list.append({"name": "terminationDate", "value": user.get("terminationDate")})
        
        raw_data["attributes"] = attributes_list

        user_state = user.get("state")

        clean_data = {k: v for k, v in raw_data.items() if v not in (None, "", [], {})}
        user_id = user_exists(api,email=clean_data["email"],username=clean_data["username"])
        if user_id is None:
            _result["Action"] = "Create"
            body = jcapiv1.Systemuserputpost(**clean_data)
            resp, err = create_user(api, body)
            if err:
                _result["Status"] = "Error"
                _result["API_Response"] = "User creation failed for {}".format(raw_data['email'])
            else:
                _result["Status"] = "Success"
                if user_state is not None:
                    setAccountStatus(resp.id, user_state)       
        else:
            _result["Action"] = "Update"
            exclude_keys = {"email", "username", "firstname", "lastname"}
            clean_data = {k: v for k, v in raw_data.items() if v not in (None, "", [], {}) and k not in exclude_keys}
            resp, err = update_user(api,user_id,clean_data)
            if err:
                _result["Status"] = "Error"
                _result["API_Response"] = "Exception: {}".format(err)                
            else:
                _result["Status"] = "Success"
        if user_state is not None:
            setAccountStatus(user_id, user_state)
        if user is userlist[-1]:
            for emp in employee_manager_pair:
                emp_uid = user_exists(api,emp["emp"])
                manager_uid = user_exists(api,emp["manager"])
                set_manager(api,emp_uid,manager_uid)
    except Exception as e:
        _result["Status"] = "Error"
        _result["API_Response"] = "Exception: {}".format(e.__str__())    
    finally:
        execution_result.append(_result)



if len(execution_result) > 0:
    write_log_to_csv(execution_result)


