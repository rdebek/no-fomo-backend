from flask import Flask
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from os import environ

AUTH_TOKEN = environ.get('AUTH_TOKEN')
INSTA_LOGIN = environ.get('INSTA_LOGIN')
INSTA_PASSWORD = environ.get('INSTA_PASSWORD')

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('DATABASE_URI')
db = SQLAlchemy(app)
