import requests
import time



ipaddr = '192.168.0.101'
request_url = 'http://' + ipaddr + ':80/ISAPI/System/deviceInfo'

# Set the authentication information
admin_username=''
admin_password=''
auth = requests.auth.HTTPDigestAuth(admin_username, admin_password)

# Send the request and receive response
response = requests.get(request_url, auth=auth)

# Output response content
print("authening...\nresponse=\n")
print(response.text)
time.sleep(1)


# After authentication is done successfully,
# find a person management capability.
request_url = 'http://' + ipaddr + ':80/ISAPI/AccessControl/capabilities?format=json'
response = requests.get(request_url)
print(response)
time.sleep(1)



