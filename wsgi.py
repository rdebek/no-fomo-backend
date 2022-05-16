import datetime
import hashlib
import json
import re
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from os import environ
from random import randint
from statistics import mean
from typing import List

import requests
import tweepy
from apscheduler.schedulers.background import BackgroundScheduler
from exponent_server_sdk import (
    PushClient,
    PushMessage,
)
from flask import Flask, request, Response
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

AUTH_TOKEN = environ.get('AUTH_TOKEN')
INSTA_LOGIN = environ.get('INSTA_LOGIN')
INSTA_PASSWORD = environ.get('INSTA_PASSWORD')
SENDER_ADDRESS = environ.get('SENDER_EMAIL')
SENDER_PASS = environ.get('EMAIL_PASSWORD')
BEARER_TOKEN = environ.get('BEARER_TOKEN')

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('DATABASE_URI')
db = SQLAlchemy(app)
insta_api_client = None
sched = BackgroundScheduler()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    token = db.Column(db.String(6), nullable=True)

    def __repr__(self):
        return f'id: {self.id}, email: {self.email}, password: {self.password}, token: {self.token}'


class Trend(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), nullable=False)
    trend = db.Column(db.String(50), nullable=False)
    percentage = db.Column(db.String(10), nullable=False)
    token = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f'id: {self.id}, email: {self.email}, trend: {self.trend}, percentage: {self.percentage}, ' \
               f'token: {self.token}'


class Trends(Resource):
    def get(self):
        auth_token = request.args.get('auth')
        if not auth_token or auth_token != AUTH_TOKEN:
            return Response(status=400)
        email = request.args.get('email')
        trends = Trend.query.filter_by(email=email).all()
        return Response(json.dumps({'data': [{'name': record.trend, 'percentage': record.percentage,
                                              '7_days_data': TwitterApi().get_tweet_count(record.trend, 'day')} for
                                             record in trends]}))

    def post(self):
        auth_token = request.form.get('auth')
        if not auth_token or auth_token != AUTH_TOKEN:
            return Response(status=400)
        mode = request.form['mode']
        email = request.form['email']
        trend_name = request.form['trend']
        if mode == 'add':
            percentage = request.form['percentage']
            token = request.form['token']
            trend = Trend(email=email, trend=trend_name, percentage=percentage, token=token)
            try:
                db.session.add(trend)
                db.session.commit()
            except Exception as e:
                print(e)
                return Response(json.dumps({'status': 'error'}), status=400)
            return Response(json.dumps({'status': 'ok'}), status=200)
        elif mode == 'remove':
            try:
                Trend.query.filter_by(email=email, trend=trend_name).delete()
                db.session.commit()
            except Exception as e:
                print(e)
                return Response(json.dumps({'status': 'error'}), status=400)
            return Response(json.dumps({'status': 'ok'}))


class TwitterApi:
    def __init__(self):
        auth = tweepy.OAuth2BearerHandler(BEARER_TOKEN)
        self.api_v1_client = tweepy.API(auth)
        self.api_v2_client = tweepy.Client(BEARER_TOKEN)

    def get_available_places(self) -> dict:
        available_places = self.api_v1_client.available_trends()
        available_places.sort(key=self.sort_by_name)
        return available_places

    def get_trends_for_place(self, woeid: int) -> List:
        return_arr = []
        trends_arr = self.api_v1_client.get_place_trends(woeid)[0]['trends']
        for trend in trends_arr:
            if trend['tweet_volume']:
                return_arr.append(trend)
        return_arr.sort(key=self.sort_by_tweet_volume, reverse=True)
        return return_arr

    def get_tweet_count(self, query: str, granularity: str) -> dict:
        res = self.api_v2_client.get_recent_tweets_count(query, granularity=granularity)
        return {'data': res.data, 'total_count': res.meta['total_tweet_count']}

    @staticmethod
    def sort_by_tweet_volume(trend):
        return trend['tweet_volume']

    @staticmethod
    def sort_by_name(place: dict) -> str:
        return place['name']


class Twitter(Resource):
    def post(self):
        auth_token = request.form.get('auth')
        if not auth_token or auth_token != AUTH_TOKEN:
            return Response(status=400)
        twitter_api = TwitterApi()
        mode = request.form['mode']
        if mode == 'places':
            return Response(json.dumps(twitter_api.get_available_places()), status=200)
        elif mode == 'trends':
            woeid = int(request.form['woeid'])
            return Response(json.dumps(twitter_api.get_trends_for_place(woeid)), status=200)
        elif mode == 'counts':
            query = request.form['query']
            granularity = request.form['granularity']
            return Response(json.dumps(twitter_api.get_tweet_count(query, granularity)), status=200)


class InstagramApi:
    def __init__(self):
        self.session = requests.Session()
        self.logged_in = False

    def login(self):
        link = 'https://www.instagram.com/accounts/login/'
        login_url = 'https://www.instagram.com/accounts/login/ajax/'

        time = int(datetime.now().timestamp())

        payload = {
            'username': INSTA_LOGIN,
            'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{time}:{INSTA_PASSWORD}',
            'queryParams': {},
            'optIntoOneTap': 'false'
        }

        r = self.session.get(link)
        csrf = re.findall(r"csrf_token\":\"(.*?)\"", r.text)[0]
        self.session.post(login_url, data=payload, headers={
            "user-agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 "
                          "Safari/537.36",
            "x-requested-with": "XMLHttpRequest",
            "referer": "https://www.instagram.com/accounts/login/",
            "x-csrftoken": csrf
        })
        self.logged_in = True

    def get_places_info(self, lat, long):
        return self.session.get(f'https://www.instagram.com/location_search/?latitude={lat}+&longitude={long}').json()


class Instagram(Resource):
    def post(self):
        global insta_api_client
        auth_token = request.form.get('auth')
        if not auth_token or auth_token != AUTH_TOKEN:
            return Response(status=400)

        if not insta_api_client:
            print('creating insta client')
            insta_api_client = InstagramApi()

        if not insta_api_client.logged_in:
            print('logging in')
            insta_api_client.login()

        lat, long = request.form['lat'], request.form['long']
        return insta_api_client.get_places_info(lat, long)


class EmailVerfication(Resource):

    def post(self):
        auth_token = request.form.get('auth')
        if not auth_token or auth_token != AUTH_TOKEN:
            return Response(status=400)

        receiver_address = request.form['email']
        token = request.form.get('token')

        if token:
            return Response(json.dumps({'verify': self.verify_token(receiver_address, token)}), status=200)

        self.send_mail(receiver_address)
        return Response(json.dumps({'msg': 'Verification mail sent.'}), status=200)

    @staticmethod
    def verify_token(receiver_address, token):
        return token == User.query.filter_by(email=receiver_address).first().token

    @staticmethod
    def send_mail(receiver_address):
        mail_content = f'''Hello,
        In order to verify your account please copy the below code:
        {User.query.filter_by(email=receiver_address).first().token}
        Thank You
        '''
        receiver_address = receiver_address
        message = MIMEMultipart()
        message['From'] = SENDER_ADDRESS
        message['To'] = receiver_address
        message['Subject'] = 'NO FOMO account verification.'
        message.attach(MIMEText(mail_content, 'plain'))
        session = smtplib.SMTP('smtp.gmail.com', 587)
        session.starttls()
        session.login(SENDER_ADDRESS, SENDER_PASS)
        text = message.as_string()
        session.sendmail(SENDER_ADDRESS, receiver_address, text)
        session.quit()


class Login(Resource):
    def post(self):
        auth_token = request.form.get('auth')
        if not auth_token or auth_token != AUTH_TOKEN:
            return Response(status=400)

        email = request.form['email']
        password = Register.get_md5_hash(request.form['password'])

        return Response(json.dumps({'login': User.query.filter_by(email=email).first().password == password}))


class Register(Resource):

    def post(self):
        auth_token = request.form.get('auth')
        if not auth_token or auth_token != AUTH_TOKEN:
            return Response(status=400)

        email = request.form['email']
        password = request.form['password']

        user = User(email=email, password=self.get_md5_hash(password), token=self.generate_token())
        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError as e:
            print(e)
            return Response(json.dumps({'msg': 'Email is already in use.', 'error': '1'}), status=400)

        return Response(json.dumps({'msg': 'Account created successfully.'}), status=200)

    @staticmethod
    def generate_token():
        return "".join([str(randint(0, 9)) for _ in range(6)])

    @staticmethod
    def get_md5_hash(password):
        return hashlib.md5(password.encode()).hexdigest()


api.add_resource(Register, '/register')
api.add_resource(EmailVerfication, '/email')
api.add_resource(Login, '/login')
api.add_resource(Instagram, '/instagram')
api.add_resource(Twitter, '/twitter')
api.add_resource(Trends, '/trends')


def send_push_message(trend: Trend, percentage_reached: float):
    msg = PushMessage(trend.token, title=f'Threshold for trend "{trend.trend}" reached!',
                      body=f'Current percentage: {round(percentage_reached, 2)}%\nAwaited: {trend.percentage}%',
                      display_in_foreground=True, sound='default')
    PushClient().publish(msg)


def check_trends_status():
    trends = Trend.query.all()

    for trend in trends:
        if not trend.token:
            continue

        data = TwitterApi().get_tweet_count(trend.trend, 'day')
        avg = mean([data_point['tweet_count'] for data_point in data['data']][:-1])
        current_percent = compute_percent(avg, data['data'][-1]['tweet_count'])
        if 0 > int(trend.percentage) > current_percent or 0 < int(trend.percentage) < current_percent:
            send_push_message(trend, current_percent)
            trend.token = ''
            db.session.add(trend)

    db.session.commit()


def compute_percent(avg, last_count):
    try:
        percent = ((last_count - avg) / avg) * 100
    except ZeroDivisionError:
        return 0
    return percent


check_trends_status()

if __name__ == '__main__':
    sched.add_job(check_trends_status, 'interval', hours=1)
    sched.start()
    app.run(debug=False)
