from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from google.auth.transport import requests
from google.oauth2 import id_token
from src.models.models import db, User, Role
from datetime import datetime
import json

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/auth/google', methods=['POST'])
def google_auth():
    """Authenticate user with Google OAuth token"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'error': 'Token is required'}), 400
        
        # For development, we'll skip actual Google verification
        # In production, uncomment the following lines:
        # try:
        #     idinfo = id_token.verify_oauth2_token(token, requests.Request(), current_app.config['GOOGLE_CLIENT_ID'])
        #     google_id = idinfo['sub']
        #     email = idinfo['email']
        #     name = idinfo.get('given_name', '')
        #     surname = idinfo.get('family_name', '')
        # except ValueError:
        #     return jsonify({'error': 'Invalid token'}), 401
        
        # For development, extract from token payload (mock)
        google_id = data.get('google_id', 'dev_user_123')
        email = data.get('email', 'dev@example.com')
        name = data.get('name', 'Dev')
        surname = data.get('surname', 'User')
        
        # Check if user exists
        user = User.query.filter_by(google_id=google_id).first()
        
        if not user:
            # Create new user with default employee role
            employee_role = Role.query.filter_by(name='Employee').first()
            if not employee_role:
                return jsonify({'error': 'Default role not found'}), 500
            
            user = User(
                google_id=google_id,
                email=email,
                name=name,
                surname=surname,
                role_id=employee_role.id
            )
            db.session.add(user)
            db.session.commit()
        
        # Create JWT tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        new_token = create_access_token(identity=current_user_id)
        return jsonify({'access_token': new_token}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user information"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (client-side token removal)"""
    return jsonify({'message': 'Successfully logged out'}), 200

