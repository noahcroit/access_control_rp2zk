import asyncio
import async_timeout
import queue
import argparse
import json
import aiomqtt
from access_control import FailSecureLock
from access_control import ZktecoLock



async def main():
    # Initialize parser
    parser = argparse.ArgumentParser()
    # Adding optional argument
    # Read arguments from command line
    parser.add_argument("-j", "--json", help="JSON file for the configuration", default='config.json')
    args = parser.parse_args()

    # Extract config data from .json
    f = open(args.json)
    cfg = json.load(f)
    f.close()

    # Create devices
    locker = FailSecureLock("KMITL failsecure locker", cfg)
    accessctrl = ZktecoLock("ZKteco Proface X", cfg, "serverroom")
    accessctrl.connect()

    # Create async tasks
    asyncio.create_task(locker.run())
    asyncio.create_task(accessctrl.run())

    while True:
        print("main loop...")
        await asyncio.sleep(5)



if __name__ == '__main__':
    asyncio.run(main())
