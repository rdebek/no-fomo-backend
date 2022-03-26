from no_fomo_api.endpoints.email_verification import EmailVerfication
from no_fomo_api.endpoints.register import Register
from no_fomo_api.app_config import api, app

if __name__ == '__main__':
    api.add_resource(Register, '/register')
    api.add_resource(EmailVerfication, '/email')
    app.run(debug=True)
