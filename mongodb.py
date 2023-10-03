from datetime import datetime

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


class MongoDB:
    def __init__(self, username: str, password: str, cluster_url: str):
        uri = f"mongodb+srv://{username}:{password}@{cluster_url}/?retryWrites=true&w=majority"
        self.client = MongoClient(uri, server_api=ServerApi('1'))
        self.database = self.client["iot2"]
        self.datalog_collection = self.database["datalog"]
        self.alarm_collection = self.database["alarms"]

    def ping(self):
        try:
            self.client.admin.command('ping')
            print("Ping successful. Connected to MongoDB!")
        except Exception as e:
            print(e)

    def upload_data(self, data: dict) -> str:
        return self.datalog_collection.insert_one(data).inserted_id

    def trigger_alarm(self, data_id: str, type: str) -> None:
        self.alarm_collection.insert_one({
            "data_id": data_id,
            "type": type,
            "triggered_at": datetime.utcnow(),
            "ended_at": None
        })

    def ack_alarm(self) -> None:
        for alarm in self.alarm_collection.find({"ended_at": None}):
            self.alarm_collection.update_one({"_id": alarm["_id"]}, {"$set": {"ended_at": datetime.utcnow()}})

    def get_data(self):
        return self.datalog_collection.find()

    def get_alarms(self):
        return self.alarm_collection.find()

    def close(self):
        self.database.client.close()


if __name__ == '__main__':
    from dotenv import load_dotenv
    import os

    load_dotenv()
    db = MongoDB(os.getenv('MANGODB_USERNAME'), os.getenv('MANGODB_PASSWORD'), os.getenv('MANGODB_CLUSTER_URL'))
    db.ping()
    print("Uploading data")
    upload_id = db.upload_data({"AM2320Humidity": 0,
                                "AM2320Temperature": 0,
                                "TMP36": 0,
                                "timestamp": datetime.utcnow()})

    print("Data uploaded")
    print("Triggering alarm")
    db.trigger_alarm(upload_id, "test_alarm")
    print("Alarm triggered")
    input("Press enter to ack alarm...")
    print("Acknowledging alarm")
    db.ack_alarm()
    print("Alarm acknowledged")
