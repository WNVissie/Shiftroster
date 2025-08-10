from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.models.models import db, ShiftRoster, User, Shift, Timesheet
from src.utils.decorators import permission_required, get_current_user
from datetime import datetime, date
from sqlalchemy import and_, or_

roster_bp = Blueprint('roster', __name__)

@roster_bp.route('/roster', methods=['GET'])
@jwt_required()
def get_roster():
    """Get shift roster with optional filtering"""
    try:
        current_user = get_current_user()
        
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        employee_id = request.args.get('employee_id', type=int)
        shift_id = request.args.get('shift_id', type=int)
        status = request.args.get('status')
        
        # Build query based on user role
        if current_user.role_ref.name == 'Admin':
            query = ShiftRoster.query
        elif current_user.role_ref.name == 'Manager':
            # Managers can see all rosters (for approval)
            query = ShiftRoster.query
        else:
            # Employees can only see their own rosters
            query = ShiftRoster.query.filter(ShiftRoster.employee_id == current_user.id)
        
        # Apply filters
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(ShiftRoster.date >= start_date_obj)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(ShiftRoster.date <= end_date_obj)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
        
        if employee_id:
            query = query.filter(ShiftRoster.employee_id == employee_id)
        
        if shift_id:
            query = query.filter(ShiftRoster.shift_id == shift_id)
        
        if status:
            query = query.filter(ShiftRoster.status == status)
        
        # Order by date and shift start time
        roster_entries = query.join(Shift).order_by(ShiftRoster.date, Shift.start_time).all()
        
        return jsonify({
            'roster': [entry.to_dict() for entry in roster_entries],
            'total': len(roster_entries)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@roster_bp.route('/roster', methods=['POST'])
@jwt_required()
def create_roster_entry():
    """Create a new roster entry"""
    try:
        current_user = get_current_user()
        
        # Check permissions
        if current_user.role_ref.name not in ['Admin', 'Manager']:
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['employee_id', 'shift_id', 'date', 'hours']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate employee exists
        employee = User.query.get(data['employee_id'])
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
        
        # Validate shift exists
        shift = Shift.query.get(data['shift_id'])
        if not shift:
            return jsonify({'error': 'Shift not found'}), 404
        
        # Parse date
        try:
            roster_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Check for existing roster entry
        existing_entry = ShiftRoster.query.filter(
            and_(
                ShiftRoster.employee_id == data['employee_id'],
                ShiftRoster.date == roster_date
            )
        ).first()
        
        if existing_entry:
            return jsonify({'error': 'Employee already has a shift scheduled for this date'}), 400
        
        # Create roster entry
        roster_entry = ShiftRoster(
            employee_id=data['employee_id'],
            shift_id=data['shift_id'],
            date=roster_date,
            hours=data['hours'],
            notes=data.get('notes', '')
        )
        
        db.session.add(roster_entry)
        db.session.commit()
        
        return jsonify({
            'message': 'Roster entry created successfully',
            'roster_entry': roster_entry.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@roster_bp.route('/roster/<int:roster_id>', methods=['PUT'])
@jwt_required()
def update_roster_entry(roster_id):
    """Update a roster entry"""
    try:
        current_user = get_current_user()
        
        # Check permissions
        if current_user.role_ref.name not in ['Admin', 'Manager']:
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        roster_entry = ShiftRoster.query.get(roster_id)
        if not roster_entry:
            return jsonify({'error': 'Roster entry not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'employee_id' in data:
            employee = User.query.get(data['employee_id'])
            if not employee:
                return jsonify({'error': 'Employee not found'}), 404
            roster_entry.employee_id = data['employee_id']
        
        if 'shift_id' in data:
            shift = Shift.query.get(data['shift_id'])
            if not shift:
                return jsonify({'error': 'Shift not found'}), 404
            roster_entry.shift_id = data['shift_id']
        
        if 'date' in data:
            try:
                roster_entry.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        if 'hours' in data:
            roster_entry.hours = data['hours']
        
        if 'notes' in data:
            roster_entry.notes = data['notes']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Roster entry updated successfully',
            'roster_entry': roster_entry.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@roster_bp.route('/roster/<int:roster_id>', methods=['DELETE'])
@jwt_required()
def delete_roster_entry(roster_id):
    """Delete a roster entry"""
    try:
        current_user = get_current_user()
        
        # Check permissions
        if current_user.role_ref.name not in ['Admin', 'Manager']:
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        roster_entry = ShiftRoster.query.get(roster_id)
        if not roster_entry:
            return jsonify({'error': 'Roster entry not found'}), 404
        
        # Check if there are associated timesheets
        if roster_entry.timesheets:
            return jsonify({'error': 'Cannot delete roster entry with associated timesheets'}), 400
        
        db.session.delete(roster_entry)
        db.session.commit()
        
        return jsonify({'message': 'Roster entry deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@roster_bp.route('/roster/<int:roster_id>/approve', methods=['POST'])
@jwt_required()
def approve_roster_entry(roster_id):
    """Approve or reject a roster entry"""
    try:
        current_user = get_current_user()
        
        # Check permissions
        if current_user.role_ref.name not in ['Admin', 'Manager']:
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        roster_entry = ShiftRoster.query.get(roster_id)
        if not roster_entry:
            return jsonify({'error': 'Roster entry not found'}), 404
        
        data = request.get_json()
        action = data.get('action')  # 'approve' or 'reject'
        
        if action not in ['approve', 'reject']:
            return jsonify({'error': 'Action must be either "approve" or "reject"'}), 400
        
        roster_entry.status = 'approved' if action == 'approve' else 'rejected'
        roster_entry.approved_by = current_user.id
        roster_entry.approved_at = datetime.utcnow()
        
        if 'notes' in data:
            roster_entry.notes = data['notes']
        
        db.session.commit()
        
        return jsonify({
            'message': f'Roster entry {action}d successfully',
            'roster_entry': roster_entry.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@roster_bp.route('/roster/bulk', methods=['POST'])
@jwt_required()
def create_bulk_roster():
    """Create multiple roster entries at once"""
    try:
        current_user = get_current_user()
        
        # Check permissions
        if current_user.role_ref.name not in ['Admin', 'Manager']:
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        entries = data.get('entries', [])
        
        if not entries:
            return jsonify({'error': 'No entries provided'}), 400
        
        created_entries = []
        errors = []
        
        for i, entry_data in enumerate(entries):
            try:
                # Validate required fields
                required_fields = ['employee_id', 'shift_id', 'date', 'hours']
                for field in required_fields:
                    if field not in entry_data:
                        errors.append(f'Entry {i+1}: {field} is required')
                        continue
                
                # Validate employee and shift
                employee = User.query.get(entry_data['employee_id'])
                if not employee:
                    errors.append(f'Entry {i+1}: Employee not found')
                    continue
                
                shift = Shift.query.get(entry_data['shift_id'])
                if not shift:
                    errors.append(f'Entry {i+1}: Shift not found')
                    continue
                
                # Parse date
                try:
                    roster_date = datetime.strptime(entry_data['date'], '%Y-%m-%d').date()
                except ValueError:
                    errors.append(f'Entry {i+1}: Invalid date format')
                    continue
                
                # Check for existing entry
                existing_entry = ShiftRoster.query.filter(
                    and_(
                        ShiftRoster.employee_id == entry_data['employee_id'],
                        ShiftRoster.date == roster_date
                    )
                ).first()
                
                if existing_entry:
                    errors.append(f'Entry {i+1}: Employee already scheduled for this date')
                    continue
                
                # Create roster entry
                roster_entry = ShiftRoster(
                    employee_id=entry_data['employee_id'],
                    shift_id=entry_data['shift_id'],
                    date=roster_date,
                    hours=entry_data['hours'],
                    notes=entry_data.get('notes', '')
                )
                
                db.session.add(roster_entry)
                created_entries.append(roster_entry)
                
            except Exception as e:
                errors.append(f'Entry {i+1}: {str(e)}')
        
        if errors:
            db.session.rollback()
            return jsonify({
                'error': 'Some entries could not be created',
                'errors': errors
            }), 400
        
        db.session.commit()
        
        return jsonify({
            'message': f'{len(created_entries)} roster entries created successfully',
            'entries': [entry.to_dict() for entry in created_entries]
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

