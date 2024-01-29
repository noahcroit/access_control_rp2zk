from machine import Timer
from secure_doorlock import *
import time



### Main Program
if __name__ == '__main__':

    # Initialization
    print("Initialize.....")
    door = SecureDoor()
    door.hwinit()
    time.sleep(5)

    # Superloop
    while True:
        door.step()
        time.sleep(0.1)


