from pymongo import MongoClient
from influxdb_client_3 import InfluxDBClient3, Point
# from influxdb_client_3.client.write_api import SYNCHRONOUS
from datetime import datetime, timezone,timedelta
from zoneinfo import ZoneInfo
import time


mongo_client = MongoClient("mongodb://admin:neepodapati@149.165.155.201:27017/admin")

mongo_db = mongo_client["INT_records"]

collection = mongo_db["bursts"]
count=0

# Setup InfluxDB
client = InfluxDBClient3(
    #host="http://localhost:8181",
    host="http://149.165.159.143:8181",
    #token="apiv3_GWMhJX4vaLXTNNl7Jystram7pBR3IVSyahDUN6JaeDijsFea0XYcH5NnTr-DkabS-o3xmHe3B68SuDOfOp_crQ",
    token="apiv3_IBJTLhGoJUNQTtS_nj5Qq19nlel3KJfGdC6Br_DLC3HmQGkVyjfV5ECXVWE_xLR-CnoOyLVF0kAiBfGptLjTXw",

    database="INT_records_key"
)


# Load last max timestamp from file
try:
    with open("last_ts.txt", "r") as f:
        last_ts = f.read()
except:
    last_ts = "2000-01-01T18:45:19.178360Z"  # start far back




while True:
    print(last_ts)
    # Aggregation pipeline
    pipeline  =  [
    {
        '$addFields': {
            'key': {
                '$concat': [
                    'switch: ', {
                        '$toString': '$key.switch'
                    }, ', ', 'port: ', {
                        '$toString': '$key.port'
                    }, ', ', 'queue: ', {
                        '$toString': '$key.queue'
                    }
                ]
            }
        }
    }, {
        '$match': {
            'Timestamp': {
                '$gt': last_ts
            }
        }
    }, {
        '$match': {
            'vlan_id': {
                '$eq': 0
            }
        }
    }, {
        '$project': {
            '_id': 0, 
            "date":'$Timestamp',
            'key': 1
        }
    }
]
    results = list(collection.aggregate(pipeline))
    
    
    if results:
        for doc in results:
            if doc["date"] > last_ts:
                last_ts = doc["date"]
            doc["date"]=datetime.fromisoformat(str(doc["date"]).replace("Z", "+00:00"))
            count+=1
            print(str(doc)+"  "+str(count))
            
           
            point = (
                Point("key_test")
                .tag("key", doc["key"])         # Use vlan as a tag
                .field("count", 1)   
                .time(doc["date"])
            )
            client.write(record=point,precision='ms')



        # Update last_ts to max timestamp from batch
        
        with open("last_ts.txt", "w") as f:
            f.write(last_ts)

    time.sleep(1800)  # sleep for 30 minutes
