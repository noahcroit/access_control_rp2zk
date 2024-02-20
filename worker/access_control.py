import asyncio
import async_timeout
import aiomqtt
import aioredis
import queue
import json
import time
from zk import ZK
from zk import const as zk_const
from datetime import datetime



class SecureLock:
    def __init__(self, name, cfg):
        self.name = name
        self.cfg = cfg
        self.doorstate = None
        self.con = None

    def connect(self):
        pass

    def disconnect(self):
        pass

    def isDoorLock(self):
        pass

    async def lock(self):
        pass

    async def unlock(self):
        pass

    async def run(self):
        pass



class FailSecureLock(SecureLock):
    def __init__(self, name, cfg):
        super().__init__(name, cfg)
        # MQTT client
        self.mqtt_broker = self.cfg['mqtt_broker']
        self.mqtt_port = int(self.cfg['mqtt_port'])
        self.topic_data = self.cfg['mqtt_topics'][0]
        self.topic_lock = self.cfg['mqtt_topics'][1]
        # REDIS client
        usr = self.cfg['redis_user']
        pwd = self.cfg['redis_pwd']
        self.redis = aioredis.from_url('redis://127.0.0.1:6379', username=usr, password=pwd)
        self.rpubsub = self.redis.pubsub()
        # data
        self.state = None
        self.vbatt = None
        self.ischarge = None
        self.isopen = None

    def displayData(self):
        print("locker data ", self.name)
        print("state=", self.state, ", isopen=", self.isopen, ", vbatt=", self.vbatt, ", ischarge=", self.ischarge)

    async def updateTag(self):
        ch = self.cfg['device_tags']['failsecure']['vbatt']
        await self.redis.publish("tag:"+ch, self.vbatt)
        ch = self.cfg['device_tags']['failsecure']['state']
        await self.redis.publish("tag:"+ch, self.state)
        ch = self.cfg['device_tags']['failsecure']['ischarge']
        await self.redis.publish("tag:"+ch, self.ischarge)
        ch = self.cfg['device_tags']['failsecure']['isopen']
        await self.redis.publish("tag:"+ch, self.isopen)

    async def listenMqtt(self):
        async with aiomqtt.Client(self.mqtt_broker) as client:
            await client.subscribe(self.topic_data)
            async for message in client.messages:
                # decode door data (json format) into tag data. ready to write into REDIS
                json_string = message.payload.decode('utf-8')
                data_json = json.loads(json_string)
                self.vbatt = data_json['vbatt']
                self.state = data_json['state']
                self.ischarge = data_json['ischarge']
                self.isopen = data_json['isopen']
                self.displayData()
                print("Finish MQTT sub & update value")
                await self.updateTag()

    async def listenRedis(self):
        # Tag list for REDIS sub
        tagname_cmd = self.cfg['device_tags']['failsecure']['cmd']
        # REDIS subscribe
        await self.rpubsub.subscribe('settag:'+tagname_cmd)
        while True:
            # wait redis message
            msg = await self.rpubsub.get_message(ignore_subscribe_messages=True)
            # check received message
            if msg is not None:
                print(f"(Reader) Message Received: {msg}")
                # create list data with 2 fields
                # [REDIS channel, value]
                #ch = msg['channel'].decode('utf-8')
                #ch = ch.split(':')[1]
                val = msg['data'].decode('utf-8')

                # check if CMD is lock or unlock
                if val == "unlock":
                    await self.unlock()
                elif val == "lock":
                    await self.lock()
            await asyncio.sleep(1)

    def isDoorOpen(self):
        if self.isopen == 'True':
            return True
        return False

    async def lock(self):
        async with aiomqtt.Client(self.mqtt_broker, self.mqtt_port, keepalive=1) as client:
            await client.publish(self.topic_lock, payload="lock")

    async def unlock(self):
        async with aiomqtt.Client(self.mqtt_broker, self.mqtt_port, keepalive=1) as client:
            await client.publish(self.topic_lock, payload="unlock")

    async def run(self):
        print("failsecure:" + self.name + ", start running")
        asyncio.create_task(self.listenRedis())
        asyncio.create_task(self.listenMqtt())



class ZktecoLock(SecureLock):
    def __init__(self, name, cfg, roomtype):
        super().__init__(name, cfg)
        self.room_type = roomtype
        self.room_list = ['serverroom', 'classroom']
        self.zk_client = ZK(self.cfg['profacex_ip'], self.cfg['profacex_port'], timeout=60)
        self.conn = None
        self.unlocking = False
        # REDIS client
        usr = self.cfg['redis_user']
        pwd = self.cfg['redis_pwd']
        self.redis = aioredis.from_url('redis://127.0.0.1:6379', username=usr, password=pwd)
        self.rpubsub = self.redis.pubsub()

    def connect(self):
        print('connect to ZKteco: ', self.name)
        self.conn = self.zk_client.connect()

    def disconnect(self):
        if self.conn:
            print('disconnect to ZKteco: ', self.name)
            self.conn.disconnect()

    def enable(self):
        self.conn.enable_device()

    def disable(self):
        self.conn.disable_device()

    def synctime(self):
        self.conn.set_time(datetime.now())

    def getUsers(self):
        users = self.conn.get_users()
        return users

    def displayInfoUsers(self):
        d_users = {}
        users = self.getUsers()
        for user in users:
            d_user = {}
            privilege = 'User'
            if user.privilege == zk_const.USER_ADMIN:
                privilege = 'Admin'
            print('- UID #{}'.format(user.uid))
            print('  Name       : {}'.format(user.name))
            print('  Privilege  : {}'.format(privilege))
            print('  Password   : {}'.format(user.password))
            print('  Group ID   : {}'.format(user.group_id))
            print('  User  ID   : {}'.format(user.user_id))
            d_user.update({"username":user.name})
            d_user.update({"password":user.password})
            d_user.update({"privilege":privilege})
            d_users.update({user.user_id:d_user})
        return d_users

    def addUser(self, name, userid, pwd, userlevel):
        self.conn.set_user(name=name, privilege=userlevel, password=pwd, user_id=userid)

    def delUser(self, userid=None, name=""):
        if userid:
            self.conn.delete_user(user_id=userid)

    def generate_otp(self):
        import random
        otp = "".join([random.choice("0123456789") for _ in range(4)])
        return otp

    def isDoorLock(self):
        pass

    async def unlock_delay(self, duration_sec=10):
        if not self.unlocking:
            self.unlocking = True
            t_start = int(time.time())
            t_diff = 0
            while t_diff < duration_sec and self.unlocking:
                self.disable()
                self.conn.unlock()
                self.unlocking = True
                self.enable()
                # calculate diff time
                await asyncio.sleep(3)
                t_diff = int(time.time()) - t_start
            self.unlocking = False

    def softlock(self):
        self.unlocking = False

    async def unlock_latch(self):
        self.unlocking = True
        while self.unlocking:
            self.conn.unlock()
            await asyncio.sleep(3)

    async def room_reserve(self, epox_start, epox_end, room_pwd="1234"):
        print("Unlock start at ", epox_start, ", end at", epox_end)
        # read epox time
        diff = epox_end - epox_start
        time_current = int(time.time())
        # do nothing until epox_start
        while time_current < epox_start:
            await asyncio.sleep(3)
            time_current = int(time.time())
        # create temporary user for attendance within period of time, and delete user
        print("Create temporary user for ", diff, "sec")
        self.addUser(name="reserve", userid="100", pwd=room_pwd, userlevel=zk_const.USER_DEFAULT)
        # reserve method
        # "always unlock" or "only add user"
        #await self.unlock_delay(duration_sec=diff)
        await asyncio.sleep(diff)
        self.delUser(userid="100")

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
            epox_start = int(data["epox_start"])
            epox_end = int(data["epox_end"])
            return epox_start, epox_end

    async def listenAtten(self):
        while True:
            print("Listen to atten event...")
            await asyncio.sleep(10)

    async def listenRedis(self):
        # Tag list for REDIS sub
        tagname_reserve = self.cfg['device_tags']['profacex']['reserve_request']
        tagname_add = self.cfg['device_tags']['profacex']['adduser']
        tagname_del = self.cfg['device_tags']['profacex']['deluser']
        tagname_userinfo = self.cfg['device_tags']['profacex']['userinfo']
        tagname_response = self.cfg['device_tags']['profacex']['response']
        tagname_sync = self.cfg['device_tags']['profacex']['synctime']
        tagname_lock = self.cfg['device_tags']['profacex']['lock']
        tagname_unlock = self.cfg['device_tags']['profacex']['unlock']
        # REDIS subscribe
        await self.rpubsub.subscribe('settag:'+tagname_reserve)
        await self.rpubsub.subscribe('settag:'+tagname_add)
        await self.rpubsub.subscribe('settag:'+tagname_del)
        await self.rpubsub.subscribe('settag:'+tagname_userinfo)
        await self.rpubsub.subscribe('settag:'+tagname_sync)
        while True:
            # wait redis message
            msg = await self.rpubsub.get_message(ignore_subscribe_messages=True)
            # check received message
            if msg is not None:
                print(f"(Reader) Message Received: {msg}")
                # create list data with 2 fields
                # [REDIS channel, value]
                ch = msg['channel'].decode('utf-8')
                ch = ch.split(':')[1]
                val = msg['data'].decode('utf-8')

                # check tagname
                if ch == tagname_reserve:
                    # extract message info
                    epox_start, epox_end = self.redisJsonLoad(func="reserve", json_string=val)
                    # generate OTP as password for room reserver & publish as ACK
                    otp = self.generate_otp()
                    d_otp = {"reserve" : {"id": "100", "otp": otp}}
                    json_message = json.dumps(d_otp)
                    await self.redis.publish("tag:"+tagname_response, json_message)
                    # make room reservation
                    asyncio.create_task(self.room_reserve(epox_start, epox_end, otp))

                elif ch == tagname_add:
                    # extract message info
                    userid, username, pwd = self.redisJsonLoad(func="add", json_string=val)
                    # add user
                    self.addUser(name=username, userid=userid, pwd=pwd, userlevel=zk_const.USER_DEFAULT)

                elif ch == tagname_del:
                    # extract message info
                    userid, username = self.redisJsonLoad(func="del", json_string=val)
                    self.delUser(userid=userid)

                elif ch == tagname_userinfo:
                    d_users = self.displayInfoUsers()
                    json_message = json.dumps({"users":d_users})
                    await self.redis.publish("tag:"+tagname_response, json_message)
                    print("userinfo sent")

                elif ch == tagname_sync:
                    self.synctime()

                elif ch == tagname_lock:
                    self.softlock()

                elif ch == tagname_unlock:
                    asyncio.create_task(self.unlock_latch())

            await asyncio.sleep(1)

    async def run(self):
        if self.conn:
            print("ZKteco:" + self.name + ", start running")
            asyncio.create_task(self.listenRedis())
            asyncio.create_task(self.listenAtten())

