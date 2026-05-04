from flask import current_app
from app.extensions import db
from app.models import User, Role, PermissionRole, Permission, UserVideo, Video, Grenade, GameMap
from app.models.video import get_youtube_thumbnail_url


def setup_database():
    """Creates any missing tables. Seed data is loaded only into an empty database (no roles yet)."""
    db.create_all()

    if Role.query.first() is not None:
        return

    create_roles()

    # Every map with a filter button on the index page, so the dashboard can add videos to it
    for map_name in ["mirage", "inferno", "ancient", "vertigo", "anubis", "overpass", "nuke"]:
        db.session.add(GameMap(name=map_name, description=f"Description for {map_name}"))
    db.session.flush()

    videos_data = [
    
    {"map": "mirage", "type": "smoke", "title": "Default Window Smoke", "url": "https://www.youtube.com/embed/fgmsybJwumk", "image": "static/images/thumbs/mirageThumb.avif","bookmarked": False},
    {"map": "mirage", "type": "smoke", "title": "Alternative Window Smoke", "url": "https://www.youtube.com/embed/YaX8BC6Rcr8", "image": "static/images/thumbs/mirageThumb.avif","bookmarked": False},
    {"map": "mirage", "type": "smoke", "title": "Instant Window Smoke - Spawn 1", "url": "https://www.youtube.com/embed/ZK8f7RkAkr0", "image": "static/images/thumbs/mirageThumb.avif","bookmarked": False},
    {"map": "mirage", "type": "smoke", "title": "Instant Window Smoke - Spawn 9", "url": "https://www.youtube.com/embed/_c_QuEC--po", "image": "static/images/thumbs/mirageThumb.avif","bookmarked": False},
    {"map": "mirage", "type": "smoke", "title": "Connector Smokes", "url": "https://www.youtube.com/embed/vw9TA6B9smU", "image": "static/images/thumbs/mirageThumb.avif","bookmarked": False},
    {"map": "mirage", "type": "smoke", "title": "CT Spawn Smoke", "url": "https://www.youtube.com/embed/abDW34VVw28", "image": "static/images/thumbs/mirageThumb.avif","bookmarked": False},
    {"map": "mirage", "type": "smoke", "title": "Jungle Smoke", "url": "https://www.youtube.com/embed/wOCypFL0YYY", "image": "static/images/thumbs/mirageThumb.avif","bookmarked": False},
    {"map": "mirage", "type": "smoke", "title": "Stairs Smoke", "url": "https://www.youtube.com/embed/5pdLW5UhSls", "image": "static/images/thumbs/mirageThumb.avif","bookmarked": False},
    {"map": "mirage", "type": "smoke", "title": "Jungle & Stairs Smokes", "url": "https://www.youtube.com/embed/8PmNJE6dKs4", "image": "static/images/thumbs/mirageThumb.avif","bookmarked": False},
    {"map": "mirage", "type": "flash", "title": "Jungle to A Flash", "url": "https://www.youtube.com/embed/VDEml3BCGfw", "image": "static/images/thumbs/mirageThumb.avif","bookmarked": False},
    {"map": "mirage", "type": "flash", "title": "Connector to Mid Flash", "url": "https://www.youtube.com/embed/gb8Spr0TDpk", "image": "static/images/thumbs/mirageThumb.avif","bookmarked": False},
    {"map": "mirage", "type": "molly", "title": "Sandwich Molotov", "url": "https://www.youtube.com/embed/CoOkYYVyJRo", "image": "static/images/thumbs/mirageThumb.avif","bookmarked": False},
    {"map": "mirage", "type": "nade", "title": "Window Nade", "url": "https://www.youtube.com/embed/vfTC6_dCWgs", "image": "static/images/thumbs/mirageThumb.avif","bookmarked": False},
    {"map": "inferno", "type": "smoke", "title": "Coffins B Site Smoke", "url": "https://www.youtube.com/embed/MFmdWi_42tM", "image": "static/images/thumbs/infernoThumb.jpg","bookmarked": False},
    {"map": "inferno", "type": "smoke", "title": "CT Spawn B Site Smoke", "url": "https://www.youtube.com/embed/E2lcbeg4wAg", "image": "static/images/thumbs/infernoThumb.jpg","bookmarked": False},
    {"map": "inferno", "type": "smoke", "title": "Fast CT Spawn B Site Smoke", "url": "https://www.youtube.com/embed/JwWcMriGSDg", "image": "static/images/thumbs/infernoThumb.jpg","bookmarked": False},
    {"map": "inferno", "type": "smoke", "title": "Default & Fast Long Smokes", "url": "https://www.youtube.com/embed/JIvizM2Jxc4", "image": "static/images/thumbs/infernoThumb.jpg","bookmarked": False},
    {"map": "inferno", "type": "nade", "title": "CT Mid Nade", "url": "https://www.youtube.com/embed/vn2rgmzDY1M", "image": "static/images/thumbs/infernoThumb.jpg","bookmarked": False},
    {"map": "inferno", "type": "molly", "title": "Triple Box Molotov", "url": "https://www.youtube.com/embed/7l0fHTj8_dk", "image": "static/images/thumbs/infernoThumb.jpg","bookmarked": False},
    {"map": "inferno", "type": "flash", "title": "Fallen B Site Flash", "url": "https://www.youtube.com/embed/nEvI93qDYiQ", "image": "static/images/thumbs/infernoThumb.jpg","bookmarked": False},
    {"map": "inferno", "type": "flash", "title": "B Site Car Retake Flash", "url": "https://www.youtube.com/embed/djpNJl57cUY", "image": "static/images/thumbs/infernoThumb.jpg","bookmarked": False},
    
    ]
    
    for video_data in videos_data:
        game_map_name = video_data.get("map")
        grenade_name = video_data.get("type")

        game_map = GameMap.query.filter_by(name=game_map_name).first()
        if not game_map:
            game_map = GameMap(name=game_map_name, description=f"Description for {game_map_name}")
            db.session.add(game_map)
            db.session.flush()

        grenade = Grenade.query.filter_by(name=grenade_name).first()
        if not grenade:
            grenade = Grenade(name=grenade_name, description=f"Description for {grenade_name}")
            db.session.add(grenade)
            db.session.flush()

        video = Video(
            title=video_data["title"],
            url=video_data["url"],
            description=f"Description for {video_data['title']}",
            is_public=True,
            notes=f"Notes for {video_data['title']}",
            thumbnail_url= get_youtube_thumbnail_url(video_data["url"])
        )
        video.grenade=grenade
        video.game_map = game_map
        db.session.add(video)
        db.session.flush()
        embed_url = video.url
        video.thumbnail_url = get_youtube_thumbnail_url(embed_url)
        db.session.flush()


    admin_role = Role.query.filter_by(name='Admin').first()
    user_role = Role.query.filter_by(name='User').first()
    Free_account_role = Role.query.filter_by(name='Free-Account').first()


    # Create two users
    user1 = User(
        email='user1@example.com',
        username='free-account',
        password_hash='hashed_password', 
        is_authenticated=True,
        first_name='User',
        last_name='One',
        notes='Some notes for user 1'
    )

    user1.set_password('password')
    db.session.add(user1)
    user1.assign_role(Free_account_role)

    user2 = User(
        email='user2@example.com',
        username='user',
        password_hash='hashed_password',
        is_authenticated=True,
        first_name='User',
        last_name='Two',
        notes='Some notes for user 2'
    )
    user2.set_password('password')
    db.session.add(user2)
    user2.assign_role(user_role)
    db.session.commit()



    admin= User(
        email='admin@example.com',
        username='admin',
        password_hash='hashed_password', 
        is_authenticated=True,
        first_name='Dr',
        last_name='Doofenshmirtz',
        notes='Doofenshmirtz'
    )

    admin.role = admin_role
    admin.set_password('password')  
    db.session.add(admin)


    db.session.commit()


def create_roles():
    
    roles_data = [
        {'name': 'Admin', 'permissions': [('Add video', 'Add videos'), ('Delete video', 'Delete videos'), ('Change roles', 'Change roles'), ('Delete user', 'Delete users')]},
        {'name': 'User', 'permissions': [('View videos', 'View videos'), ('bookmark', 'Bookmark videos')]},
        {'name': 'Free-Account', 'permissions': [('view 3 videos', 'Limited to 3 videos in total')]},
        {'name': 'Anonymous-Account', 'permissions': [('view 2 videos', 'Limited to 2 videos in total')] },
    ]


    for role_data in roles_data:
        role_name = role_data['name']
        permissions = role_data['permissions']

        role = Role.query.filter_by(name=role_name).first()
       
        if role is None:
            role = Role(name=role_name)
            db.session.add(role)

           
            for permission_name, description in permissions:
                permission = Permission.query.filter_by(name=permission_name).first()
                if permission is None:
                    permission = Permission(name=permission_name, description=description)
                    db.session.add(permission)

               
                permission_role = PermissionRole(role=role, permission=permission)
                db.session.add(permission_role)

    db.session.flush()
    db.session.commit()
