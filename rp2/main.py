import gc
from machine import Timer
from machine import WDT
from secure_doorlock import *
import time
import network
from umqtt.simple import MQTTClient
import ubinascii
from q_scheduler import FunctionQueueTask
from q_scheduler import FunctionQueueScheduler
import json



def mqttSubscribeCallback(topic, msg):
    global nc
    global door

    print("incoming MQTT message, ", (topic, msg))
    msg = msg.decode()
    if msg == "lock":
        door.lockEnable()
    elif msg == "unlock":
        door.lockDisable()



def task_displayAllDoorInfo():
    global door
    global door_dict

    door_dict["vbatt"] = str(door.getVbatt())
    door_dict["isopen"] = str(door.isDoorOpen())
    door_dict["ischarge"] = str(door.isChargerActivated())
    door_dict["state"] = str(door.state)
    print(door_dict)

def task_stepDoorState():
    global door
    door.step()

def task_mqttPublish():
    global door_dict
    global door
    global nc
    global wlan
    global mqtt_c
    global mqtt_connected
    global mqtt_client_id
    global wdt

    if door.state == 'IDLE':
        # try to connect WLAN first
        timeout=0
        if not wlan.isconnected():
            try:
                print('connecting to WLAN...')
                wlan.active(True)
                wlan.connect(nc["ssid"],nc["pwd"])
                while not wlan.isconnected() and timeout < 20:
                    timeout += 1
                    time.sleep(0.1)
            except Exception as e:
                print(e)
                gc.collect()
                mqtt_connected = False

        # feed watchdog first to prevent reset itself due to long duration of connection
        wdt.feed()

        # do mqtt when WLAN is connected successfully
        # otherwise, wait for next call
        if wlan.isconnected():
            print("WLAN connected!")
            try:
                if not mqtt_connected:
                    mqtt_c.connect()
                    topic=nc["topics"][1].encode()
                    print('MQTT Subscribe to ', topic)
                    mqtt_c.subscribe(topic)

                topic=nc["topics"][0].encode()
                print('MQTT Publish to ', topic)
                data = json.dumps(door_dict).encode()
                mqtt_c.publish(topic, data, qos=0)
                mqtt_connected = True

            except Exception as e:
                print(e)
                gc.collect()
                mqtt_connected = False
    else:
        wlan.active(False)
        mqtt_connected = False

def task_mqttSubscribe():
    global nc
    global mqtt_c
    global mqtt_connected
    global mqtt_client_id
    topic=nc["topics"][1].encode()

    try:
        mqtt_c.check_msg()
    except:
        try:
            mqtt_c.connect()
            print('MQTT Subscribe to ', topic)
            mqtt_c.subscribe(topic)
            mqtt_connected = True
        except:
            print('MQTT Reconnect Failed')
            mqtt_connected = False



# Main Program
if __name__ == '__main__':

    # Read configuration file (WLAN network, MQTT broker etc.)
    filename='network_config.json'
    with open(filename) as fp:
        nc = json.load(fp)

    # Initialize door's hardware and its dictionary (to store sensor data etc.)
    print("Initialize door...")
    door_dict = {}
    door = SecureDoor()
    door.hwinit()

    # WLAN & MQTT
    wlan = network.WLAN(network.STA_IF)
    mqtt_client_id = ubinascii.hexlify(machine.unique_id())
    mqtt_c = MQTTClient(mqtt_client_id, nc["mqtt_broker"], port=nc["mqtt_port"], keepalive=nc["keepalive"])
    mqtt_c.set_callback(mqttSubscribeCallback)
    mqtt_connected = False

    # Task scheduler (function queue scheduler)
    # Less task ID -> Most Priority
    print("Create task & task scheduler")
    schd = FunctionQueueScheduler()
    t1 = FunctionQueueTask(task_fn=task_mqttSubscribe, task_id=1, scheduler=schd)
    t2 = FunctionQueueTask(task_fn=task_mqttPublish, task_id=2, scheduler=schd)
    t3 = FunctionQueueTask(task_fn=task_displayAllDoorInfo, task_id=3, scheduler=schd)
    t4 = FunctionQueueTask(task_fn=task_stepDoorState, task_id=4, scheduler=schd)
    schd.installTask(t1)
    schd.installTask(t2)
    schd.installTask(t3)
    schd.installTask(t4)

    # Set timer(s) for task trigger
    print("Initialize timer to trigger each tasks")
    tim1 = Timer()
    tim2 = Timer()
    tim3 = Timer()
    tim4 = Timer()
    tim1.init(period=17000, mode=Timer.PERIODIC, callback=t1.handler)
    tim2.init(period=15000, mode=Timer.PERIODIC, callback=t2.handler)
    tim3.init(period=5000, mode=Timer.PERIODIC, callback=t3.handler)
    tim4.init(period=2000, mode=Timer.PERIODIC, callback=t4.handler)
    wdt = WDT(timeout=8300)

    # Superloop
    # monitor watchdog and errors
    print("loop start!")
    while True:
        # task scheduler
        schd.popTask()
        time.sleep(0.2)

        # feed watchdog timer
        wdt.feed()


