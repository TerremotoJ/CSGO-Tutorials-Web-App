from functools import wraps
from flask import abort, g, url_for
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.models.permission import Permission

from app.models.role import Role


# Roles with a limit on the total number of videos they can watch (the count never resets)
WATCH_LIMITS = {'Free-Account': 3, 'Anonymous-Account': 2}


def role_required(*role_names):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if hasattr(g.user, "has_role") and any(g.user.has_role(name) for name in role_names):
                return view_func(*args, **kwargs)
            abort(403)

        return wrapper

    return decorator



class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), server_default='1', index=True)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    username = db.Column(db.String(50), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.Text(), nullable=False)  
    
    is_anonymous = db.Column(db.Boolean, server_default='False')
    watched_videos = db.Column(db.Integer, nullable=True) # maybe it's better to put this in PermissionRole / permission
    
    authenticated = db.Column(db.Boolean, server_default='False')
    profile_pic = db.Column(db.String(255), server_default = 'chicken.png')
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    last_login_at = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.current_timestamp())
    notes = db.Column(db.Text, server_default='') 

    grenade_id = db.Column(db.Integer, db.ForeignKey('grenade.id'), nullable=True, index=True)# why is this here?
        
    bookmarked_videos= db.relationship('UserVideo', backref='user', lazy=True,overlaps="bookmarked_videos,user")

    role = db.relationship('Role', backref='user_role', overlaps="user_role,users")

    def __init__(self, email, username, first_name, last_name,notes='',is_authenticated = None, password_hash=None, profile_pic=None, watched_videos=None, is_anonymous = None):
        self.email = email
        self.username = username
        self.password_hash = password_hash
        self.is_authenticated = is_authenticated
        self.profile_pic = profile_pic
        self.first_name = first_name
        self.last_name = last_name
        self.notes = notes
        self.watched_videos = watched_videos
        self.is_anonymous = is_anonymous

    def to_json(self):    
        return {"username": self.username, "email": self.email} 
    def is_authenticated(self):    
        return self.authenticated  
    def is_active(self):    
        return True  
    def is_anonymous(self):    
        return self.is_anonymous
    def get_id(self):    
        return str(self.id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_image(self):
        
        if self.profile_pic:
            image_file = url_for("static", filename='profile_pics/' + self.profile_pic)
        else:
            image_file = url_for("static", filename='profile_pics/chicken.png')    

        return image_file


    def assign_role(self, role):
        

            
        self.role = role
            
        if self.get_role_name() == "Free-Account" or self.get_role_name() == "Anonymous-Account":
            #print(f"Role assigned: {self.get_role_name()}, setting watched_videos to 0")
            self.watched_videos = 0
        else:
            self.watched_videos = 1
            
        
        db.session.commit()

    def has_role(self, role_name):
        return self.role.name == role_name # changed to this because a user will only be able to have one role
        #return any(r.name == role_name for r in (self.role or [])) # to return empty if there is no role yet, otherwise the app won't start


    def get_role_name(self):
        return self.role.name if self.role else None


def get_or_create_anonymous_user():
    base_username = 'anonymous'
    counter = 1

    while True:

        username = f'{base_username}{counter}'

        existing_user = User.query.filter_by(username=username).first()

        if existing_user is None:
            anonymous_user = User(
                email=f'{username}@example.com',
                username=username,
                password_hash='hashed_password',  
                is_authenticated=True,
                first_name='Anonymous',
                last_name='User',
                notes=f'Some notes for {username}',
                is_anonymous = True,
            )

            
            anonymous_user_role = Role.query.filter_by(name='Anonymous-Account').first()
            if anonymous_user_role:
                anonymous_user.role = anonymous_user_role

            else:
                anonymous_user_role = Role(name= 'Anonymous-Account')
                db.session.add(anonymous_user_role)
                db.session.flush()
               
                anonymous_user_permission = Permission(name = 'View 2 videos', description= 'Limited to 2 videos in total')
                db.session.add(anonymous_user_permission)
                db.session.flush()
                anonymous_user.role = anonymous_user_role



            db.session.add(anonymous_user)
            db.session.commit()
            anonymous_user.assign_role(anonymous_user_role)
            db.session.commit()
            return anonymous_user

        counter += 1
        username = f'{base_username}{counter}'





from app import login_manager

@login_manager.user_loader
def load_user(id):
    return db.session.get(User, int(id))
