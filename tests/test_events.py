from vidmelt import events


def test_in_memory_event_bus_publish_subscribe():
    bus = events.InMemoryEventBus()
    subscriber = bus.subscribe()

    bus.publish({"message": "hello"}, "update")
    event_type, payload = subscriber.get(timeout=1)

    assert event_type == "update"
    assert payload["message"] == "hello"

    bus.unsubscribe(subscriber)
    # Ensure unsubscribe prevents future deliveries
    bus.publish({"message": "world"}, "update")
    assert subscriber.empty()
