from app.extensions import db

class Permission(db.Model):
    __tablename__ = 'permission'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    description = db.Column(db.String(200), nullable=False, server_default='')
    notes = db.Column(db.Text, server_default='')



    permissions_roles = db.relationship('PermissionRole', backref='permission', overlaps='permission,permissions_roles')


    def __init__(self, name, description, notes=''):
        self.name = name
        self.description = description
        self.notes = notes

    def __repr__(self):
        return f'<Permission {self.name}>'