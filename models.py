from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Device(db.Model):
    __tablename__ = 'devices'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    device_id = db.Column(db.String(100), unique=True, nullable=False)
    location = db.Column(db.String(200))
    status = db.Column(db.String(20), default='offline')  # online, offline, error
    last_checkin = db.Column(db.DateTime)
    current_playlist_id = db.Column(db.Integer, db.ForeignKey('playlists.id'))
    assigned_media_id = db.Column(db.Integer, db.ForeignKey('media_files.id'))  # Single media assignment
    assignment_updated_at = db.Column(db.DateTime)  # When assignment last changed
    current_media = db.Column(db.String(200))
    ip_address = db.Column(db.String(15))
    pending_command = db.Column(db.String(50))  # reboot, restart_service, etc.
    command_timestamp = db.Column(db.DateTime)  # when command was issued
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    current_playlist = db.relationship('Playlist', backref='assigned_devices')
    assigned_media = db.relationship('MediaFile', backref='assigned_devices')
    
    def is_online(self):
        if not self.last_checkin:
            return False
        return datetime.utcnow() - self.last_checkin < timedelta(minutes=5)
    
    def __repr__(self):
        return f'<Device {self.name}>'

class MediaFile(db.Model):
    __tablename__ = 'media_files'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    original_filename = db.Column(db.String(200), nullable=False)
    file_type = db.Column(db.String(20), nullable=False)  # image, video
    file_size = db.Column(db.Integer)
    duration = db.Column(db.Integer)  # in seconds, for videos
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    uploader = db.relationship('User', backref='uploaded_media')
    
    def __repr__(self):
        return f'<MediaFile {self.original_filename}>'

class Playlist(db.Model):
    __tablename__ = 'playlists'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    loop_playlist = db.Column(db.Boolean, default=True)
    default_duration = db.Column(db.Integer, default=10)  # seconds per item
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref='created_playlists')
    items = db.relationship('PlaylistItem', backref='playlist', cascade='all, delete-orphan', order_by='PlaylistItem.order_index')
    
    def __repr__(self):
        return f'<Playlist {self.name}>'

class PlaylistItem(db.Model):
    __tablename__ = 'playlist_items'
    
    id = db.Column(db.Integer, primary_key=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlists.id'), nullable=False)
    media_file_id = db.Column(db.Integer, db.ForeignKey('media_files.id'), nullable=False)
    order_index = db.Column(db.Integer, nullable=False)
    duration = db.Column(db.Integer)  # override default duration if set
    
    # Relationships
    media_file = db.relationship('MediaFile', backref='playlist_items')
    
    def __repr__(self):
        return f'<PlaylistItem {self.playlist_id}:{self.order_index}>'

class DeviceLog(db.Model):
    __tablename__ = 'device_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    log_type = db.Column(db.String(20), nullable=False)  # info, warning, error
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    device = db.relationship('Device', backref='logs')
    
    def __repr__(self):
        return f'<DeviceLog {self.device_id}:{self.log_type}>'
