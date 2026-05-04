from app.extensions import db


class PermissionRole(db.Model):
    __tablename__ = 'permission_role'

    id = db.Column(db.Integer, primary_key=True)
    permission_id = db.Column(db.Integer, db.ForeignKey('permission.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    created_at = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.current_timestamp())
    notes = db.Column(db.Text, server_default='')

    role = db.relationship('Role', back_populates='permissions_role')
    permissions = db.relationship('Permission', backref='permission_roles', overlaps='permission,permissions_roles')

    def __init__(self, permission, role, notes=''):
        self.permission = permission
        self.role = role
        self.notes = notes