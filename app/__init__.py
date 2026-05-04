import os
from flask import Blueprint, Flask
from flask_migrate import Migrate
from app.errors import register_error_handlers
from config import Config
from app.extensions import db,login_manager, csrf
from app.db_setup import create_roles, setup_database


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # SQLite cannot create the database file when its folder (instance/ by default) is missing;
    # relative SQLite paths go to app.instance_path, which Flask-SQLAlchemy creates itself
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    db_path = db_uri[len('sqlite:///'):]
    if db_uri.startswith('sqlite:///') and os.path.isabs(db_path):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Initialize Flask extensions here
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app) 
    


    with app.app_context():
        setup_database()




    register_error_handlers(app, db)


    # Register blueprints here
    from app.routes import main
    app.register_blueprint(main)
     
    Migrate(app, db) 
    
    return app



