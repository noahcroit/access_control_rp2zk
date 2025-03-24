import json
import xml.etree.ElementTree as ET 
import xmltodict
import requests



class DSK1T105AM():
    def __init__(self, user, password, ipaddr, port):
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
    
    """
    async def room_reserve(self, epoch_start, epoch_end, room_pwd="1234"):
        #print("Unlock start at ", epoch_start, ", end at", epoch_end)
        logging.info("Unlock start at ", epoch_start, ", end at", epoch_end)
        # read epoch time
        diff = epoch_end - epoch_start
        time_current = int(time.time())
        # do nothing until epoch_start
        if time_current <= epoch_start:
            while time_current < epoch_start:
                await asyncio.sleep(3)
                time_current = int(time.time())
            # create temporary user for attendance within period of time, and delete user
            #print("Create temporary user for ", diff, "sec")
            logging.info("Create temporary user for ", diff, "sec")
            self.addUser(name="reserve", userid="100", pwd=room_pwd, userlevel=zk_const.USER_DEFAULT)
            # reserve method
            # "always unlock" or "only add user"
            await self.unlock_delay(duration_sec=diff)
            #await asyncio.sleep(diff)
            self.delUser(userid="100")
        else:
            #print("reserved start time has been passed")
            logging.info("reserved start time has been passed")
    """
    """
    def redisJsonLoad(self, json_string, func="ls"):
        data = json.loads(json_string)
        if func == "ls":
            pass
        elif func == "add":
            uid  = data["id"]
            user = data["username"]
            pwd  = data["password"]
            return uid, user, pwd
        elif func == "del":
            uid  = data["id"]
            user = data["username"]
            return uid, user
        elif func == "reserve":
            epoch_start = int(data["epoch_start"])
            epoch_end = int(data["epoch_end"])
            return epoch_start, epoch_end
    """
