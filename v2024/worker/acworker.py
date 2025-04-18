import sys
import asyncio
import async_timeout
import aioredis
import queue
import argparse
import json
import logging
#import aiomqtt
from door import DSK1T105AM
import time
import datetime as DT



def json_decode_from_backend(json_string, func="ls"):
    data = json.loads(json_string)
    if func == "ls":
        pass
    elif func == "add":
        uid  = int(data["id"])
        user = data["username"]
        pwd  = data["password"]
        valid_en = data["valid_enable"] == "true"
        epoch_start = int(data["epoch_start"])
        epoch_end = int(data["epoch_end"])
        return uid, user, pwd, valid_en, epoch_start, epoch_end
    elif func == "del":
        uid  = int(data["id"])
        user = data["username"]
        return uid, user
    elif func == "schedule":
        days = data["days"]
        tstart = data["start"]
        tend = data["end"]
        return days, tstart, tend
    else:
        return None



def epoch2iso(epoch):
    iso = DT.datetime.utcfromtimestamp(epoch).isoformat()
    return iso

def strtime2seconds(strtime):
    h, m, s = strtime.split(":")
    h = int(h)
    m = int(m)
    s = int(s)
    seconds = s + 60*m + 3600*h
    return seconds

"""
async def task_mqttsub():
    global cfg
    global q2client
    logger.info('Starting a MQTT subscribe task for receiving door info')
    while True:
        try:
            async with aiomqtt.Client(cfg['mqtt_broker'], int(cfg['mqtt_port'])) as client:
                await client.subscribe(cfg['mqtt_topics'][0])
                await client.subscribe(cfg['mqtt_topics'][1])
                await client.subscribe(cfg['mqtt_topics'][2])
                await client.subscribe(cfg['mqtt_topics'][3])
                async for message in client.messages:
                    payload = message.payload.decode('utf-8')
        except Exception as e:
            logger.warning("task: mqtt subscribe will be stop")
            break
        await asyncio.sleep(1)



async def task_mqttpub():
    global cfg
    global q2device
    logger.info('Starting a MQTT publish for controling LOCK/UNLOCK')
    while True:
        try:
            if not q2device.empty():
                data = q2device.get().decode('utf-8')
        except Exception as e:
            logger.warning("task: mqtt publish will be stop")
            break
        await asyncio.sleep(1)
"""


async def task_listen2backend(channel: aioredis.client.PubSub, taglist):
    global q2accessctrl
    logger.info('Starting a REDIS sub for Reservation/Person Management at DS-K1T105AM')
    # subscribe for listening to all tags
    for tag in taglist:
        prefix, t = tag.split(":")
        if prefix == "settag":
            await channel.subscribe(tag)
        else:
            print("{} is not a sub tag".format(tag))

    # listening loop
    while True:
        try:
            async with async_timeout.timeout(1):
                message = await channel.get_message(ignore_subscribe_messages=True)
                if message is not None:
                    logger.info('Incoming REDIS pub message')
                    ch = message['channel'].decode('utf-8')
                    tag_fullname = ch.split(':')[1]
                    val = message['data'].decode('utf-8')
                    data=(tag_fullname, val)
                    if q2accessctrl.full():
                        discard = q2accessctrl.get()
                    q2accessctrl.put(data)
                await asyncio.sleep(0.1)
        except asyncio.TimeoutError:
            break



async def task_update2backend(redis_client):
    global q2backend
    logger.info('Starting a REDIS pub for sending data to backend')
    while True:
        if not q2backend.empty():
            # for islocked only, if there are more type of message (JSON etc), json.dump is needed
            d = q2backend.get()
            ch, txdata = d
            logger.info("Publish tag value to REDIS")
            logger.info("tag : %s, value : %s", ch, txdata)
            await redis_client.publish(ch, txdata)
        await asyncio.sleep(0.1)



async def task_accessctrl(l_device):
    global cfg
    global q2accessctrl
    global q2backend
    dict_scheduler = {} 
    dict_device = {}
    tick = 0
    logger.info('Starting a access control tasks (DS-K1T105AM and pico failsecure)')
    for name, device_info in l_device:
        print(name)
        print(device_info)  
        d = DSK1T105AM(name, 
                        device_info["admin_user"],
                        device_info["admin_password"],
                        device_info["ipaddr"],
                        device_info["port"],
                        cfg["redis_url"],
                        cfg["redis_port"],
                        cfg["redis_pwd"]
                    )
        d.start_listen2event()
        dict_device.update({name: d})
    while True:
        # For islock monitoring
        if tick % 5 == 0:
            for device_name in dict_device:
                val = str(dict_device[device_name].islocked)
                tag_fullname = "tag:access_control." + device_name + ".islocked"
                data=(tag_fullname, val)
                if q2backend.full():
                    discard = q2backend.get()
                q2backend.put(data)

        # For settag from backend
        if not q2accessctrl.empty():
            logger.info('Read message from queue for AC devices')
            tag_fullname, val = q2accessctrl.get()
            system_name, device_name, tagname = tag_fullname.split('.')
            print(system_name, device_name, tagname, val)

            if tagname == "lock":
                logger.info("lock requested!")
                res = dict_device[device_name].isapi_doorctrl("close")
            elif tagname == "always_lock":
                logger.info("always lock requested!")
                res = dict_device[device_name].isapi_doorctrl("alwaysClose")
            elif tagname == "unlock":
                logger.info("unlock requested!")
                res = dict_device[device_name].isapi_doorctrl("open")
            elif tagname == "always_unlock":
                logger.info("always unlock requested!")
                res = dict_device[device_name].isapi_doorctrl("alwaysOpen")
            elif tagname == "unlock_schedule":
                logger.info("start unlock schedule requested!")
                days, tstart, tend = json_decode_from_backend(val, func="schedule")
                print(days, tstart, tend)
                t_scheduler = asyncio.create_task(unlock_scheduler(days, tstart, tend, dict_device[device_name]))
                dict_scheduler.update({device_name: t_scheduler})
            elif tagname == "stop_schedule":
                logger.info("stop unlock schedule requested!")
                dict_scheduler[device_name].cancel()
                dict_device[device_name].isapi_doorctrl("close")
            elif tagname == "adduser":
                logger.info("add user requested!")
                uid, user, pwd, valid, tstart, tend = json_decode_from_backend(val, func="add")
                tstart = epoch2iso(tstart)
                tend = epoch2iso(tend)
                logger.info(tstart, tend)
                if dict_device[device_name].isapi_searchUser(uid):
                    dict_device[device_name].isapi_delUser(uid, user)
                res = dict_device[device_name].isapi_addUser(uid, user, pwd, valid, tstart, tend)
            elif tagname == "deluser":
                logger.info("delete user requested!")
                uid, user = json_decode_from_backend(val, func="del")
                if dict_device[device_name].isapi_searchUser(uid):
                    res = dict_device[device_name].isapi_delUser(uid, user)
        await asyncio.sleep(1)
        tick += 1



async def unlock_scheduler(days, startTime, endTime, device):
    logger.info('Starting open scheduler')
    device.isapi_doorctrl("close")
    startSeconds = strtime2seconds(startTime)
    endSeconds = strtime2seconds(endTime)
    days_int = []
    for day in days:
        days_int.append(int(day))
    while True:
        day = DT.datetime.today().isoweekday()
        if day in days_int:
            await asyncio.sleep(5)
            currentTime = DT.datetime.now().strftime("%H:%M:%S")
            currentSeconds = strtime2seconds(currentTime)
            if (currentSeconds >= startSeconds) and (currentSeconds <= endSeconds): 
                if device.islocked:
                    device.isapi_doorctrl("alwaysOpen")
            else:
                if not device.islocked:
                    device.isapi_doorctrl("close")
        else:
            await asyncio.sleep(60)




async def main():
    global cfg
    # REDIS initialization
    logger.info('REDIS client initialize')
    redis_client = aioredis.from_url("redis://" + cfg["redis_url"] + ":" + str(cfg["redis_port"]), password=cfg["redis_pwd"])
    pubsub = redis_client.pubsub()
    logger.info('REDIS OK')

    print("List of devices and tags")
    l_tag = []
    l_device = []
    for device, device_info in cfg["devices"].items():
        print(device)
        l_device.append((device, device_info))
        for key, tag in device_info["tagnames"].items():
            l_tag.append(tag)
            print(tag)
    
    # create task(s)
    t1 = asyncio.create_task(task_listen2backend(pubsub, l_tag))
    t2 = asyncio.create_task(task_update2backend(redis_client))
    t3 = asyncio.create_task(task_accessctrl(l_device))

    # main loop
    while True:
        logger.info('Checking the status of all tasks')
        await asyncio.sleep(1)
        # check tasks
        if t1.done():
            logger.info('Restart a task_listen')
            t1 = asyncio.create_task(task_listen2backend(pubsub, l_tag))
        if t2.done():
            logger.info('Restart a task_send')
            t2 = asyncio.create_task(task_update2backend(redis_client))
        if t3.done():
            logger.info('Restart a task_accessctrl')
            t3 = asyncio.create_task(task_accessctrl(l_device))



if __name__ == '__main__':
    # Initialize parser
    parser = argparse.ArgumentParser()
    # Adding optional argument
    # Read arguments from command line
    parser.add_argument("-c", "--cfg", help="JSON file for the configuration file of all devices", default='config.json')
    args = parser.parse_args()

    # Extract config data from .json
    try:
        f = open(args.cfg, 'rb')
        cfg = json.load(f)
        f.close()
    except OSError:
        logger.error('Configuration file does not exist!')
        sys.exit()

    q2accessctrl = queue.Queue(maxsize=256)
    q2backend = queue.Queue(maxsize=256)

    # setup logging system
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # run main program
    logger.info('Starting an access control worker')
    asyncio.run(main())
