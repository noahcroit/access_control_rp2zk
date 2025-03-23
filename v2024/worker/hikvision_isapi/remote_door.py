import requests
import json
import xml.etree.ElementTree as ET 
import time
import argparse



def generate_http_digest_authen(username: str, password: str):
    auth = requests.auth.HTTPDigestAuth(username, password)
    return auth

def generate_xml_doorctrl(cmd):
    namespace = "http://www.isapi.org/ver20/XMLSchema"
    root = ET.Element(f'{{{namespace}}}RemoteControlDoor')
    ET.register_namespace("", namespace)
    root.set("version", "2.0")
    child_cmd = ET.SubElement(root, 'cmd')
    child_cmd.text = cmd
    ET.dump(root)
    return ET.tostring(root, 'utf-8')

def isapi_accessctrl_remote_doorctrl(ipaddr: str, port: int, cmd: str, auth):
    if cmd in ["open", "close", "alwaysOpen", "alwaysClose"]:
        # generate XML string for remote door control
        payload = generate_xml_doorctrl(cmd)
        doorID = 1
        request_url = "http://" + ipaddr + ":" + str(port) + "/ISAPI/AccessControl/RemoteControl/door/" + str(doorID)
        response = requests.put(request_url, data=payload, auth=auth)
        return response
    else:
        return None



if __name__ == '__main__':
    # Initialize parser
    parser = argparse.ArgumentParser()
    # Adding optional argument
    parser.add_argument("-d", "--doorcmd", help="door CMD (open, close, alwaysOpen, alwaysClose)", default="open")
    parser.add_argument("-c", "--cfg", help="JSON configuration file for access control", default="config.json")

    # Read arguments from command line
    args = parser.parse_args()
    f_cfg = open(args.cfg)

    # Authentication Setup
    cfg = json.load(f_cfg)
    ipaddr = cfg["ip_address"]
    port = cfg["port_isapi"]
    admin_username = cfg["admin_user"]
    admin_password = cfg["admin_password"]
    auth = generate_http_digest_authen(admin_username, admin_password)

    # Remote Door Control
    # cmd -> "open, close, alwaysOpen, alwaysClose" 
    cmd=args.doorcmd
    response = isapi_accessctrl_remote_doorctrl(ipaddr, port, cmd, auth)
    print(response.text)

