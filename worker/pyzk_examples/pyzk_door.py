from zk import ZK, const
import time
conn = None
zk = ZK('192.168.8.201', port=4370, timeout=5)
try:
    print('Connecting to device ...')
    conn = zk.connect()
    print('Disabling device ...')
    conn.disable_device()

    print ('--- Opening door 10s ---')
    conn.unlock(30)
    time.sleep(1)
    print(conn.get_lock_state())
    conn.enable_device()
    print (' -- done!---')

except Exception as e:
    print("Process terminate : {}".format(e))
finally:
    if conn:
        conn.disconnect()
