import os
from datetime import datetime

import matplotlib.pyplot as plt
from dotenv import load_dotenv

from mqtt import MQTT


def append_data(message, sensor_index: int):
    print("Received message for sensor (" + str(sensor_index) + "): " + message.payload.decode("utf-8"))
    data[sensor_index][0].append(datetime.now())
    data[sensor_index][1].append(float(message.payload.decode("utf-8")))
    update_plot()


def append_alarm(message):
    alarms.append((datetime.now(), False, message.payload.decode("utf-8")))
    update_plot()


def ack_alarm():
    for i in range(len(alarms)):
        alarms[i] = (alarms[i][0], True, alarms[i][2])


def update_plot():
    fig.clear()
    ax = fig.gca()
    ax2 = ax.twinx()
    ax2.plot(data[0][0], data[0][1], 'g', label="AM2320Humidity")
    ax.plot(data[1][0], data[1][1], 'r', label="AM2320Temperature")
    ax.plot(data[2][0], data[2][1], 'b', label="TMP36")
    for alarm in alarms:
        ax.axvline(x=alarm[0], color='g' if alarm[1] == True else 'r')
        if alarm[2]:
            ax.text(alarm[0], 0, alarm[2], rotation=90)
    ax.legend(loc='upper left')
    ax2.legend(loc='upper right')
    ax2.set_ylim(0, 100)
    ax.set_ylim(0, 40)
    fig.canvas.draw()
    fig.canvas.flush_events()


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

    plt.ion()
    fig = plt.figure()

    mqtt.client.loop_forever()
