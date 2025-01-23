import sys
import os
sys.path.insert(1,os.path.abspath("../pyzk"))
from zk import ZK, const
import time

conn = None
zk = ZK('192.168.1.82', port=4370, timeout=60, verbose=True)
try:
    print('Connecting to device ...')
    conn = zk.connect()
    print('Disabling device ...')
    conn.disable_device()
    print('Firmware Version: : {}'.format(conn.get_firmware_version()))
    print('Platform Version: : {}'.format(conn.get_platform()))
    print('memsize : {}'.format(conn.read_sizes()))
    # print '--- Get User ---'
    users = conn.get_users()
    for user in users:
        privilege = 'User'
        if user.privilege == const.USER_ADMIN:
            privilege = 'Admin'

        print('- UID #{}'.format(user.uid))
        print('  Name       : {}'.format(user.name))
        print('  Privilege  : {}'.format(privilege))
        print('  Password   : {}'.format(user.password))
        print('  Group ID   : {}'.format(user.group_id))
        print('  User  ID   : {}'.format(user.user_id))

    print('Enabling device ...')
    conn.enable_device()
except Exception as e:
    print("Process terminate : {}".format(e))
finally:
    if conn:
        conn.disconnect()
