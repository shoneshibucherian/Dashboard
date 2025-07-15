from flask import Flask, jsonify, request
from pymongo import MongoClient
import datetime
import sys
app = Flask(__name__)
uri= sys.argv[1]
print(f"uri is: {repr(uri)}", flush=True)
print("uri is",uri)
client = MongoClient(uri)

db = client["real_INT_records"]

collection = db["real_bursts"]


def convert_time(time):
    print(type(time))
    timestamp_ms = float(time)
    # Convert milliseconds to seconds
    timestamp_sec = timestamp_ms / 1000

    dt_object = datetime.datetime.fromtimestamp(timestamp_sec)

    print("Date and Time:", dt_object)
    # You can also format it as a string:
    return  dt_object.strftime('%Y-%m-%dT%H:%M:%S')




#time of the day stacked bar graph
@app.route("/time_of_day")
def time_of_day():
    start=request.args.get('start')
    end=request.args.get('end')
    freq_time_day = [
    {
        '$addFields': {
            'date': {
                '$dateFromString': {
                    'dateString': '$timestamp'
                }
            }
        }
    }, {
        '$addFields': {
            'Hour': {
                '$hour': '$date'
            }, 
            'day': {
                '$dateToString': {
                    'format': '%Y-%m-%d', 
                    'date': '$date'
                }
            }
        }
    }
    #{
    #    '$match': {
    #        'day': {
    #            '$gte': start, 
    #            '$lte': end
    #        }
    #    }
    #}
    ,{
        '$addFields': {
            'time_bucket': {
                '$switch': {
                    'branches': [
                        {
                            'case': {
                                '$lt': [
                                    '$Hour', 6
                                ]
                            }, 
                            'then': 'early_morning'
                        }, {
                            'case': {
                                '$lt': [
                                    '$Hour', 12
                                ]
                            }, 
                            'then': 'morning'
                        }, {
                            'case': {
                                '$lt': [
                                    '$Hour', 18
                                ]
                            }, 
                            'then': 'afternoon'
                        }
                    ], 
                    'default': 'evening'
                }
            }
        }
    }, {
        '$group': {
            '_id': {
                'day': '$day', 
                'bucket': '$time_bucket'
            }, 
            'counter': {
                '$sum': 1
            }
        }
    }, {
        '$group': {
            '_id': '$_id.day', 
            'early_morning': {
                '$sum': {
                    '$cond': [
                        {
                            '$eq': [
                                '$_id.bucket', 'early_morning'
                            ]
                        }, '$counter', 0
                    ]
                }
            }, 
            'morning': {
                '$sum': {
                    '$cond': [
                        {
                            '$eq': [
                                '$_id.bucket', 'morning'
                            ]
                        }, '$counter', 0
                    ]
                }
            }, 
            'afternoon': {
                '$sum': {
                    '$cond': [
                        {
                            '$eq': [
                                '$_id.bucket', 'afternoon'
                            ]
                        }, '$counter', 0
                    ]
                }
            }, 
            'evening': {
                '$sum': {
                    '$cond': [
                        {
                            '$eq': [
                                '$_id.bucket', 'evening'
                            ]
                        }, '$counter', 0
                    ]
                }
            }
        }
    }, {
        '$project': {
            '_id': 0, 
            'date': '$_id', 
            'early_morning': 1, 
            'morning': 1, 
            'afternoon': 1, 
            'evening': 1
        }
    }, {
        '$sort': {
            'date': 1
        }
    }
]
    results = collection.aggregate(freq_time_day)
    return jsonify(list(results))

def vlan_pipeline(start,end,interval):
    print(start+" "+end)
    pipeline=[
        {
            '$addFields': {
                'date': {
                    '$dateFromString': {
                        'dateString': '$timestamp'
                    }
                }
            }
        }, {
            '$match': {
                'timestamp': {
                    '$gt': start, 
                    '$lt': end
                },
                "key.vlan_id":{"$ne":0}
            }
        }, {
            '$group': {
                '_id': {
                    'y': {
                        '$year': '$date'
                    }, 
                    'm': {
                        '$month': '$date'
                    }, 
                    'd': {
                        '$dayOfMonth': '$date'
                    }, 
                    'h': {
                        '$hour': '$date'
                    }, 
                    'vlan': '$key.vlan_id'
                }, 
                'countVlan': {
                    '$count': {}
                }
            }
        }, {
            '$addFields': {
                'date': {
                    '$concat': [
                    'd', {
                        '$toString': {
                            '$cond': {
                                'if': {
                                    '$lt': [
                                        '$_id.d', 10
                                    ]
                                }, 
                                'then': {
                                    '$concat': [
                                        '0', {
                                            '$toString': '$_id.d'
                                        }
                                    ]
                                }, 
                                'else': {
                                    '$toString': '$_id.d'
                                }
                            }
                        }
                    }, ' ', {
                        '$toString': {
                            '$cond': {
                                'if': {
                                    '$lt': [
                                        '$_id.h', 10
                                    ]
                                }, 
                                'then': {
                                    '$concat': [
                                        '0', {
                                            '$toString': '$_id.h'
                                        }
                                    ]
                                }, 
                                'else': {
                                    '$toString': '$_id.h'
                                }
                            }
                        }
                    },"h"
                ]
                }, 
                'vlan': {
                    '$concat': [
                        'vlan_id:', {
                            '$convert': {
                                'input': '$_id.vlan', 
                                'to': 'string'
                            }
                        }
                    ]
                }
            }
        }, {
            '$match': {
                'vlan': {
                    '$ne': 'vlan_id:0'
                }
            }
        }, {
            '$project': {
                '_id': 0, 
                'vlan': 1, 
                'date': 1, 
                'countVlan': 1
            }
        }, {
            '$sort': {
                'date': 1
            }
        }
    ]
    
    hours=(int(request.args.get("to"))-int(request.args.get("from")))/3600000
    if interval[1]=='h' and hours<=24:
        pipeline[3]["$addFields"]["date"]["$concat"]=[
                    {
                        '$toString': {
                            '$cond': {
                                'if': {
                                    '$lt': [
                                        '$_id.h', 10
                                    ]
                                }, 
                                'then': {
                                    '$concat': [
                                        '0', {
                                            '$toString': '$_id.h'
                                        }
                                    ]
                                }, 
                                'else': {
                                    '$toString': '$_id.h'
                                }
                            }
                        }
                    },"h"
            ]
    if interval[1]=="d":
        del pipeline[2]["$group"]["_id"]["h"]
        print("hours", hours)
        pipeline[3]["$addFields"]["date"]["$concat"]=[
                    {
                        '$toString': {
                            '$cond': {
                                'if': {
                                    '$lt': [
                                        '$_id.m', 10
                                    ]
                                }, 
                                'then': {
                                    '$concat': [
                                        '0', {
                                            '$toString': '$_id.m'
                                        }
                                    ]
                                }, 
                                'else': {
                                    '$toString': '$_id.m'
                                }
                            }
                        }
                    }, '/', {
                        '$toString': {
                            '$cond': {
                                'if': {
                                    '$lt': [
                                        '$_id.d', 10
                                    ]
                                }, 
                                'then': {
                                    '$concat': [
                                        '0', {
                                            '$toString': '$_id.d'
                                        }
                                    ]
                                }, 
                                'else': {
                                    '$toString': '$_id.d'
                                }
                            }
                        }
                    }
            ]
                
            
    if interval[1]=="M":
        del pipeline[2]["$group"]["_id"]["d"]
        del pipeline[2]["$group"]["_id"]["h"]
        
        pipeline[3]["$addFields"]["date"]["$concat"] = [
                    {
                        '$toString': {
                            '$cond': {
                                'if': {
                                    '$lt': [
                                        '$_id.m', 10
                                    ]
                                }, 
                                'then': {
                                    '$concat': [
                                        '0', {
                                            '$toString': '$_id.m'
                                        }
                                    ]
                                }, 
                                'else': {
                                    '$toString': '$_id.m'
                                }
                            }
                        }
                    },"M"
            ]
    if interval[1]=="y":
        del pipeline[2]["$group"]["_id"]["d"]
        del pipeline[2]["$group"]["_id"]["h"]
        del pipeline[2]["$group"]["_id"]["m"]
        pipeline[3]["$addFields"]["date"]["$concat"] = [
                        {
                            '$toString': '$_id.y'
                        }
                    ]
    
    return pipeline

        





def key_pipeline(start,end,interval):
    print(start+" "+end)
    pipeline=[
        {
            '$addFields': {
                'date': {
                    '$dateFromString': {
                        'dateString': '$timestamp'
                    }
                }
            }
        }, {
            '$match': {
                'timestamp': {
                    '$gt': start, 
                    '$lt': end
                },
                "key.vlan_id":{"$eq":0}
            }
        }, {
            '$group': {
                '_id': {
                    'y': {
                        '$year': '$date'
                    }, 
                    'm': {
                        '$month': '$date'
                    }, 
                    'd': {
                        '$dayOfMonth': '$date'
                    }, 
                    'h': {
                        '$hour': '$date'
                    }, 
                    'key': '$key'
                }, 
                'countVlan': {
                    '$count': {}
                }
            }
        }, {
            '$addFields': {
                'date': {
                    '$concat': [
                    'd', {
                        '$toString': {
                            '$cond': {
                                'if': {
                                    '$lt': [
                                        '$_id.d', 10
                                    ]
                                }, 
                                'then': {
                                    '$concat': [
                                        '0', {
                                            '$toString': '$_id.d'
                                        }
                                    ]
                                }, 
                                'else': {
                                    '$toString': '$_id.d'
                                }
                            }
                        }
                    }, ' ', {
                        '$toString': {
                            '$cond': {
                                'if': {
                                    '$lt': [
                                        '$_id.h', 10
                                    ]
                                }, 
                                'then': {
                                    '$concat': [
                                        '0', {
                                            '$toString': '$_id.h'
                                        }
                                    ]
                                }, 
                                'else': {
                                    '$toString': '$_id.h'
                                }
                            }
                        }
                    },"h"
                ]
                }, 
                'key': {
                    '$concat': [
                        'switch:', {
                            '$toString': '$_id.key.switch'
                        }, ', port: ', {
                            '$toString': '$_id.key.port'
                        }, ', queue: ', {
                            '$toString': '$_id.key.queue'
                        }
                    ]
            }
            }
        }, {
            '$project': {
                '_id': 0, 
                'key': 1, 
                'date': 1, 
                'countVlan': 1
            }
        }, {
            '$sort': {
                'date': 1
            }
        }
    ]
    
    hours=(int(request.args.get("to"))-int(request.args.get("from")))/3600000
    if interval[1]=='h' and hours<=24:
        pipeline[3]["$addFields"]["date"]["$concat"]=[
                    {
                        '$toString': {
                            '$cond': {
                                'if': {
                                    '$lt': [
                                        '$_id.h', 10
                                    ]
                                }, 
                                'then': {
                                    '$concat': [
                                        '0', {
                                            '$toString': '$_id.h'
                                        }
                                    ]
                                }, 
                                'else': {
                                    '$toString': '$_id.h'
                                }
                            }
                        }
                    },"h"
            ]
    if interval[1]=="d":
        del pipeline[2]["$group"]["_id"]["h"]
        print("hours", hours)
        pipeline[3]["$addFields"]["date"]["$concat"]=[
                    {
                        '$toString': {
                            '$cond': {
                                'if': {
                                    '$lt': [
                                        '$_id.m', 10
                                    ]
                                }, 
                                'then': {
                                    '$concat': [
                                        '0', {
                                            '$toString': '$_id.m'
                                        }
                                    ]
                                }, 
                                'else': {
                                    '$toString': '$_id.m'
                                }
                            }
                        }
                    }, '/', {
                        '$toString': {
                            '$cond': {
                                'if': {
                                    '$lt': [
                                        '$_id.d', 10
                                    ]
                                }, 
                                'then': {
                                    '$concat': [
                                        '0', {
                                            '$toString': '$_id.d'
                                        }
                                    ]
                                }, 
                                'else': {
                                    '$toString': '$_id.d'
                                }
                            }
                        }
                    }
            ]
                
            
    if len(interval)==3:
        del pipeline[2]["$group"]["_id"]["d"]
        del pipeline[2]["$group"]["_id"]["h"]
        
        pipeline[3]["$addFields"]["date"]["$concat"] = [
                    {
                        '$toString': {
                            '$cond': {
                                'if': {
                                    '$lt': [
                                        '$_id.m', 10
                                    ]
                                }, 
                                'then': {
                                    '$concat': [
                                        '0', {
                                            '$toString': '$_id.m'
                                        }
                                    ]
                                }, 
                                'else': {
                                    '$toString': '$_id.m'
                                }
                            }
                        }
                    },"M"
            ]
    if interval[1]=="y":
        del pipeline[2]["$group"]["_id"]["d"]
        del pipeline[2]["$group"]["_id"]["h"]
        del pipeline[2]["$group"]["_id"]["m"]
        pipeline[3]["$addFields"]["date"]["$concat"] = [
                        {
                            '$toString': '$_id.y'
                        }
                    ]
    
    return pipeline





@app.route("/key_show")
def key():
    start=convert_time(request.args.get("from"))
    end=convert_time(request.args.get("to"))
    interval= request.args.get("time")
    print(request.args.get("time")+" "+request.args.get("time"))
    get_key_pipeline=key_pipeline(start,end,interval)
    results = collection.aggregate(get_key_pipeline)
    return jsonify(list(results))

@app.route("/vlan_show")
def vlan():
    start=convert_time(request.args.get("from"))
    end=convert_time(request.args.get("to"))
    interval= request.args.get("time")
    print(request.args.get("time")+" "+request.args.get("time"))
    get_vlan_pipeline=vlan_pipeline(start,end,interval)
    results = collection.aggregate(get_vlan_pipeline)
    
    return jsonify(list(results))







#time series graph
@app.route("/bandwidth_vs_time")
def get_data():
    bandwidth_vs_time = [
        {
            "$project" :{
                "_id":0,
                "_value":"$max_bandwidth",
                "_time": "$timestamp"
            }
        },
    ]
    results = collection.aggregate(bandwidth_vs_time)
    data = list(collection.find({}, {"_id": 0}))
    print(len(data)) # exclude MongoDB’s default _id
    return jsonify(list(results))





#PI- chart
@app.route("/bandwidth_vs_key_")
def get_band_vs_key():
    bandwidth_vs_key = [
    {
        '$match': {
            'key.vlan_id': {
                '$eq': 0
            }
        }
    },
    {
        '$group': {
            '_id': '$key',
            'countKey': {
                '$count': {}
            },
            'AverageBandWidth': {
                '$avg': '$max_bandwidth'
            }
        }
    }, {
        '$addFields': {
            'totalband': {
                '$multiply': [
                    '$countKey', '$AverageBandWidth'
                ]
            },
            'key': {
                '$concat': [
                    'switch:', {
                        '$convert': {
                            'input': '$_id.switch',
                            'to': 'string'
                        }
                    }, ', port: ', {
                        '$toString': '$_id.port'
                    }, ', queue: ', {
                        '$toString': '$_id.queue'
                    }
                ]
            }
        }
    }, {
        '$group': {
            '_id': 'null',
            'totalSum': {
                '$sum': '$totalband'
            },
            'data': {
                '$push': '$$ROOT'
            }
        }
    }, {
        '$unwind': {
            'path': '$data'
        }
    }, {
        '$project': {
            '_id': '$data.key',
            'percentage': {
                '$multiply': [
                    {
                        '$divide': [
                            '$data.totalband', '$totalSum'
                        ]
                    }, 100
                ]
            }
        }
    }
]
    results = collection.aggregate(bandwidth_vs_key)
   # exclude MongoDB’s default _id
    print(results)
    return jsonify(list(results))



#PI- chart
@app.route("/bandwidth_vs_vlan")
def get_band_vs_vlan():
    bandwidth_vs_vlan = [
  {
    "$group":
      {
        "_id": "$key.vlan_id",
        "countKey": {
          "$count": {}
        },
        "AverageBandWidth": {
          "$avg": "$max_bandwidth"
        }
      }
  },
  {
    "$addFields":
      {
        "totalband": {
          "$multiply": [
            "$countKey",
            "$AverageBandWidth"
          ]
        },
        "vlan": {
          "$concat": [
            "vlan_id:",
            {
              "$convert": {
                "input": "$_id.vlan_id",
                "to": "string"
              }
            }
          ]
        }
      }
  },{
      "$match":{
          "vlan":{"$ne":"vlan_id:0"}
      }
  },{
    "$group":
      {
        "_id": "null",
        "totalSum": {
          "$sum": "$totalband"
        },
        "data": {
          "$push": "$$ROOT"
        }
      }
  },
  {
    "$unwind":
      {
        "path": "$data"
      }
  },
  {
    "$project":
      {
        "_id": "$data.vlan",
        #"countKey": "$data.countKey",
        #"AverageBandWidth":
        #  "$data.AverageBandWidth",
        "percentage": {
          "$multiply": [
            {
              "$divide": [
                "$data.totalband",
                "$totalSum"
              ]
            },
            100
          ]
        }
      }
  }

    ]
    results = collection.aggregate(bandwidth_vs_vlan)
   # exclude MongoDB’s default _id

    return jsonify(list(results))


@app.route("/ping")
def pinger():
    list={"result":200}
    return jsonify(list)

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000)
