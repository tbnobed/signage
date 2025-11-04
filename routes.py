import os
import uuid
import re
import mimetypes
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, Response, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename, safe_join
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
    # Count devices that are actually online (last checkin within 5 minutes)
    all_devices = Device.query.all()
    online_devices = sum(1 for device in all_devices if device.is_online())
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

@main.route('/control')
@login_required
def control():
    devices_list = Device.query.order_by(Device.name).all()
    playlists = Playlist.query.filter_by(is_active=True).order_by(Playlist.name).all()
    media_files = MediaFile.query.order_by(MediaFile.original_filename).all()
    
    online_count = sum(1 for device in devices_list if device.is_online())
    offline_count = len(devices_list) - online_count
    
    return render_template('control.html', 
                         devices=devices_list, 
                         playlists=playlists, 
                         media_files=media_files,
                         online_count=online_count,
                         offline_count=offline_count)

@main.route('/devices')
@login_required
def devices():
    devices_list = Device.query.order_by(Device.created_at.desc()).all()
    playlists = Playlist.query.filter_by(is_active=True).all()
    media_files = MediaFile.query.order_by(MediaFile.created_at.desc()).all()
    return render_template('devices.html', devices=devices_list, playlists=playlists, media_files=media_files)

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
        device.assigned_media_id = None  # Clear single media assignment (exclusivity)
        device.assignment_updated_at = datetime.utcnow()  # Update timestamp
    else:
        device.current_playlist_id = None
        device.assignment_updated_at = datetime.utcnow()  # Update timestamp even when clearing
    
    db.session.commit()
    flash('Playlist assigned successfully', 'success')
    return redirect(url_for('main.devices'))

@main.route('/devices/<int:device_id>/assign-media', methods=['POST'])
@login_required
def assign_media(device_id):
    device = Device.query.get_or_404(device_id)
    media_id = request.form.get('media_id')
    
    if media_id:
        # Validate media file exists
        media_file = MediaFile.query.get(int(media_id))
        if not media_file:
            flash('Media file not found', 'error')
            return redirect(url_for('main.devices'))
            
        device.assigned_media_id = int(media_id)
        device.current_playlist_id = None  # Clear playlist assignment (exclusivity)
        device.assignment_updated_at = datetime.utcnow()  # Update timestamp
    else:
        device.assigned_media_id = None
        device.assignment_updated_at = datetime.utcnow()  # Update timestamp even when clearing
    
    db.session.commit()
    flash('Single media assigned successfully', 'success')
    return redirect(url_for('main.devices'))

@main.route('/devices/<int:device_id>/delete', methods=['POST'])
@login_required
def delete_device(device_id):
    device = Device.query.get_or_404(device_id)
    device_name = device.name
    
    # Delete associated device logs first (cascade)
    DeviceLog.query.filter_by(device_id=device_id).delete()
    
    # Delete the device
    db.session.delete(device)
    db.session.commit()
    
    flash(f'Device "{device_name}" and its logs have been deleted successfully', 'success')
    return redirect(url_for('main.devices'))

@main.route('/devices/<int:device_id>/reboot', methods=['POST'])
@login_required
def reboot_device(device_id):
    device = Device.query.get_or_404(device_id)
    
    # Set pending reboot command
    device.pending_command = 'reboot'
    device.command_timestamp = datetime.utcnow()
    db.session.commit()
    
    flash(f'Reboot command sent to "{device.name}". Device will reboot on next check-in.', 'info')
    return redirect(url_for('main.devices'))

@main.route('/devices/<int:device_id>/update', methods=['POST'])
@login_required
def update_device(device_id):
    device = Device.query.get_or_404(device_id)
    
    # Set pending update command
    device.pending_command = 'update'
    device.command_timestamp = datetime.utcnow()
    db.session.commit()
    
    flash(f'Update command sent to "{device.name}". Client will update on next check-in.', 'success')
    return redirect(url_for('main.devices'))

@main.route('/devices/<int:device_id>/update-name', methods=['POST'])
@login_required
def update_device_name(device_id):
    device = Device.query.get_or_404(device_id)
    
    data = request.get_json()
    new_name = data.get('name', '').strip()
    
    if not new_name:
        return jsonify({'success': False, 'error': 'Device name cannot be empty'}), 400
    
    device.name = new_name
    db.session.commit()
    
    return jsonify({'success': True, 'name': new_name})

@main.route('/devices/<int:device_id>/update-location', methods=['POST'])
@login_required
def update_device_location(device_id):
    device = Device.query.get_or_404(device_id)
    
    data = request.get_json()
    new_location = data.get('location', '').strip()
    
    device.location = new_location if new_location else None
    db.session.commit()
    
    return jsonify({'success': True, 'location': new_location})

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

@main.route('/media/add-stream', methods=['POST'])
@login_required
def add_stream():
    stream_name = request.form.get('stream_name', '').strip()
    stream_url = request.form.get('stream_url', '').strip()
    stream_type = request.form.get('stream_type', '').strip()
    
    if not all([stream_name, stream_url, stream_type]):
        flash('All fields are required for streaming media', 'error')
        return redirect(url_for('main.media'))
    
    # Validate URL format based on stream type
    url_valid = False
    if stream_type == 'rtmp' and stream_url.startswith('rtmp://'):
        url_valid = True
    elif stream_type == 'hls' and ('.m3u8' in stream_url or 'm3u8' in stream_url):
        url_valid = True
    elif stream_type == 'http' and (stream_url.startswith('http://') or stream_url.startswith('https://')):
        url_valid = True
    
    if not url_valid:
        flash(f'Invalid URL format for {stream_type.upper()} stream', 'error')
        return redirect(url_for('main.media'))
    
    # Check if stream URL already exists
    existing_stream = MediaFile.query.filter_by(stream_url=stream_url).first()
    if existing_stream:
        flash('This stream URL is already added to your library', 'warning')
        return redirect(url_for('main.media'))
    
    # Create streaming media file record
    media_file = MediaFile(
        original_filename=stream_name,
        file_type='stream',
        is_stream=True,
        stream_url=stream_url,
        stream_type=stream_type,
        uploaded_by=current_user.id
    )
    
    db.session.add(media_file)
    db.session.commit()
    
    flash(f'{stream_type.upper()} stream "{stream_name}" added successfully', 'success')
    return redirect(url_for('main.media'))

@main.route('/media/<int:media_id>/delete', methods=['POST'])
@login_required
def delete_media(media_id):
    media_file = MediaFile.query.get_or_404(media_id)
    
    # Check if media is used in any playlists
    if PlaylistItem.query.filter_by(media_file_id=media_id).first():
        flash('Cannot delete media file that is used in playlists', 'error')
        return redirect(url_for('main.media'))
    
    # Delete file from filesystem (only for uploaded files, not streams)
    if media_file.filename:  # Streams have filename=None
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], media_file.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    db.session.delete(media_file)
    db.session.commit()
    
    flash('Media file deleted successfully', 'success')
    return redirect(url_for('main.media'))

@main.route('/uploads/<path:filename>')
def uploaded_file(filename):
    # Use safe_join to prevent path traversal attacks
    file_path = safe_join(app.config['UPLOAD_FOLDER'], filename)
    
    if not file_path or not os.path.exists(file_path):
        abort(404)
    
    # Handle HTTP Range requests for video streaming
    range_header = request.headers.get('Range')
    
    if range_header:
        # Parse Range header (e.g., "bytes=0-1023" or "bytes=1024-")
        file_size = os.path.getsize(file_path)
        range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
        
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
            
            # Ensure valid range
            start = max(0, min(start, file_size - 1))
            end = max(start, min(end, file_size - 1))
            length = end - start + 1
            
            # Read the requested byte range
            with open(file_path, 'rb') as f:
                f.seek(start)
                data = f.read(length)
            
            # Determine content type
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                if filename.lower().endswith(('.mp4', '.mov')):
                    content_type = 'video/mp4'
                elif filename.lower().endswith('.webm'):
                    content_type = 'video/webm'
                elif filename.lower().endswith('.avi'):
                    content_type = 'video/avi'
                else:
                    content_type = 'application/octet-stream'
            
            # Create 206 Partial Content response
            response = Response(data, 206, mimetype=content_type)
            response.headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'
            response.headers['Accept-Ranges'] = 'bytes'
            response.headers['Content-Length'] = str(length)
            response.headers['Cache-Control'] = 'public, max-age=3600'
            
            return response
    
    # Fallback to normal file serving for non-range requests
    response = send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    # Add headers for better video playback support
    if filename.lower().endswith(('.mp4', '.webm', '.avi', '.mov', '.mkv')):
        response.headers['Accept-Ranges'] = 'bytes'
        response.headers['Cache-Control'] = 'public, max-age=3600'
    
    return response

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

@api.route('/devices/ping')
def devices_ping():
    """Simple ping endpoint for health checks"""
    return jsonify({'status': 'ok', 'message': 'pong'})

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
    
    # Update TeamViewer ID if provided by client
    if data.get('teamviewer_id'):
        device.teamviewer_id = data.get('teamviewer_id')
    
    # Update client version if provided by client
    if data.get('client_version'):
        device.client_version = data.get('client_version')
    
    db.session.commit()
    
    # Keep device_checkin backward compatible - only return actual playlist IDs as integers
    response = {
        'status': 'ok',
        'playlist_id': device.current_playlist_id  # Always integer or None for backward compatibility
    }
    
    # Check for pending commands
    if device.pending_command:
        response['command'] = device.pending_command
        response['command_timestamp'] = device.command_timestamp.isoformat() if device.command_timestamp else None
        
        # Clear the command after sending it
        device.pending_command = None
        device.command_timestamp = None
        db.session.commit()
    
    return jsonify(response)

@api.route('/client/version', methods=['GET'])
def get_client_version():
    """Get the latest client version and download information"""
    # Read version directly from client_agent.py to avoid duplication
    latest_version = "2.3.1"  # Fallback
    try:
        import re
        client_path = os.path.join(os.path.dirname(__file__), 'client_agent.py')
        if os.path.exists(client_path):
            with open(client_path, 'r') as f:
                content = f.read()
                match = re.search(r'CLIENT_VERSION\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    latest_version = match.group(1)
    except Exception as e:
        app.logger.warning(f"Could not read version from client_agent.py: {e}")
    
    # GitHub repository information
    github_repo = "https://github.com/tbnobed/signage.git"
    download_base = f"{request.url_root}auth/client-setup-sh"
    
    # Check if the requesting client needs an update
    current_version = request.args.get('current_version')
    needs_update = False
    
    if current_version and current_version != latest_version:
        needs_update = True
    
    return jsonify({
        'latest_version': latest_version,
        'needs_update': needs_update,
        'download_url': download_base,
        'github_repo': github_repo,
        'update_available': needs_update,
        'release_notes': 'MPV integration for gapless video playback - eliminates flickering during loops'
    })

@api.route('/devices/<device_id>/playlist-status')
def get_device_playlist_status(device_id):
    """Lightweight endpoint to check if playlist has been updated AND urgent commands"""
    device = Device.query.filter_by(device_id=device_id).first()
    
    if not device:
        return jsonify({'error': 'Device not found'}), 404
    
    response = {}
    
    # Include urgent commands (like reboot) in rapid checks for immediate delivery
    if device.pending_command:
        response['command'] = device.pending_command
        response['command_timestamp'] = device.command_timestamp.isoformat() if device.command_timestamp else None
        
        # Clear the command after sending it (same as main checkin)
        device.pending_command = None
        device.command_timestamp = None
        db.session.commit()
    
    # Check for single media assignment first (takes precedence)
    if device.assigned_media_id:
        media_file = MediaFile.query.get(device.assigned_media_id)
        if media_file:
            # Use negative ID for synthetic playlist to avoid conflicts (backward compatible)
            synthetic_playlist_id = -device.assigned_media_id  # Negative integer, stays numeric
            last_updated = device.assignment_updated_at or media_file.created_at
            response.update({
                'playlist_id': synthetic_playlist_id,  # Numeric for backward compatibility
                'last_updated': last_updated.isoformat()
            })
            return jsonify(response)
    
    # Fall back to regular playlist assignment
    if not device.current_playlist_id:
        response.update({'playlist_id': None, 'last_updated': None})
        return jsonify(response)
    
    playlist = Playlist.query.get(device.current_playlist_id)
    if not playlist or not playlist.is_active:
        response.update({'playlist_id': None, 'last_updated': None})
        return jsonify(response)
    
    response.update({
        'playlist_id': playlist.id,
        'last_updated': playlist.updated_at.isoformat()
    })
    
    return jsonify(response)

@api.route('/devices/<device_id>/playlist')
def get_device_playlist(device_id):
    device = Device.query.filter_by(device_id=device_id).first()
    
    if not device:
        return jsonify({'error': 'Device not found'}), 404
    
    # Check for single media assignment first (takes precedence)
    if device.assigned_media_id:
        media_file = MediaFile.query.get(device.assigned_media_id)
        if media_file:
            # Create synthetic playlist for single media file (backward compatible numeric ID)
            synthetic_playlist_id = -device.assigned_media_id  # Negative integer to avoid conflicts
            last_updated = device.assignment_updated_at or media_file.created_at
            playlist_data = {
                'id': synthetic_playlist_id,  # Numeric for backward compatibility
                'name': media_file.original_filename,
                'loop': True,  # Always loop single media
                'default_duration': 10,  # Default image duration
                'last_updated': last_updated.isoformat(),
                'items': [{
                    'id': media_file.id,
                    'filename': media_file.filename,
                    'original_filename': media_file.original_filename,
                    'file_type': media_file.file_type,
                    'duration': 10 if media_file.file_type == 'image' else None,  # Only set duration for images, None for videos and streams
                    'url': url_for('main.uploaded_file', filename=media_file.filename, _external=True) if not media_file.is_stream else media_file.stream_url,
                    'is_stream': media_file.is_stream or False,
                    'stream_url': media_file.stream_url,
                    'stream_type': media_file.stream_type
                }]
            }
            return jsonify({'playlist': playlist_data})
    
    # Fall back to regular playlist assignment
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
        'last_updated': playlist.updated_at.isoformat(),
        'items': []
    }
    
    for item in playlist.items:
        playlist_data['items'].append({
            'id': item.media_file_id,
            'filename': item.media_file.filename,
            'original_filename': item.media_file.original_filename,
            'file_type': item.media_file.file_type,
            'duration': item.duration or (playlist.default_duration if item.media_file.file_type == 'image' else None),
            'url': url_for('main.uploaded_file', filename=item.media_file.filename, _external=True) if not item.media_file.is_stream else item.media_file.stream_url,
            'is_stream': item.media_file.is_stream or False,
            'stream_url': item.media_file.stream_url,
            'stream_type': item.media_file.stream_type
        })
    
    return jsonify({'playlist': playlist_data})

@api.route('/devices/<device_id>/logs', methods=['POST'])
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

@main.route('/download/client_agent.py')
def download_client_agent():
    """Download the fixed client agent script"""
    from flask import send_file
    try:
        return send_file('client_agent.py', as_attachment=True, download_name='client_agent.py')
    except FileNotFoundError:
        return "Client agent script not found", 404

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
