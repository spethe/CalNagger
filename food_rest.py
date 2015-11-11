# -*- coding: utf-8 -*-
"""
Created on Sat Oct 31 12:33:46 2015
@author: swanand
"""
import os
import dweepy
import requests
import json
from flask import Flask
from flask import request
from pymongo import MongoClient
from urlparse import urlparse
import datetime

app = Flask(__name__)
MONGO_URL = os.environ.get('MONGOLAB_URI')
@app.route('/')
def hello_world():
    return 'Hello World!'



@app.route('/calories', methods=['GET'])
def getCaloriesForBarcode():
    
    barcode = request.args.get('barcode', '7613032921767') 
    
    print 'Should print++++++' + barcode
    url='http://world.openfoodfacts.org/api/v0/product/' + barcode + '.json'
    print 'URL is ----' + url
    data = requests.get(url)
    dumpToMongo(data.json())
    info = dumpToDweet(data.json())
    return json.dumps(json.dumps(info),indent=4)
    
def dumpToMongo(data):
   
    try:
        info ={'user':'1',
               'genericName': data['product']['generic_name'],
               'code': data['code'],
               'calories':data['product']['nutriments']['energy']
              }
    except:
        info ={'user':'1',
               'genericName': 'a',
               'code': '000',
               'calories':'111'
              }
          
    if MONGO_URL:
        client = MongoClient(MONGO_URL)
        db = client[urlparse(MONGO_URL).path[1:]]
    else:
        client = MongoClient()
        db = client['calnagger']
        
    conColl = db['consumption']
    conColl.insert(info)
    docs = [getDocsForToday(conColl)]
    print 'Todays Doc Count ----' + docs.count
    return {'user':'1',
           'genericName': data['product']['generic_name'],
           'code': data['code'],
           'calories':data['product']['nutriments']['energy']
          }

def dumpToDweet(data):
    info={}
    info.setdefault('user','1')
    info.setdefault('product',{})
    info['product'].setdefault('generic_name','default-name')
    info['product'].setdefault('nutriments', {})
    info['product']['nutriments'].setdefault('energy',0)
    info.setdefault('code','000000')
    info ={ 'user':'1',
            'genericName': data['product']['generic_name'],
            'code': data['code'],
            'calories':data['product']['nutriments']['energy']
          }
   
    dweepy.dweet_for('decisive-train', info)
    return {'user':'1',
           'genericName': data['product']['generic_name'],
           'code': data['code'],
           'calories':data['product']['nutriments']['energy']
          }   

def getDocsForToday(conColl):
    today = datetime.datetime.today()
    return conColl.find({
    '_id': {
        '$gte':datetime.datetime(today.year,today.month,today.day),
        '$lt': datetime.datetime.now()
    }
});
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)