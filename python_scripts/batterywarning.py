def persistent_warning_message(devices):
    devices = "\n".join(devices)
    service_data = {
        "title": "Low Battery",
        "notification_id": "low_battery",
        "message": f"{devices}\n",
    }
    hass.services.call("persistent_notification", "create", service_data, False)
    logger.info(service_data["message"])


def get_battery_entities():
    def get_device_tracker_battery_entities():
        out = {}
        for entity_id in hass.states.entity_ids("device_tracker"):
            state = hass.states.get(entity_id)
            if "battery_level" in state.attributes:
                out.update({entity_id: state.attributes["battery_level"]})
        return out

    def get_sensor_battery_entities():
        out = {}
        for entity_id in hass.states.entity_ids("sensor"):
            state = hass.states.get(entity_id)
            if (
                state.attributes.get("device_class") is "battery"
                and "is_charging" not in state.attributes
                and "charging" not in state.state
                and "discharging" not in state.state
                and "unavailable" not in state.state
            ):
                out.update({entity_id: int(state.state)})
        return out

    entities = {}
    entities.update(get_device_tracker_battery_entities())
    entities.update(get_sensor_battery_entities())
    return entities


def get_low_battery_entities(battery_entities, threshold):
    if len(battery_entities) is 0:
        return None
    return [
        ''.join(entity_id + ': ' + str(value) + '%') for entity_id, value in battery_entities.items() if value < threshold
    ]


threshold = data.get("threshold", 10)
low_battery_devices = get_low_battery_entities(get_battery_entities(), threshold)
if len(low_battery_devices) > 0:
    persistent_warning_message(low_battery_devices)