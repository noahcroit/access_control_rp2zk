from machine import Timer
from machine import WDT
from secure_doorlock import *
import time
import network
from umqtt.simple import MQTTClient
import ubinascii
from q_scheduler import FunctionQueueTask
from q_scheduler import FunctionQueueScheduler



def task_displayAllDoorInfo():
    global door
    door_dict = {}
    door_dict["vbatt"] = door.getVbatt()
    door_dict["isopen"] = door.isDoorOpen()
    door_dict["ischarge"] = door.isChargerActivated()
    door_dict["state"] = door.state
    print(door_dict)

def task_stepDoorState():
    global door
    door.step()

def task_mqttPublish():
    pass

# Main Program
if __name__ == '__main__':

    # Initialize hardware
    print("Initialize.....")
    door = SecureDoor()
    door.hwinit()
    #wlan = network.WLAN(network.STA_IF)
    #wlan.active(False)

    # Task scheduler (function queue scheduler)
    schd = FunctionQueueScheduler()
    t1 = FunctionQueueTask(task_fn=task_stepDoorState, task_id=1, scheduler=schd)
    t2 = FunctionQueueTask(task_fn=task_displayAllDoorInfo, task_id=2, scheduler=schd)
    schd.installTask(t1)
    schd.installTask(t2)

    # Set timer(s) for task trigger
    tim1 = Timer()
    tim2 = Timer()
    tim3 = Timer()
    tim1.init(period=1000, mode=Timer.PERIODIC, callback=t1.handler)
    tim2.init(period=5000, mode=Timer.PERIODIC, callback=t2.handler)
    wdt = WDT(timeout=8300)

    # Superloop
    # monitor watchdog and errors
    while True:
        # task scheduler
        schd.popTask()
        time.sleep(0.5)

        # feed watchdog timer
        wdt.feed()


