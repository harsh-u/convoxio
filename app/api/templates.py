import logging
import json
import requests
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Template

logger = logging.getLogger(__name__)

templates_api = Blueprint('templates_api', __name__)

@templates_api.route('/templates', methods=['GET'])
@login_required
def get_templates():
    """Get all templates for current user"""
    try:
        templates = Template.query.filter_by(user_id=current_user.id)\
            .order_by(Template.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'templates': [{
                'id': t.id,
                'name': t.name,
                'language': t.language,
                'content': t.content,
                'status': t.status,
                'category': t.category,
                'header_type': t.header_type,
                'header_text': t.header_text,
                'header_image_url': t.header_image_url,
                'footer_text': t.footer_text,
                'buttons_json': t.buttons_json,
                'meta_template_id': t.meta_template_id,
                'created_at': t.created_at.isoformat()
            } for t in templates]
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Get templates error: {str(e)}")
        return jsonify({'error': 'Failed to load templates'}), 500

@templates_api.route('/templates/approved', methods=['GET'])
@login_required
def get_approved_templates():
    """Get only approved templates for messaging"""
    try:
        templates = Template.query.filter_by(
            user_id=current_user.id, 
            status='Approved'
        ).order_by(Template.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'templates': [{
                'id': t.id,
                'name': t.name,
                'language': t.language,
                'content': t.content,
                'category': t.category,
                'header_type': t.header_type,
                'header_text': t.header_text,
                'footer_text': t.footer_text,
                'created_at': t.created_at.isoformat()
            } for t in templates]
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Get approved templates error: {str(e)}")
        return jsonify({'error': 'Failed to load approved templates'}), 500

@templates_api.route('/templates', methods=['POST'])
@login_required
def create_template():
    """Create a new message template"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'language', 'content', 'category']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        logger.info(f"📝 New template submission: {data['name']} by user {current_user.id}")
        
        # Build components array for Meta API
        components = []
        
        # Header
        header_type = data.get('header_type', 'NONE')
        if header_type == 'TEXT' and data.get('header_text'):
            components.append({
                "type": "HEADER", 
                "format": "TEXT", 
                "text": data['header_text']
            })
        elif header_type == 'IMAGE' and data.get('header_image_url'):
            components.append({
                "type": "HEADER", 
                "format": "IMAGE", 
                "example": {"header_handle": data['header_image_url']}
            })
        
        # Body (always required)
        components.append({
            "type": "BODY", 
            "text": data['content']
        })
        
        # Footer
        if data.get('footer_text'):
            components.append({
                "type": "FOOTER", 
                "text": data['footer_text']
            })
        
        # Buttons
        buttons = []
        for i in range(1, 4):
            btn_type = data.get(f'button{i}_type')
            btn_text = data.get(f'button{i}_text')
            btn_url = data.get(f'button{i}_url')
            
            if btn_type == 'QUICK_REPLY' and btn_text:
                buttons.append({"type": "QUICK_REPLY", "text": btn_text})
            elif btn_type == 'CALL_TO_ACTION' and btn_text:
                btn = {"type": "CALL_TO_ACTION", "text": btn_text}
                if btn_url:
                    btn["url"] = btn_url
                buttons.append(btn)
        
        if buttons:
            components.append({"type": "BUTTONS", "buttons": buttons})
        
        buttons_json_str = json.dumps(buttons) if buttons else None
        
        # Create template in database first
        template = Template(
            user_id=current_user.id,
            name=data['name'],
            language=data['language'],
            content=data['content'],
            status='Pending',
            category=data['category'],
            header_type=header_type,
            header_text=data.get('header_text'),
            header_image_url=data.get('header_image_url'),
            footer_text=data.get('footer_text'),
            buttons_json=buttons_json_str
        )
        
        # Submit to Meta if user has WhatsApp connected
        if current_user.whatsapp_access_token and current_user.waba_id:
            try:
                url = f"https://graph.facebook.com/v19.0/{current_user.waba_id}/message_templates"
                headers = {"Authorization": f"Bearer {current_user.whatsapp_access_token}"}
                payload = {
                    "name": data['name'],
                    "language": {"code": data['language']},
                    "components": components,
                    "category": data['category']
                }
                
                response = requests.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    resp_json = response.json()
                    template.meta_template_id = resp_json.get("id")
                    template.status = 'Pending'
                    logger.info(f"✅ Template submitted to Meta: {template.name}")
                else:
                    logger.error(f"❌ Meta API error: {response.status_code} {response.text}")
                    template.status = 'Rejected'
                    
            except Exception as e:
                logger.error(f"❌ Error submitting template to Meta: {e}")
                template.status = 'Rejected'
        
        db.session.add(template)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Template created successfully',
            'template': {
                'id': template.id,
                'name': template.name,
                'status': template.status,
                'meta_template_id': template.meta_template_id,
                'created_at': template.created_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Create template error: {str(e)}")
        return jsonify({'error': 'Failed to create template'}), 500

@templates_api.route('/templates/<int:template_id>', methods=['GET'])
@login_required
def get_template(template_id):
    """Get specific template details"""
    try:
        template = Template.query.filter_by(id=template_id, user_id=current_user.id).first()
        
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        return jsonify({
            'success': True,
            'template': {
                'id': template.id,
                'name': template.name,
                'language': template.language,
                'content': template.content,
                'status': template.status,
                'category': template.category,
                'header_type': template.header_type,
                'header_text': template.header_text,
                'header_image_url': template.header_image_url,
                'footer_text': template.footer_text,
                'buttons_json': template.buttons_json,
                'meta_template_id': template.meta_template_id,
                'created_at': template.created_at.isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Get template error: {str(e)}")
        return jsonify({'error': 'Failed to load template'}), 500

@templates_api.route('/templates/<int:template_id>', methods=['DELETE'])
@login_required
def delete_template(template_id):
    """Delete a template"""
    try:
        template = Template.query.filter_by(id=template_id, user_id=current_user.id).first()
        
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        db.session.delete(template)
        db.session.commit()
        
        logger.info(f"🗑️ Template deleted: {template.name} by user {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Template deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Delete template error: {str(e)}")
        return jsonify({'error': 'Failed to delete template'}), 500