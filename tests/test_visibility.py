"""Fix 6: only admins see videos that are not public."""
from app.extensions import db
from app.models import Video

HIDDEN = 4


def hide_video(app):
    with app.app_context():
        db.session.get(Video, HIDDEN).is_public = False
        db.session.commit()


def listed_ids(client):
    return {v['id'] for v in client.get('/get_videos').get_json()['videos']}


def test_list_hides_private_videos_from_non_admins(app, client_for):
    hide_video(app)
    for username in [None, 'anonymous', 'free-account', 'user']:
        ids = listed_ids(client_for(username))
        assert HIDDEN not in ids and len(ids) == 20, username
    assert HIDDEN in listed_ids(client_for('admin'))


def test_per_video_endpoints_hide_private_videos(app, client_for):
    hide_video(app)
    for username in ['anonymous', 'free-account', 'user']:
        assert client_for(username).post(f'/watch_video/{HIDDEN}').status_code == 404, username
    response = client_for('user').post('/update_bookmark_state', json={'video_id': HIDDEN, 'is_bookmarked': True})
    assert response.status_code == 404
    assert client_for('admin').post(f'/watch_video/{HIDDEN}').status_code == 200


def test_admin_can_make_a_video_private_from_the_dashboard(app, client_for):
    with app.app_context():
        video = db.session.get(Video, HIDDEN)
        form = {'title': video.title, 'url': video.url, 'description': video.description, 'notes': video.notes}
    assert client_for('admin').post(f'/edit/video/{HIDDEN}', data=form).status_code == 200
    assert HIDDEN not in listed_ids(client_for('user'))
