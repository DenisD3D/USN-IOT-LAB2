import os
from dotenv import load_dotenv
import requests


class ThingSpeak:
    def __init__(self, api_key):
        self._url = 'https://api.thingspeak.com/update?api_key=' + api_key

    def upload_data(self, data: dict) -> None:
        requests.get(f"{self._url}&field1={data['AM2320Humidity']}&field2={data['AM2320Temperature']}&field3={data['TMP36']}")


if __name__ == '__main__':
    load_dotenv()
    ts = ThingSpeak(os.getenv('THINGSPEAK_API_KEY'))
    ts.upload_data({"AM2320Humidity": 0,
                    "AM2320Temperature": 0,
                    "TMP36": 0})
