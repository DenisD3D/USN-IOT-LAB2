import os
import signal
import threading
import time
from datetime import datetime, timedelta

from dotenv import load_dotenv

from mongodb import MongoDB
from mqtt import MQTT
from sensors import should_fake_sensor, AM2320Humidity, AM2320Temperature, TMP36
from thingspeak import ThingSpeak


def signal_handler(_, __):
    global is_running
    print("Exiting after next reading...")
    is_running = False


def button_watch_thread_func():
    global is_alarm_set
    GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    while is_running:
        if not is_alarm_set:
            time.sleep(0.1)
            continue

        if GPIO.input(17) == GPIO.HIGH:
            print("Alarm acknowledged")
            GPIO.output(18, GPIO.LOW)
            is_alarm_set = False
            SENSORS["AM2320Humidity"]["alarm"]["is_active"] = False
            SENSORS["AM2320Temperature"]["alarm"]["is_active"] = False
            SENSORS["TMP36"]["alarm"]["is_active"] = False
            db.ack_alarm()  # Acknowledge alarm in database
            mqtt.publish("alarm_ack")  # Publish alarm ack to MQTT

        time.sleep(0.1)


if __name__ == '__main__':
    load_dotenv()  # Load environment variables from .env file
    signal.signal(signal.SIGINT, signal_handler)  # Handle Ctrl+C

    is_running = True
    is_alarm_set = False

    # Initialize RaspberryPi GPIO
    if not should_fake_sensor():
        from RPi import GPIO

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(18, GPIO.OUT)

        # Initialize button watch thread
        button_watch_thread = threading.Thread(target=button_watch_thread_func)
        button_watch_thread.setDaemon(True)
        button_watch_thread.start()

    # Define sensors
    SENSORS = {
        "AM2320Humidity": {
            "sensor": AM2320Humidity(low_pass_filter_interval=2.3),
            "alarm": {
                "min": 0,
                "max": 60
            },
        },
        "AM2320Temperature": {
            "sensor": AM2320Temperature(low_pass_filter_interval=2.3),
            "alarm": {
                "min": 0,
                "max": 25
            },
        },
        "TMP36": {
            "sensor": TMP36(low_pass_filter_interval=2.3),
            "alarm": {
                "min": 0,
                "max": 30
            },
        }
    }

    for sensor in SENSORS:
        SENSORS[sensor]["is_active"] = False


    # Initialize database
    db = MongoDB(os.getenv('MANGODB_USERNAME'), os.getenv('MANGODB_PASSWORD'), os.getenv('MANGODB_CLUSTER_URL'))

    # Initialize ThingSpeak
    ts = ThingSpeak(os.getenv('THINGSPEAK_API_KEY'))
    last_thingspeak_upload = datetime.now() - timedelta(seconds=15)

    # Initialize mqtt
    mqtt = MQTT(os.getenv("MQTT_BROKER_URL"), int(os.getenv("MQTT_BROKER_PORT")), os.getenv("MQTT_USERNAME"), os.getenv("MQTT_PASSWORD"))
    mqtt.client.loop_start()

    while is_running:
        time.sleep(2)

        # Read sensors values
        sensors_values = {}
        for sensor_name, sensor_data in SENSORS.items():
            sensor_value = sensor_data["sensor"].get_filtered_value()
            sensors_values[sensor_name] = sensor_value
            if sensor_value is not None:
                print(f"{sensor_name}: {sensor_value:.2f}")
            time.sleep(0.1)

        # Upload data to MongoDB
        data_id = db.upload_data({**sensors_values, "timestamp": datetime.utcnow()})

        # Upload data to ThingSpeak
        if (datetime.now() - last_thingspeak_upload).total_seconds() > 15:  # Upload data every 15 seconds due to ThingSpeak rate limit
            ts.upload_data(sensors_values)
            last_thingspeak_upload = datetime.now()

        # Publish data to MQTT
        for sensor_name, sensor_value in sensors_values.items():
            if sensor_value is None:
                continue
            mqtt.publish(sensor_name, sensor_value)

        # Check for alarms
        for sensor_name, sensor_data in SENSORS.items():
            if sensors_values[sensor_name] is None:
                continue

            if not (sensor_data["alarm"]["min"] < sensors_values[sensor_name] < sensor_data["alarm"]["max"]) and sensor_data["alarm"]["is_active"] is False:
                print(f"{sensor_name} alarm!")
                is_alarm_set = True
                sensor_data["alarm"]["is_active"] = True
                if not should_fake_sensor():
                    GPIO.output(18, GPIO.HIGH)  # Turn on alarm
                db.trigger_alarm(data_id, sensor_name)  # Create alarm in database
                mqtt.publish("alarm", sensor_name)  # Publish alarm to MQTT

    # Stop mqtt
    mqtt.client.loop_stop()

    # Stop MongoDB
    db.close()
