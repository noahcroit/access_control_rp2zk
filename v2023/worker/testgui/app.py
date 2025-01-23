import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from qt_supportsw import Ui_Form
import asyncio
import aioredis
import json
import threading
from datetime import datetime



def convert_to_epoch(date_str):
  """Converts a string of date in the format YYYY-MM-DD HH:MM:SS to epoch.

  Args:
      date_str: The string of date to convert.

  Returns:
      The epoch timestamp of the date.
  """
  date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
  epoch_time = int(date_obj.timestamp())
  return epoch_time



class AccessControlSupportSW_UI():
    def __init__(self):
        self.form = QWidget()
        self.ui = Ui_Form()
        self.ui.setupUi(self.form)
        self.ui.pushButtonFailsecureLock.clicked.connect(self.button_handler_failsecuretoggle)
        self.ui.pushButtonZkListUser.clicked.connect(self.button_handler_userinfo)
        self.ui.pushButtonZkAdduser.clicked.connect(self.button_handler_adduser)
        self.ui.pushButtonZkDeluser.clicked.connect(self.button_handler_deluser)
        self.ui.pushButtonZkReserve.clicked.connect(self.button_handler_reserve)
        self.ui.pushButtonZkLock.clicked.connect(self.button_handler_locktoggle)
        self.ui.labelOTP.setText("")
        now = datetime.now()
        formatted_datetime = now.strftime("%Y-%m-%d %H:%M:%S")
        self.ui.lineEditTimeStart.setText(formatted_datetime)
        self.lockstate = False
        self.toggle_lockzk = False
        self.redis = aioredis.from_url('redis://192.168.8.104:6379', username="default", password="ictadmin")
        self.rpubsub = self.redis.pubsub()
        self.q_rpub = []
        self.lockstate_zk = False

    def show(self):
        self.form.show()

    def button_handler_failsecuretoggle(self):
        if self.lockstate:
        	self.lockstate = False
        else:
        	self.lockstate = True

    def button_handler_userinfo(self):
        ch="access_control.profacex.userinfo"
        self.q_rpub.append((ch, "1"))
        print("print userinfo")

    def button_handler_adduser(self):
        userid = self.ui.lineEditID.text()
        username = self.ui.lineEditName.text()
        password = self.ui.lineEditPwd.text()
        d = {"id":userid, "username":username, "password":password}
        json_message = json.dumps(d)
        ch="access_control.profacex.adduser"
        self.q_rpub.append((ch, json_message))
        print("add user")
        print(json_message)

    def button_handler_deluser(self):
        userid = self.ui.lineEditID.text()
        username = self.ui.lineEditName.text()
        d = {"id":userid, "username":username}
        json_message = json.dumps(d)
        ch="access_control.profacex.deluser"
        self.q_rpub.append((ch, json_message))
        print("delete user")
        print(json_message)

    def button_handler_reserve(self):
        date_start = self.ui.lineEditTimeStart.text()
        date_end = self.ui.lineEditTimeEnd.text()
        t_start = convert_to_epoch(date_start)
        t_end = convert_to_epoch(date_end)
        d = {"epoch_start":t_start, "epoch_end":t_end}
        json_message = json.dumps(d)
        ch="access_control.profacex.reserve_request"
        self.q_rpub.append((ch, json_message))
        print("reserve request")

    def button_handler_locktoggle(self):
        if self.toggle_lockzk:
            ch="access_control.profacex.lock"
            self.toggle_lockzk = False
            print("Zk lock")
        else:
            ch="access_control.profacex.unlock"
            self.toggle_lockzk = True
            print("Zk unlock")
        self.q_rpub.append((ch, "1"))



    async def redisPubLoop(self):
        while True:
            if self.q_rpub:
                ch, val = self.q_rpub.pop()
                await self.redis.publish("settag:"+ch, val)
            await asyncio.sleep(1)

    async def redisSubLoop(self):
        # Tag list for REDIS sub
        tagname_response = "access_control.profacex.response"
        # REDIS subscribe
        await self.rpubsub.subscribe('tag:'+tagname_response)
        while True:
            # wait redis message
            msg = await self.rpubsub.get_message(ignore_subscribe_messages=True)
            # check received message
            if msg is not None:
                #print(f"(Reader) Message Received: {msg}")
                # create list data with 2 fields
                # [REDIS channel, value]
                ch = msg['channel'].decode('utf-8')
                ch = ch.split(':')[1]
                val = msg['data'].decode('utf-8')

                # check tagname
                if ch == tagname_response:
                    d = json.loads(val)
                    print("Response received!")
                    if 'reserve' in d:
                        self.ui.labelOTP.setText(d["reserve"]["otp"])
                        print(d["reserve"])
                    if 'users' in d:
                        print(d["users"])
            await asyncio.sleep(1)

async def task_redis(w):
    c1 = asyncio.create_task(w.redisPubLoop())
    c2 = asyncio.create_task(w.redisSubLoop())
    await asyncio.wait([c1, c2])



if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = AccessControlSupportSW_UI()

    # Thread for async function using asyncio.run() in a separate thread
    t1 = threading.Thread(target=asyncio.run, args=(task_redis(w),))
    t1.start()

    w.show()
    sys.exit(app.exec())

