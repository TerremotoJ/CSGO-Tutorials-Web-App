"""Fixes 2 and 3: adding a video from the dashboard, and the per-row Delete buttons."""
from html.parser import HTMLParser
from pathlib import Path

from app.extensions import db
from app.models import GameMap, Grenade, Video

STATIC = Path(__file__).resolve().parent.parent / 'app' / 'static'


class _Collector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.selects = {}
        self._select = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'select':
            self._select = attrs.get('name')
            self.selects[self._select] = []
        elif tag == 'option' and self._select:
            self.selects[self._select].append(attrs.get('value'))

    def handle_endtag(self, tag):
        if tag == 'select':
            self._select = None


def parse(html):
    collector = _Collector()
    collector.feed(html)
    return collector


def assert_unique_ids(html):
    ids = parse(html).ids
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    assert not duplicates, duplicates


def ids_of(app, model):
    with app.app_context():
        return {str(row.id) for row in model.query.all()}


def test_dashboard_has_map_and_grenade_selects_and_unique_ids(app, client_for):
    html = client_for('admin').get('/admin_dashboard').get_data(as_text=True)
    assert_unique_ids(html)
    selects = parse(html).selects
    assert set(selects['map']) == {''} | ids_of(app, GameMap)
    assert set(selects['grenade']) == {''} | ids_of(app, Grenade)
    assert len(selects['map']) == 1 + 7
    assert 'id="addVideoForm"' in html


def video_form(app, **overrides):
    with app.app_context():
        data = {
            'title': 'Ancient Mid Smoke',
            'url': 'https://www.youtube.com/embed/abcdefghijk',
            'description': 'd',
            'notes': 'n',
            'is_public': 'on',
            'map': str(GameMap.query.filter_by(name='ancient').first().id),
            'grenade': str(Grenade.query.filter_by(name='smoke').first().id),
        }
    data.update(overrides)
    return {k: v for k, v in data.items() if v is not None}


def test_add_video_saves_map_and_grenade(app, client_for):
    response = client_for('admin').post('/add_video', data=video_form(app))
    assert response.status_code == 200
    with app.app_context():
        video = db.session.get(Video, response.get_json()['videoId'])
        assert (video.game_map.name, video.grenade.name) == ('ancient', 'smoke')
        assert video.thumbnail_url == 'https://img.youtube.com/vi/abcdefghijk/maxresdefault.jpg'


def test_add_video_bad_input_is_400(app, client_for):
    client = client_for('admin')
    with app.app_context():
        existing = Video.query.first()
        existing_title, existing_url = existing.title, existing.url
        before = Video.query.count()
    bad_inputs = [
        {'map': None},
        {'map': '9999'},
        {'map': 'mirage'},
        {'grenade': None},
        {'grenade': '9999'},
        {'title': ''},
        {'url': 'https://example.com/video'},
        {'url': None},
        {'title': existing_title},
        {'url': existing_url},
    ]
    for overrides in bad_inputs:
        response = client.post('/add_video', data=video_form(app, **overrides))
        assert response.status_code == 400, overrides
        assert response.get_json()['error'], overrides
    with app.app_context():
        assert Video.query.count() == before


def test_delete_buttons_do_not_share_an_id():
    script = (STATIC / 'adminDashboard.js').read_text()
    assert '"DeleteButton"' not in script and '#DeleteButton' not in script
    # The modal reads the video id from the button that opened it
    assert 'event.relatedTarget' in script
    assert 'deleteVideoButton' in script


def test_delete_video_route_deletes_that_video(app, client_for):
    with app.app_context():
        ids = [v.id for v in Video.query.order_by(Video.id).all()]
    target = ids[5]
    response = client_for('admin').post(f'/delete/video/{target}')
    assert response.status_code == 302
    with app.app_context():
        remaining = [v.id for v in Video.query.order_by(Video.id).all()]
    assert remaining == [i for i in ids if i != target]


def test_edit_user_has_no_password_reset(app, client_for):
    from app.models import User
    with app.app_context():
        user = User.query.filter_by(username='user').first()
        user_id, before = user.id, user.password_hash
    response = client_for('admin').post(f'/edit/user/{user_id}', data={'reset_password': '1', 'notes': 'new notes'})
    assert response.status_code == 200
    messages = ' '.join(response.get_json()['flash_messages'])
    assert 'password' not in messages.lower() and 'email' not in messages.lower()
    with app.app_context():
        user = db.session.get(User, user_id)
        assert user.password_hash == before and user.notes == 'new notes'


def edit_form(app, video_id, **overrides):
    with app.app_context():
        video = db.session.get(Video, video_id)
        data = {'title': video.title, 'url': video.url, 'description': video.description,
                'notes': video.notes, 'is_public': 'on'}
    data.update(overrides)
    return data


def test_edit_video_duplicate_or_bad_values_are_400(app, client_for):
    client = client_for('admin')
    with app.app_context():
        other = db.session.get(Video, 2)
        other_title, other_url = other.title, other.url
        before = (db.session.get(Video, 1).title, db.session.get(Video, 1).url)
    for overrides, message in [
        ({'title': other_title}, 'A video with this title already exists.'),
        ({'url': other_url}, 'A video with this URL already exists.'),
        ({'title': ''}, 'Enter a title.'),
        ({'url': 'https://example.com/v'}, 'Enter a YouTube embed URL'),
    ]:
        response = client.post('/edit/video/1', data=edit_form(app, 1, **overrides))
        assert response.status_code == 400, overrides
        assert message in response.get_json()['error'], overrides
    with app.app_context():
        video = db.session.get(Video, 1)
        assert (video.title, video.url) == before


def test_edit_video_saves_and_keeps_its_own_title(app, client_for):
    client = client_for('admin')
    response = client.post('/edit/video/1', data=edit_form(app, 1, notes='changed'))
    assert response.status_code == 200
    response = client.post('/edit/video/1', data=edit_form(app, 1, url='https://www.youtube.com/embed/zzzzzzzzzzz'))
    assert response.status_code == 200
    with app.app_context():
        video = db.session.get(Video, 1)
        assert video.notes == 'changed'
        assert video.thumbnail_url == 'https://img.youtube.com/vi/zzzzzzzzzzz/maxresdefault.jpg'


def test_edit_video_errors_are_shown_in_the_modal():
    script = (STATIC / 'adminDashboard.js').read_text()
    assert '#editVideoModal' in script and 'The video could not be saved.' in script
