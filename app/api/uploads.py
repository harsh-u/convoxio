import logging
import os
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import Upload

logger = logging.getLogger(__name__)

uploads_api = Blueprint('uploads_api', __name__)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@uploads_api.route('/upload', methods=['POST'])
@login_required
def upload_documents():
    """Upload business documents (PAN/GST)"""
    try:
        if 'pan_file' not in request.files and 'gst_file' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        uploads = []
        uploaded_files = []
        
        for file_key in ['pan_file', 'gst_file']:
            if file_key in request.files:
                file = request.files[file_key]
                if file.filename == '':
                    continue
                    
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filetype = 'PAN' if file_key == 'pan_file' else 'GST'
                    
                    # Check if user already has this document type
                    existing_upload = Upload.query.filter_by(
                        user_id=current_user.id,
                        filetype=filetype
                    ).first()
                    
                    if existing_upload:
                        # Remove old file
                        old_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], existing_upload.filename)
                        if os.path.exists(old_file_path):
                            os.remove(old_file_path)
                        db.session.delete(existing_upload)
                    
                    # Save new file
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    
                    # Create upload record
                    upload = Upload(
                        filename=filename,
                        filetype=filetype,
                        user_id=current_user.id
                    )
                    db.session.add(upload)
                    uploads.append(upload)
                    uploaded_files.append({
                        'filename': filename,
                        'filetype': filetype,
                        'size': os.path.getsize(file_path)
                    })
                    
                    logger.info(f"📄 {filetype} document uploaded: {filename} by user {current_user.id}")
                else:
                    return jsonify({'error': f'Invalid file type for {file_key}. Only PDF, JPG, PNG allowed.'}), 400
        
        if uploads:
            db.session.commit()
            
            # Check if both documents are now uploaded
            user_uploads = Upload.query.filter_by(user_id=current_user.id).all()
            has_pan = any(u.filetype == 'PAN' for u in user_uploads)
            has_gst = any(u.filetype == 'GST' for u in user_uploads)
            docs_complete = has_pan and has_gst
            
            return jsonify({
                'success': True,
                'message': f'{len(uploads)} document(s) uploaded successfully',
                'uploaded_files': uploaded_files,
                'docs_complete': docs_complete,
                'has_pan': has_pan,
                'has_gst': has_gst
            }), 200
        
        return jsonify({'error': 'No valid files uploaded'}), 400
        
    except Exception as e:
        logger.error(f"❌ Upload error: {str(e)}")
        return jsonify({'error': 'Failed to upload documents'}), 500

@uploads_api.route('/uploads', methods=['GET'])
@login_required
def get_uploads():
    """Get all uploaded documents for current user"""
    try:
        uploads = Upload.query.filter_by(user_id=current_user.id).all()
        
        return jsonify({
            'success': True,
            'uploads': [{
                'id': upload.id,
                'filename': upload.filename,
                'filetype': upload.filetype,
                'upload_date': upload.id  # Using ID as proxy for upload order
            } for upload in uploads],
            'has_pan': any(u.filetype == 'PAN' for u in uploads),
            'has_gst': any(u.filetype == 'GST' for u in uploads),
            'docs_complete': len([u for u in uploads if u.filetype in ['PAN', 'GST']]) >= 2
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Get uploads error: {str(e)}")
        return jsonify({'error': 'Failed to load uploads'}), 500

@uploads_api.route('/uploads/<int:upload_id>', methods=['DELETE'])
@login_required
def delete_upload(upload_id):
    """Delete an uploaded document"""
    try:
        upload = Upload.query.filter_by(id=upload_id, user_id=current_user.id).first()
        
        if not upload:
            return jsonify({'error': 'Upload not found'}), 404
        
        # Remove file from filesystem
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], upload.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Remove from database
        db.session.delete(upload)
        db.session.commit()
        
        logger.info(f"🗑️ Document deleted: {upload.filename} by user {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Document deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Delete upload error: {str(e)}")
        return jsonify({'error': 'Failed to delete document'}), 500