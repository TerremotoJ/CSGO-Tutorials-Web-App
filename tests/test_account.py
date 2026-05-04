"""Fix 5: "Change email" and "Change password" save, with the right messages."""
from werkzeug.security import check_password_hash

from app.models import User


def get_user(app, username):
    with app.app_context():
        return User.query.filter_by(username=username).first()


def change_email(client, email):
    return client.post('/manage_account', data={'email-email': email, 'email-submit': 'Change Email'},
                       follow_redirects=True)


def change_password(client, old, new, confirm=None):
    return client.post('/manage_account', data={
        'password-old_password': old,
        'password-new_password': new,
        'password-confirm_password': new if confirm is None else confirm,
        'password-submit': 'Change Password',
    }, follow_redirects=True)


def test_change_email_saves(app, client_for):
    response = change_email(client_for('user'), 'new-address@example.com')
    assert 'Email changed successfully.' in response.get_data(as_text=True)
    assert get_user(app, 'user').email == 'new-address@example.com'


def test_change_email_rejects_invalid_and_taken(app, client_for):
    client = client_for('user')
    for email, message in [
        ('not-an-email', 'Invalid email address.'),
        ('admin@example.com', 'Email address already in use.'),
        ('user2@example.com', 'This is your current email address.'),
    ]:
        html = change_email(client, email).get_data(as_text=True)
        assert message in html, email
        assert 'Email changed successfully.' not in html
    assert get_user(app, 'user').email == 'user2@example.com'


def test_change_password_saves_a_werkzeug_hash(app, client_for):
    client = client_for('user')
    html = change_password(client, 'password', 'a-new-password').get_data(as_text=True)
    assert 'Password changed successfully.' in html

    user = get_user(app, 'user')
    assert user.password_hash.startswith(('scrypt:', 'pbkdf2:'))
    assert check_password_hash(user.password_hash, 'a-new-password')

    client.get('/logout')
    assert client.post('/login', data={'username': 'user', 'password': 'password'}).headers['Location'] == '/login'
    assert client.post('/login', data={'username': 'user', 'password': 'a-new-password'}).headers['Location'] == '/'


def test_change_password_needs_current_password_and_matching_confirm(app, client_for):
    client = client_for('user')
    before = get_user(app, 'user').password_hash

    html = change_password(client, 'wrong-password', 'a-new-password').get_data(as_text=True)
    assert 'Incorrect old password.' in html
    # Only the submitted form is validated, so the email form shows no error
    assert 'This field is required.' not in html

    html = change_password(client, 'password', 'a-new-password', confirm='different').get_data(as_text=True)
    assert 'Passwords must match' in html

    assert get_user(app, 'user').password_hash == before


def test_change_profile_picture_still_works(app, client_for):
    response = client_for('user').post('/manage_account', data={
        'pic-profile_pic': 'dog.png', 'pic-submit': 'Change Profile Picture'}, follow_redirects=True)
    assert 'Profile picture changed successfully.' in response.get_data(as_text=True)
    assert get_user(app, 'user').profile_pic == 'dog.png'
