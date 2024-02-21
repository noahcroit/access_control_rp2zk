import sys
import os
sys.path.insert(1,os.path.abspath("./pyzk"))
from zk import ZK, const
import time

conn = None
z = ZK('192.168.8.110', port=4370, password=0, timeout=60, verbose=True)
try:
    print('Connecting to device ...')
    conn = z.connect()
    conn.enable_device()
    conn.clear_attendance()
    print('Connected! Enable device')
    print('Live Capture, Wait for event...')
    timeout=0
    for attendance in conn.live_capture(3):
        if attendance is None:
            timeout += 1
        else:
            print (attendance)

        # simulate by let other task to run
        time.sleep(2)

except Exception as e:
    print("Process terminate : {}".format(e))
finally:
    if conn:
        conn.disconnect()
