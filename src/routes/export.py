from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.models import User, Employee, Roster, Shift, Role, Area, Skill, Timesheet
from utils.decorators import admin_required, manager_required
import pandas as pd
import io
import csv
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import tempfile
import os

export_bp = Blueprint('export', __name__)

@export_bp.route('/employees/csv', methods=['GET'])
@jwt_required()
@manager_required
def export_employees_csv():
    """Export employees data to CSV format"""
    try:
        employees = Employee.query.all()
        
        # Prepare data for CSV
        data = []
        for emp in employees:
            role_name = emp.role.name if emp.role else ''
            area_name = emp.area.name if emp.area else ''
            skills = ', '.join([skill.name for skill in emp.skills]) if emp.skills else ''
            
            data.append({
                'Employee ID': emp.employee_id,
                'Name': emp.name,
                'Surname': emp.surname,
                'Email': emp.email,
                'Contact Number': emp.contact_number,
                'Role': role_name,
                'Area of Responsibility': area_name,
                'Skills': skills,
                'Hire Date': emp.hire_date.strftime('%Y-%m-%d') if emp.hire_date else '',
                'Status': 'Active' if emp.is_active else 'Inactive'
            })
        
        # Create CSV in memory
        output = io.StringIO()
        if data:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        # Create response
        output.seek(0)
        response_data = output.getvalue()
        output.close()
        
        # Create file-like object for response
        file_obj = io.BytesIO(response_data.encode('utf-8'))
        
        return send_file(
            file_obj,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'employees_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_bp.route('/employees/excel', methods=['GET'])
@jwt_required()
@manager_required
def export_employees_excel():
    """Export employees data to Excel format"""
    try:
        employees = Employee.query.all()
        
        # Prepare data for Excel
        data = []
        for emp in employees:
            role_name = emp.role.name if emp.role else ''
            area_name = emp.area.name if emp.area else ''
            skills = ', '.join([skill.name for skill in emp.skills]) if emp.skills else ''
            
            data.append({
                'Employee ID': emp.employee_id,
                'Name': emp.name,
                'Surname': emp.surname,
                'Email': emp.email,
                'Contact Number': emp.contact_number,
                'Role': role_name,
                'Area of Responsibility': area_name,
                'Skills': skills,
                'Hire Date': emp.hire_date.strftime('%Y-%m-%d') if emp.hire_date else '',
                'Status': 'Active' if emp.is_active else 'Inactive'
            })
        
        # Create Excel file in memory
        df = pd.DataFrame(data)
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Employees', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Employees']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'employees_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_bp.route('/roster/csv', methods=['GET'])
@jwt_required()
@manager_required
def export_roster_csv():
    """Export roster data to CSV format"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = Roster.query
        if start_date:
            query = query.filter(Roster.date >= start_date)
        if end_date:
            query = query.filter(Roster.date <= end_date)
            
        roster_entries = query.all()
        
        # Prepare data for CSV
        data = []
        for entry in roster_entries:
            employee = entry.employee
            shift = entry.shift
            
            data.append({
                'Date': entry.date.strftime('%Y-%m-%d'),
                'Employee ID': employee.employee_id,
                'Employee Name': f"{employee.name} {employee.surname}",
                'Role': employee.role.name if employee.role else '',
                'Area': employee.area.name if employee.area else '',
                'Shift': shift.name,
                'Start Time': shift.start_time,
                'End Time': shift.end_time,
                'Duration (Hours)': shift.duration_hours,
                'Status': entry.status.title(),
                'Approved By': entry.approved_by.name if entry.approved_by else '',
                'Approved At': entry.approved_at.strftime('%Y-%m-%d %H:%M') if entry.approved_at else ''
            })
        
        # Create CSV in memory
        output = io.StringIO()
        if data:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        output.seek(0)
        response_data = output.getvalue()
        output.close()
        
        file_obj = io.BytesIO(response_data.encode('utf-8'))
        
        return send_file(
            file_obj,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'roster_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_bp.route('/roster/excel', methods=['GET'])
@jwt_required()
@manager_required
def export_roster_excel():
    """Export roster data to Excel format"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = Roster.query
        if start_date:
            query = query.filter(Roster.date >= start_date)
        if end_date:
            query = query.filter(Roster.date <= end_date)
            
        roster_entries = query.all()
        
        # Prepare data for Excel
        data = []
        for entry in roster_entries:
            employee = entry.employee
            shift = entry.shift
            
            data.append({
                'Date': entry.date.strftime('%Y-%m-%d'),
                'Employee ID': employee.employee_id,
                'Employee Name': f"{employee.name} {employee.surname}",
                'Role': employee.role.name if employee.role else '',
                'Area': employee.area.name if employee.area else '',
                'Shift': shift.name,
                'Start Time': shift.start_time,
                'End Time': shift.end_time,
                'Duration (Hours)': shift.duration_hours,
                'Status': entry.status.title(),
                'Approved By': entry.approved_by.name if entry.approved_by else '',
                'Approved At': entry.approved_at.strftime('%Y-%m-%d %H:%M') if entry.approved_at else ''
            })
        
        # Create Excel file in memory
        df = pd.DataFrame(data)
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Roster', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Roster']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'roster_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_bp.route('/timesheets/pdf', methods=['GET'])
@jwt_required()
@manager_required
def export_timesheets_pdf():
    """Export timesheets to PDF format"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        employee_id = request.args.get('employee_id')
        
        query = Timesheet.query
        if start_date:
            query = query.filter(Timesheet.date >= start_date)
        if end_date:
            query = query.filter(Timesheet.date <= end_date)
        if employee_id:
            query = query.filter(Timesheet.employee_id == employee_id)
            
        timesheets = query.all()
        
        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        # Content
        story = []
        
        # Title
        title = Paragraph("Timesheet Report", title_style)
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Date range info
        if start_date and end_date:
            date_info = Paragraph(f"Period: {start_date} to {end_date}", styles['Normal'])
            story.append(date_info)
            story.append(Spacer(1, 12))
        
        # Table data
        data = [['Date', 'Employee', 'Shift', 'Hours', 'Status', 'Approved By']]
        
        for timesheet in timesheets:
            employee = timesheet.employee
            shift = timesheet.shift
            approved_by = timesheet.approved_by.name if timesheet.approved_by else 'Pending'
            
            data.append([
                timesheet.date.strftime('%Y-%m-%d'),
                f"{employee.name} {employee.surname}",
                shift.name if shift else 'N/A',
                str(timesheet.hours_worked),
                timesheet.status.title(),
                approved_by
            ])
        
        # Create table
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'timesheets_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_bp.route('/templates/employees', methods=['GET'])
@jwt_required()
@manager_required
def download_employee_template():
    """Download CSV template for employee import"""
    try:
        # Template headers
        headers = [
            'Employee ID',
            'Name',
            'Surname', 
            'Email',
            'Contact Number',
            'Role',
            'Area of Responsibility',
            'Skills (comma-separated)',
            'Hire Date (YYYY-MM-DD)',
            'Status (Active/Inactive)'
        ]
        
        # Sample data
        sample_data = [
            'EMP001',
            'John',
            'Doe',
            'john.doe@company.com',
            '+1234567890',
            'Employee',
            'Kitchen',
            'Food Preparation, Customer Service',
            '2024-01-15',
            'Active'
        ]
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerow(sample_data)  # Include sample row
        
        output.seek(0)
        response_data = output.getvalue()
        output.close()
        
        file_obj = io.BytesIO(response_data.encode('utf-8'))
        
        return send_file(
            file_obj,
            mimetype='text/csv',
            as_attachment=True,
            download_name='employee_import_template.csv'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_bp.route('/analytics/pdf', methods=['GET'])
@jwt_required()
@manager_required
def export_analytics_pdf():
    """Export analytics dashboard to PDF format"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1
        )
        
        # Content
        story = []
        
        # Title
        title = Paragraph("Analytics Dashboard Report", title_style)
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Date range
        if start_date and end_date:
            date_info = Paragraph(f"Report Period: {start_date} to {end_date}", styles['Normal'])
            story.append(date_info)
            story.append(Spacer(1, 20))
        
        # Key Metrics
        story.append(Paragraph("Key Performance Indicators", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Sample metrics (in real app, fetch from database)
        metrics_data = [
            ['Metric', 'Value', 'Change'],
            ['Total Employees', '35', '+2'],
            ['Active Shifts', '197', '+15'],
            ['Approval Rate', '94%', '+2%'],
            ['Utilization Rate', '92%', '+1%']
        ]
        
        metrics_table = Table(metrics_data)
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(metrics_table)
        story.append(Spacer(1, 20))
        
        # Employee Distribution
        story.append(Paragraph("Employee Distribution by Role", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        role_data = [
            ['Role', 'Count', 'Percentage'],
            ['Admin', '2', '6%'],
            ['Manager', '5', '14%'],
            ['Employee', '25', '71%'],
            ['Guest', '3', '9%']
        ]
        
        role_table = Table(role_data)
        role_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(role_table)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'analytics_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

