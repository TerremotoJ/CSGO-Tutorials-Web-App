
import re
from app.extensions import db


class Video(db.Model):
    __tablename__ = 'video'

    id = db.Column(db.Integer, primary_key=True)
    grenade_id = db.Column(db.Integer, db.ForeignKey('grenade.id'), nullable=False, index=True)
    game_map_id = db.Column(db.Integer, db.ForeignKey('game_map.id'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False, unique=True, index=True)
    url = db.Column(db.String(50), nullable=False, unique=True, index=True)
    description = db.Column(db.String(60), nullable=False) 
    is_public = db.Column(db.Boolean, nullable=False, server_default='False')
    notes = db.Column(db.Text, server_default='')  
    thumbnail_url = db.Column(db.String(255))
    bookmark_count = db.Column(db.Integer, nullable=False, server_default='0')

    grenade = db.relationship('Grenade', backref='videos')
    game_map = db.relationship('GameMap', backref='videos')
    
    def __init__(self, title, url, description, is_public,thumbnail_url, notes='' ):
        self.title = title
        self.url = url
        self.description = description
        self.is_public = is_public
        self.notes = notes
        self.bookmark_count = 0 # initializes bookmark_count= 0 when creating a new video
        self.thumbnail_url = thumbnail_url


def get_youtube_video_id(embed_url):
    pattern = re.compile(r"/embed/([a-zA-Z0-9_-]+)")
    match = pattern.search(embed_url)
    return match.group(1) if match else None


def get_youtube_thumbnail_url(embed_url):
    video_id = get_youtube_video_id(embed_url)
    if video_id:
        return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
    else:
        return None
    

