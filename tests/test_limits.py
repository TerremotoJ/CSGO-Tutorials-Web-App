"""Fix 9: bookmarks and watch limits are checked on the server."""
import pytest

from app.models import User, UserVideo


def watched(app, username):
    with app.app_context():
        return User.query.filter_by(username=username).first().watched_videos


@pytest.mark.parametrize('username', [None, 'anonymous', 'free-account'])
def test_bookmarking_is_refused_for_other_roles(app, client_for, username):
    response = client_for(username).post('/update_bookmark_state', json={'video_id': 1, 'is_bookmarked': True})
    assert response.status_code == 403
    with app.app_context():
        assert UserVideo.query.count() == 0


@pytest.mark.parametrize('username', ['user', 'admin'])
def test_bookmarking_works_for_admin_and_user(app, client_for, username):
    client = client_for(username)
    assert client.get('/check_bookmark_permission').get_json() == {'can_bookmark': True}
    response = client.post('/update_bookmark_state', json={'video_id': 1, 'is_bookmarked': True})
    assert response.get_json() == {'is_bookmarked': True}
    videos = client.get('/get_videos?bookmark=true').get_json()['videos']
    assert [v['id'] for v in videos] == [1]
    client.post('/update_bookmark_state', json={'video_id': 1, 'is_bookmarked': False})
    assert client.get('/get_videos?bookmark=true').get_json()['videos'] == []


@pytest.mark.parametrize('username, limit', [('free-account', 3), ('anonymous', 2)])
def test_watch_limit_is_enforced_on_the_server(app, client_for, username, limit):
    client = client_for(username)
    owner = 'anonymous1' if username == 'anonymous' else username

    videos = client.get('/get_videos').get_json()['videos']
    assert videos and all(v['url'] is None for v in videos)

    for count in range(1, limit + 1):
        response = client.post(f'/watch_video/{count}')
        assert response.status_code == 200
        assert response.get_json()['url'].startswith('https://www.youtube.com/embed/')
        assert watched(app, owner) == count

    info = client.get('/check_watch_count').get_json()
    assert info == {'watched_videos': limit, 'can_watch': False, 'max_videos': limit}

    response = client.post(f'/watch_video/{limit + 1}')
    assert response.status_code == 403
    assert 'url' not in response.get_json()
    assert watched(app, owner) == limit


def test_old_unchecked_counter_endpoint_is_gone(client_for):
    assert client_for('free-account').post('/update_watch_count').status_code == 404


@pytest.mark.parametrize('username', ['user', 'admin'])
def test_full_roles_get_urls_without_a_limit(app, client_for, username):
    client = client_for(username)
    videos = client.get('/get_videos').get_json()['videos']
    assert all(v['url'] for v in videos)
    assert client.get('/check_watch_count').get_json()['can_watch'] is True
    before = watched(app, username)
    for video_id in range(1, 6):
        assert client.post(f'/watch_video/{video_id}').status_code == 200
    assert watched(app, username) == before


def test_watch_unknown_video_is_404(client_for):
    assert client_for('free-account').post('/watch_video/9999').status_code == 404
