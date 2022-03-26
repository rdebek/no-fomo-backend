from no_fomo_api.app_config import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    token = db.Column(db.String(6), nullable=True)

    def __repr__(self):
        return f'id: {self.id}, email: {self.email}, password: {self.password}, token: {self.token}'
