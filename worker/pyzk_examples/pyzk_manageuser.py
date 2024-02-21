from zk import ZK, const
import time

conn = None
try:
    print('Connecting to device ...')
    zk = ZK('192.168.8.201', port=4370, timeout=10)
    conn = zk.connect()
    print('Disabling device ...')
    conn.disable_device()
    print('Firmware Version: : {}'.format(conn.get_firmware_version()))
    # Create user
    print("Testing... Adding user")
    conn.set_user(uid=4, name='test@kmitl.ac.th', privilege=const.USER_ADMIN, password='4444', group_id='', user_id='4', card=0)
    # print '--- Get User ---'
    conn.enable_device()
    conn.disconnect()

    # wait for 1min to test login
    time.sleep(60)

    print('Connecting to device ...')
    zk = ZK('192.168.8.201', port=4370, timeout=10)
    conn = zk.connect()
    conn.disable_device()
    # Delete User
    print("Testing... Deleting user")
    conn.delete_user(uid=4)
    conn.enable_device()

except Exception as e:
    print("Process terminate : {}".format(e))
finally:
    if conn:
        conn.disconnect()
