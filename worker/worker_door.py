import asyncio
import aioredis
import async_timeout
import queue
import argparse
import json
import aiomqtt



async def redis_sub(cfg):
    # Tag list for REDIS sub
    tagname_cmd = cfg['tagname']['failsecure']['cmd']
    usr = cfg['redis_user']
    pwd = cfg['redis_pwd']
    q_rsub = queue.Queue()

    # REDIS client initialize
    redis = aioredis.from_url('redis://127.0.0.1:6379', username=usr, password=pwd)
    pubsub = redis.pubsub()
    # REDIS subscribe
    await pubsub.subscribe('settag:'+tagname_cmd)

    while True:
        try:
            async with async_timeout.timeout(10):
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

                    # MQTT publish
                    await mqtt_pub(cfg, q_rsub)
                # yield
                await asyncio.sleep(0.5)

        except asyncio.TimeoutError:
            print("asyncio timeout in redis sub")
        except:
            continue

async def mqtt_sub(cfg):
    broker = cfg['mqtt_broker']
    port = cfg['mqtt_port']
    topic = cfg['mqtt_topics'][0]
    tagname_isopen = cfg['tagname']['failsecure']['isopen']
    tagname_ischarge = cfg['tagname']['failsecure']['ischarge']
    tagname_vbatt = cfg['tagname']['failsecure']['vbatt']
    tagname_state = cfg['tagname']['failsecure']['state']

    q_rpub = queue.Queue()

    while True:
        try:
            async with async_timeout.timeout(5):
                print('MQTT subscribing')
                async with aiomqtt.Client(broker) as client:
                    await client.subscribe(topic)
                    async for message in client.messages:
                        print(message.payload)
                        # decode door data (json format) into tag data. ready to write into REDIS
                        json_string = message.payload.decode('utf-8')
                        data_json = json.loads(json_string)
                        print('put data to rpub Q')
                        q_rpub.put((tagname_isopen, data_json['isopen']))
                        q_rpub.put((tagname_ischarge, data_json['ischarge']))
                        q_rpub.put((tagname_vbatt, data_json['vbatt']))
                        q_rpub.put((tagname_state, data_json['state']))
                        await redis_pub(cfg, q_rpub)
                await asyncio.sleep(0.5)

        except asyncio.TimeoutError:
            print("asyncio timeout in redis sub")
        except Exception as e:
            print(e)
            continue



async def redis_pub(cfg, q_rpub):
    # Tag list for REDIS pub
    tagname_isopen = cfg['tagname']['failsecure']['isopen']
    tagname_ischarge = cfg['tagname']['failsecure']['ischarge']
    tagname_vbatt = cfg['tagname']['failsecure']['vbatt']
    tagname_state = cfg['tagname']['failsecure']['state']
    usr = cfg['redis_user']
    pwd = cfg['redis_pwd']

    # REDIS client
    redis = aioredis.from_url('redis://127.0.0.1:6379', username=usr, password=pwd)

    try:
        async with async_timeout.timeout(30):
            # check the queue if there are any data(s) to REDIS set/publish
            while not q_rpub.empty():
                # extract data for channel and value
                # queue's data needs to be list-type with 2 fields
                # [REDIS channel, value]
                data = q_rpub.get()
                ch  = data[0]
                val = data[1]
                # REDIS set/publish
                print('REDIS publishing : ', data)
                await redis.publish("tag:"+ch, str(val))
            else:
                print("pub Q is empty..")
            # yield
            await asyncio.sleep(0.5)

    except asyncio.TimeoutError:
        print("asyncio timeout in redis pub")

async def mqtt_pub(cfg, q_rsub):
    broker = cfg['mqtt_broker']
    port = cfg['mqtt_port']
    topic = cfg['mqtt_topics'][1]

    try:
        async with async_timeout.timeout(30):
            while not q_rsub.empty():
                data = q_rsub.get()
                ch = data[0]
                val = data[1]
                print("MQTT pubishing")
                async with aiomqtt.Client(broker) as client:
                    await client.publish(topic, payload=val)
            await asyncio.sleep(1)

    except asyncio.TimeoutError:
        print("asyncio timeout in redis sub")



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

    # Create async tasks
    asyncio.create_task(redis_sub(cfg))
    asyncio.create_task(mqtt_sub(cfg))

    while True:
        print("waiting for message...")
        await asyncio.sleep(5)



if __name__ == '__main__':
    asyncio.run(main())
