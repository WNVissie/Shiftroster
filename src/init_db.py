import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask
from src.models.models import db, Role, AreaOfResponsibility, Skill, User, Shift, ShiftRoster, Timesheet
from src.config import config
from datetime import datetime, date, time
import json

def create_app():
    app = Flask(__name__)
    app.config.from_object(config['development'])
    db.init_app(app)
    return app

def init_database():
    app = create_app()
    
    with app.app_context():
        # Drop all tables and recreate
        db.drop_all()
        db.create_all()
        
        # Create default roles
        roles_data = [
            {
                'name': 'Admin',
                'permissions': json.dumps({
                    'manage_employees': True,
                    'manage_roles': True,
                    'manage_shifts': True,
                    'manage_areas': True,
                    'manage_skills': True,
                    'view_all_rosters': True,
                    'approve_rosters': True,
                    'approve_timesheets': True,
                    'view_analytics': True,
                    'export_data': True
                })
            },
            {
                'name': 'Manager',
                'permissions': json.dumps({
                    'view_team_rosters': True,
                    'approve_rosters': True,
                    'approve_timesheets': True,
                    'view_analytics': True,
                    'export_data': True
                })
            },
            {
                'name': 'Employee',
                'permissions': json.dumps({
                    'view_own_roster': True,
                    'view_own_timesheet': True
                })
            },
            {
                'name': 'Guest',
                'permissions': json.dumps({
                    'view_public_info': True
                })
            }
        ]
        
        for role_data in roles_data:
            role = Role(**role_data)
            db.session.add(role)
        
        # Create areas of responsibility
        areas_data = [
            {'name': 'Front Desk', 'description': 'Customer service and reception'},
            {'name': 'Kitchen', 'description': 'Food preparation and cooking'},
            {'name': 'Housekeeping', 'description': 'Cleaning and maintenance'},
            {'name': 'Security', 'description': 'Safety and security monitoring'},
            {'name': 'Management', 'description': 'Administrative and supervisory tasks'},
            {'name': 'IT Support', 'description': 'Technical support and maintenance'},
            {'name': 'Sales', 'description': 'Sales and customer relations'},
            {'name': 'Warehouse', 'description': 'Inventory and logistics'}
        ]
        
        for area_data in areas_data:
            area = AreaOfResponsibility(**area_data)
            db.session.add(area)
        
        # Create skills
        skills_data = [
            {'name': 'Customer Service', 'description': 'Excellent customer interaction skills'},
            {'name': 'Cooking', 'description': 'Food preparation and culinary skills'},
            {'name': 'Cleaning', 'description': 'Professional cleaning techniques'},
            {'name': 'Security Monitoring', 'description': 'Security systems and protocols'},
            {'name': 'Leadership', 'description': 'Team management and leadership'},
            {'name': 'Computer Skills', 'description': 'Basic to advanced computer proficiency'},
            {'name': 'Sales Techniques', 'description': 'Sales strategies and customer persuasion'},
            {'name': 'Inventory Management', 'description': 'Stock control and logistics'},
            {'name': 'First Aid', 'description': 'Basic medical emergency response'},
            {'name': 'Communication', 'description': 'Effective verbal and written communication'}
        ]
        
        for skill_data in skills_data:
            skill = Skill(**skill_data)
            db.session.add(skill)
        
        # Create shift types
        shifts_data = [
            {
                'name': 'Morning Shift',
                'start_time': time(6, 0),
                'end_time': time(14, 0),
                'hours': 8.0,
                'description': 'Early morning shift',
                'color': '#3498db'
            },
            {
                'name': 'Afternoon Shift',
                'start_time': time(14, 0),
                'end_time': time(22, 0),
                'hours': 8.0,
                'description': 'Afternoon to evening shift',
                'color': '#e74c3c'
            },
            {
                'name': 'Night Shift',
                'start_time': time(22, 0),
                'end_time': time(6, 0),
                'hours': 8.0,
                'description': 'Overnight shift',
                'color': '#9b59b6'
            },
            {
                'name': 'Part Time Morning',
                'start_time': time(9, 0),
                'end_time': time(13, 0),
                'hours': 4.0,
                'description': 'Part-time morning shift',
                'color': '#2ecc71'
            },
            {
                'name': 'Part Time Evening',
                'start_time': time(17, 0),
                'end_time': time(21, 0),
                'hours': 4.0,
                'description': 'Part-time evening shift',
                'color': '#f39c12'
            }
        ]
        
        for shift_data in shifts_data:
            shift = Shift(**shift_data)
            db.session.add(shift)
        
        # Commit all the reference data first
        db.session.commit()
        
        # Create sample users (employees)
        admin_role = Role.query.filter_by(name='Admin').first()
        manager_role = Role.query.filter_by(name='Manager').first()
        employee_role = Role.query.filter_by(name='Employee').first()
        
        front_desk_area = AreaOfResponsibility.query.filter_by(name='Front Desk').first()
        kitchen_area = AreaOfResponsibility.query.filter_by(name='Kitchen').first()
        management_area = AreaOfResponsibility.query.filter_by(name='Management').first()
        
        users_data = [
            {
                'google_id': 'admin123',
                'email': 'admin@company.com',
                'name': 'John',
                'surname': 'Admin',
                'employee_id': 'EMP001',
                'contact_no': '+1234567890',
                'role_id': admin_role.id,
                'area_of_responsibility_id': management_area.id
            },
            {
                'google_id': 'manager123',
                'email': 'manager@company.com',
                'name': 'Jane',
                'surname': 'Manager',
                'employee_id': 'EMP002',
                'contact_no': '+1234567891',
                'role_id': manager_role.id,
                'area_of_responsibility_id': management_area.id
            },
            {
                'google_id': 'employee123',
                'email': 'employee1@company.com',
                'name': 'Bob',
                'surname': 'Employee',
                'employee_id': 'EMP003',
                'contact_no': '+1234567892',
                'role_id': employee_role.id,
                'area_of_responsibility_id': front_desk_area.id
            },
            {
                'google_id': 'employee456',
                'email': 'employee2@company.com',
                'name': 'Alice',
                'surname': 'Cook',
                'employee_id': 'EMP004',
                'contact_no': '+1234567893',
                'role_id': employee_role.id,
                'area_of_responsibility_id': kitchen_area.id
            }
        ]
        
        for user_data in users_data:
            user = User(**user_data)
            db.session.add(user)
        
        db.session.commit()
        
        # Add skills to users
        customer_service_skill = Skill.query.filter_by(name='Customer Service').first()
        cooking_skill = Skill.query.filter_by(name='Cooking').first()
        leadership_skill = Skill.query.filter_by(name='Leadership').first()
        
        bob = User.query.filter_by(employee_id='EMP003').first()
        alice = User.query.filter_by(employee_id='EMP004').first()
        jane = User.query.filter_by(employee_id='EMP002').first()
        
        if bob and customer_service_skill:
            bob.skills.append(customer_service_skill)
        if alice and cooking_skill:
            alice.skills.append(cooking_skill)
        if jane and leadership_skill:
            jane.skills.append(leadership_skill)
        
        db.session.commit()
        
        print("Database initialized successfully with sample data!")
        print("Sample users created:")
        print("- Admin: admin@company.com (EMP001)")
        print("- Manager: manager@company.com (EMP002)")
        print("- Employee 1: employee1@company.com (EMP003)")
        print("- Employee 2: employee2@company.com (EMP004)")

if __name__ == '__main__':
    init_database()

