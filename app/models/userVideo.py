from app.extensions import db


class UserVideo(db.Model):
    __tablename__ = 'user_video'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'), nullable=False)
    is_bookmarked = db.Column(db.Boolean, nullable=False, server_default='False')
    notes = db.Column(db.Text, server_default='')

    user_videos = db.relationship('User', backref='user_bookmarked_videos', lazy=True,overlaps="bookmarked_videos,user")
    video = db.relationship('Video', backref='user_videos', lazy=True)
   
    def __init__(self,user_id=None, video=None, is_bookmarked=False, notes=''):
        self.video = video
        self.is_bookmarked = is_bookmarked
        self.notes = notes
        self.user_id= user_id