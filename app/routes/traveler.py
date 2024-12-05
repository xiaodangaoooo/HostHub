from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.utils.db import get_db
from app.utils.db_utils import get_recent_listings

traveler_bp = Blueprint('traveler', __name__)

@traveler_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role_type != 'traveler':
        flash('Access denied. Traveler privileges required.')
        return redirect(url_for('main.index'))
    
    # Get recent listings
    recent_listings = get_recent_listings(5)
    
    # Get user's applications if you have that functionality
    applications = []  # Replace with actual application data
    
    return render_template('traveler/dashboard.html',
                         recent_listings=recent_listings,
                         applications=applications)

@traveler_bp.route('/search')
def search_listings():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Get search parameters
        location = request.args.get('location', '')
        work_type = request.args.get('work_type', '')
        duration = request.args.get('duration', '')
        
        # Base query
        query = '''
            SELECT l.*, loc.city, loc.country, 
                   u.first_name, u.last_name,
                   h.rating as host_rating
            FROM Listing l
            JOIN Location loc ON l.location_id = loc.location_id
            JOIN Host h ON l.host_id = h.user_id
            JOIN User u ON h.user_id = u.user_id
            WHERE l.status = 'active'
        '''
        params = []
        
        # Add search filters
        if location:
            query += ''' AND (loc.city LIKE %s OR loc.country LIKE %s)'''
            params.extend([f'%{location}%', f'%{location}%'])
            
        if work_type:
            query += ''' AND l.work_type LIKE %s'''
            params.append(f'%{work_type}%')
            
        if duration:
            query += ''' AND l.duration_day <= %s'''
            params.append(duration)
            
        cursor.execute(query, params)
        listings = cursor.fetchall()
        
        return render_template('traveler/search.html', listings=listings)
    finally:
        cursor.close()

@traveler_bp.route('/listing/<int:listing_id>')
def view_listing(listing_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Get listing details
        cursor.execute('''
            SELECT l.*, loc.*, u.first_name, u.last_name, h.rating
            FROM Listing l
            JOIN Location loc ON l.location_id = loc.location_id
            JOIN Host h ON l.host_id = h.user_id
            JOIN User u ON h.user_id = u.user_id
            WHERE l.listing_id = %s
        ''', (listing_id,))
        listing = cursor.fetchone()
        
        if not listing:
            flash('Listing not found.')
            return redirect(url_for('traveler.search_listings'))
            
        return render_template('traveler/listing_detail.html', listing=listing)
    finally:
        cursor.close()