import sys
import asyncio
import async_timeout
import aioredis
import aiomqtt
import requests
import queue
import argparse
import json
import logging



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



async def task_redissub(channel: aioredis.client.PubSub):
    global cfg
    global q2device
    logger.info('Starting a REDIS sub for Reservation/Person Management at DS-K1T105AM')
    while True:
        try:
            async with async_timeout.timeout(1):
                message = await channel.get_message(ignore_subscribe_messages=True)
                if message is not None:
                    q2device.put(message['data'])
                await asyncio.sleep(0.1)
        except asyncio.TimeoutError:
            pass



async def task_redispub(redis, channel_pub):
    global q2client
    logger.info('Starting a REDIS pub for sending door status, list of users at DS-K1T105AM')
    while True:
        if not q2client.empty():
            txdata = q2client.get()
            await redis.publish(channel_pub, txdata)
        await asyncio.sleep(1)



async def main():
    global cfg
    # Initialize parser
    parser = argparse.ArgumentParser()
    # Adding optional argument
    # Read arguments from command line
    parser.add_argument("-j", "--json", help="JSON file for the configuration", default='config.json')
    args = parser.parse_args()

    # Extract config data from .json
    try:
        f = open(args.json, 'rb')
        cfg = json.load(f)
        f.close()
    except OSError:
        logger.error('Configuration file does not exist!')
        sys.exit()

    # REDIS initialization
    logger.info('REDIS client initialize')
    redis = aioredis.from_url("redis://localhost")
    pubsub = redis.pubsub()
    await pubsub.subscribe('ch:from_client')
    logger.info('REDIS OK')

    # create task(s)
    t_rsub = asyncio.create_task(task_redissub(pubsub))
    t_rpub = asyncio.create_task(task_redispub(redis, 'ch:from_device'))
    t_mqttsub = asyncio.create_task(task_mqttsub())
    t_mqttpub = asyncio.create_task(task_mqttpub())

    # main loop
    while True:
        logger.info('Checking the status of all tasks')
        await asyncio.sleep(1)
        # check tasks
        if t_rsub.done():
            logger.info('Restart a task_redissub')
            t_rsub = asyncio.create_task(task_redissub(pubsub))
        if t_rpub.done():
            logger.info('Restart a task_redispub')
            t_rpub = asyncio.create_task(task_redispub(redis, 'ch:from_device'))
        if t_mqttsub.done():
            logger.info('Restart a task_mqttsub')
            t_mqttsub = asyncio.create_task(task_mqttsub())
        if t_mqttpub.done():
            logger.info('Restart a task_mqttpub')
            t_mqttpub = asyncio.create_task(task_mqttpub())



if __name__ == '__main__':
    cfg = None
    q2client = queue.Queue(maxsize=256)
    q2device = queue.Queue(maxsize=256)

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
