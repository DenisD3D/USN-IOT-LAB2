import os
from datetime import datetime

import matplotlib.pyplot as plt
from dotenv import load_dotenv

from mqtt import MQTT


def append_data(message, sensor_index: int):
    print("Received message: " + message.payload.decode("utf-8"))
    data[sensor_index][0].append(datetime.now())
    data[sensor_index][1].append(float(message.payload.decode("utf-8")))
    update_plot()


def append_alarm(message):
    alarms.append((datetime.now(), False, message.payload.decode("utf-8")))
    update_plot()

def ack_alarm():
    for alarm in alarms:
        alarm[1] = True


def update_plot():
    plt.plot(data[0][0], data[0][1])
    plt.plot(data[1][0], data[1][1])
    plt.plot(data[2][0], data[2][1])
    for alarm in alarms:
        plt.axvline(x=alarm[0], color='g' if alarm[1] == True else 'r')
        if alarm[2]:
            plt.text(alarm[0], 0, alarm[2], rotation=90)
    plt.legend(legend)
    plt.show()


if __name__ == '__main__':
    load_dotenv()

    mqtt = MQTT(os.getenv("MQTT_BROKER_URL"), int(os.getenv("MQTT_BROKER_PORT")), os.getenv("MQTT_USERNAME"), os.getenv("MQTT_PASSWORD"))

    data = [[[], []], [[], []], [[], []]]
    alarms = []
    mqtt.subscribe("AM2320Humidity", lambda client, userdata, message: append_data(message, 0))
    mqtt.subscribe("AM2320Temperature", lambda client, userdata, message: append_data(message, 1))
    mqtt.subscribe("TMP36", lambda client, userdata, message: append_data(message, 2))
    mqtt.subscribe("alarm", lambda client, userdata, message: append_alarm(message))
    mqtt.subscribe("alarm_ack", lambda client, userdata, message: ack_alarm())
    legend = ["AM2320Humidity", "AM2320Temperature", "TMP36"]

    mqtt.client.loop_forever()
