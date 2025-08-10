from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.models.models import db, Role, AreaOfResponsibility, Skill, Shift
from src.utils.decorators import permission_required, role_required
from datetime import time
import json

admin_bp = Blueprint('admin', __name__)

# Roles Management
@admin_bp.route('/roles', methods=['GET'])
@jwt_required()
def get_roles():
    """Get all roles"""
    try:
        roles = Role.query.all()
        return jsonify({
            'roles': [role.to_dict() for role in roles],
            'total': len(roles)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/roles', methods=['POST'])
@permission_required('manage_roles')
def create_role():
    """Create a new role"""
    try:
        data = request.get_json()
        
        if 'name' not in data:
            return jsonify({'error': 'Role name is required'}), 400
        
        # Check if role already exists
        existing_role = Role.query.filter_by(name=data['name']).first()
        if existing_role:
            return jsonify({'error': 'Role with this name already exists'}), 400
        
        role = Role(
            name=data['name'],
            permissions=json.dumps(data.get('permissions', {}))
        )
        
        db.session.add(role)
        db.session.commit()
        
        return jsonify({
            'message': 'Role created successfully',
            'role': role.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/roles/<int:role_id>', methods=['PUT'])
@permission_required('manage_roles')
def update_role(role_id):
    """Update a role"""
    try:
        role = Role.query.get(role_id)
        if not role:
            return jsonify({'error': 'Role not found'}), 404
        
        data = request.get_json()
        
        if 'name' in data:
            # Check if another role has this name
            existing_role = Role.query.filter(Role.name == data['name'], Role.id != role_id).first()
            if existing_role:
                return jsonify({'error': 'Role with this name already exists'}), 400
            role.name = data['name']
        
        if 'permissions' in data:
            role.permissions = json.dumps(data['permissions'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Role updated successfully',
            'role': role.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/roles/<int:role_id>', methods=['DELETE'])
@permission_required('manage_roles')
def delete_role(role_id):
    """Delete a role"""
    try:
        role = Role.query.get(role_id)
        if not role:
            return jsonify({'error': 'Role not found'}), 404
        
        # Check if role is in use
        if role.users:
            return jsonify({'error': 'Cannot delete role that is assigned to users'}), 400
        
        db.session.delete(role)
        db.session.commit()
        
        return jsonify({'message': 'Role deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Areas of Responsibility Management
@admin_bp.route('/areas', methods=['GET'])
@jwt_required()
def get_areas():
    """Get all areas of responsibility"""
    try:
        areas = AreaOfResponsibility.query.all()
        return jsonify({
            'areas': [area.to_dict() for area in areas],
            'total': len(areas)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/areas', methods=['POST'])
@permission_required('manage_areas')
def create_area():
    """Create a new area of responsibility"""
    try:
        data = request.get_json()
        
        if 'name' not in data:
            return jsonify({'error': 'Area name is required'}), 400
        
        # Check if area already exists
        existing_area = AreaOfResponsibility.query.filter_by(name=data['name']).first()
        if existing_area:
            return jsonify({'error': 'Area with this name already exists'}), 400
        
        area = AreaOfResponsibility(
            name=data['name'],
            description=data.get('description', '')
        )
        
        db.session.add(area)
        db.session.commit()
        
        return jsonify({
            'message': 'Area created successfully',
            'area': area.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/areas/<int:area_id>', methods=['PUT'])
@permission_required('manage_areas')
def update_area(area_id):
    """Update an area of responsibility"""
    try:
        area = AreaOfResponsibility.query.get(area_id)
        if not area:
            return jsonify({'error': 'Area not found'}), 404
        
        data = request.get_json()
        
        if 'name' in data:
            # Check if another area has this name
            existing_area = AreaOfResponsibility.query.filter(
                AreaOfResponsibility.name == data['name'], 
                AreaOfResponsibility.id != area_id
            ).first()
            if existing_area:
                return jsonify({'error': 'Area with this name already exists'}), 400
            area.name = data['name']
        
        if 'description' in data:
            area.description = data['description']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Area updated successfully',
            'area': area.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/areas/<int:area_id>', methods=['DELETE'])
@permission_required('manage_areas')
def delete_area(area_id):
    """Delete an area of responsibility"""
    try:
        area = AreaOfResponsibility.query.get(area_id)
        if not area:
            return jsonify({'error': 'Area not found'}), 404
        
        # Check if area is in use
        if area.users:
            return jsonify({'error': 'Cannot delete area that is assigned to users'}), 400
        
        db.session.delete(area)
        db.session.commit()
        
        return jsonify({'message': 'Area deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Skills Management
@admin_bp.route('/skills', methods=['GET'])
@jwt_required()
def get_skills():
    """Get all skills"""
    try:
        skills = Skill.query.all()
        return jsonify({
            'skills': [skill.to_dict() for skill in skills],
            'total': len(skills)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/skills', methods=['POST'])
@permission_required('manage_skills')
def create_skill():
    """Create a new skill"""
    try:
        data = request.get_json()
        
        if 'name' not in data:
            return jsonify({'error': 'Skill name is required'}), 400
        
        # Check if skill already exists
        existing_skill = Skill.query.filter_by(name=data['name']).first()
        if existing_skill:
            return jsonify({'error': 'Skill with this name already exists'}), 400
        
        skill = Skill(
            name=data['name'],
            description=data.get('description', '')
        )
        
        db.session.add(skill)
        db.session.commit()
        
        return jsonify({
            'message': 'Skill created successfully',
            'skill': skill.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/skills/<int:skill_id>', methods=['PUT'])
@permission_required('manage_skills')
def update_skill(skill_id):
    """Update a skill"""
    try:
        skill = Skill.query.get(skill_id)
        if not skill:
            return jsonify({'error': 'Skill not found'}), 404
        
        data = request.get_json()
        
        if 'name' in data:
            # Check if another skill has this name
            existing_skill = Skill.query.filter(
                Skill.name == data['name'], 
                Skill.id != skill_id
            ).first()
            if existing_skill:
                return jsonify({'error': 'Skill with this name already exists'}), 400
            skill.name = data['name']
        
        if 'description' in data:
            skill.description = data['description']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Skill updated successfully',
            'skill': skill.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/skills/<int:skill_id>', methods=['DELETE'])
@permission_required('manage_skills')
def delete_skill(skill_id):
    """Delete a skill"""
    try:
        skill = Skill.query.get(skill_id)
        if not skill:
            return jsonify({'error': 'Skill not found'}), 404
        
        # Check if skill is in use
        if skill.employees:
            return jsonify({'error': 'Cannot delete skill that is assigned to employees'}), 400
        
        db.session.delete(skill)
        db.session.commit()
        
        return jsonify({'message': 'Skill deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Shifts Management
@admin_bp.route('/shifts', methods=['GET'])
@jwt_required()
def get_shifts():
    """Get all shift types"""
    try:
        shifts = Shift.query.all()
        return jsonify({
            'shifts': [shift.to_dict() for shift in shifts],
            'total': len(shifts)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/shifts', methods=['POST'])
@permission_required('manage_shifts')
def create_shift():
    """Create a new shift type"""
    try:
        data = request.get_json()
        
        required_fields = ['name', 'start_time', 'end_time', 'hours']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if shift already exists
        existing_shift = Shift.query.filter_by(name=data['name']).first()
        if existing_shift:
            return jsonify({'error': 'Shift with this name already exists'}), 400
        
        # Parse time strings
        try:
            start_time = time.fromisoformat(data['start_time'])
            end_time = time.fromisoformat(data['end_time'])
        except ValueError:
            return jsonify({'error': 'Invalid time format. Use HH:MM'}), 400
        
        shift = Shift(
            name=data['name'],
            start_time=start_time,
            end_time=end_time,
            hours=data['hours'],
            description=data.get('description', ''),
            color=data.get('color', '#3498db')
        )
        
        db.session.add(shift)
        db.session.commit()
        
        return jsonify({
            'message': 'Shift created successfully',
            'shift': shift.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/shifts/<int:shift_id>', methods=['PUT'])
@permission_required('manage_shifts')
def update_shift(shift_id):
    """Update a shift type"""
    try:
        shift = Shift.query.get(shift_id)
        if not shift:
            return jsonify({'error': 'Shift not found'}), 404
        
        data = request.get_json()
        
        if 'name' in data:
            # Check if another shift has this name
            existing_shift = Shift.query.filter(
                Shift.name == data['name'], 
                Shift.id != shift_id
            ).first()
            if existing_shift:
                return jsonify({'error': 'Shift with this name already exists'}), 400
            shift.name = data['name']
        
        if 'start_time' in data:
            try:
                shift.start_time = time.fromisoformat(data['start_time'])
            except ValueError:
                return jsonify({'error': 'Invalid start_time format. Use HH:MM'}), 400
        
        if 'end_time' in data:
            try:
                shift.end_time = time.fromisoformat(data['end_time'])
            except ValueError:
                return jsonify({'error': 'Invalid end_time format. Use HH:MM'}), 400
        
        if 'hours' in data:
            shift.hours = data['hours']
        
        if 'description' in data:
            shift.description = data['description']
        
        if 'color' in data:
            shift.color = data['color']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Shift updated successfully',
            'shift': shift.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/shifts/<int:shift_id>', methods=['DELETE'])
@permission_required('manage_shifts')
def delete_shift(shift_id):
    """Delete a shift type"""
    try:
        shift = Shift.query.get(shift_id)
        if not shift:
            return jsonify({'error': 'Shift not found'}), 404
        
        # Check if shift is in use
        if shift.shift_rosters:
            return jsonify({'error': 'Cannot delete shift that is used in rosters'}), 400
        
        db.session.delete(shift)
        db.session.commit()
        
        return jsonify({'message': 'Shift deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

