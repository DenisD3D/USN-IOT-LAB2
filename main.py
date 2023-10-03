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


def button_watch_thread():
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
            db.ack_alarm()

        time.sleep(0.1)


if __name__ == '__main__':
    load_dotenv()  # Load environment variables from .env file
    signal.signal(signal.SIGINT, signal_handler)  # Handle Ctrl+C

    # Initialize RaspberryPi GPIO
    if not should_fake_sensor():
        from RPi import GPIO

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(18, GPIO.OUT)

        # Initialize button watch thread
        button_watch_thread = threading.Thread(target=button_watch_thread)
        button_watch_thread.start()

    # Define sensors
    SENSORS = {
        "AM2320Humidity": {
            "sensor": AM2320Humidity(low_pass_filter_interval=2.3),
            "alarm": {
                "min": 0,
                "max": 100
            },
        },
        "AM2320Temperature": {
            "sensor": AM2320Temperature(low_pass_filter_interval=2.3),
            "alarm": {
                "min": 0,
                "max": 100
            },
        },
        "TMP36": {
            "sensor": TMP36(low_pass_filter_interval=2.3),
            "alarm": {
                "min": 0,
                "max": 100
            },
        }
    }

    # Initialize database
    db = MongoDB(os.getenv('MANGODB_USERNAME'), os.getenv('MANGODB_PASSWORD'), os.getenv('MANGODB_CLUSTER_URL'))

    # Initialize ThingSpeak
    ts = ThingSpeak(os.getenv('THINGSPEAK_API_KEY'))
    last_thingspeak_upload = datetime.now() - timedelta(seconds=15)

    # Initialize mqtt
    mqtt = MQTT(os.getenv("MQTT_BROKER_URL"), int(os.getenv("MQTT_BROKER_PORT")), os.getenv("MQTT_USERNAME"), os.getenv("MQTT_PASSWORD"))
    mqtt.client.loop_start()

    is_alarm_set = False
    is_running = True
    while is_running:
        time.sleep(2)

        # Read sensors values
        sensors_values = {}
        for sensor_name, sensor_data in SENSORS.items():
            sensor_value = sensor_data["sensor"].get_filtered_value()
            sensors_values[sensor_name] = sensor_value
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
            mqtt.publish(sensor_name, sensor_value)

        # Check for alarms
        for sensor_name, sensor_data in SENSORS.items():
            if not (sensor_data["alarm"]["min"] < sensors_values[sensor_name] < sensor_data["alarm"]["max"]):
                print(f"{sensor_name} alarm!")
                is_alarm_set = True
                if not should_fake_sensor():
                    GPIO.output(18, GPIO.HIGH)  # Turn on alarm
                db.trigger_alarm(data_id, sensor_name)  # Create alarm in database
                mqtt.publish("alarm", sensor_name)  # Publish alarm to MQTT

    # Stop mqtt
    mqtt.client.loop_stop()

    # Stop MongoDB
    db.close()
