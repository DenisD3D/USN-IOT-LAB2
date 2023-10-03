import os

import paho.mqtt.client as paho
from dotenv import load_dotenv
from paho import mqtt


class MQTT:
    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = paho.Client(protocol=paho.MQTTv5)
        self.client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
        self.client.username_pw_set(self.username, self.password)
        self.client.connect(self.host, self.port)

    def publish(self, topic, message= None):
        self.client.publish(f"IOT2/{topic}", message)

    def subscribe(self, topic, callback):
        self.client.subscribe(f"IOT2/{topic}")
        self.client.message_callback_add(f"IOT2/{topic}", callback)


if __name__ == '__main__':
    load_dotenv()

    mqtt = MQTT(os.getenv("MQTT_BROKER_URL"), int(os.getenv("MQTT_BROKER_PORT")), os.getenv("MQTT_USERNAME"), os.getenv("MQTT_PASSWORD"))
    mqtt.publish("AM2320Humidity", 0)
    mqtt.publish("AM2320Temperature", 0)
    mqtt.publish("TMP36", 0)

    mqtt.client.loop_forever()