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
        data[0].append(humidity_am)
        data[1].append(temp_am)
        data[2].append(temp_tmp)


    alarms = []
    for alarm in db.get_alarms():
        alarms.append((alarm["triggered_at"].replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal()), alarm["ended_at"] is not None, alarm.get("type")))

    plt.plot(time, data[0])
    plt.plot(time, data[1])
    plt.plot(time, data[2])
    for alarm in alarms:
        plt.axvline(x=alarm[0], color='g' if alarm[1] == True else 'r')
        if alarm[2]:
            plt.text(alarm[0], 0, alarm[2], rotation=90)
    plt.legend(legend)
    plt.show()
