import asyncio
import aioredis
import async_timeout
import queue
import argparse
import json
import aiomqtt



async def redis_sub(cfg, q_rsub):
    # Tag list for REDIS sub
    tagname_cmd = cfg['tagname']['failsecure']['cmd']

    # REDIS client initialize
    redis = aioredis.from_url('redis://localhost')
    pubsub = redis.pubsub()
    # REDIS subscribe
    await pubsub.subscribe('settag:'+tagname_cmd)

    while True:
        try:
            async with async_timeout.timeout(5):
                # wait redis message
                msg = await pubsub.get_message(ignore_subscribe_messages=True)
                # check received message
                if msg is not None:
                    print(f"(Reader) Message Received: {msg}")
                    # create list data with 2 fields
                    # [REDIS channel, value]
                    ch = msg['channel'].decode('utf-8')
                    ch = ch.split(':')[1]
                    val = msg['data'].decode('utf-8')
                    # put list data into queue
                    q_rsub.put((ch, val))
                # yield
                await asyncio.sleep(0.5)

        except asyncio.TimeoutError:
            print("asyncio timeout in redis sub")
        except:
            continue

async def redis_pub(cfg, q_rpub):
    # Tag list for REDIS pub
    tagname_isopen = cfg['tagname']['failsecure']['isopen']
    tagname_ischarge = cfg['tagname']['failsecure']['ischarge']
    tagname_vbatt = cfg['tagname']['failsecure']['vbatt']
    tagname_state = cfg['tagname']['failsecure']['state']

    # REDIS client
    redis = aioredis.from_url('redis://localhost')

    while True:
        try:
            async with async_timeout.timeout(5):
                # check the queue if there are any data(s) to REDIS set/publish
                if not q_rpub.empty():
                    # extract data for channel and value
                    # queue's data needs to be list-type with 2 fields
                    # [REDIS channel, value]
                    data = q_rpub.get()
                    ch  = data[0]
                    val = data[1]
                    # REDIS set/publish
                    await redis.set("tag:"+ch, str(val))
                else:
                    print("pub Q is empty..")
                # yield
                await asyncio.sleep(0.5)

        except asyncio.TimeoutError:
            print("asyncio timeout in redis pub")
        except:
            continue

async def mqtt_pub(cfg, q_rsub):
    broker = cfg['mqtt_broker']
    port = cfg['mqtt_port']
    topic = cfg['mqtt_topics'][1]

    while True:
        try:
            async with async_timeout.timeout(5):
                if not q_rsub.empty():
                    data = q_rsub.get()
                    ch = data[0]
                    val = data[1]
                    print("MQTT pubishing")
                    async with aiomqtt.Client(broker) as client:
                        await client.publish(topic, payload=val)
                await asyncio.sleep(1)

        except asyncio.TimeoutError:
            print("asyncio timeout in redis sub")
        except:
            continue

async def mqtt_sub(cfg, q_rpub):
    broker = cfg['mqtt_broker']
    port = cfg['mqtt_port']
    topic = cfg['mqtt_topics'][0]
    tagname_isopen = cfg['tagname']['failsecure']['isopen']
    tagname_ischarge = cfg['tagname']['failsecure']['ischarge']
    tagname_vbatt = cfg['tagname']['failsecure']['vbatt']
    tagname_state = cfg['tagname']['failsecure']['state']
    tags = [tagname_isopen, tagname_ischarge, tagname_vbatt, tagname_state]

    while True:
        try:
            async with async_timeout.timeout(5):
                print('MQTT subscribing')
                async with aiomqtt.Client(broker) as client:
                    await client.subscribe(topic)
                    async for message in client.messages:
                        print(message.payload)
                        # decode door data (json format) into tag data. ready to write into REDIS
                        json_string = message.payload.decode('decode')
                        data_json = json.loads(json_string)
                        for tag in tags:
                            q_rsub.put((tag, data_json[tag]))



        except asyncio.TimeoutError:
            print("asyncio timeout in redis sub")
        except:
            continue



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

    # Shared queue
    q_rsub = queue.Queue()
    q_rpub = queue.Queue()

    # Create async tasks
    asyncio.create_task(redis_sub(cfg, q_rsub))
    asyncio.create_task(redis_pub(cfg, q_rpub))
    asyncio.create_task(mqtt_sub(cfg, q_rpub))
    asyncio.create_task(mqtt_pub(cfg, q_rsub))

    while True:
        print("waiting for message...")
        await asyncio.sleep(5)



if __name__ == '__main__':
    asyncio.run(main())
