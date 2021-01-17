sensor = data.get('sensor')
input_select = data.get('input_select')

if sensor is not None and input_select is not None:
    sensor_entities = hass.states.get(sensor).attributes['devices']
    list = []
    for e in sensor_entities:
        list.append(e['name'])
    service_data = {'entity_id': input_select,
                    'options': list}
    hass.services.call('input_select', 'set_options', service_data)
else:
    logger.warning('Missing arguments!')