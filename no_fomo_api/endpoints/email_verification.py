from flask_restful import Resource
from flask import request, Response


class EmailVerfication(Resource):
    def get(self):
        return 'wtf'