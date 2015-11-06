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
from pymongo import MongoClient
from urlparse import urlparse
app = Flask(__name__)
MONGO_URL = os.environ.get('MONGOLAB_URI')
@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/calories', methods=['GET'])
def getCaloriesForBarcode():
    url='http://world.openfoodfacts.org/api/v0/product/7613032921767.json'
    data = requests.get(url)
    info = dumpToDweet(data.json())
    dumpToMongo(data.json())
    return json.dumps(json.dumps(info),indent=4)
    
def dumpToMongo(data):
    info ={'user':'1',
           'genericName': data['product']['generic_name'],
           'code': data['code'],
           'calories':data['product']['nutriments']['energy']
          }
          
    if MONGO_URL:
        client = MongoClient(MONGO_URL)
        db = client[urlparse(MONGO_URL).path[1:]]
    else:
        client = MongoClient()
        db = client['calnagger']
        
    conColl = db['consumption']
    conColl.update({'user':'1'},{'$set':info},True)
    return {'user':'1',
           'genericName': data['product']['generic_name'],
           'code': data['code'],
           'calories':data['product']['nutriments']['energy']
          }

def dumpToDweet(data):
    info ={'user':'1',
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

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)