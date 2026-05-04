# CS-TWOTS: CS:GO Grenade Tutorial Website

A Flask web app for watching CS:GO grenade lineup videos (embedded YouTube clips), filtered by map and grenade type. It was a group project for a university course. Data is kept in SQLite through SQLAlchemy.

## Features

- **Video list.** Filter videos by map and by grenade type (smoke, flash, molotov, HE). The seed data has 21 videos for Mirage and Inferno; the other map buttons (Ancient, Vertigo, Anubis, Overpass, Nuke) show nothing until an admin adds videos for them from the dashboard.
- **Four roles.** `Admin`, `User`, `Free-Account` and `Anonymous-Account`. Each user has one role.
- **Anonymous visitors.** A visitor who is not logged in gets a new `anonymousN` account in the database and is logged in to it, so their views can be counted.
- **Watch limits.** `Anonymous-Account` users can watch 2 videos and `Free-Account` users 3, in total: the count never resets. `Admin` and `User` have no limit. The server enforces the limit: for the limited roles the video list carries no video URLs, and the page asks `/watch_video/<id>` for one URL at a time. That endpoint counts the view and refuses once the limit is reached.
- **Bookmarks.** `Admin` and `User` accounts can bookmark videos and show only their bookmarks. Other roles get a 403 from the bookmark endpoint.
- **Public and hidden videos.** Each video has an "Is Public" flag. Videos that are not public are listed and playable only for admins.
- **Sign up and log in.** New accounts get the `Free-Account` role. The sign-up form checks whether a username is taken as you type.
- **Account page.** Change your email (it must be valid and not used by another account), change your password (the current password is required), choose a profile picture from a fixed set, or delete the account.
- **Admin dashboard** (`/admin_dashboard`). Lists users and videos. An admin can change a user's username, role and notes, delete a user, add a video (title, YouTube embed URL, map and grenade from lists, description, notes, public flag), edit a video's title, URL, description, notes and public flag, and delete a video. Deleting a user or a video also deletes the bookmarks that point to it. The page talks to the server with jQuery AJAX calls.

## Tech stack

- Python, Flask 3, Flask-SQLAlchemy (SQLAlchemy 2), Flask-Login, Flask-WTF and WTForms
- SQLite by default (`instance/app.db`); the `DATABASE_URL` environment variable overrides it
- Jinja templates, Bootstrap 5, jQuery and plain JavaScript (`fetch`)
- Role checks are done by a small `role_required` decorator in `app/models/user.py`.
- Flask-Migrate is registered, but there are no migration files; missing tables are created with `db.create_all()` on start. A table that already exists is not changed, so after a model change, delete `instance/app.db` to rebuild it.
- pytest and the Flask test client for the tests

## Project structure

```
config.py            settings (SECRET_KEY, database URL)
app/__init__.py      app factory: extensions, database setup, blueprint
app/routes.py        all routes, including the admin and AJAX endpoints
app/db_setup.py      creates missing tables; loads seed videos, maps, roles and accounts into an empty database
app/models/          SQLAlchemy models (User, Role, Permission, Video, GameMap, Grenade, UserVideo)
app/forms.py         WTForms forms
app/templates/       Jinja templates
app/static/          JavaScript, CSS and images
tests/               pytest tests (each test uses its own temporary SQLite file)
```

## How to run

Use Python 3.12, 3.13 or 3.14. The tests were run on Python 3.14. For 3.12 and 3.13, pip finds a prebuilt package for every pinned version (checked on macOS, Windows and Linux), but the tests have not been run on those versions.

### 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate      # macOS / Linux
.venv\Scripts\activate         # Windows
```

### 2. Install the dependencies

```bash
pip install -r requirements.txt
```

### 3. Set the secret key

The app needs a `SECRET_KEY` environment variable and will not start without one. Generate a random value:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Set it in your shell: `export SECRET_KEY=<value>` on macOS/Linux, `set SECRET_KEY=<value>` in the Windows command prompt.

### 4. Start the server

```bash
flask run
```

The site is then at http://127.0.0.1:5000. On the first start the app creates `instance/app.db` (and the `instance` folder), the tables, and the seed videos and accounts. Later starts keep your data and do not load the seed data again. To start over, stop the server and delete `instance/app.db`.

### 5. Run the tests

```bash
pip install -r requirements-dev.txt
pytest
```

The tests set their own `SECRET_KEY`, use a temporary SQLite file per test and never open `instance/app.db`.

## Local test accounts

The seed data in `app/db_setup.py` creates these accounts on the first start. They exist only in your local database and are meant for local development.

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `password` |
| User | `user` | `password` |
| Free-Account | `free-account` | `password` |

## Security

What the code does:

- Passwords are stored as Werkzeug hashes (`generate_password_hash` and `check_password_hash`).
- Flask-WTF CSRF protection is on for the whole app, and the forms and AJAX requests send the token. A request without a valid token gets a 400 error page.
- Admin routes check the role on the server with `role_required('Admin')` and return 403 to everyone else.
- The bookmark endpoint returns 403 to roles other than `Admin` and `User`. The watch limit is checked on the server before a video URL is sent, and the check and the count happen in one database update.
- Videos that are not public are left out of the list and refused by the per-video endpoints for everyone except admins.
- Logging in needs a username and password; there is no API-key login.
- `SECRET_KEY` is read from the environment; there is no default value in the code.
- Jinja escapes template output, and the JavaScript passes data through `escapeHtml` before putting it into HTML strings.

What it does not do:

- Anonymous accounts are tied to the browser's cookies. A visitor who clears cookies gets a new `anonymousN` account and a new watch count.
- There is no rate limiting on log-in or sign-up, and email addresses are not verified.
