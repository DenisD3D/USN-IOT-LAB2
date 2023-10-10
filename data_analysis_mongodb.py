import os

import matplotlib.pyplot as plt
from dateutil.tz import tz
from dotenv import load_dotenv

from mongodb import MongoDB

if __name__ == '__main__':
    load_dotenv()

    db = MongoDB(os.getenv('MANGODB_USERNAME'), os.getenv('MANGODB_PASSWORD'), os.getenv('MANGODB_CLUSTER_URL'))

    time = []
    data = [[], [], []]
    legend = ["AM2320Humidity", "AM2320Temperature", "TMP36"]
    for row in db.get_data():
        t = row["timestamp"].replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())
        humidity_am = row["AM2320Humidity"]
        temp_am = row["AM2320Temperature"]
        temp_tmp = row["TMP36"]

        time.append(t)
        if humidity_am is not None:
            data[0].append(humidity_am)
        else:
            data[0].append(data[0][-1])
        if temp_am is not None:
            data[1].append(temp_am)
        else:
            data[1].append(data[1][-1])
        if temp_tmp is not None:
            data[2].append(temp_tmp)
        else:
            data[2].append(data[2][-1])

    alarms = []
    for alarm in db.get_alarms():
        alarms.append((alarm["triggered_at"].replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal()), alarm["ended_at"] is not None, alarm.get("type")))

    fig = plt.figure()
    ax = fig.gca()
    ax2 = ax.twinx()
    ax2.plot(time, data[0], 'g', label="AM2320Humidity")
    ax.plot(time, data[1], 'r', label="AM2320Temperature")
    ax.plot(time, data[2], 'b', label="TMP36")
    for alarm in alarms:
        ax.axvline(x=alarm[0], color='g' if alarm[1] == True else 'r')
        if alarm[2]:
            ax.text(alarm[0], 0, alarm[2], rotation=90)
    ax.legend(loc='upper left')
    ax2.legend(loc='upper right')
    ax2.set_ylim(0, 100)
    ax.set_ylim(0, 40)
    plt.show()
