import asyncio
import async_timeout
import aiomqtt
import aioredis
import queue
import json
import datetime
from zk import ZK
from zk import const as zk_const



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

    def getUsers(self):
        users = self.conn.get_users()
        return users

    def displayInfoUsers(self):
        users = self.getUsers()
        for user in users:
            privilege = 'User'
            if user.privilege == zk_const.USER_ADMIN:
                privilege = 'Admin'
            print('- UID #{}'.format(user.uid))
            print('  Name       : {}'.format(user.name))
            print('  Privilege  : {}'.format(privilege))
            print('  Password   : {}'.format(user.password))
            print('  Group ID   : {}'.format(user.group_id))
            print('  User  ID   : {}'.format(user.user_id))

    def isDoorLock(self):
        pass

    async def unlock(self, duration_min=1):
        if not self.unlocking:
            self.disable()
            self.conn.unlock(duration_min * 6)
            self.unlocking = True
            self.enable()
            duration_sec = duration_min * 60
            t_start = datetime.datetime.now(datetime.timezone.utc)
            t_diff = 0
            while t_diff < duration_sec:
                # calculate diff time
                diff = datetime.datetime.now(datetime.timezone.utc) - t_start
                t_diff = int(diff.total_seconds())
                await asyncio.sleep(5)
            self.unlocking = False

    async def listenRedis(self):
        # Tag list for REDIS sub
        tagname_lock = self.cfg['device_tags']['profacex']['lockctrl']
        tagname_add = self.cfg['device_tags']['profacex']['adduser']
        tagname_del = self.cfg['device_tags']['profacex']['deluser']
        # REDIS subscribe
        await self.rpubsub.subscribe('settag:'+tagname_lock)
        await self.rpubsub.subscribe('settag:'+tagname_add)
        await self.rpubsub.subscribe('settag:'+tagname_del)
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
                if ch == tagname_lock:
                    await self.unlock(duration_min=int(val))
            await asyncio.sleep(1)

    async def run(self):
        if self.conn:
            print("ZKteco:" + self.name + ", start running")
            asyncio.create_task(self.listenRedis())

