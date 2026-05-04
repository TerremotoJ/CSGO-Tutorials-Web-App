"""Fix 1: no request can log in with an api_key parameter or an Authorization header."""
from app.extensions import login_manager
from app.models import User

SEEDED_KEYS = ['api_key1', 'api_key2', 'api_key3', 'api_key_for_anonymous1']


def test_no_request_loader_and_no_api_key_column():
    assert login_manager._request_callback is None
    assert 'api_key' not in User.__table__.columns


def test_api_key_values_do_not_log_in(client_for):
    client_for('anonymous')  # creates anonymous1, which used to get a seeded key
    for key in SEEDED_KEYS:
        client = client_for(None)
        assert client.get(f'/get_users_data?api_key={key}').status_code == 403
        assert client.get('/get_users_data', headers={'Authorization': f'Basic {key}'}).status_code == 403
        response = client.get(f'/manage_account?api_key={key}')
        assert response.status_code == 302 and '/login' in response.headers['Location']
