from datetime import datetime
import pandas as pandas
import pytz

# configure logging
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
# handler = logging.StreamHandler(sys.stdout)
# handler.setLevel(logging.DEBUG)
# formatter = logging.Formatter(
#     '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# handler.setFormatter(formatter)
# logger.addHandler(handler)

# template definitions
TEMPLATE_TIME_MS = '<TIME_MS>'
TEMPLATE_TIME_STR = '<TIME_STR>'


# MAIN MAPPER FUNCTION

def annotate_event(event, template_timestamps=False):
    try:
        # check if event is valid
        valid = 'sourceId' in event and \
                'metricId' in event and \
                'value' in event and \
                ('timestamp' in event or template_timestamps)

        # if the event is not valid, return None
        if not valid:
            return None

        # otherwise, return mapped event
        rdf_event = map_observation_to_rdf(
            event, template_timestamps=template_timestamps)
        return remove_whitespace(rdf_event) if rdf_event is not None else rdf_event

    except Exception as e:
        print(e)
        return None


def map_observation_to_rdf(event, template_timestamps=False):
    result = map_observation(source_id=event['sourceId'],
                             metric_id=event['metricId'],
                             value=event['value'],
                             timestamp=event['timestamp'] if not template_timestamps else None)
    return result


# MAPPING FUNCTIONS OF HEADACHE PARTS

def map_observation(metric_id,
                    source_id,
                    value,
                    timestamp):
    # extract patient ID from source ID
    split = source_id.split(".", 1)
    patient_id = split[0]
    source_id = split[1]

    # replace spaces by underscores in metricId
    metric_id = metric_id.replace(' ', '_')

    # add suffix to sensor (sourceId) based on metricId
    source_id = update_source_id(source_id, metric_id)

    # generate timestamp
    uuid = generate_uuid(metric_id, patient_id)
    if timestamp:
        timestamp_utc = timestamp
        time_str =timestamp
    else:
        timestamp_utc = TEMPLATE_TIME_MS
        time_str = TEMPLATE_TIME_STR

    # map value
    value_str, metric_group = map_value(value, metric_id)

    # create RDF data
    if metric_group == "CONTEXT":
        return OBSERVATION_TEMPLATE_CONTEXT_DAHCC % (uuid,
                                                     uuid, source_id,
                                                     uuid, uuid, metric_id,
                                                     uuid, str(timestamp_utc),
                                                     uuid, value
                                                     )
        # return OBSERVATION_TEMPLATE_CONTEXT % (source_id,
        #                                        patient_id, metric_id, uuid,
        #                                        patient_id, metric_id, uuid,
        #                                        metric_id, time_str, str(timestamp_utc), value_str)
    elif metric_group == "WEARABLE":
            return OBSERVATION_TEMPLATE_CONTEXT_DAHCC % (uuid,
                                                     uuid, source_id,
                                                     uuid, uuid, metric_id,
                                                     uuid, str(timestamp_utc),
                                                     uuid, value
                                                     )


        # return OBSERVATION_TEMPLATE_WEARABLE % (source_id,
        #                                         patient_id, metric_id, uuid,
        #                                         patient_id, metric_id, uuid,
        #                                         metric_id, time_str, str(timestamp_utc), value_str)


def map_value(value, metric_id):
    value_type, metric_group = float, None
    if metric_id in METRIC_TYPES_CONTEXT:
        value_type, metric_group = METRIC_TYPES_CONTEXT[metric_id], "CONTEXT"
    elif metric_id in METRIC_TYPES_WEARABLE:
        value_type, metric_group = METRIC_TYPES_WEARABLE[metric_id], "WEARABLE"

    if value_type == bool:
        processed_value = int(1) if value == 1 or value == '1' else int(0)
    else:
        processed_value = value

    return VALUE_TEMPLATE % (processed_value, TYPE_MAP[value_type]), metric_group


def update_source_id(source_id, metric_id):
    if metric_id in SENSOR_SUFFIX_MAP:
        return '%s.%s' % (source_id, SENSOR_SUFFIX_MAP[metric_id])
    else:
        return source_id


# MAPPING TEMPLATES

EXAMPLE_OBSERVATION = """
<https://dahcc.idlab.ugent.be/Protego/_participant1/obs0> <http://rdfs.org/ns/void#inDataset> <https://dahcc.idlab.ugent.be/Protego/_participant1> .
<https://dahcc.idlab.ugent.be/Protego/_participant1/obs0> <https://saref.etsi.org/core/measurementMadeBy> <https://dahcc.idlab.ugent.be/Homelab/SensorsAndActuators/70:ee:50:67:30:b2> .
<https://dahcc.idlab.ugent.be/Protego/_participant1/obs0> <https://saref.etsi.org/core/relatesToProperty> <https://dahcc.idlab.ugent.be/Homelab/SensorsAndActuators/org.dyamand.types.common.AtmosphericPressure> .
<https://dahcc.idlab.ugent.be/Protego/_participant1/obs0> <https://saref.etsi.org/core/hasTimestamp> "2022-01-03T09:04:55.000000"^^<http://www.w3.org/2001/XMLSchema#dateTime> .
<https://dahcc.idlab.ugent.be/Protego/_participant1/obs0> <https://saref.etsi.org/core/hasValue> "1013.1"^^<http://www.w3.org/2001/XMLSchema#float> 

"""

OBSERVATION_TEMPLATE_CONTEXT_DAHCC = """
<https://dahcc.idlab.ugent.be/Protego/_participant1/obs%s> <http://rdfs.org/ns/void#inDataset> <https://dahcc.idlab.ugent.be/Protego/_participant1> .
<https://dahcc.idlab.ugent.be/Protego/_participant1/obs%s> <https://saref.etsi.org/core/measurementMadeBy> <https://dahcc.idlab.ugent.be/Homelab/SensorsAndActuators/%s> .
<https://dahcc.idlab.ugent.be/Protego/_participant1/obs%s> <http://purl.org/dc/terms/isVersionOf> <https://saref.etsi.org/core/Measurement> .
<https://dahcc.idlab.ugent.be/Protego/_participant1/obs%s> <https://saref.etsi.org/core/relatesToProperty> <https://dahcc.idlab.ugent.be/Homelab/SensorsAndActuators/%s> .
<https://dahcc.idlab.ugent.be/Protego/_participant1/obs%s> <https://saref.etsi.org/core/hasTimestamp> "%s"^^<http://www.w3.org/2001/XMLSchema#dateTime> .
<https://dahcc.idlab.ugent.be/Protego/_participant1/obs%s> <https://saref.etsi.org/core/hasValue> "%s"^^<http://www.w3.org/2001/XMLSchema#float> .

"""

OBSERVATION_TEMPLATE_CONTEXT = """
<https://dahcc.idlab.ugent.be/Homelab/SensorsAndActuators/%s>
    <https://saref.etsi.org/core/makesMeasurement> <http://protego.idlab.ugent.be/%s/%s/obs%s> .
<http://protego.idlab.ugent.be/%s/%s/obs%s>
    <https://saref.etsi.org/core/relatesToProperty> <https://dahcc.idlab.ugent.be/Homelab/SensorsAndActuators/%s> ;
    <https://saref.etsi.org/core/hasTimestamp> "%s"^^<http://www.w3.org/2001/XMLSchema#dateTime> ;
    <https://dahcc.idlab.ugent.be/Ontology/Sensors/hasTimestampUTC> "%s"^^<http://www.w3.org/2001/XMLSchema#integer> ;
    <https://saref.etsi.org/core/hasValue> %s .
"""

OBSERVATION_TEMPLATE_WEARABLE = """
<https://dahcc.idlab.ugent.be/Homelab/SensorsAndWearables/%s>
    <https://saref.etsi.org/core/makesMeasurement> <http://protego.idlab.ugent.be/%s/%s/obs%s> .
<http://protego.idlab.ugent.be/%s/%s/obs%s>
    <https://saref.etsi.org/core/relatesToProperty> <https://dahcc.idlab.ugent.be/Homelab/SensorsAndWearables/%s> ;
    <https://saref.etsi.org/core/hasTimestamp> "%s"^^<http://www.w3.org/2001/XMLSchema#dateTime> ;
    <https://dahcc.idlab.ugent.be/Ontology/Sensors/hasTimestampUTC> "%s"^^<http://www.w3.org/2001/XMLSchema#integer> ;
    <https://saref.etsi.org/core/hasValue> %s .
"""

VALUE_TEMPLATE = "\"%s\"^^%s"

# CONVERTERS OF JSON VALUES TO ONTOLOGY CONCEPTS

METRIC_TYPES_CONTEXT = {
    "airquality.co2": float,
    "airquality.voc_total": bool,
    "energy.consumption": float,
    "energy.power": float,
    "environment.blind": float,
    "environment.button": bool,
    "environment.dimmer": float,
    "environment.light": float,
    "environment.lightswitch": bool,
    "environment.motion": bool,
    "environment.open": bool,
    "environment.relativehumidity": float,
    "environment.relay": bool,
    "environment.temperature": float,
    "environment.voltage": float,
    "environment.waterRunning::bool": bool,
    "mqtt.lastMessage": str,
    "org.dyamand.aqura.AquraLocationState_Protego User": str,
    "org.dyamand.aqura.AquraLocationState_Protego_User": str,
    "org.dyamand.types.airquality.CO2": float,
    "org.dyamand.types.common.AtmosphericPressure": float,
    "org.dyamand.types.common.Loudness": float,
    "org.dyamand.types.common.RelativeHumidity": float,
    "org.dyamand.types.common.Temperature": float,
    "people.presence.detected": bool,
    "people.presence.numberDetected": float,
    "weather.pressure": float,
    "weather.rainrate": float,
    "weather.windspeed": float
}

METRIC_TYPES_WEARABLE = {
    "org.dyamand.types.health.BodyTemperature": float,
    "org.dyamand.types.common.Load": float,
    "org.dyamand.types.health.DiastolicBloodPressure": float,
    "org.dyamand.types.health.HeartRate": float,
    "org.dyamand.types.health.SystolicBloodPressure": float,
    "org.dyamand.types.health.GlucoseLevel": float,
    "smartphone.acceleration.x": float,
    "smartphone.acceleration.y": float,
    "smartphone.acceleration.z": float,
    "smartphone.ambient_light": float,
    "smartphone.ambient_noise.amplitude": float,
    "smartphone.ambient_noise.frequency": float,
    "smartphone.application": str,
    "smartphone.gravity.x": float,
    "smartphone.gravity.y": float,
    "smartphone.gravity.z": float,
    "smartphone.gyroscope.x": float,
    "smartphone.gyroscope.y": float,
    "smartphone.gyroscope.z": float,
    "smartphone.keyboard": str,
    "smartphone.linear_acceleration.x": float,
    "smartphone.linear_acceleration.y": float,
    "smartphone.linear_acceleration.z": float,
    "smartphone.location.accuracy": float,
    "smartphone.location.altitude": float,
    "smartphone.location.bearing": float,
    "smartphone.location.latitude": float,
    "smartphone.location.longitude": float,
    "smartphone.magnetometer.x": float,
    "smartphone.magnetometer.y": float,
    "smartphone.magnetometer.z": float,
    "smartphone.proximity": float,
    "smartphone.rotation.x": float,
    "smartphone.rotation.y": float,
    "smartphone.rotation.z": float,
    "smartphone.screen": str,
    "smartphone.sleepAPI.API_confidence": float,
    "smartphone.sleepAPI.model_type": str,
    "smartphone.sleepAPI.t_start": float,
    "smartphone.sleepAPI.t_stop": float,
    "smartphone.step": float,
    "wearable.acceleration.x": float,
    "wearable.acceleration.y": float,
    "wearable.acceleration.z": float,
    "wearable.battery_level": float,
    "wearable.bvp": float,
    "wearable.gsr": float,
    "wearable.ibi": float,
    "wearable.on_wrist": bool,
    "wearable.skt": float
}

SENSOR_SUFFIX_MAP = {
    "org.dyamand.aqura.AquraLocationState_Protego_User": "Tag",
    "wearable.acceleration.x": 'Accelerometer',
    "wearable.acceleration.y": 'Accelerometer',
    "wearable.acceleration.z": 'Accelerometer',
    "wearable.battery_level": 'BatteryLevelMeter',
    "wearable.bvp": 'PPGSensor',
    "wearable.gsr": 'GSRSensor',
    "wearable.ibi": 'PPGSensor',
    "wearable.on_wrist": 'OnWristDetector',
    "wearable.skt": 'Thermopile'
}

TYPE_MAP = {
    float: "<http://www.w3.org/2001/XMLSchema#float>",
    int: "<http://www.w3.org/2001/XMLSchema#integer>",
    bool: "<http://www.w3.org/2001/XMLSchema#integer>",
    str: "<http://www.w3.org/2001/XMLSchema#string>"
}


# HELPER FUNCTIONS

def convert_timestamp_to_string(timestamp):
    return datetime.fromtimestamp(float(timestamp) / 1000.0,
                                  pytz.timezone('Europe/Brussels')). \
        strftime('%Y-%m-%dT%H:%M:%S')


uuid_map = {}


def generate_uuid(metric_id, patient_id):
    key = '%s' % (patient_id)
    if key not in uuid_map:
        uuid_map[key] = 0
    result = uuid_map[key]
    uuid_map[key] += 1
    return result


def remove_whitespace(given_str):
    return ' '.join(given_str.split())


def map_feather(file, sensors_to_map, number_of_events, sample_rate):
    counter = 0
    file = pandas.read_feather(file)
    for sensor in sensors_to_map:
        df = file[file['Metric'] == sensor]
        df['Sampling-Timestamp'] = pandas.to_datetime(df['Timestamp'].astype(str))
        df.set_index('Sampling-Timestamp', inplace=True)
        df.index = pandas.to_datetime(df.index)
        for index in df.index:
            # df_resampled = df.resample(f'{sample_rate}S').first().reset_index()
            df_resampled = df
            source = (df_resampled['Sensor'][index])
            metric = (df_resampled['Metric'][index])
            value = (df_resampled['Value'][index])
            timestamp = (df_resampled['Timestamp'][index])
            timestamp_str = str(timestamp)
            hour = timestamp_str[0:2]
            minute = timestamp_str[3:5]
            second = timestamp_str[6:8]
            millisecond = '000Z'
            if (timestamp_str[9:12] == ''):
                continue
            else:
                millisecond = timestamp_str[9:13] + 'Z'

            current_time = datetime.now()
            year = current_time.strftime("%Y")
            month = current_time.strftime("%m")
            day = current_time.strftime("%d")

            try: 
                time_value = str(year) + '-' + str(month) + '-' + str(day) + 'T' + str(hour) + ':' + str(minute) + ':' + str(second) + '.' + str(millisecond)
            except Exception as e:
                print('Exception is' + e)
            
            event = {
                'sourceId': source,
                'metricId': metric,
                'value': value,
                'timestamp': time_value
            }
            result = annotate_event(event)  
            with open('/home/kush/Code/feather-RDF-mapper/data/rdfData/accelerometer/acc-x-2min.nt', 'a') as file:
                pass
                counter = counter + 1
                if counter > number_of_events:
                    break
                else:
                    file.write('\n')
                    file.write(result)
if __name__ == '__main__':
    file = 'data/dataset_participant6.feather'  
    # sensors = ['wearable.bvp']
    # sensors = ['org.dyamand.types.health.SpO2']
    sensors = ['wearable.acceleration.x']
    map_feather(file= file, sensors_to_map= sensors, number_of_events= 120*32, sample_rate= 2)