import asyncio
import aioredis
import async_timeout
import queue
import argparse
import json



async def redis_sub(channel: aioredis.client.PubSub):
    global q_sub
    while True:
        try:
            async with async_timeout.timeout(3):
                # wait redis message
                msg = await channel.get_message(ignore_subscribe_messages=True)
                # check received message
                if msg is not None:
                    print(f"(Reader) Message Received: {message}")
                    # create list data with 2 fields
                    # [REDIS channel, value]
                    ch = message['channel'].decode('utf-8')
                    val = int(message['data'])
                    # put list data into queue
                    q_sub.put([ch, val])
                # yield
                await asyncio.sleep(0.5)

        except asyncio.TimeoutError:
            print("asyncio timeout in redis sub")

async def redis_pub(redis):
    global q_pub
    while True:
        try:
            async with async_timeout.timeout(3):
                # check the queue if there are any data(s) to REDIS set/publish
                if not q_pub.empty():
                    # extract data for channel and value
                    # queue's data needs to be list-type with 2 fields
                    # [REDIS channel, value]
                    data = q_pub.get()
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
    redis_username = cfg['redis_user']
    redis_password = cfg['redis_pass']
    tagname_isopen = cfg['tagname']['failsecure']['isopen']
    tagname_ischarge = cfg['tagname']['failsecure']['ischarge']
    tagname_vbatt = cfg['tagname']['failsecure']['vbatt']
    tagname_state = cfg['tagname']['failsecure']['state']
    tagname_cmd = cfg['tagname']['failsecure']['cmd']
    f.close()

    # Shared queue
    q_sub = queue.Queue()
    q_pub = queue.Queue()

    # REDIS initialize
    redis = aioredis.from_url('redis://localhost', username=redis_username, password=redis_password)
    pubsub = redis.pubsub()
    await pubsub.subscribe('settag:'+tagname_floodgate_up)
    await pubsub.subscribe('settag:'+tagname_floodgate_down)

    # Create async tasks
    asyncio.create_task(redis_sub(pubsub))
    asyncio.create_task(redis_pub(redis))

    while True:
        print("waiting for message...")
        await asyncio.sleep(5)



if __name__ == '__main__':
    asyncio.run(main())
