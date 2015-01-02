import pymongo
from bson.son import SON
from pprint import pprint

client = pymongo.MongoClient('mongodb://ben:cfa123@ds029801.mongolab.com:29801/va_circuit_court')
db = client.va_circuit_court
pprint(db.criminal_cases.aggregate([
    {'$group':{
        '_id': {
            'Court': '$Court', 
            'year': {'$year': '$OffenseDate'},
            'month': {'$month': '$OffenseDate'}
        },
        'count': {'$sum': 1}
    }},
    {'$match' : { '_id.year' : 2014 } },
    {'$sort': SON([
        ('_id.Court', 1),
        ('_id.year', 1),
        ('_id.month', 1)
    ])},
    {'$group':{
        '_id': {
            'Court': '$_id.Court'
        },
        'data': {'$push': {
            'month': '$_id.month',
            'year': '$_id.year',
            'count': '$count'
        }}
    }},
    {'$sort': SON([
        ('_id.Court', 1)
    ])}
]))

