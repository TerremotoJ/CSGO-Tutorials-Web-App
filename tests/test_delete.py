"""Fix 4: deleting a video, a user or one's own account also deletes their bookmark rows."""
from app.extensions import db
from app.models import User, UserVideo, Video


def bookmark(client, video_id):
    response = client.post('/update_bookmark_state', json={'video_id': video_id, 'is_bookmarked': True})
    assert response.status_code == 200


def user_id(app, username):
    with app.app_context():
        return User.query.filter_by(username=username).first().id


def test_delete_bookmarked_video_removes_only_its_bookmarks(app, client_for):
    user = client_for('user')
    # UserVideo 1 points to video 5 and UserVideo 2 to video 1, so filtering
    # UserVideo by id=video.id (the old bug) would delete the wrong row
    bookmark(user, 5)
    bookmark(user, 1)

    response = client_for('admin').post('/delete/video/1')
    assert response.status_code == 302

    with app.app_context():
        assert db.session.get(Video, 1) is None
        rows = [(uv.id, uv.video_id) for uv in UserVideo.query.all()]
    assert rows == [(1, 5)]


def test_admin_deletes_user_with_bookmarks(app, client_for):
    bookmark(client_for('user'), 3)
    target = user_id(app, 'user')

    response = client_for('admin').post(f'/delete/user/{target}')
    assert response.status_code == 302

    with app.app_context():
        assert db.session.get(User, target) is None
        assert UserVideo.query.filter_by(user_id=target).count() == 0
        assert db.session.get(Video, 3) is not None


def test_delete_unknown_user_is_404(client_for):
    admin = client_for('admin')
    assert admin.get('/delete/user/9999').status_code == 404
    assert admin.post('/delete/user/9999').status_code == 404


def test_delete_own_account_with_bookmarks(app, client_for):
    client = client_for('user')
    bookmark(client, 2)
    target = user_id(app, 'user')

    response = client.post('/delete_account')
    assert response.status_code == 302

    with app.app_context():
        assert db.session.get(User, target) is None
        assert UserVideo.query.count() == 0
    assert client.get('/manage_account').status_code == 302
