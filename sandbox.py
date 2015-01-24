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

def charges_by_race():
    return db.criminal_cases.aggregate([
        {'$group':{
            '_id': {
                'CodeSection': '$CodeSection',
                'Race': '$Race'
            },
            'charge': {'$first': '$Charge'},
            'avgSentenceTime': {'$avg': '$SentenceTimeDays'},
            'maxSentenceTime': {'$max': '$SentenceTimeDays'},
            'minSentenceTime': {'$min': '$SentenceTimeDays'},
            'count': {'$sum': 1}
        }},
        {'$match' : { 
            'count' : {'$gt' : 10},
            'avgSentenceTime': {'$gt': 0.0}
        }},
        {'$sort': SON([
            ('_id.CodeSection', 1)
        ])}
    ])
    

def sentence_time_overview():
    return db.criminal_cases.aggregate([
        {'$group':{
            '_id': None,
            'avgSentenceTime': {'$avg': '$SentenceTimeDays'},
            'maxSentenceTime': {'$max': '$SentenceTimeDays'},
            'totalSentenceTime': {'$sum': '$SentenceTimeDays'},
            'avgSentenceSuspended': {'$avg': '$SentenceSuspendedDays'},
            'maxSentenceSuspended': {'$max': '$SentenceSuspendedDays'},
            'totalSentenceSuspended': {'$sum': '$SentenceSuspendedDays'},
            'count': {'$sum': 1}
        }},
        {'$sort': SON([
            ('avgSentenceSuspended', 1)
        ])}
    ])
    
def sandbox():
    return db.criminal_cases.aggregate([
        {'$group':{
            '_id': {
                'CodeSection': '$CodeSection',
                'Race': '$Race'
            },
            'charge': {'$first': '$Charge'},
            'avgSentence': {'$avg': '$SentenceTimeDays'},
            'avgSentenceSuspended': {'$avg': '$SentenceSuspendedDays'},
            'count': {'$sum': 1}
        }},
        {'$group':{
            '_id': {
                'CodeSection': '$_id.CodeSection'
            },
            'races': {'$push': {
                'race': '$_id.Race',
                'avgSentence': '$avgSentence',
                'avgSentenceSuspended': '$avgSentenceSuspended',
                'count': '$count'
            }},
            'count': {'$sum': '$count'},
            'charge': {'$first': '$charge'}
        }},
        {'$sort': SON([
            ('count', 1)
        ])}
    ])

pprint(len(sandbox()['result']))
