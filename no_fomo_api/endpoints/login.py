from flask_restful import Resource
from flask import request, Response
from no_fomo_api.app_config import AUTH_TOKEN
from no_fomo_api.endpoints.register import Register
from no_fomo_api.database.user import User


class Login(Resource):
    def get(self):
        print(User.query.all())
        return 0

    def post(self):
        auth_token = request.form.get('auth')
        if not auth_token or auth_token != AUTH_TOKEN:
            return Response(status=400)

        email = request.form['email']
        password = Register.get_md5_hash(request.form['password'])

        return User.query.filter_by(email=email).first().password == password
