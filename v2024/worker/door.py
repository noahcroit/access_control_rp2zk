import json
import xml.etree.ElementTree as ET 
import xmltodict
import requests
import threading
import time
import redis



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



class DSK1T105AM():
    def __init__(self, name, user, password, ipaddr, port, redis_url, redis_port, redis_password):
        self.name = name
        self.admin_user = user
        self.admin_password = password
        self.ipaddr = ipaddr
        self.port = port
        self.islocked = None
        # REDIS for event (non-async)
        self.pub = redis.Redis(host=redis_url, port=redis_port, password=redis_password)
        self.tagname_event = "tag:access_control." + self.name + ".event"
        self.isapi_doorctrl("close")
        self.islocked = True 
    
    @staticmethod
    def _generate_http_digest_authen(username: str, password: str):
        auth = requests.auth.HTTPDigestAuth(username, password)
        return auth
    
    @staticmethod
    def _generate_xml_doorctrl(cmd):
        namespace = "http://www.isapi.org/ver20/XMLSchema"
        root = ET.Element(f'{{{namespace}}}RemoteControlDoor')
        ET.register_namespace("", namespace)
        root.set("version", "2.0")
        child_cmd = ET.SubElement(root, 'cmd')
        child_cmd.text = cmd
        ET.dump(root)
        return ET.tostring(root, 'utf-8')
    
    @staticmethod
    def _generate_payload_adduser(employeeID: int, 
                                    username: str,
                                    password: str,
                                    validEnable=False,
                                    beginTime="2025-01-01T00:00:01",
                                    endTime="2026-01-01T00:00:01",
                                    gender="male",
                                    user_type="normal"):
        body = {
            "UserInfo":
                {
                    "employeeNo":str(employeeID),
                    "name": username,
                    "userType": user_type,
                    "Valid":{
                        "enable": validEnable,
                        "beginTime": beginTime,
                        "endTime": endTime,
                        "timeType":"local"
                        },
                    "doorRight": "1",
                    "RightPlan": [
                        {
                            "doorNo": 1,
                            "planTemplateNo": "1"
                        }
                    ],
                    
                    "password":password,
                    "gender":gender
                }
            }
        return body

    @staticmethod
    def _generate_payload_deleteuser(employeeID: int):
        body = {
            "UserInfoDelCond": {                        
                "EmployeeNoList":[
                    {
                        "employeeNo": str(employeeID)
                    }
                ]
            }
        }
        return body
    
    @staticmethod
    def _generate_payload_searchuser(employeeID: int):
        body = {
            "UserInfoSearchCond": {
                "searchID": "4",
                "searchResultPosition": 0,
                "maxResults": 32,
                "EmployeeNoList":[
                    {
                        "employeeNo": str(employeeID)
                    }
                ]
            }
        }
        return body

    def isapi_deviceinfo(self):
        auth = self._generate_http_digest_authen(self.admin_user, self.admin_password)
        request_url = "http://" + self.ipaddr + ":" + str(self.port) + "/ISAPI/System/deviceInfo"
        response = requests.get(request_url, auth=auth)
        return response
    
    def isapi_doorctrl(self, cmd: str):
        if cmd in ["open", "close", "alwaysOpen", "alwaysClose"]:
            if cmd == "alwaysOpen":
                self.islocked = False
            else:
                self.islocked = True
    
            # generate XML string for remote door control
            payload = self._generate_xml_doorctrl(cmd)
            doorID = 1
            auth = self._generate_http_digest_authen(self.admin_user, self.admin_password)
            request_url = "http://" + self.ipaddr + ":" + str(self.port) + "/ISAPI/AccessControl/RemoteControl/door/" + str(doorID)
            response = requests.put(request_url, data=payload, auth=auth)
            return response
        else:
            return None
    
    def isapi_searchUser(self, employeeID):
        auth = self._generate_http_digest_authen(self.admin_user, self.admin_password)
        body = self._generate_payload_searchuser(employeeID)
        request_url = "http://" + self.ipaddr + ":" + str(self.port) + "/ISAPI/AccessControl/UserInfo/Search?format=json"
        response = requests.post(request_url, data=json.dumps(body), auth=auth)
        res_json = json.loads(response.content)
        if res_json["UserInfoSearch"]["responseStatusStrg"] == "NO MATCH":
            return False
        else:
            return True

    def isapi_addUser(self, employeeID, username, password, valid=False, begin="", end=""):
        auth = self._generate_http_digest_authen(self.admin_user, self.admin_password)
        body = self._generate_payload_adduser(employeeID, username, password, valid, begin, end)
        request_url = "http://" + self.ipaddr + ":" + str(self.port) + "/ISAPI/AccessControl/UserInfo/Record?format=json"
        response = requests.post(request_url, data=json.dumps(body), auth=auth)
        res_json = json.loads(response.content)
        return res_json

    def isapi_delUser(self, employeeID, username=""):
        if employeeID > 1:
            auth = self._generate_http_digest_authen(self.admin_user, self.admin_password)
            # delete only user, not admin (ID=1)
            body = self._generate_payload_deleteuser(employeeID)
            request_url = "http://" + self.ipaddr + ":" + str(self.port) + "/ISAPI/AccessControl/UserInfo/Delete?format=json"
            response = requests.put(request_url, data=json.dumps(body), auth=auth)
            res_json = json.loads(response.content)
            return res_json
        else:
            return None

    def generate_otp(self):
        import random
        otp = "".join([random.choice("0123456789") for _ in range(8)])
        return otp

    def isDoorLock(self):
        pass
   
    def start_listen2event(self):
        self.task_event = threading.Thread(target=self._listen2event, args=())
        self.task_event.start()

    @staticmethod
    def _listen2event(self):
        s = decoder_statemachine()
        auth = self._generate_http_digest_authen(self.admin_user, self.admin_password)
        request_url = "http://" + self.ipaddr + ":" + str(self.port) + "/ISAPI/Event/notification/alertStream"
        r = requests.get(request_url, stream=True, auth=auth)
        r.raise_for_status()
        for line in r.iter_lines(chunk_size=1):
            event_json = s.step(line)
            if event_json != None:
                self._publish_event(event_json) 

    @staticmethod
    def _publish_event(self, event):
        print("Event incoming from device:", self.name)
        print(event)
        event_type = event["eventType"]
        data = {}
        
        try:
            if event_type == "AccessControllerEvent":
                card_id = event["AccessControllerEvent"]["cardNo"]
                if not card_id == "":
                    data.update({"card_id" : event["AccessControllerEvent"]["cardNo"]})
                    data.update({"access_id" : event["AccessControllerEvent"]["employeeNoString"]})
                    timestamp = event["dateTime"]
                    d = {}
                    d.update({"event_type" : event_type})
                    d.update({"device" : self.name})
                    d.update({"data" : data})
                    d.update({"timestamp" : timestamp})
                    message = json.dumps(d)
                    self.pub.publish(self.tagname_event, message)
                else:
                    print("An event with empty Card ID")
        except Exception as e:
            print(e)
        
