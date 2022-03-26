from flask import request, Response
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from random import randint
import hashlib

from no_fomo_api.database.user import User
from no_fomo_api.app_config import db


class Register(Resource):

    def post(self):
        email = request.form['email']
        password = request.form['password']
        user = User(email=email, password=self.get_md5_hash(password))
        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError as e:
            print(e)
            return Response('Email is already in use.', status=400)
        user.token = self.generate_token()
        db.session.commit()
        return Response(status=200)

    @staticmethod
    def generate_token():
        return "".join([str(randint(0, 9)) for i in range(6)])

    @staticmethod
    def get_md5_hash(password):
        return hashlib.md5(password.encode()).hexdigest()