from flask_restful import Resource
from flask import request, Response
from no_fomo_api.database.user import User
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from os import environ
from no_fomo_api.app_config import AUTH_TOKEN

SENDER_ADDRESS = environ.get('SENDER_EMAIL')
SENDER_PASS = environ.get('EMAIL_PASSWORD')


class EmailVerfication(Resource):

    def post(self):
        auth_token = request.form.get('auth')
        if not auth_token or auth_token != AUTH_TOKEN:
            return Response(status=400)

        receiver_address = request.form['email']
        token = request.form.get('token')

        if token:
            return self.verify_token(receiver_address, token)

        self.send_mail(receiver_address)
        return {'email': 'sent'}

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
