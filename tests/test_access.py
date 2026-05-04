"""Admin routes are refused (403) for every role except Admin; logged-in routes need a login."""
import pytest

ADMIN_GETS = [
    '/admin_dashboard',
    '/get_users_data',
    '/get_videos_data',
    '/get_user_data/1',
    '/get_video_data/1',
    '/delete/user/1',
    '/delete/video/1',
]

ADMIN_POSTS = [
    '/add_video',
    '/edit/user/1',
    '/delete/user/1',
    '/edit/video/1',
    '/delete/video/1',
]


@pytest.mark.parametrize('username', [None, 'anonymous', 'free-account', 'user'])
def test_non_admins_get_403_on_admin_routes(client_for, username):
    client = client_for(username)
    for url in ADMIN_GETS:
        assert client.get(url).status_code == 403, url
    for url in ADMIN_POSTS:
        assert client.post(url, data={'title': 'x'}).status_code == 403, url


def test_admin_gets_200_on_admin_routes(client_for):
    client = client_for('admin')
    for url in ADMIN_GETS:
        assert client.get(url).status_code == 200, url


def test_logged_out_is_sent_to_login(client_for):
    client = client_for(None)
    for url in ['/manage_account', '/check_bookmark_permission']:
        response = client.get(url)
        assert response.status_code == 302 and '/login' in response.headers['Location'], url
    assert client.post('/watch_video/1').status_code == 302


def test_logged_in_user_visiting_login_stays_logged_in(client_for):
    client = client_for('user')
    response = client.get('/login')
    assert response.status_code == 302 and response.headers['Location'] == '/'
    assert client.get('/manage_account').status_code == 200


def test_anonymous_account_is_logged_out_on_login_page(client_for):
    client = client_for('anonymous')
    assert client.get('/check_watch_count').status_code == 200
    response = client.get('/login')
    assert response.status_code == 200 and 'name="username"' in response.get_data(as_text=True)
    assert client.get('/check_watch_count').status_code == 401
    response = client.post('/login', data={'username': 'admin', 'password': 'password'})
    assert response.headers['Location'] == '/'
    assert client.get('/admin_dashboard').status_code == 200
