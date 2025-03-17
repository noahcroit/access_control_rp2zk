import requests



ipaddr = '192.168.0.101'
request_url = 'http://' + ipaddr + ':80/ISAPI/System/deviceInfo'

# Set the authentication information
admin_username='admin'
admin_password='ABC37451977'
auth = requests.auth.HTTPDigestAuth(admin_username, admin_password)

# Send the request and receive response
response = requests.get(request_url, auth=auth)

# Output response content
print(response.text)
