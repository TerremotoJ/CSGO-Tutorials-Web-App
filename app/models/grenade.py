from app.extensions import db


class Grenade(db.Model):
    __tablename__ = 'grenade'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.String(200), nullable=False, server_default='')
    notes = db.Column(db.Text, server_default='')
    
    user = db.relationship('User', backref='grenade')

    def __init__(self, name, description, notes=''):
        self.name = name
        self.description = description
        self.notes = notes