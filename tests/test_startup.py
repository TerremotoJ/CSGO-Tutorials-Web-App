"""Fixes 7, 10, 11 and 8: start-up keeps data, seed values, requirements file, CSRF error page."""
from pathlib import Path

from app.extensions import db
from app.models import GameMap, User, Video

ROOT = Path(__file__).resolve().parent.parent


def counts(app):
    with app.app_context():
        return User.query.count(), Video.query.count(), GameMap.query.count()


def test_restart_keeps_data_and_does_not_reseed(make_app, tmp_path):
    db_path = tmp_path / 'persist.db'
    first = make_app(db_path)
    assert counts(first) == (3, 21, 7)

    response = first.test_client().post('/signup', data={
        'username': 'newplayer', 'email': 'newplayer@example.com', 'first_name': 'New',
        'last_name': 'Player', 'password': 'pw-12345', 'confirmPassword': 'pw-12345'})
    assert response.status_code == 302

    second = make_app(db_path)
    assert counts(second) == (4, 21, 7)
    with second.app_context():
        assert User.query.filter_by(username='newplayer').first() is not None


def test_database_folder_is_created(make_app, tmp_path):
    db_path = tmp_path / 'missing-folder' / 'app.db'
    assert not db_path.parent.exists()
    app = make_app(db_path)
    assert db_path.exists()
    assert app.test_client().get('/login').status_code == 200


def test_seed_emails_use_example_com(app):
    with app.app_context():
        emails = [u.email for u in User.query.all()]
    assert emails and all(e.endswith('@example.com') for e in emails)
    assert 'admin@example.com' in emails


def test_requirements_file():
    raw = (ROOT / 'requirements.txt').read_bytes()
    assert not raw.startswith(b'\xef\xbb\xbf')
    text = raw.decode('utf-8').lower()
    assert 'psycopg2' not in text
    assert 'sqlalchemy==2.0.23' not in text


def test_no_per_day_wording():
    for path in ['app/static/script.js', 'app/db_setup.py', 'app/models/user.py']:
        text = (ROOT / path).read_text()
        assert 'per day' not in text and 'per week' not in text and 'tomorrow' not in text, path


def test_csrf_failure_shows_a_400_page(make_app):
    client = make_app(WTF_CSRF_ENABLED=True).test_client()
    response = client.post('/login', data={'username': 'admin', 'password': 'password'})
    assert response.status_code == 400
    assert 'security token is missing or has expired' in response.get_data(as_text=True)

    client.get('/')  # anonymous account, logged in
    assert client.post('/watch_video/1').status_code == 400
