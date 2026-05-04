import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Required: the app refuses to start without it, so no default key can leak
    SECRET_KEY = os.environ['SECRET_KEY']
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
