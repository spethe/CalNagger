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
from bson.objectid import ObjectId

app = Flask(__name__)
MONGO_URL = os.environ.get('MONGOLAB_URI')
@app.route('/')
def hello_world():
    return 'Hello World!'



@app.route('/calories', methods=['GET'])
def getCaloriesForBarcode():
    
    barcode = request.args.get('barcode', '7613032921767') 
    url='http://world.openfoodfacts.org/api/v0/product/' + barcode + '.json'
    print 'URL is ----' + url
    data = requests.get(url)
    aggrData = dumpToMongo(data.json())
    info = dumpToDweet(data.json(), aggrData)
    return json.dumps(json.dumps(info),indent=4)
    
def dumpToMongo(data):
    
    info={}
    info.setdefault('user','1')
    info.setdefault('product',{})
    info['product'].setdefault('generic_name','default-name')
    info['product'].setdefault('nutriments', {})
    info['product']['nutriments'].setdefault('energy',0)
    info['product']['nutriments'].setdefault('fat_100g',0)
    info['product']['nutriments'].setdefault('proteins_100g',0)
    info['product']['nutriments'].setdefault('carbohydrates_100g',0)
    info.setdefault('code','000000')

    info ={
            'user':'1',
            'genericName': data['product']['generic_name'],
            'code': data['code'],
            'calories':int(data['product']['nutriments']['energy']),
            'fat': float(data['product']['nutriments']['fat_100g']),
            'carbohydrates': float(data['product']['nutriments']['carbohydrates_100g']),
            'proteins': float(data['product']['nutriments']['proteins_100g'])
          }
          
    if MONGO_URL:
        client = MongoClient(MONGO_URL)
        db = client[urlparse(MONGO_URL).path[1:]]
    else:
        client = MongoClient()
        db = client['calnagger']
        
    conColl = db['consumption']
    conColl.insert(info)
    aggrDocs = getDocsForToday(conColl)
    doc = next(iter(aggrDocs), None)
    doc.setdefault('caloriesForDay',0)
    doc.setdefault('fatsForDay',0.0)
    doc.setdefault('carbsForDay', 0.0)
    doc.setdefault('proteinsForDay', 0.0)
    
    return {'user':'1',
           'genericName': data['product']['generic_name'],
           'code': data['code'],
           'calories':data['product']['nutriments']['energy'],
           'caloriesForToday':str(doc['caloriesForDay']),
           'fatForToday':str(doc['fatsForDay']),
           'carbsForToday':str(doc['carbsForDay']),
           'proteinsForToday':str(doc['proteinsForDay'])
          }

def dumpToDweet(data, aggrData):
    info={}
    info.setdefault('user','1')
    info.setdefault('product',{})
    info['product'].setdefault('generic_name','default-name')
    info['product'].setdefault('nutriments', {})
    info['product']['nutriments'].setdefault('energy',0)
    info.setdefault('code','000000')
    aggrData.setdefault('caloriesForToday', '0')
    aggrData.setdefault('carbsForToday', '0')
    aggrData.setdefault('fatForToday', '0')
    aggrData.setdefault('proteinsForToday', '0')

    info ={ 'user':'1',
            'genericName': data['product']['generic_name'],
            'code': data['code'],
            'calories':data['product']['nutriments']['energy'],
            'caloriesForToday':aggrData['caloriesForToday'],
            'carbsForToday':aggrData['carbsForToday'],
            'fatForToday':aggrData['fatForToday'],
            'proteinsForToday':aggrData['proteinsForToday']
          }
   
    dweepy.dweet_for('decisive-train', info)
    return info

def getDocsForToday(conColl):
    today = datetime.datetime.today()
    print datetime.datetime.now()
    aggr = conColl.aggregate(
        [
        {'$match':{'_id': {'$gte': ObjectId.from_datetime(datetime.datetime(today.year,today.month,today.day))}}},
        {'$group':{ '_id' : None, 'caloriesForDay': { '$sum': '$calories' },
        'fatsForDay':{'$sum':'$fat'}, 'carbsForDay':{'$sum':'$carbohydrates'}, 'proteinsForDay':{'$sum':'$proteins'}}}
        ]
        )
    
    '''results = conColl.find({
                                    '_id': {
                                    '$gte': ObjectId.from_datetime(datetime.datetime(today.year,today.month,today.day))                          
    }})'''
    
    aggrDocs = list(aggr)
    
    #Add Users
    return aggrDocs
    
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)