# -*- coding: utf-8 -*-
"""
Created on Sat Oct 31 12:33:46 2015

@author: swanand
"""
import os
import requests
import json
from flask import Flask
from pymongo import MongoClient
app = Flask(__name__)

MONGO_URL='mongodb://admin:admin@ds049864.mongolab.com:49864/heroku_2xf72wpb?authMechanism=SCRAM-SHA-1'

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/calories', methods=['GET','POST'])
def getCaloriesForBarcode():
    url='http://world.openfoodfacts.org/api/v0/product/737628064502.json'
    data = requests.get(url)
    print os.environ.get("MONGOLAB_URI")
    #dumpToMongo(data.json())
    info = dumpToDweet(data.json())
    return json.dumps(json.dumps(info),indent=4)
    
def dumpToMongo(data):
    info ={'user':'1',
           'genericName': data['product']['generic_name'],
           'code': data['code'],
           'calories':data['product']['nutriments']['energy']
          }
    client = MongoClient('mongodb://admin:admin@ds049864.mongolab.com:49864/heroku_2xf72wpb?authMechanism=SCRAM-SHA-1')
    if client!= None:
        conColl = client['consumption']
        conColl.update_one({'user':'1'},{'$set':info},True)

def dumpToDweet(data):
    dweetUrl = 'http://dweet.io:80/dweet/for/decisive-train/'
    info ={'user':'1',
           'genericName': data['product']['generic_name'],
           'code': data['code'],
           'calories':data['product']['nutriments']['energy']
          }
    proxyDict = {
              "http"  : os.environ.get('FIXIE_URL', ''),
              "https" : os.environ.get('FIXIE_URL', '')
            }
    resp = requests.post(dweetUrl, data=json.dumps(info),proxies=proxyDict)
    print resp
    return {'user':'1',
           'genericName': data['product']['generic_name'],
           'code': data['code'],
           'calories':data['product']['nutriments']['energy']
          }
    
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)