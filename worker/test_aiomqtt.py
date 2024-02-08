import asyncio
import async_timeout
import aiomqtt



async def sleep(seconds):
    # Some other task that needs to run concurrently
    await asyncio.sleep(seconds)
    print(f"Slept for {seconds} seconds!")

async def mqtt_publish():
    broker = "broker.hivemq.com"
    port = 1883
    topic = "failsecure/data"
    while True:
        print("pubishing")
        async with aiomqtt.Client(broker) as client:
            await client.publish(topic, payload=28.4)
        await asyncio.sleep(1)

async def mqtt_subscribe():
    broker = "broker.hivemq.com"
    port = 1883
    topic = "failsecure/data2"
    async with aiomqtt.Client(broker) as client:
        await client.subscribe(topic)
        async for message in client.messages:
            print(message.payload)

async def main():
    # Schedule three calls *concurrently*:
    L = await asyncio.gather(
        mqtt_publish(),
        sleep(3),
        mqtt_subscribe(),
        sleep(1)
    )
    print(L)

if __name__ == '__main__':
    asyncio.run(main())
