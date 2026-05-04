"""Rendered pages changed by the fixes: unique ids and the expected controls."""
from pathlib import Path

from tests.test_dashboard import assert_unique_ids, parse

STATIC = Path(__file__).resolve().parent.parent / 'app' / 'static'


def test_index_page(client_for):
    html = client_for(None).get('/').get_data(as_text=True)
    assert_unique_ids(html)
    assert 'id="confirmWatchModal"' in html and 'id="videoModal"' in html


def test_settings_page_forms_have_their_own_field_names(make_app):
    app = make_app(WTF_CSRF_ENABLED=True)
    client = app.test_client()
    html = client.get('/login').get_data(as_text=True)
    token = html.split('name="csrf_token" type="hidden" value="')[1].split('"')[0]
    client.post('/login', data={'username': 'user', 'password': 'password', 'csrf_token': token})

    html = client.get('/manage_account').get_data(as_text=True)
    assert_unique_ids(html)
    for name in ['email-email', 'email-submit', 'password-old_password', 'password-new_password',
                 'password-confirm_password', 'password-submit', 'pic-profile_pic', 'pic-submit',
                 'email-csrf_token', 'password-csrf_token', 'pic-csrf_token']:
        assert f'name="{name}"' in html, name


def test_dashboard_page_for_admin(client_for):
    html = client_for('admin').get('/admin_dashboard').get_data(as_text=True)
    assert_unique_ids(html)
    collector = parse(html)
    assert 'map' in collector.selects and 'grenade' in collector.selects
    for control in ['addVideoTitle', 'addVideoUrl', 'addVideoMap', 'addVideoGrenade', 'submitAddVideo',
                    'deleteVideoModal', 'deleteVideoForm', 'confirmDeleteBtn']:
        assert control in collector.ids, control


def test_index_script_uses_the_server_watch_endpoint():
    script = (STATIC / 'script.js').read_text()
    assert '/watch_video/' in script
    assert '/update_watch_count' not in script
    assert 'id="watchVideos"' not in script


def script_sources(html):
    import re
    return re.findall(r'<script[^>]*src="([^"]+)"', html)


def test_each_script_is_loaded_once_and_in_order(app, client_for):
    with app.app_context():
        from app.models import User
        user_id = User.query.filter_by(username='user').first().id
    admin = client_for('admin')
    pages = {
        '/': client_for(None),
        '/login': client_for(None),
        '/signup': client_for(None),
        '/manage_account': client_for('user'),
        '/admin_dashboard': admin,
        f'/delete/user/{user_id}': admin,
        '/delete/video/1': admin,
    }
    for url, client in pages.items():
        sources = script_sources(client.get(url).get_data(as_text=True))
        names = [s.rsplit('/', 1)[-1] for s in sources]
        assert len(names) == len(set(names)), (url, names)
        # jQuery, then Bootstrap, then the page's own files (they use $ when they load)
        assert names[:2] == ['jquery-3.6.4.min.js', 'bootstrap.bundle.min.js'], (url, names)
    assert 'script.js' in [s.rsplit('/', 1)[-1] for s in script_sources(pages['/'].get('/').get_data(as_text=True))]


def test_script_js_skips_index_setup_on_other_pages():
    script = (STATIC / 'script.js').read_text()
    assert "if (!document.getElementById('cardsContainer'))" in script


def test_base_assets_resolve_on_nested_urls(client_for):
    import re
    admin = client_for('admin')
    html = admin.get('/delete/video/1').get_data(as_text=True)
    links = re.findall(r'<link[^>]*href="(/static/[^"]+)"', html)
    assert '/static/videos.css' in links and any(l.endswith('.png') for l in links)
    for link in links:
        assert admin.get(link).status_code == 200, link
