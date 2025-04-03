import requests
import argparse
import json
import xmltodict
import threading
import time



class decoder_statemachine:
    def __init__(self):
        self.state = "IDLE"
        self.response_buffer = b""
        self.response_size = 0

    def reset(self):
        self.response_buffer = b""
        self.response_size = 0
        self.state = "IDLE"
    
    def step(self, line):
        decoded = ""
        try:
            decoded = line.decode("utf-8")
            #print(decoded)
        except:
            # image bytes here ignore them
            pass

        if self.state == "IDLE":
            if decoded == "--boundary":
                self.state = "HEADER"
            return None

        elif self.state == "HEADER":
            if decoded.startswith("Content-Length"):
                decoded.replace(" ", "")
                content_length = decoded.split(":")[1]
                self.response_size = int(content_length)
            if decoded == "{":
                self.state = "BODY"
                self.response_buffer += line
                self.response_buffer += b"\n"
            return None

        elif self.state == "BODY":
            self.response_buffer += line
            if len(self.response_buffer) < self.response_size:
                self.response_buffer += b"\n"
            else:
                self.state = "EOM"
            return None

        elif self.state == "EOM":
            if decoded == "--boundary":
                event_json = json.loads(self.response_buffer)
                self.reset()
                return event_json
            return None



def generate_http_digest_authen(username: str, password: str):
    auth = requests.auth.HTTPDigestAuth(username, password)
    return auth

def isapi_listen2events(ipaddr, port, username, password):
    s = decoder_statemachine()
    auth = generate_http_digest_authen(username, password)
    request_url = "http://" + ipaddr + ":" + str(port) + "/ISAPI/Event/notification/alertStream"
    r = requests.get(request_url, stream=True, auth=auth)
    r.raise_for_status()
    for line in r.iter_lines(chunk_size=1):
        ret = s.step(line)
        if ret != None:
            print(ret) 


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
    username = cfg["admin_user"]
    password = cfg["admin_password"]

    t_event = threading.Thread(target=isapi_listen2events, args=(ipaddr, port, username, password))
    t_event.start()
    while True:
        print("Waiting for event...")
        time.sleep(10)
    
    
