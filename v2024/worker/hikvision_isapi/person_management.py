import requests
import json
import xmltodict
import time
import argparse



def generate_http_digest_authen(username: str, password: str):
    auth = requests.auth.HTTPDigestAuth(username, password)
    return auth

def isapi_accessctrl_deviceinfo(ipaddr: str, port: int, auth):
    request_url = "http://" + ipaddr + ":" + str(port) + "/ISAPI/System/deviceInfo"
    response = requests.get(request_url, auth=auth)
    return response

def isapi_accessctrl_capabilities(ipaddr: str, port: int, auth):
    request_url = "http://" + ipaddr + ":" + str(port) + "/ISAPI/AccessControl/capabilities"
    response = requests.get(request_url, auth=auth)
    return response

def isapi_accessctrl_countuser(ipaddr: str, port: int, auth):
    # Count
    # 1. See the capability by GET /ISAPI/AccessControl/UserInfo/capabilities?format=json
    # 2. supportFunction contains "get"?
    # 3. If it has, Search the number of persons by GET /ISAPI/AccessControl/UserInfo/Count?format=json
    request_url = "http://" + ipaddr + ":" + str(port) + "/ISAPI/AccessControl/UserInfo/capabilities?format=json"
    response = requests.get(request_url, auth=auth)
    res_json = json.loads(response.content)
    opts = res_json["UserInfo"]["supportFunction"]["@opt"]
    if 'get' in opts:
        print("get option exists in supportFunction")
        # Get the total number of persons in device
        request_url = "http://" + ipaddr + ":" + str(port) + "/ISAPI/AccessControl/UserInfo/Count?format=json"
        response = requests.get(request_url, auth=auth)
        res_json = json.loads(response.content)
        return res_json
    else:
        return None
    
def isapi_accessctrl_searchuser(ipaddr: str, port: int, auth, user):
    # Search
    # 1. See the capability by GET /ISAPI/AccessControl/UserInfo/capabilities?format=json
    # 2. supportFunction contains "get"?
    # 3. Search person info by POST /ISAPI/AccessControl/Userinfo/Search?format=json    
    request_url = "http://" + ipaddr + ":" + str(port) + "/ISAPI/AccessControl/UserInfo/capabilities?format=json"
    response = requests.get(request_url, auth=auth)
    res_json = json.loads(response.content)
    opts = res_json["UserInfo"]["supportFunction"]["@opt"]
    if 'get' in opts:
        print("get option exists in supportFunction")
        body = generate_payload_searchuser(user)
        request_url = "http://" + ipaddr + ":" + str(port) + "/ISAPI/AccessControl/UserInfo/Search?format=json"
        response = requests.post(request_url, data=json.dumps(body), auth=auth)
        res_json = json.loads(response.content)
        return res_json
    else:
        return None

def isapi_accessctrl_adduser(ipaddr: str, port: int, auth, user):
    # Add
    # 1. GET /ISAPI/AccessControl/UserInfo/capabilities?
    # 2. Check whether it supportFunction contains 'post' or not
    # 3. If it has, add person by POST /ISAPI/AccessControl/UserInfo/Record?format=json
    request_url = "http://" + ipaddr + ":" + str(port) + "/ISAPI/AccessControl/UserInfo/capabilities?format=json"
    response = requests.get(request_url, auth=auth)
    res_json = json.loads(response.content)
    opts = res_json["UserInfo"]["supportFunction"]["@opt"]
    
    if "post" in opts:
        print("POST option exists in supportFunction")
        print("Try adding user")
        body = generate_payload_adduser(user)
        request_url = "http://" + ipaddr + ":" + str(port) + "/ISAPI/AccessControl/UserInfo/Record?format=json"
        response = requests.post(request_url, data=json.dumps(body), auth=auth)
        res_json = json.loads(response.content)
        return res_json
    else:
        return None

def isapi_accessctrl_updateuser(ipaddr: str, port: int, auth, user):
    # Add
    # 1. GET /ISAPI/AccessControl/UserInfo/capabilities?
    # 2. Check whether it supportFunction contains 'put' or not
    # 3. If it has, add person by POST /ISAPI/AccessControl/UserInfo/Record?format=json
    request_url = "http://" + ipaddr + ":" + str(port) + "/ISAPI/AccessControl/UserInfo/capabilities?format=json"
    response = requests.get(request_url, auth=auth)
    res_json = json.loads(response.content)
    opts = res_json["UserInfo"]["supportFunction"]["@opt"]
    
    if "put" in opts:
        print("PUT option exists in supportFunction")
        print("Try updating user")
        body = generate_payload_adduser(user)
        request_url = "http://" + ipaddr + ":" + str(port) + "/ISAPI/AccessControl/UserInfo/Modify?format=json"
        response = requests.put(request_url, data=json.dumps(body), auth=auth)
        res_json = json.loads(response.content)
        return res_json
    else:
        return None

def isapi_accessctrl_deleteuser(ipaddr: str, port: int, auth, user):
    # Delete
    # 1. GET /ISAPI/AccessControl/UserInfo/capabilities?
    # 2. Check whether it supportFunction contains 'delete' or not
    # 3. If it has, delete person by PUT /ISAPI/AccessControl/UserInfo/Delete?format=json
    request_url = "http://" + ipaddr + ":" + str(port) + "/ISAPI/AccessControl/UserInfo/capabilities?format=json"
    response = requests.get(request_url, auth=auth)
    res_json = json.loads(response.content)
    opts = res_json["UserInfo"]["supportFunction"]["@opt"]
    if "delete" in opts:
        print("DELETE option exists in supportFunction")
        print("Try deleting user")
        body = generate_payload_deleteuser(user)
        request_url = "http://" + ipaddr + ":" + str(port) + "/ISAPI/AccessControl/UserInfo/Delete?format=json"
        response = requests.put(request_url, data=json.dumps(body), auth=auth)
        res_json = json.loads(response.content)
        return res_json 
    else:
        return None

def get_all_keys(d):
    for key, value in d.items():
        yield (key, value)
        if isinstance(value, dict):
            yield from get_all_keys(value)

def get_value_from_key(keyname, tree):
    for key, value in get_all_keys(tree):
        if key == keyname:
            return value
    return None

def generate_payload_adduser(user, user_type="normal"):
    body = {
        "UserInfo":
            {
                "employeeNo":str(user["employeeID"]),
                "name": user["name"],
                "userType": user_type,
                "Valid":{
                    "enable": user["valid"]["enable"] == "true",
                    "beginTime": user["valid"]["beginTime"],
                    "endTime": user["valid"]["endTime"],
                    "timeType":"local"
                    },
                "doorRight": "1",
                "RightPlan": [
                    {
                        "doorNo": 1,
                        "planTemplateNo": "1"
                    }
                ],
                
                "password":user["password"],
                "gender":user["gender"]
            }
        }
    return body

def generate_payload_searchuser(user):
    body = {
        "UserInfoSearchCond": {
            "searchID": "4",
            "searchResultPosition": 0,
            "maxResults": 32,
            "EmployeeNoList":[
                {
                    "employeeNo": str(user["employeeID"])
                }
            ]
        }
    }
    return body

def generate_payload_deleteuser(user):
    body = {
        "UserInfoDelCond": {                        
            "EmployeeNoList":[
                {
                    "employeeNo": str(user["employeeID"])
                }
            ]
        }
    }
    return body



if __name__ == '__main__':
    # Initialize parser
    parser = argparse.ArgumentParser()
    # Adding optional argument
    parser.add_argument("-m", "--mode", help="count, search, add, update, delete", default="count")
    parser.add_argument("-c", "--cfg", help="JSON configuration file for access control", default="config.json")
    parser.add_argument("-u", "--user", help="JSON user file. contains employeeID, name, pwd, gender, time etc.", default="user.json")

    # Read arguments from command line
    args = parser.parse_args()
    f_cfg = open(args.cfg)
    if not args.mode == "count": 
        f_user = open(args.user)
        user = json.load(f_user) 

    # Authentication Setup
    cfg = json.load(f_cfg)
    ipaddr = cfg["ip_address"]
    port = cfg["port_isapi"]
    admin_username = cfg["admin_user"]
    admin_password = cfg["admin_password"]
    auth = generate_http_digest_authen(admin_username, admin_password)

    # Connection test by sending the deviceInfo request
    response = isapi_accessctrl_deviceinfo(ipaddr, port, auth)
    print(response)
    print(response.text)
    
    

    # Find a Person Management capability.
    # Steps
    # 1. Request access control capabilities by calling GET /ISAPI/AccessControl/capabilities
    # 2. Check if isSupportUserInfo node is true
    #
    response = isapi_accessctrl_capabilities(ipaddr, port, auth)
    print("\nperson management response=%s", response)
    print("\n content (XML format)=\n")
    print(response.text)
    # Convert XML response to python dict
    tree_dict = xmltodict.parse(response.content)
    issupport = get_value_from_key("isSupportUserInfo", tree_dict)
    print("isSupportUserInfo = ", issupport)


    
    # If isSupportUserInfo is true,
    # Try Search, Apply, Add, Edit and Delete user, if device supports the function
    if issupport == "true":
        if args.mode == "count":
            print("\n\nCounting the number of users")
            result = isapi_accessctrl_countuser(ipaddr, port, auth)
            print(result)
            
        if args.mode == "search": 
            print("\n\nSearching User")
            result = isapi_accessctrl_searchuser(ipaddr, port, auth, user)
            print(result)
    
        if args.mode == "add":
            print("\n\nAdding User")
            result =  isapi_accessctrl_adduser(ipaddr, port, auth, user)
            print(result)
        
        if args.mode == "update":
            print("\n\nUpdating User")
            result =  isapi_accessctrl_updateuser(ipaddr, port, auth, user)
            print(result)

        if args.mode == "delete":
            print("\n\nDeleting User")
            result =  isapi_accessctrl_deleteuser(ipaddr, port, auth, user)
            print(result)
