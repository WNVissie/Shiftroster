from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.models.models import db, User, Role, AreaOfResponsibility, Skill
from src.utils.decorators import permission_required, get_current_user
from datetime import datetime

employees_bp = Blueprint('employees', __name__)

@employees_bp.route('/employees', methods=['GET'])
@jwt_required()
def get_employees():
    """Get all employees with optional filtering"""
    try:
        current_user = get_current_user()
        
        # Check permissions
        if current_user.role_ref.name not in ['Admin', 'Manager']:
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        # Get query parameters
        role_id = request.args.get('role_id', type=int)
        area_id = request.args.get('area_id', type=int)
        skill_id = request.args.get('skill_id', type=int)
        search = request.args.get('search', '')
        
        # Build query
        query = User.query
        
        if role_id:
            query = query.filter(User.role_id == role_id)
        
        if area_id:
            query = query.filter(User.area_of_responsibility_id == area_id)
        
        if skill_id:
            query = query.join(User.skills).filter(Skill.id == skill_id)
        
        if search:
            search_filter = f'%{search}%'
            query = query.filter(
                (User.name.ilike(search_filter)) |
                (User.surname.ilike(search_filter)) |
                (User.email.ilike(search_filter)) |
                (User.employee_id.ilike(search_filter))
            )
        
        employees = query.all()
        
        return jsonify({
            'employees': [emp.to_dict() for emp in employees],
            'total': len(employees)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@employees_bp.route('/employees', methods=['POST'])
@permission_required('manage_employees')
def create_employee():
    """Create a new employee"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['google_id', 'email', 'name', 'surname', 'role_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if user already exists
        existing_user = User.query.filter(
            (User.google_id == data['google_id']) | 
            (User.email == data['email'])
        ).first()
        
        if existing_user:
            return jsonify({'error': 'User with this Google ID or email already exists'}), 400
        
        # Validate role exists
        role = Role.query.get(data['role_id'])
        if not role:
            return jsonify({'error': 'Invalid role ID'}), 400
        
        # Validate area if provided
        if data.get('area_of_responsibility_id'):
            area = AreaOfResponsibility.query.get(data['area_of_responsibility_id'])
            if not area:
                return jsonify({'error': 'Invalid area of responsibility ID'}), 400
        
        # Create new employee
        employee = User(
            google_id=data['google_id'],
            email=data['email'],
            name=data['name'],
            surname=data['surname'],
            employee_id=data.get('employee_id'),
            contact_no=data.get('contact_no'),
            role_id=data['role_id'],
            area_of_responsibility_id=data.get('area_of_responsibility_id')
        )
        
        db.session.add(employee)
        db.session.commit()
        
        return jsonify({
            'message': 'Employee created successfully',
            'employee': employee.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@employees_bp.route('/employees/<int:employee_id>', methods=['GET'])
@jwt_required()
def get_employee(employee_id):
    """Get specific employee details"""
    try:
        current_user = get_current_user()
        
        # Check permissions - users can view their own profile
        if current_user.role_ref.name not in ['Admin', 'Manager'] and current_user.id != employee_id:
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        employee = User.query.get(employee_id)
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
        
        return jsonify({'employee': employee.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@employees_bp.route('/employees/<int:employee_id>', methods=['PUT'])
@jwt_required()
def update_employee(employee_id):
    """Update employee details"""
    try:
        current_user = get_current_user()
        
        # Check permissions - users can update their own profile (limited fields)
        employee = User.query.get(employee_id)
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
        
        data = request.get_json()
        
        # Admin can update all fields
        if current_user.role_ref.name == 'Admin':
            allowed_fields = ['email', 'name', 'surname', 'employee_id', 'contact_no', 'role_id', 'area_of_responsibility_id']
        # Users can only update their own contact info
        elif current_user.id == employee_id:
            allowed_fields = ['contact_no']
        else:
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        # Update allowed fields
        for field in allowed_fields:
            if field in data:
                if field == 'role_id' and data[field]:
                    role = Role.query.get(data[field])
                    if not role:
                        return jsonify({'error': 'Invalid role ID'}), 400
                
                if field == 'area_of_responsibility_id' and data[field]:
                    area = AreaOfResponsibility.query.get(data[field])
                    if not area:
                        return jsonify({'error': 'Invalid area of responsibility ID'}), 400
                
                setattr(employee, field, data[field])
        
        employee.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Employee updated successfully',
            'employee': employee.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@employees_bp.route('/employees/<int:employee_id>', methods=['DELETE'])
@permission_required('manage_employees')
def delete_employee(employee_id):
    """Delete an employee"""
    try:
        employee = User.query.get(employee_id)
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
        
        # Check if employee has associated records
        if employee.shift_rosters or employee.timesheets:
            return jsonify({'error': 'Cannot delete employee with existing shift rosters or timesheets'}), 400
        
        db.session.delete(employee)
        db.session.commit()
        
        return jsonify({'message': 'Employee deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@employees_bp.route('/employees/<int:employee_id>/skills', methods=['POST'])
@permission_required('manage_employees')
def add_employee_skill(employee_id):
    """Add skill to employee"""
    try:
        employee = User.query.get(employee_id)
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
        
        data = request.get_json()
        skill_id = data.get('skill_id')
        
        if not skill_id:
            return jsonify({'error': 'skill_id is required'}), 400
        
        skill = Skill.query.get(skill_id)
        if not skill:
            return jsonify({'error': 'Skill not found'}), 404
        
        if skill in employee.skills:
            return jsonify({'error': 'Employee already has this skill'}), 400
        
        employee.skills.append(skill)
        db.session.commit()
        
        return jsonify({
            'message': 'Skill added to employee successfully',
            'employee': employee.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@employees_bp.route('/employees/<int:employee_id>/skills/<int:skill_id>', methods=['DELETE'])
@permission_required('manage_employees')
def remove_employee_skill(employee_id, skill_id):
    """Remove skill from employee"""
    try:
        employee = User.query.get(employee_id)
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
        
        skill = Skill.query.get(skill_id)
        if not skill:
            return jsonify({'error': 'Skill not found'}), 404
        
        if skill not in employee.skills:
            return jsonify({'error': 'Employee does not have this skill'}), 400
        
        employee.skills.remove(skill)
        db.session.commit()
        
        return jsonify({
            'message': 'Skill removed from employee successfully',
            'employee': employee.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

