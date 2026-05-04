from app.extensions import db


class GameMap(db.Model):
    __tablename__ = 'game_map'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.String(200), nullable=False, server_default='')
    notes = db.Column(db.Text, server_default='')

        

    def __init__(self, name, description, notes=''):
        self.name = name
        self.description = description
        self.notes = notes

    def __repr__(self):
        return f"Map(id={self.id}, name={self.name}"