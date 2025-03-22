import requests
import argparse
import json



def generate_http_digest_authen(username: str, password: str):
    auth = requests.auth.HTTPDigestAuth(username, password)
    return auth

def isapi_accessctrl_deviceinfo(ipaddr: str, port: int, auth):
    request_url = "http://" + ipaddr + ":" + str(port) + "/ISAPI/System/deviceInfo"
    response = requests.get(request_url, auth=auth)
    return response



if __name__ == "__main__":
    # Initialize parser
    parser = argparse.ArgumentParser()
    # Adding optional argument
    parser.add_argument("-c", "--cfg", help="JSON configuration file for access control", default="config.json")

    # Read arguments from command line
    args = parser.parse_args()
    f_cfg = open(args.cfg)
    cfg = json.load(f_cfg) 
    ipaddr = cfg["ip_address"]
    port = cfg["port_isapi"]
    admin_username = cfg["admin_user"]
    admin_password = cfg["admin_password"]

    # Set the authentication information
    auth = generate_http_digest_authen(admin_username, admin_password)

    # Send the deviceInfo request and receive response
    response = isapi_accessctrl_deviceinfo(ipaddr, port, auth)

    # Output response content
    print(response)
    print(response.text)
    print(response.content)
