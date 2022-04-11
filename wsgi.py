from no_fomo_api.endpoints.email_verification import EmailVerfication
from no_fomo_api.endpoints.register import Register
from no_fomo_api.endpoints.login import Login
from no_fomo_api.app_config import api, app
from no_fomo_api.endpoints.instagram import Instagram

if __name__ == '__main__':
    api.add_resource(Register, '/register')
    api.add_resource(EmailVerfication, '/email')
    api.add_resource(Login, '/login')
    api.add_resource(Instagram, '/instagram')
    app.run(debug=True)

