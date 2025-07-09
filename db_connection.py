from pymongo import MongoClient

def get_db():
    client = MongoClient('mongodb://localhost:27017/dashboard_app')
    return client['dashboard_app']
