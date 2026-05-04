from app.extensions import db

from app.models.permission import Permission
from app.models.permissionRole import PermissionRole

class Role(db.Model):
    __tablename__ = 'role'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.String(200), nullable=False, server_default='')
    notes = db.Column(db.Text, server_default='')

    users = db.relationship('User', backref='user_role',overlaps="user_role,users")
    permissions_role = db.relationship('PermissionRole',back_populates='role')
    
    def __init__(self, name, description=None, notes=''):
        self.name = name
        self.description = description
        self.notes = notes

    def __repr__(self):
        return f'<Role {self.name}>'        
    

