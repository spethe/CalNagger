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
from datetime import datetime
from bson.objectid import ObjectId

OUNCE_TO_G = 28.3495
app = Flask(__name__)
MONGO_URL = os.environ.get('MONGOLAB_URI')

userinfo = {
'1':'peanut',
'2':'gluten'
}

@app.route('/')
def hello_world():
    return 'Hello World!'



@app.route('/calories', methods=['GET'])
def getCaloriesForBarcode():
    
    barcode = request.args.get('barcode', '00214036') 
    weight = request.args.get('weight','16')
    user = request.args.get('user','2')
    wt_in_g = float(weight) * OUNCE_TO_G
    no_of_100g= wt_in_g/100
    url='http://world.openfoodfacts.org/api/v0/product/' + barcode + '.json'
    
    print 'URL is ----' + url
    print 'NO-100   --- ' + str(no_of_100g)
    data = requests.get(url)
    
    aggrData = dumpToMongo(data.json(),no_of_100g, user)
    info = dumpToDweet(data.json(), aggrData, user)
    return json.dumps(json.dumps(info),indent=4)
    
def dumpToMongo(data, no_of_100g, user):
    info = getDefaultInfo(user);

    info ={
            'user': user,
            'genericName': data['product']['product_name'],
            'code': data['code'],
            'calories':int(data['product']['nutriments']['energy']),
            'fat': float(data['product']['nutriments']['fat_100g'])*no_of_100g,
            'carbohydrates': float(data['product']['nutriments']['carbohydrates_100g'])*no_of_100g,
            'proteins': float(data['product']['nutriments']['proteins_100g']) * no_of_100g
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
    doc = getDefaultAggrDoc(doc)
    
    return {'user':user,
           'genericName': data['product']['product_name'],
           'code': data['code'],
           'calories':data['product']['nutriments']['energy'],
           'caloriesForToday':str(doc['caloriesForDay']),
           'fatForToday':str(doc['fatsForDay']),
           'carbsForToday':str(doc['carbsForDay']),
           'proteinsForToday':str(doc['proteinsForDay'])
          }


def getDefaultAggrDoc(doc):
    doc.setdefault('caloriesForDay',0)
    doc.setdefault('fatsForDay',0.0)
    doc.setdefault('carbsForDay', 0.0)
    doc.setdefault('proteinsForDay', 0.0)
    return doc;
    
def getDefaultInfo(user):
    info={}
    info.setdefault('user', user)
    info.setdefault('product',{})
    info['product'].setdefault('generic_name','default-name')
    info['product'].setdefault('nutriments', {})
    info['product']['nutriments'].setdefault('energy',0)
    info['product']['nutriments'].setdefault('fat_100g',0)
    info['product']['nutriments'].setdefault('proteins_100g',0)
    info['product']['nutriments'].setdefault('carbohydrates_100g',0)
    info.setdefault('code','000000')
    return info
    
def dumpToDweet(data, aggrData, user):

    alert = isProhibited(data,user)
    info = getDefaultInfo(user)
    aggrData = getDefaultAggrDoc(aggrData)
    
    info ={ 'user': user,
            'genericName': data['product']['product_name'],
            'code': data['code'],
            'calories':data['product']['nutriments']['energy'],
            'caloriesForToday':aggrData['caloriesForToday'],
            'carbsForToday':aggrData['carbsForToday'],
            'fatForToday':aggrData['fatForToday'],
            'proteinsForToday':aggrData['proteinsForToday'],
            'weekly_calories':'10,2,3,5,6,7,8',
            'alert': alert
            
          }
   
    dweepy.dweet_for('decisive-train', info)
    return info

def isProhibited(data,user):
    product = data['product']
    product.setdefault('traces','')
    traces = str(product.get('traces'))
    if userinfo[user] == '':
        return '';
    
    if traces.find(userinfo[user]):
        alert=userinfo[user]
    return alert
    
def getDocsForToday(conColl):
    today = datetime.today()
    aggr = conColl.aggregate(
        [
        {'$match':{'_id': {'$gte': ObjectId.from_datetime(datetime(today.year,today.month,today.day))}}},
        {'$group':{ '_id' : None, 'caloriesForDay': { '$sum': '$calories' },
        'fatsForDay':{'$sum':'$fat'}, 'carbsForDay':{'$sum':'$carbohydrates'}, 'proteinsForDay':{'$sum':'$proteins'}}}
        ]
        )
    
    aggrDocs = list(aggr)
    
    return aggrDocs
    
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)