import os
import pymongo
from bson.son import SON
from pprint import pprint

client = pymongo.MongoClient(os.environ['MONGO_URI'])
db = client.va_circuit_court


def num_cases_per_month_by_court():
    return db.criminal_cases.aggregate([
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
    ])

def crime_type():
    return db.criminal_cases.aggregate([
        {'$group':{
            '_id': {
                'Charge': '$Charge'
            },
            'count': {'$sum': 1}
        }},
        {'$sort': SON([
            ('count', -1)
        ])},
        {'$limit': 10}
    ])

def sentence():
    return db.criminal_cases.aggregate([
        {'$group':{
            '_id': {
                'Court': '$Court',
                'Sex': '$Sex'
            },
            'count': {'$sum': 1}
        }},
        {'$group':{
            '_id': {
                'Court': '$_id.Court'
            },
            'data': {'$push': {
                'Sex': '$_id.Sex',
                'count': '$count'
            }},
            'count': {'$sum': '$count'}
        }},
        {'$sort': SON([
            ('_id.Court', 1)
        ])}
    ])

pprint(sentence())
