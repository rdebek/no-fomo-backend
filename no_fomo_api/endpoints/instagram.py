from flask_restful import Resource
from flask import request, Response
from no_fomo_api.app_config import AUTH_TOKEN
from no_fomo_api.Socials.instagram_api import InstagramApi


class Instagram(Resource):
    def post(self):
        auth_token = request.form.get('auth')
        if not auth_token or auth_token != AUTH_TOKEN:
            return Response(status=400)

        insta_api = InstagramApi()
        insta_api.login()

        lat, long = request.form['lat'], request.form['long']
        return insta_api.get_places_info(lat, long)