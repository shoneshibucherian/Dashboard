from pymongo import MongoClient
from influxdb_client_3 import InfluxDBClient3, Point
# from influxdb_client_3.client.write_api import SYNCHRONOUS
from datetime import datetime, timezone,timedelta
from zoneinfo import ZoneInfo

offset = timedelta(hours=6)

mongo_client = MongoClient("mongodb://admin:neepodapati@149.165.155.201:27017/admin")

mongo_db = mongo_client["INT_records"]

collection = mongo_db["bursts"]


# Setup InfluxDB
client = InfluxDBClient3(
    #host="http://localhost:8181",
    host="http://149.165.159.143:8181",
    #token="apiv3_GWMhJX4vaLXTNNl7Jystram7pBR3IVSyahDUN6JaeDijsFea0XYcH5NnTr-DkabS-o3xmHe3B68SuDOfOp_crQ",
    token="apiv3_IBJTLhGoJUNQTtS_nj5Qq19nlel3KJfGdC6Br_DLC3HmQGkVyjfV5ECXVWE_xLR-CnoOyLVF0kAiBfGptLjTXw",

    database="INT_records"
)


# Aggregation pipeline
# pipeline =  [
#     {
#         '$addFields': {
#             'date': {
#                 '$dateFromString': {
#                     'dateString': '$Timestamp'
#                 }
#             }, 
#             'vlan': {
#                 '$concat': [
#                     'vlan_id:', {
#                         '$convert': {
#                             'input': '$vlan_id', 
#                             'to': 'string'
#                         }
#                     }
#                 ]
#             }
#         }
#     }, {
#         '$match': {
#             'Timestamp': {
#                 '$gt': '2025-06-24T00:00:57.906+00:00', 
#                 '$lt': '2025-06-24T23:58:57.906+00:00'
#             }
#         }
#     }, {
#         '$match': {
#             'vlan': {
#                 '$ne': 'vlan_id:0'
#             }
#         }
#     }, {
#         '$project': {
#             '_id': 0, 
#             'date': {
#                 '$dateTrunc': {
#                     'date': '$date', 
#                     'unit': 'hour'
#                 }
#             }, 
#             'vlan': 1
#         }
#     }, {
#         '$group': {
#             '_id': {
#                 'time': '$date', 
#                 'vlan': '$vlan'
#             }, 
#             'count': {
#                 '$count': {}
#             }
#         }
#     }, {
#         '$project': {
#             '_id': 0, 
#             'time': '$_id.time', 
#             'vlan': '$_id.vlan', 
#             'count': 1
#         }
#     }, {
#         '$sort': {
#             '_id.time': 1
#         }
#     }
# ]


pipeline_ok =  [
    {
        '$addFields': {
            'date': {
                '$dateFromString': {
                    'dateString': '$Timestamp'
                }
            }, 
            'vlan': {
                '$concat': [
                    'vlan_id:', {
                        '$convert': {
                            'input': '$vlan_id', 
                            'to': 'string'
                        }
                    }
                ]
            }
        }
    }, 
    # {
    #     '$match': {
    #         'Timestamp': {
    #             '$gt': '2025-06-24T00:00:57.906+00:00', 
    #             '$lt': '2025-06-24T23:58:57.906+00:00'
    #         }
    #     }
    # },
      {
        '$match': {
            'vlan': {
                '$ne': 'vlan_id:0'
            }
        }
    }, {
        '$project': {
            '_id': 0, 
            'date': {
                '$dateTrunc': {
                    'date': '$date', 
                    'unit': 'hour'
                }
            }, 
            'vlan': 1
        }
    }, {
        '$sort': {
            '_id.time': 1
        }
    }
]

pipeline_test =  [
    {
        '$addFields': {
            'vlan': {
                '$concat': [
                    'vlan_id:', {
                        '$convert': {
                            'input': '$vlan_id', 
                            'to': 'string'
                        }
                    }
                ]
            }
        }
    }, 
    # {
    #     '$match': {
    #         'Timestamp': {
    #             '$gt': '2025-06-24T00:00:57.906+00:00', 
    #             '$lt': '2025-06-24T23:58:57.906+00:00'
    #         }
    #     }
    # },
      {
        '$match': {
            'vlan': {
                '$ne': 'vlan_id:0'
            }
        }
    }, {
        '$project': {
            '_id': 0, 
            "time":"$Timestamp",
            'vlan': 1
        }
    }, 
    # {
    #     '$sort': {
    #         '_id.time': 1
    #     }
    # }
]

# Run aggregation
results = collection.aggregate(pipeline_test)

count=0
# Write to InfluxDB
# for doc in results:
#     # print(doc["time"])
#     doc["date"]=doc["date"].replace(tzinfo=timezone.utc)+ timedelta(microseconds=count)
#     # offset_time = base_time 
#     # doc["time"]=str(doc["time"])
    
#     print(doc)
#     count+=0.0001
#     # doc["time"] = datetime.fromisoformat(doc["time"].replace("Z", "+00:00"))
#     # timestamp = datetime.fromisoformat(doc["time"])
    
#     point = (
#         Point("vlan_test")
#         .tag("vlan", doc["vlan"])         # Use vlan as a tag
#         .field("count", 1)   
#         # .field("countVlan", doc["count"])
#         # .field("stime", str(doc["date"]))
#         .time(doc["date"])
#     )
#     # write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
#     client.write(record=point,precision='s')

# Write to InfluxDB
for doc in results:
    # print(doc["time"])
    # doc["date"]=doc["date"].replace(tzinfo=timezone.utc)+ timedelta(microseconds=count)
    # offset_time = base_time 
    # doc["time"]=str(doc["time"])
    doc["time"]=datetime.fromisoformat(doc["time"].replace("Z", "+00:00"))
    
    print(doc)
    count+=0.0001
    # doc["time"] = datetime.fromisoformat(doc["time"].replace("Z", "+00:00"))
    # timestamp = datetime.fromisoformat(doc["time"])
    
    point = (
        Point("vlan_test")
        .tag("vlan", doc["vlan"])         # Use vlan as a tag
        .field("count", 1)   
        # .field("countVlan", doc["count"])
        # .field("stime", str(doc["date"]))
        .time(doc["time"])
    )
    # write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
    client.write(record=point,precision='s')



with collection.watch() as stream:
    for change in stream:
        if change["operationType"] == "insert":
            doc = change["fullDocument"]
            # doc["Timestamp"]=doc["Timestamp"].replace(tzinfo=timezone.utc)+ timedelta(microseconds=count)
            doc["Timestamp"]=datetime.fromisoformat(doc["Timestamp"].replace("Z", "+00:00"))
            doc["vlan_id"]="vlan_id:"+doc["vlan_id"]
            count+=0.0001
            # Prepare and write to InfluxDB
            point = (Point("vlan_test") 
                .tag("vlan_id", doc["vlan_id"]) 
                .field("count", 1) 
                .time(doc["Timestamp"], write_precision='s')
              )  # ensure correct precision
            client.write(record=point,precision='s')
            

# print(results)
