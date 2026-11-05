
def test_bus_delivers_to_subscriber():
    import asyncio

    from factoria.realtime.events import EventBus

    async def scenario():
        bus = EventBus()
        queue = bus.subscribe()
        bus.publish({"type": "command_status", "command_id": "c1", "status": "EXECUTED"})
        return await asyncio.wait_for(queue.get(), timeout=1)

    message = asyncio.run(scenario())
    assert message["type"] == "command_status"
    assert message["command_id"] == "c1"


def test_bus_drops_when_full():
    import asyncio

    from factoria.realtime.events import EventBus

    async def scenario():
        bus = EventBus()
        queue = bus.subscribe(maxsize=1)
        bus.publish({"n": 1})
        bus.publish({"n": 2})  # не должно упасть
        return await queue.get()

    assert asyncio.run(scenario())["n"] == 1
