from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.models import db, Employee, Role, Area, Skill, employee_skills
from utils.decorators import admin_required, manager_required
import pandas as pd
import csv
import io
from datetime import datetime
from werkzeug.utils import secure_filename
import os

import_bp = Blueprint('import', __name__)

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@import_bp.route('/employees/csv', methods=['POST'])
@jwt_required()
@admin_required
def import_employees_csv():
    """Import employees from CSV file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only CSV and Excel files are allowed'}), 400
        
        # Read file content
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        
        # Validate required columns
        required_columns = ['Employee ID', 'Name', 'Surname', 'Email']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({'error': f'Missing required columns: {", ".join(missing_columns)}'}), 400
        
        # Process each row
        imported_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Check if employee already exists
                existing_employee = Employee.query.filter_by(employee_id=row['Employee ID']).first()
                if existing_employee:
                    errors.append(f"Row {index + 2}: Employee ID {row['Employee ID']} already exists")
                    continue
                
                # Get or create role
                role = None
                if pd.notna(row.get('Role')):
                    role = Role.query.filter_by(name=row['Role']).first()
                    if not role:
                        role = Role(name=row['Role'], description=f"Auto-created role: {row['Role']}")
                        db.session.add(role)
                        db.session.flush()
                
                # Get or create area
                area = None
                if pd.notna(row.get('Area of Responsibility')):
                    area = Area.query.filter_by(name=row['Area of Responsibility']).first()
                    if not area:
                        area = Area(name=row['Area of Responsibility'], description=f"Auto-created area: {row['Area of Responsibility']}")
                        db.session.add(area)
                        db.session.flush()
                
                # Create employee
                employee = Employee(
                    employee_id=row['Employee ID'],
                    name=row['Name'],
                    surname=row['Surname'],
                    email=row['Email'],
                    contact_number=row.get('Contact Number', ''),
                    role_id=role.id if role else None,
                    area_id=area.id if area else None,
                    hire_date=pd.to_datetime(row['Hire Date']).date() if pd.notna(row.get('Hire Date')) else None,
                    is_active=row.get('Status', 'Active').lower() == 'active'
                )
                
                db.session.add(employee)
                db.session.flush()
                
                # Process skills
                if pd.notna(row.get('Skills')):
                    skill_names = [s.strip() for s in str(row['Skills']).split(',')]
                    for skill_name in skill_names:
                        if skill_name:
                            skill = Skill.query.filter_by(name=skill_name).first()
                            if not skill:
                                skill = Skill(name=skill_name, description=f"Auto-created skill: {skill_name}")
                                db.session.add(skill)
                                db.session.flush()
                            
                            # Add skill to employee
                            employee.skills.append(skill)
                
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")
                continue
        
        # Commit all changes
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully imported {imported_count} employees',
            'imported_count': imported_count,
            'errors': errors
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@import_bp.route('/employees/validate', methods=['POST'])
@jwt_required()
@admin_required
def validate_employee_import():
    """Validate employee import file without importing"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only CSV and Excel files are allowed'}), 400
        
        # Read file content
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        
        # Validate structure
        required_columns = ['Employee ID', 'Name', 'Surname', 'Email']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        validation_results = {
            'valid': len(missing_columns) == 0,
            'total_rows': len(df),
            'missing_columns': missing_columns,
            'available_columns': list(df.columns),
            'sample_data': df.head(3).to_dict('records') if len(df) > 0 else [],
            'warnings': []
        }
        
        if validation_results['valid']:
            # Check for duplicate employee IDs in file
            duplicate_ids = df[df.duplicated(['Employee ID'], keep=False)]['Employee ID'].tolist()
            if duplicate_ids:
                validation_results['warnings'].append(f"Duplicate Employee IDs found in file: {', '.join(map(str, set(duplicate_ids)))}")
            
            # Check for existing employee IDs in database
            existing_ids = []
            for emp_id in df['Employee ID']:
                if Employee.query.filter_by(employee_id=emp_id).first():
                    existing_ids.append(emp_id)
            
            if existing_ids:
                validation_results['warnings'].append(f"Employee IDs already exist in database: {', '.join(map(str, existing_ids))}")
            
            # Check email format
            invalid_emails = []
            for index, row in df.iterrows():
                email = row.get('Email', '')
                if email and '@' not in email:



                    invalid_emails.append(f"Row {index + 2}: {email}")
            
            if invalid_emails:
                validation_results['warnings'].append(f"Invalid email formats: {', '.join(invalid_emails[:5])}")
        
        return jsonify(validation_results), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@import_bp.route('/backup/create', methods=['POST'])
@jwt_required()
@admin_required
def create_backup():
    """Create a backup of all system data"""
    try:
        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'employees': [],
            'roles': [],
            'areas': [],
            'skills': [],
            'shifts': []
        }
        
        # Export employees
        employees = Employee.query.all()
        for emp in employees:
            backup_data['employees'].append({
                'employee_id': emp.employee_id,
                'name': emp.name,
                'surname': emp.surname,
                'email': emp.email,
                'contact_number': emp.contact_number,
                'role': emp.role.name if emp.role else None,
                'area': emp.area.name if emp.area else None,
                'skills': [skill.name for skill in emp.skills],
                'hire_date': emp.hire_date.isoformat() if emp.hire_date else None,
                'is_active': emp.is_active
            })
        
        # Export roles
        roles = Role.query.all()
        for role in roles:
            backup_data['roles'].append({
                'name': role.name,
                'description': role.description
            })
        
        # Export areas
        areas = Area.query.all()
        for area in areas:
            backup_data['areas'].append({
                'name': area.name,
                'description': area.description
            })
        
        # Export skills
        skills = Skill.query.all()
        for skill in skills:
            backup_data['skills'].append({
                'name': skill.name,
                'description': skill.description,
                'category': skill.category
            })
        
        # Export shifts
        from models.models import Shift
        shifts = Shift.query.all()
        for shift in shifts:
            backup_data['shifts'].append({
                'name': shift.name,
                'start_time': shift.start_time,
                'end_time': shift.end_time,
                'duration_hours': shift.duration_hours
            })
        
        # Create JSON file in memory
        import json
        backup_json = json.dumps(backup_data, indent=2)
        file_obj = io.BytesIO(backup_json.encode('utf-8'))
        
        return send_file(
            file_obj,
            mimetype='application/json',
            as_attachment=True,
            download_name=f'system_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@import_bp.route('/backup/restore', methods=['POST'])
@jwt_required()
@admin_required
def restore_backup():
    """Restore system data from backup file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No backup file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.json'):
            return jsonify({'error': 'Invalid file

