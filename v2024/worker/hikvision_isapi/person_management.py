import requests
import time



ipaddr = '192.168.0.101'
port = 80
request_url = 'http://' + ipaddr + ':' + str(port) + '/ISAPI/System/deviceInfo'

# Set the authentication information
admin_username='admin'
admin_password='ABC37451977'
auth = requests.auth.HTTPDigestAuth(admin_username, admin_password)

# Send the request and receive response
response = requests.get(request_url, auth=auth)

# Output response content
print("authening...\nresponse=\n")
print(response.text)
time.sleep(1)


# After authentication is done successfully,
# find a person management capability.
# Steps
# 1. Request access control capabilities by calling GET /ISAPI/AccessControl/capabilities
# 2. Check if isSupportUserInfo node is True
# 3. If True, we can search, add, delete the users
#
# Send HTTP request
request_url = 'http://' + ipaddr + ':' + str(port) + '/ISAPI/AccessControl/capabilities'
response = requests.get(request_url, auth=auth)
print("\nperson management response=\n")
print(response)
print(response.content)

# Convert XML response to python dict
import xmltodict
tree_dict = xmltodict.parse(response.content)

# Search for node name isSupportUserInfo and its value
def get_all_keys(d):
    for key, value in d.items():
        yield (key, value)
        if isinstance(value, dict):
            yield from get_all_keys(value)

def get_value_from_key(keyname):
    for key, value in get_all_keys(tree_dict):
        if key == keyname:
            return value
    return None
issupport = get_value_from_key('isSupportUserInfo')
print('isSupportUserInfo = ', issupport)

# Try Search, Apply, Add, Edit and Delete user, if device supports the function
if issupport == 'true':
    # Search
    # 1. See the capability by GET /ISAPI/AccessControl/UserInfo/capabilities?format=json
    # 2. supportFunction contains "get"?
    # 3. If it has, Search the number of persons by GET /ISAPI/AccessControl/UserInfo/Count?format=json
    # 4. Search person info by POST /ISAPI/AccessControl/Userinfo/Search?format=json

    # Add
    # 1. GET /ISAPI/AccessControl/UserInfo/capabilities?
    # 2. Check whether it supportFunction contains 'post' or not
    # 3. If it has, add person by POST /ISAPI/AccessControl/UserInfo/Record?format=json
    
    # Delete
    # 1. GET /ISAPI/AccessControl/capabilities
    # 2. Check whether it contains isSupportUserInfoDetailDelete as 'true' or not
    # 3. If it has, delete person by PUT /ISAPI/AccessControl/UserInfoDetail/Delete?format=json
    # 4. Get the progress of deleting by GET /ISAPI/AccessControl/UserInfoDetail/DeleteProcess repeatly
    pass 
    

