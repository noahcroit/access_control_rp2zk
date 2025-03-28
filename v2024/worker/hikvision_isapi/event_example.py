import requests
import argparse
import json
import xmltodict
import threading
import time




def generate_http_digest_authen(username: str, password: str):
    auth = requests.auth.HTTPDigestAuth(username, password)
    return auth

def isapi_listen2events(ipaddr, port):
    auth = generate_http_digest_authen(admin_username, admin_password)
    request_url = "http://" + ipaddr + ":" + str(port) + "/ISAPI/Event/notification/alertStream"
    r = requests.get(request_url, stream=True, auth=auth)
    r.raise_for_status()
    for line in r.iter_lines():
        try:
            decoded = line.decode("utf-8")
            print(decoded)
        except:
            # image bytes here ignore them
            continue




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

    t_event = threading.Thread(target=isapi_listen2events, args=(ipaddr, port))
    t_event.start()
    while True:
        print("Waiting for event...")
        time.sleep(10)
    
    
