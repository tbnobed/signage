import os
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import app, db
from models import User, Device, MediaFile, Playlist, PlaylistItem, DeviceLog

main = Blueprint('main', __name__)
# API Blueprint for client communication
api = Blueprint('api', __name__, url_prefix='/api')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov', 'mkv', 'webm'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main.route('/dashboard')
@login_required
def dashboard():
    total_devices = Device.query.count()
    online_devices = Device.query.filter_by(status='online').count()
    total_media = MediaFile.query.count()
    total_playlists = Playlist.query.count()
    
    recent_devices = Device.query.order_by(Device.last_checkin.desc()).limit(5).all()
    recent_media = MediaFile.query.order_by(MediaFile.created_at.desc()).limit(5).all()
    
    return render_template('dashboard.html',
                         total_devices=total_devices,
                         online_devices=online_devices,
                         total_media=total_media,
                         total_playlists=total_playlists,
                         recent_devices=recent_devices,
                         recent_media=recent_media)

@main.route('/devices')
@login_required
def devices():
    devices_list = Device.query.order_by(Device.created_at.desc()).all()
    playlists = Playlist.query.filter_by(is_active=True).all()
    return render_template('devices.html', devices=devices_list, playlists=playlists)

@main.route('/devices/add', methods=['POST'])
@login_required
def add_device():
    name = request.form['name']
    device_id = request.form['device_id']
    location = request.form.get('location', '')
    
    if Device.query.filter_by(device_id=device_id).first():
        flash('Device ID already exists', 'error')
        return redirect(url_for('main.devices'))
    
    device = Device(
        name=name,
        device_id=device_id,
        location=location
    )
    
    db.session.add(device)
    db.session.commit()
    
    flash('Device added successfully', 'success')
    return redirect(url_for('main.devices'))

@main.route('/devices/<int:device_id>/assign', methods=['POST'])
@login_required
def assign_playlist(device_id):
    device = Device.query.get_or_404(device_id)
    playlist_id = request.form.get('playlist_id')
    
    if playlist_id:
        device.current_playlist_id = int(playlist_id)
    else:
        device.current_playlist_id = None
    
    db.session.commit()
    flash('Playlist assigned successfully', 'success')
    return redirect(url_for('main.devices'))

@main.route('/media')
@login_required
def media():
    media_files = MediaFile.query.order_by(MediaFile.created_at.desc()).all()
    return render_template('media.html', media_files=media_files)

@main.route('/media/upload', methods=['POST'])
@login_required
def upload_media():
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('main.media'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('main.media'))
    
    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Determine file type
        file_type = 'video' if file_extension in ['mp4', 'avi', 'mov', 'mkv', 'webm'] else 'image'
        
        media_file = MediaFile(
            filename=unique_filename,
            original_filename=original_filename,
            file_type=file_type,
            file_size=os.path.getsize(file_path),
            uploaded_by=current_user.id
        )
        
        db.session.add(media_file)
        db.session.commit()
        
        flash('File uploaded successfully', 'success')
    else:
        flash('Invalid file type', 'error')
    
    return redirect(url_for('main.media'))

@main.route('/media/<int:media_id>/delete', methods=['POST'])
@login_required
def delete_media(media_id):
    media_file = MediaFile.query.get_or_404(media_id)
    
    # Check if media is used in any playlists
    if PlaylistItem.query.filter_by(media_file_id=media_id).first():
        flash('Cannot delete media file that is used in playlists', 'error')
        return redirect(url_for('main.media'))
    
    # Delete file from filesystem
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], media_file.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    db.session.delete(media_file)
    db.session.commit()
    
    flash('Media file deleted successfully', 'success')
    return redirect(url_for('main.media'))

@main.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@main.route('/playlists')
@login_required
def playlists():
    playlists_list = Playlist.query.order_by(Playlist.created_at.desc()).all()
    return render_template('playlists.html', playlists=playlists_list)

@main.route('/playlists/add', methods=['POST'])
@login_required
def add_playlist():
    name = request.form['name']
    description = request.form.get('description', '')
    default_duration = int(request.form.get('default_duration', 10))
    
    playlist = Playlist(
        name=name,
        description=description,
        default_duration=default_duration,
        created_by=current_user.id
    )
    
    db.session.add(playlist)
    db.session.commit()
    
    flash('Playlist created successfully', 'success')
    return redirect(url_for('main.playlists'))

@main.route('/playlists/<int:playlist_id>/edit')
@login_required
def edit_playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    media_files = MediaFile.query.all()
    return render_template('playlist_edit.html', playlist=playlist, media_files=media_files)

@main.route('/playlists/<int:playlist_id>/update', methods=['POST'])
@login_required
def update_playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    
    # Debug: Log form data
    print(f"DEBUG: Form data received: {dict(request.form)}")
    print(f"DEBUG: media_ids: {request.form.getlist('media_ids')}")
    print(f"DEBUG: durations: {request.form.getlist('durations')}")
    
    playlist.name = request.form['name']
    playlist.description = request.form.get('description', '')
    playlist.default_duration = int(request.form.get('default_duration', 10))
    playlist.loop_playlist = 'loop_playlist' in request.form
    playlist.updated_at = datetime.utcnow()
    
    # Update playlist items
    PlaylistItem.query.filter_by(playlist_id=playlist_id).delete()
    
    media_ids = request.form.getlist('media_ids')
    durations = request.form.getlist('durations')
    
    for i, media_id in enumerate(media_ids):
        if media_id:
            duration = int(durations[i]) if durations[i] else None
            item = PlaylistItem(
                playlist_id=playlist_id,
                media_file_id=int(media_id),
                order_index=i,
                duration=duration
            )
            db.session.add(item)
            print(f"DEBUG: Added playlist item - media_id: {media_id}, duration: {duration}")
    
    db.session.commit()
    flash('Playlist updated successfully', 'success')
    return redirect(url_for('main.playlists'))

@main.route('/playlists/<int:playlist_id>/delete', methods=['POST'])
@login_required
def delete_playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    
    # Check if playlist is assigned to any devices
    if Device.query.filter_by(current_playlist_id=playlist_id).first():
        flash('Cannot delete playlist that is assigned to devices', 'error')
        return redirect(url_for('main.playlists'))
    
    db.session.delete(playlist)
    db.session.commit()
    
    flash('Playlist deleted successfully', 'success')
    return redirect(url_for('main.playlists'))

# API Endpoints for client communication

@api.route('/devices/<device_id>/checkin', methods=['POST'])
def device_checkin(device_id):
    device = Device.query.filter_by(device_id=device_id).first()
    
    if not device:
        return jsonify({'error': 'Device not found'}), 404
    
    data = request.get_json() or {}
    
    device.status = 'online'
    device.last_checkin = datetime.utcnow()
    device.current_media = data.get('current_media')
    device.ip_address = request.remote_addr
    
    db.session.commit()
    
    response = {
        'status': 'ok',
        'playlist_id': device.current_playlist_id
    }
    
    return jsonify(response)

@api.route('/devices/<device_id>/playlist')
def get_device_playlist(device_id):
    device = Device.query.filter_by(device_id=device_id).first()
    
    if not device:
        return jsonify({'error': 'Device not found'}), 404
    
    if not device.current_playlist_id:
        return jsonify({'playlist': None})
    
    playlist = Playlist.query.get(device.current_playlist_id)
    if not playlist or not playlist.is_active:
        return jsonify({'playlist': None})
    
    playlist_data = {
        'id': playlist.id,
        'name': playlist.name,
        'loop': playlist.loop_playlist,
        'default_duration': playlist.default_duration,
        'items': []
    }
    
    for item in playlist.items:
        playlist_data['items'].append({
            'id': item.media_file_id,
            'filename': item.media_file.filename,
            'original_filename': item.media_file.original_filename,
            'file_type': item.media_file.file_type,
            'duration': item.duration or playlist.default_duration,
            'url': url_for('main.uploaded_file', filename=item.media_file.filename, _external=True)
        })
    
    return jsonify({'playlist': playlist_data})

@api.route('/devices/<device_id>/log', methods=['POST'])
def device_log(device_id):
    device = Device.query.filter_by(device_id=device_id).first()
    
    if not device:
        return jsonify({'error': 'Device not found'}), 404
    
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'Invalid log data'}), 400
    
    log_entry = DeviceLog(
        device_id=device.id,
        log_type=data.get('type', 'info'),
        message=data['message']
    )
    
    db.session.add(log_entry)
    db.session.commit()
    
    return jsonify({'status': 'ok'})

@main.route('/api/devices/status')
def devices_status():
    """Get device status for dashboard refresh"""
    devices = Device.query.all()
    device_data = []
    
    for device in devices:
        device_data.append({
            'id': device.id,
            'name': device.name,
            'device_id': device.device_id,
            'status': device.status,
            'is_online': device.is_online(),
            'last_checkin': device.last_checkin.isoformat() if device.last_checkin else None,
            'current_media': device.current_media,
            'location': device.location
        })
    
    return jsonify(device_data)

@main.route('/download/client')
def download_client():
    """Download the client agent script"""
    from flask import send_file
    try:
        return send_file('client_agent.py', as_attachment=True, download_name='signage_client.py')
    except FileNotFoundError:
        return "Client script not found", 404

@main.route('/download/setup.sh')
def download_setup_script():
    """Download the setup shell script"""
    from flask import send_file
    try:
        return send_file('setup_client.sh', as_attachment=True, download_name='setup_client.sh')
    except FileNotFoundError:
        return "Setup script not found", 404

@main.route('/download/setup.py')
def download_setup_python():
    """Download the Python setup script"""
    from flask import send_file
    try:
        return send_file('setup_client.py', as_attachment=True, download_name='setup_client.py')
    except FileNotFoundError:
        return "Python setup script not found", 404

@main.route('/install')
def install_script():
    """Generate dynamic install script with correct server URL"""
    from flask import request, Response
    
    # Read the template shell script
    try:
        with open('setup_client.sh', 'r') as f:
            script_content = f.read()
    except FileNotFoundError:
        return "Setup script template not found", 404
    
    # Replace placeholder with actual server URL
    server_url = request.url_root.rstrip('/')
    script_content = script_content.replace('YOUR_SERVER_URL', server_url)
    
    # Return as downloadable script
    return Response(
        script_content,
        mimetype='application/x-sh',
        headers={
            'Content-Disposition': 'attachment; filename=setup_client.sh',
            'Content-Type': 'text/x-shellscript'
        }
    )
