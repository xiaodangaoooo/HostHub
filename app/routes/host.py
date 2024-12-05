from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.utils.db_utils import (
    get_host_listings,
    create_location,
    create_listing,
    get_listing_details,
    update_listing,
    update_location,
    delete_listing
)
from app.utils.db import get_db

host_bp = Blueprint('host', __name__)

@host_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role_type != 'host':
        flash('Access denied. Host privileges required.')
        return redirect(url_for('main.index'))
    
    listings, active_count, applications_count = get_host_listings(current_user.id)
    return render_template('host/dashboard.html',
                         listings=listings,
                         active_listings=active_count,
                         applications_count=applications_count)

@host_bp.route('/listings/create', methods=['GET', 'POST'])
@login_required
def create_listing_route():
    if current_user.role_type != 'host':
        flash('Access denied. Host privileges required.')
        return redirect(url_for('main.index'))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Check and create host record if needed
        cursor.execute('SELECT * FROM Host WHERE user_id = %s', (current_user.id,))
        host = cursor.fetchone()
        
        if not host:
            cursor.execute('''
                INSERT INTO Host (user_id, rating)
                VALUES (%s, 0.0)
            ''', (current_user.id,))
            db.commit()
            
        if request.method == 'POST':
            title = request.form.get('title')
            description = request.form.get('description')
            work_hours = request.form.get('work_hours')
            duration = request.form.get('duration')
            work_type = request.form.get('work_type')
            country = request.form.get('country')
            state = request.form.get('state')
            city = request.form.get('city')
            zip_code = request.form.get('zip_code')
            
            if not all([title, description, work_hours, duration, work_type, country, city]):
                flash('Please fill in all required fields.')
                return render_template('host/listing_form.html')
            
            # Create location
            location_id = create_location(country, state, city, zip_code)
            if not location_id:
                flash('Error creating location.')
                return render_template('host/listing_form.html')
            
            # Create listing
            listing_id = create_listing(
                current_user.id,
                location_id,
                title,
                description,
                work_hours,
                duration,
                work_type
            )
            
            if listing_id:
                flash('Listing created successfully!')
                return redirect(url_for('host.dashboard'))
            else:
                flash('Error creating listing.')
                return render_template('host/listing_form.html')
    finally:
        cursor.close()
    
    return render_template('host/listing_form.html')

@host_bp.route('/listings/<int:listing_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_listing(listing_id):
    if current_user.role_type != 'host':
        flash('Access denied. Host privileges required.')
        return redirect(url_for('main.index'))
    
    listing, _ = get_listing_details(listing_id, current_user.id)
    if not listing:
        flash('Listing not found or access denied.', 'error')
        return redirect(url_for('host.dashboard'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        work_hours = request.form.get('work_hours')
        duration = request.form.get('duration')
        work_type = request.form.get('work_type')
        country = request.form.get('country')
        state = request.form.get('state')
        city = request.form.get('city')
        zip_code = request.form.get('zip_code')
        
        if not all([title, description, work_hours, duration, work_type, country, city]):
            flash('Please fill in all required fields.', 'error')
            return render_template('host/listing_form.html', listing=listing)
        
        # Update both location and listing
        if update_location(listing['location_id'], country, state, city, zip_code) and \
           update_listing(listing_id, current_user.id, title, description, work_hours, duration, work_type):
            flash('Listing updated successfully!', 'success')
            return redirect(url_for('host.dashboard'))
        else:
            flash('Error updating listing.', 'error')
            return render_template('host/listing_form.html', listing=listing)
    
    return render_template('host/listing_form.html', listing=listing)

@host_bp.route('/listings/<int:listing_id>/delete', methods=['POST'])
@login_required
def delete_listing_route(listing_id):
    if current_user.role_type != 'host':
        flash('Access denied. Host privileges required.')
        return redirect(url_for('main.index'))
    
    if delete_listing(listing_id, current_user.id):
        flash('Listing deleted successfully!', 'success')
    else:
        flash('Error deleting listing.', 'error')
    
    return redirect(url_for('host.dashboard'))

@host_bp.route('/listings/<int:listing_id>')
@login_required
def view_listing(listing_id):
    if current_user.role_type != 'host':
        flash('Access denied. Host privileges required.')
        return redirect(url_for('main.index'))
    
    listing, applications = get_listing_details(listing_id, current_user.id)
    
    if not listing:
        flash('Listing not found or access denied.')
        return redirect(url_for('host.dashboard'))
    
    return render_template('host/view_listing.html', 
                         listing=listing,
                         applications=applications)