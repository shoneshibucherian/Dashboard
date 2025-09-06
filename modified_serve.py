"""A modified_serve.py hosts a Flask app, 
where it recives queries from the dashboard.
It connects to a MongoDB database and
 performs aggregation queries based on the received queries."""
import datetime
import sys
from flask import Flask, jsonify, request
from pymongo import MongoClient
app = Flask(__name__)

# pylint: disable=unused-argument,redefined-outer-name, line-too-long

if __name__ == "__main__":
    uri = sys.argv[1]
    client = MongoClient("mongodb://" + uri)
    db = client[sys.argv[2]]
    collection = db[sys.argv[3]]

    try:
        client.admin.command('ping')
        print("Connected successfully to server")
    except Exception as e:
        print("Server not available")
else:
    # When imported for pytest, we'll patch this in tests
    collection = None

def convert_time(time):
    """Convert milliseconds since epoch to a formatted date-time string."""
    print(type(time))
    timestamp_ms = float(time)
    # Convert milliseconds to seconds
    timestamp_sec = timestamp_ms / 1000

    dt_object = datetime.datetime.fromtimestamp(timestamp_sec)

    print("Date and Time:", dt_object)
    # You can also format it as a string:
    return  dt_object.strftime('%Y-%m-%dT%H:%M:%S')

def extract_expression(data):
    """Extracts the comparison operator and value from the input string.
    this function would recieve data in the form of >30 and it should return a {$gt:30}"""
    # Extract the 'state' field from the incoming data
    if data is not None:
        if data.startswith('>='):
            return {'$gte': float(data[2:])}
        elif data.startswith('<='):
            return {'$lte': float(data[2:])}
        elif data.startswith('>'):
            return {'$gt': float(data[1:])}
        elif data.startswith('<'):
            return {'$lt': float(data[1:])}
        elif data.startswith('<='):
            return {'$lte': float(data[2:])}
        elif data.startswith('='):
            return {'$eq': float(data[1:])}
        else:
            # print("*"*12,data)
            return {'$gt': 0}
    return None

def extract_keys(phy,vlan):
    """Extracts the port, queue, switch, and VLAN ID from the query."""
    switch=-1
    port=-1
    queue=-1
    vlan_id=-1
    if phy!="All":
        #phy will be in the form "switch:262146, port: 17, queue: 0",
        #the number associated with switch, port , queue must assigned to the respective variables
        parts = phy.split(", ")
        for part in parts:
            print(part)
            key, value = part.split(":")
            if key == "switch":
                switch = int(value)
            elif key == "port":
                port = int(value)
            elif key == "queue":
                queue = int(value)
    if vlan!="All":
        print(vlan)
        vlan_id=int(vlan)
    return switch, port, queue, vlan_id

def create_match_stage():
    """Creates a MongoDB match stage based on the request arguments to filter documents."""
    match=[
            {
                '$match': {
                    'duration_sec': {
                        '$gt': 0
                    },'mb_start_bw': {
                        '$gt': 0
                    },
                    'max_bandwidth': {
                        '$gt': 0
                    },
                    'key.port': {
                        '$ne': -1
                    },
                    'key.switch': {
                        '$ne': -1
                    },
                    'key.queue': {
                        '$ne': -1
                    },
                    'key.vlan_id': {
                        '$ne': -1
                    }
            }
        }
    ]
    dict_of_simple_no={"duration_sec":request.args.get('duration'),
    "max_bandwidth":request.args.get('max_band'),
    "mb_start_bw":request.args.get('start_band'),
    }
    dict_of_simple_no["key.switch"], dict_of_simple_no["key.port"], dict_of_simple_no["key.queue"], dict_of_simple_no["key.vlan_id"]= extract_keys(request.args.get('phy'),
                                                                                               request.args.get('vlan'))

    print(dict_of_simple_no)
    for key, value in dict_of_simple_no.items():
        if value is not None and value !="" and (key=="duration_sec" or key=="max_bandwidth" or key=="mb_start_bw"):
            expr=extract_expression(value)
            print(expr)
            match[0]["$match"][key]=expr
        elif value!=-1 and value !="":
            match[0]["$match"][key]={"$eq":value}
    return match

#time of the day stacked bar graph
@app.route("/time_of_day")
def time_of_day():
    """Creates a time-of-day aggregation pipeline and returns the results as JSON."""
    docfilter=create_match_stage()
    # start=request.args.get('start')
    # end=request.args.get('end')
    start=convert_time(request.args.get("from"))
    start_date=start.split("T")[0]
    end=convert_time(request.args.get("to"))
    end_date=end.split("T")[0]
    print(start+" "+end)
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
                        },
                        {
                        '$match': {
                            'day': {
                                '$gte': start_date, 
                                '$lte': end_date
                            }
                        }
                        }
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
    results = collection.aggregate(docfilter+freq_time_day)
    return jsonify(list(results))

def vlan_pipeline(start,end,interval):
    """Creates a VLAN aggregation pipeline based on the provided start and end times and interval."""
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
                    # '$count': {}
                    '$sum': 1
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
                            '$toString': '$_id.vlan'

                            # '$convert': {
                            #     'input': '$_id.vlan',
                            #     'to': 'string'
                            # }
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
    """Creates a physical key aggregation pipeline based on the provided start and end times and interval."""
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
                    # '$count': {}
                    '$sum': 1

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
    """Creates a physical key aggregation pipeline and returns the results as JSON."""
    start=convert_time(request.args.get("from"))
    end=convert_time(request.args.get("to"))
    interval= request.args.get("time")
    docfilter=create_match_stage()
    print(request.args.get("time")+" "+request.args.get("time"))
    get_key_pipeline=key_pipeline(start,end,interval)
    print(docfilter)
    results = collection.aggregate(docfilter+get_key_pipeline)
    return jsonify(list(results))

@app.route("/vlan_show")
def vlan():
    """Creates a VLAN aggregation pipeline and returns the results as JSON."""
    start=convert_time(request.args.get("from"))
    end=convert_time(request.args.get("to"))
    interval= request.args.get("time")
    print(request.args.get("time")+" "+request.args.get("time"))
    get_vlan_pipeline=vlan_pipeline(start,end,interval)
    docfilter=create_match_stage()
    print(docfilter)
    results = collection.aggregate(docfilter+get_vlan_pipeline)

    return jsonify(list(results))







#time series graph
@app.route("/bandwidth_vs_time")
def get_data():
    """Creates a bandwidth vs. time aggregation pipeline and returns the results as JSON."""
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
    """
    Creates a bandwidth vs. key aggregation pipeline and returns the results as JSON.
    """
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
                # '$count': {}
                '$sum': 1
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
                        '$toString': '$_id.switch'
                        # '$convert': {
                        #     'input': '$_id.switch',
                        #     'to': 'string'
                        # }
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
    """
    Creates a bandwidth vs. VLAN aggregation pipeline and returns the results as JSON.
    """
    bandwidth_vs_vlan = [
  {
    "$group":
      {
        "_id": "$key.vlan_id",
        "countKey": {
        #   "$count": {}
            '$sum': 1

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
            '$toString': "$_id"

            #   "$convert": {
            #     "input": "$_id",
            #     "to": "string"
            #   }
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

@app.route("/get_phy_keys")
def get_phy_keys():
    """
    Creates a physical key aggregation pipeline and returns the a list of unique physical keys as JSON
    which would be displayed as options in the dropdown menu in the dashboard.
    """
    phy_keys = [
    {
        '$group': {
            '_id': {
                '$concat': [
                    'switch:', {
                        '$toString': '$key.switch'
                    }, ', port:', {
                        '$toString': '$key.port'
                    }, ', queue:', {
                        '$toString': '$key.queue'
                    }
                ]
            }
        }
    }
]
    results = collection.aggregate(phy_keys)
    return jsonify(list(results))

@app.route("/get_vlan_ids")
def get_vlan_ids():
    """
    Creates a VLAN ID aggregation pipeline and returns the a list of unique VLAN IDs as JSON
    which would be displayed as options in the dropdown menu in the dashboard."""
    vlan_ids = [
    {
        '$group': {
            '_id': {
                '$concat': [
                     {
                        '$toString': [
                            '$key.vlan_id'
                        ]
                    }
                ]
            }
        }
    }
]
    results = collection.aggregate(vlan_ids)
    return jsonify(list(results))

@app.route("/ping")
def pinger():
    """A simple ping endpoint to check if the server is running."""
    status={"result":200}
    return jsonify(status)

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000)
