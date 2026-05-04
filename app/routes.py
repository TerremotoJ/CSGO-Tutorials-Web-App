import os
from flask import Blueprint, Flask, current_app, flash, g, get_flashed_messages, render_template, request, session, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from app.forms import ChangeEmailForm, ChangePasswordForm, ChangeProfilePicForm, LoginForm, RegistrationForm
from app.models import User, Role, PermissionRole, Permission, UserVideo, Video, Grenade, GameMap
from flask_login import current_user, login_required, login_user, logout_user
from app import db

import sqlalchemy as sa

from app.models.user import WATCH_LIMITS, get_or_create_anonymous_user, role_required
from app.models.video import get_youtube_thumbnail_url, get_youtube_video_id

main = Blueprint('main', __name__)

# Roles that can bookmark videos and get video URLs without a watch limit
FULL_ACCESS_ROLES = ('Admin', 'User')


def current_role_name():
    return current_user.get_role_name() if current_user.is_authenticated else None


def visible_videos():
    """Video query limited to public videos for everyone except admins."""
    if current_role_name() == 'Admin':
        return Video.query
    return Video.query.filter(Video.is_public == True)


def video_form_errors(title, embed_url, video_id=None):
    """Checks a video's title and URL; video_id is the video being edited, which may keep its own values."""
    others = Video.query.filter(Video.id != video_id) if video_id else Video.query
    errors = []
    if not title:
        errors.append('Enter a title.')
    elif others.filter(Video.title == title).first():
        errors.append('A video with this title already exists.')
    if not get_youtube_video_id(embed_url):
        errors.append('Enter a YouTube embed URL (https://www.youtube.com/embed/...).')
    elif others.filter(Video.url == embed_url).first():
        errors.append('A video with this URL already exists.')
    return errors


def delete_user_videos(**filters):
    """Deletes the UserVideo (bookmark) rows matching the filters; they block deleting a user or video."""
    for user_video in UserVideo.query.filter_by(**filters).all():
        db.session.delete(user_video)
    db.session.flush()

@main.before_request
def before_request():
    g.user = current_user


@main.route('/check_username_availability', methods=['POST'])
def check_username_availability():
    username = request.form.get('username')
    user = User.query.filter_by(username=username).first()
    return jsonify({'available': user is None})


@main.route('/check_bookmark_permission', methods=['GET'])
@login_required
def check_bookmark_permission():
    return jsonify({'can_bookmark': current_role_name() in FULL_ACCESS_ROLES})


@main.route('/get_videos', methods=['GET'])
def get_videos():
    try:
        map_filter = request.args.get('map')
        grenade_filter = request.args.get('grenade')
        bookmark_filter = request.args.get('bookmark')
        query = visible_videos().join(Video.game_map).join(Video.grenade)

        if map_filter and map_filter != 'all':
            query = query.filter(GameMap.name == map_filter)
        if grenade_filter:
            query = query.filter(Grenade.name == grenade_filter)
        if bookmark_filter == 'true' and current_user.is_authenticated:
            query = query.join(UserVideo).filter(sa.and_(UserVideo.user_id == current_user.id, UserVideo.is_bookmarked == True))

        videos = query.all()

        # Limited roles get no URLs here; /watch_video hands them out one at a time
        show_urls = current_role_name() in FULL_ACCESS_ROLES
        videos_list = [
            {
                'id': video.id,
                'title': video.title,
                'url': video.url if show_urls else None,
                'thumbnail_url': video.thumbnail_url,
                'game_map': video.game_map.name,
                'grenade': video.grenade.name,
                'is_bookmarked': is_video_bookmarked(video.id)
            }
            for video in videos
        ]




        response_data = {'videos': videos_list, 'userRole': current_role_name()}
        return jsonify(response_data)

    except Exception as e:
        print(f"Error in get_videos: {e}")
        return jsonify({'error': 'An error occurred'}), 500

def is_video_bookmarked(video_id):
    if not current_user.is_authenticated:
        return False
    user_video = UserVideo.query.filter_by(user_id=current_user.id, video_id=video_id).first()
    return user_video.is_bookmarked if user_video else False




@main.route('/check_watch_count', methods=['GET'])
def check_watch_count():
    if not current_user.is_authenticated:
        return jsonify({'error': 'User is not authenticated.'}), 401

    max_videos = WATCH_LIMITS.get(current_role_name())
    watched_videos = current_user.watched_videos or 0
    can_watch = max_videos is None or watched_videos < max_videos

    return jsonify({'watched_videos': watched_videos, 'can_watch': can_watch, 'max_videos': max_videos})


@main.route('/watch_video/<int:video_id>', methods=['POST'])
@login_required
def watch_video(video_id):
    """Returns a video's URL. For roles with a watch limit it counts the view and refuses once the limit is reached."""
    video = visible_videos().filter(Video.id == video_id).first()
    if video is None:
        return jsonify({'error': 'Video not found.'}), 404

    role_name = current_role_name()
    if role_name in FULL_ACCESS_ROLES:
        return jsonify({'url': video.url})

    max_videos = WATCH_LIMITS.get(role_name)
    if max_videos is None:
        return jsonify({'error': 'Your account cannot watch videos.'}), 403

    # Check and increment in one UPDATE so parallel requests cannot pass the limit together
    watched = sa.func.coalesce(User.watched_videos, 0)
    counted = User.query.filter(User.id == current_user.id, watched < max_videos).update(
        {User.watched_videos: watched + 1}, synchronize_session=False)
    db.session.commit()

    if not counted:
        return jsonify({
            'error': f'You have reached the limit of {max_videos} videos for this account.',
            'watched_videos': current_user.watched_videos,
            'max_videos': max_videos,
        }), 403

    return jsonify({'url': video.url, 'watched_videos': current_user.watched_videos, 'max_videos': max_videos})


@main.route('/', methods=['GET', 'POST'])
def index():
    profile_pic = None
    videos = None
    bookmarked_video_ids = []
    
    if current_user.is_authenticated :

        videos = visible_videos().all()
        bookmarked_video_ids = [video.id for video in current_user.bookmarked_videos]
        if current_user.profile_pic:
            profile_pic = current_user.profile_pic
        else:
            current_user.profile_pic = "chicken.png"
            db.session.commit()
            profile_pic = "chicken.png"
    elif current_user.is_anonymous:
        anonymous_user = get_or_create_anonymous_user()
        login_user(anonymous_user, remember=True)
        videos = visible_videos().all()


    return render_template('index.html', videos=videos, profile_pic=profile_pic, bookmarked_video_ids=bookmarked_video_ids)


@main.route('/update_bookmark_state', methods=['POST'])
@role_required(*FULL_ACCESS_ROLES)
def update_bookmark_state():
    data = request.get_json(silent=True) or {}
    video_id = data.get('video_id')
    is_bookmarked = bool(data.get('is_bookmarked'))

    video = visible_videos().filter(Video.id == video_id).first()
    if video is None:
        return jsonify({'error': 'Video not found.'}), 404

    user_video = UserVideo.query.filter_by(user_id=current_user.id, video_id=video.id).first()

    if not user_video:
        user_video = UserVideo(user_id=current_user.id, video=video, is_bookmarked=is_bookmarked)
        db.session.add(user_video)
    else:
        user_video.is_bookmarked = is_bookmarked

    db.session.commit()

    return jsonify({'is_bookmarked': is_bookmarked})


@main.route('/login', methods=['GET', 'POST'])
def login():
    
    # A visitor who is not logged in is on a temporary Anonymous-Account; log it out so they can log in
    if current_role_name() == 'Anonymous-Account':
        logout_user()
    elif current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm(request.form)

    if request.method == 'POST' and form.validate():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
           
            flash('Invalid username or password')
            return redirect(url_for('main.login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('main.index')) 
    return render_template("login.html", form=form)


@main.route('/logout')
def logout():
    logout_user()
    session.pop('_flashes', None)
    return redirect(url_for('main.index'))

@main.route('/signup', methods=['GET', 'POST'])
def signup():

    if current_user.is_authenticated and not current_user.get_role_name() == "Anonymous-Account":
        return redirect(url_for('main.index'))
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User(username=form.username.data,first_name=form.first_name.data,last_name=form.last_name.data, email=form.email.data, is_authenticated=False)
        role = Role.query.filter_by(name="Free-Account").first()
        user.assign_role(role)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('main.login'))

    return render_template("signup.html", form = form)


@main.route('/manage_account', methods=['GET', 'POST'])
@login_required
def manage_account():
    profile_pics = []
    
    for image in os.listdir(os.path.join(current_app.root_path, 'static', 'profile_pics')):
        if image.endswith(('jpg', 'jpeg', 'png')):
            profile_pics.append({'filename': image, 'path': url_for('static', filename=f'profile_pics/{image}')})

    
    # The prefixes give each form its own field names, so only the submitted form is validated
    change_email_form = ChangeEmailForm(prefix='email')
    change_password_form = ChangePasswordForm(prefix='password')
    change_profile_pic_form = ChangeProfilePicForm(prefix='pic')

    if change_email_form.submit.data and change_email_form.validate_on_submit():
        current_user.email = change_email_form.email.data.strip()
        db.session.commit()
        flash('Email changed successfully.', 'success')
        return redirect(url_for('main.manage_account'))

    elif change_password_form.submit.data and change_password_form.validate_on_submit():
        current_user.set_password(change_password_form.new_password.data)
        db.session.commit()
        flash('Password changed successfully.', 'success')
        return redirect(url_for('main.manage_account'))

    elif change_profile_pic_form.submit.data and change_profile_pic_form.validate_on_submit():
        current_user.profile_pic = change_profile_pic_form.profile_pic.data
        db.session.commit()
        flash('Profile picture changed successfully.', 'success')
        return redirect(url_for('main.manage_account'))

    return render_template('settings.html', 
                           change_email_form=change_email_form,
                           change_password_form=change_password_form,
                           change_profile_pic_form=change_profile_pic_form,profile_pics=profile_pics)

@main.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    
    
    user = User.query.filter_by(id=current_user.id).first()
    delete_user_videos(user_id=user.id)
    db.session.delete(user)
    db.session.commit()
    logout_user()
    flash('Account deleted successfully.', 'success')
    return redirect(url_for('main.index'))



@main.route('/admin_dashboard', methods=['GET'])
@role_required('Admin')
def admin_dashboard():
    
    users = User.query.all()
    game_maps = GameMap.query.order_by(GameMap.name).all()
    grenades = Grenade.query.order_by(Grenade.name).all()

    return render_template('admin_dashboard.html', users=users, game_maps=game_maps, grenades=grenades)

@main.route('/edit/user/<int:user_id>', methods=['POST'])
@role_required('Admin')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    roles = Role.query.all()

    if request.method == 'POST':

        role_id = request.form.get('role')
        username =  request.form.get('username')
        notes =  request.form.get('notes')

        role = Role.query.filter_by(id=role_id).first()
        
        response_data = {'success': False}

        if role and not user.has_role(role.name):
            user.assign_role(role)
            flash('User role was successfully updated!', 'success')
            response_data['success'] = True

        if notes and not user.notes == notes:
            user.notes = notes
            flash('User notes were successfully updated!', 'success')
            response_data['success'] = True

        if username and not user.username == username:
            if User.query.filter_by(username=username).first():
                pass
                flash('Username already in use! Use another one please', 'error')
            else:
                user.username = username
                flash('Username was successfully updated!', 'success')
                response_data['success'] = True

        db.session.flush()
        db.session.commit()
        response_data['userId'] = user.id
        
        response_data = {
            'success': True,
            'flash_messages': get_flashed_messages(),
            'userId': user.id,
        }

        return jsonify(response_data)
    

@main.route('/delete/user/<int:user_id>', methods=['GET', 'POST'])
@role_required('Admin')
def delete_user(user_id):
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
            delete_user_videos(user_id=user.id)
            db.session.delete(user)
            db.session.commit()
            flash('User deleted successfully.', 'success')
            return redirect(url_for('main.admin_dashboard'))

    return render_template('delete_user.html', user=user)



@main.route('/get_users_data', methods=['GET'])
@role_required('Admin')
def get_users_data():
    session.pop('_flashes', None)

    users = User.query.all()

    users_list = [
        {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.get_role_name(),
            'editUrl': url_for('main.edit_user', user_id=user.id),
            'deleteUrl': url_for('main.delete_user', user_id=user.id),
        }
        for user in users
    ]

    return jsonify({'users': users_list})


@main.route('/get_video_data/<int:user_id>', methods=['GET'])
@role_required('Admin')
def get_video_data(user_id):
    try:
        session.pop('_flashes', None)

        video = Video.query.get_or_404(user_id)
        
        video_data = {
            'id': video.id,
            'grenade_id': video.grenade_id,
            'game_map_id': video.game_map_id,
            'title': video.title,
            'url': video.url,
            'description': video.description,
            'notes': video.notes,
            'is_public': video.is_public,
            'thumbnail_url': video.thumbnail_url,
            'url': video.url,
            'bookmark_count': video.bookmark_count,
        }

        return jsonify(video_data)

    except Exception as e:
        print(f"Error in get_user_data: {e}")
        return jsonify({'error': 'An error occurred'}), 500
    


@main.route('/get_videos_data', methods=['GET'])
@role_required('Admin')
def get_videos_data():
    videos = Video.query.all()

    videos_list = [
        {
            'id': video.id,
            'title': video.title,
            'url': video.url,
            'thumbnail_url': video.thumbnail_url,
            'game_map': video.game_map.name,
            'grenade': video.grenade.name,
            'deleteUrl': url_for('main.delete_video', video_id=video.id),
            

        }
        for video in videos
    ]

    return jsonify({'videos': videos_list})

@main.route('/edit/video/<int:video_id>', methods=['POST'])
@role_required('Admin')
def edit_video(video_id):
    video = Video.query.get_or_404(video_id)

    if request.method == 'POST':

        title = (request.form.get('title') or '').strip()
        url = (request.form.get('url') or '').strip()
        description = request.form.get('description') or ''
        notes = request.form.get('notes') or ''
        is_public = 'is_public' in request.form

        errors = video_form_errors(title, url, video_id=video.id)
        if errors:
            return jsonify({'success': False, 'error': ' '.join(errors), 'flash_messages': errors}), 400

        video.title = title
        video.url = url
        video.thumbnail_url = get_youtube_thumbnail_url(url)
        video.description = description
        video.notes = notes
        video.is_public = is_public

        db.session.commit()

        flash('Video details updated successfully!', 'success')

        return jsonify({
            'success': True,
            'flash_messages': get_flashed_messages(),
            'videoId': video.id,
        })
    
@main.route('/get_user_data/<int:user_id>', methods=['GET'])
@role_required('Admin')
def get_user_data(user_id):
    try:
        session.pop('_flashes', None)

        user = User.query.get_or_404(user_id)
        
        roles = Role.query.all()

        roles_data = [{'id': role.id, 'name': role.name} for role in roles]
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'notes': user.notes,
            'role': user.get_role_name(),
            'roles': roles_data,
            'selectedRoleId': user.role_id,
        }

        return jsonify(user_data)

    except Exception as e:
        print(f"Error in get_user_data: {e}")
        return jsonify({'error': 'An error occurred'}), 500


@main.route('/add_video', methods=['POST'])
@role_required('Admin')
def add_video():
    title = (request.form.get('title') or '').strip()
    embed_url = (request.form.get('url') or '').strip()
    description = request.form.get('description') or ''
    notes = request.form.get('notes') or ''
    is_public = bool(request.form.get('is_public'))

    map_id = request.form.get('map', type=int)
    grenade_id = request.form.get('grenade', type=int)
    game_map = db.session.get(GameMap, map_id) if map_id else None
    grenade = db.session.get(Grenade, grenade_id) if grenade_id else None

    errors = video_form_errors(title, embed_url)
    if game_map is None:
        errors.append('Choose a map from the list.')
    if grenade is None:
        errors.append('Choose a grenade from the list.')
    if errors:
        return jsonify({'error': ' '.join(errors), 'flash_messages': errors}), 400

    thumbnail_url = get_youtube_thumbnail_url(embed_url)

    new_video = Video(
        title=title,
        url=embed_url,
        description=description,
        is_public=is_public,
        notes=notes,
        thumbnail_url=thumbnail_url
    )
    new_video.grenade=grenade
    new_video.game_map = game_map
    db.session.add(new_video)
    db.session.commit()

    flash_messages = ["Video added successfully."]
    return jsonify({'flash_messages': flash_messages, 'videoId': new_video.id})



@main.route('/delete/video/<int:video_id>', methods=['GET', 'POST'])
@role_required('Admin')
def delete_video(video_id):
    video = Video.query.get_or_404(video_id)

    if request.method == 'POST':
        

        delete_user_videos(video_id=video.id)
        db.session.delete(video)
        db.session.commit()
        flash('Video deleted successfully.', 'success')
        return redirect(url_for('main.admin_dashboard'))

    return render_template('delete_video.html', video=video)
