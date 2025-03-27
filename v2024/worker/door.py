import json
import xml.etree.ElementTree as ET 
import xmltodict
import requests
import threading
import time



class DSK1T105AM():
    def __init__(self, name, user, password, ipaddr, port):
        self.name = name
        self.admin_user = user
        self.admin_password = password
        self.ipaddr = ipaddr
        self.port = port
        self.doorstate = None
        # generate authentication
    
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
   
    def start_listen2event(self, cb):
        self.task_event = threading.Thread(target=self._listen2event, args=(cb,))
        self.task_event.start()

    def _listen2event(self, cb):
        while True:
            auth = self._generate_http_digest_authen(self.admin_user, self.admin_password)
            request_url = "http://" + self.ipaddr + ":" + str(self.port) + "/ISAPI/Event/notification/alertStream"
            r = requests.get(request_url, stream=True, auth=auth)
            r.raise_for_status()

            in_header = False             # are we parsing headers at the moment
            grabbing_response = False     # are we grabbing the response at the moment
            response_size = 0             # the response size that we take from Content-Length
            response_buffer = b""         # where we keep the reponse bytes

            for line in r.iter_lines():
                decoded = ""
                try:
                    decoded = line.decode("utf-8")
                except:
                    # image bytes here ignore them
                    continue
                
                if decoded == "--boundary":                
                    in_header = True

                if in_header:
                    if decoded.startswith("Content-Length"):
                        decoded.replace(" ", "")
                        content_length = decoded.split(":")[1]
                        response_size = int(content_length)

                    if decoded == "":
                        in_header = False
                        grabbing_response = True

                elif grabbing_response:
                    response_buffer += line

                    if len(response_buffer) != response_size:
                        response_buffer += b"\n"
                    else:
                        # time to convert it json and return it
                        grabbing_response = False
                        dic = json.loads(response_buffer)
                        response_buffer = b"" 
                        cb(dic, self.name)
     
