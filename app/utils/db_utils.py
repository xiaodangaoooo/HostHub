# app/utils/db_utils.py

from app.utils.db import get_db
from datetime import datetime

# Host-related functions
def get_host_listings(host_id):
    """
    Get all listings for a specific host with application counts.
    
    Args:
        host_id (int): The host's user ID
        
    Returns:
        tuple: (listings, active_listings_count, total_applications)
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute('''
            SELECT l.*, loc.city, loc.country,
                   (SELECT COUNT(*) FROM Application a WHERE a.listing_id = l.listing_id) as application_count
            FROM Listing l
            JOIN Location loc ON l.location_id = loc.location_id
            WHERE l.host_id = %s
        ''', (host_id,))
        listings = cursor.fetchall()
        
        # Count active listings
        active_count = sum(1 for l in listings if l['status'] == 'active')
        
        cursor.execute('''
            SELECT COUNT(*) as count
            FROM Application a
            JOIN Listing l ON a.listing_id = l.listing_id
            WHERE l.host_id = %s
        ''', (host_id,))
        applications_count = cursor.fetchone()['count']
        
        return listings, active_count, applications_count
    finally:
        cursor.close()

def create_location(country, state, city, zip_code):
    """
    Create a new location record.
    
    Args:
        country (str): Country name
        state (str): State/province name (optional)
        city (str): City name
        zip_code (str): ZIP/Postal code (optional)
        
    Returns:
        int: ID of the created location or None if failed
    """
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO Location (country, state, city, zip_code)
            VALUES (%s, %s, %s, %s)
        ''', (country, state or None, city, zip_code or None))
        db.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error creating location: {e}")
        db.rollback()
        return None
    finally:
        cursor.close()

def update_location(location_id, country, state, city, zip_code):
    """
    Update an existing location.
    
    Args:
        location_id (int): ID of location to update
        country (str): New country name
        state (str): New state/province name
        city (str): New city name
        zip_code (str): New ZIP/Postal code
        
    Returns:
        bool: Success status
    """
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute('''
            UPDATE Location
            SET country = %s, state = %s, city = %s, zip_code = %s
            WHERE location_id = %s
        ''', (country, state, city, zip_code, location_id))
        db.commit()
        return True
    except Exception as e:
        print(f"Error updating location: {e}")
        db.rollback()
        return False
    finally:
        cursor.close()

# Listing functions
def create_listing(host_id, location_id, title, description, work_hours, duration, work_type):
    """
    Create a new listing.
    
    Args:
        host_id (int): Host's user ID
        location_id (int): ID of the associated location
        title (str): Listing title
        description (str): Listing description
        work_hours (int): Weekly work hours
        duration (int): Duration in days
        work_type (str): Type of work
        
    Returns:
        int: ID of the created listing or None if failed
    """
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO Listing (
                host_id, location_id, title, description,
                work_hour, duration_day, work_type, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'active')
        ''', (host_id, location_id, title, description, work_hours, duration, work_type))
        db.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error creating listing: {e}")
        db.rollback()
        return None
    finally:
        cursor.close()

def get_listing_details(listing_id, host_id=None):
    """
    Get detailed listing information including application statistics.
    
    Args:
        listing_id (int): ID of the listing
        host_id (int, optional): Host's user ID for verification
        
    Returns:
        tuple: (listing_details, applications)
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Base query
        query = '''
            SELECT 
                l.*, loc.*,
                COUNT(a.application_id) as total_applications,
                SUM(CASE WHEN a.status = 'pending' THEN 1 ELSE 0 END) as pending_applications,
                SUM(CASE WHEN a.status = 'accepted' THEN 1 ELSE 0 END) as accepted_applications
            FROM Listing l
            JOIN Location loc ON l.location_id = loc.location_id
            LEFT JOIN Application a ON l.listing_id = a.listing_id
            WHERE l.listing_id = %s
        '''
        params = [listing_id]
        
        # Add host verification if specified
        if host_id is not None:
            query += ' AND l.host_id = %s'
            params.append(host_id)
            
        query += '''
            GROUP BY l.listing_id, l.title, l.description, l.work_hour, 
                     l.duration_day, l.status, l.work_type, 
                     loc.city, loc.country, loc.state, loc.zip_code
        '''
        
        cursor.execute(query, params)
        listing = cursor.fetchone()
        
        if not listing:
            return None, None
            
        # Get applications if any
        cursor.execute('''
            SELECT 
                a.*, 
                u.first_name, u.last_name,
                t.language_spoken, t.skills
            FROM Application a
            JOIN Traveler t ON a.traveler_id = t.user_id
            JOIN User u ON t.user_id = u.user_id
            WHERE a.listing_id = %s
            ORDER BY a.date_applied DESC
        ''', (listing_id,))
        applications = cursor.fetchall()
        
        return listing, applications
    finally:
        cursor.close()

def update_listing(listing_id, host_id, title, description, work_hours, duration, work_type):
    """
    Update an existing listing.
    
    Args:
        listing_id (int): ID of the listing to update
        host_id (int): Host's user ID for verification
        title (str): New listing title
        description (str): New listing description
        work_hours (int): New weekly work hours
        duration (int): New duration in days
        work_type (str): New type of work
        
    Returns:
        bool: Success status
    """
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute('''
            UPDATE Listing
            SET title = %s, description = %s, work_hour = %s,
                duration_day = %s, work_type = %s
            WHERE listing_id = %s AND host_id = %s
        ''', (title, description, work_hours, duration, work_type, listing_id, host_id))
        
        db.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error updating listing: {e}")
        db.rollback()
        return False
    finally:
        cursor.close()

def delete_listing(listing_id, host_id):
    """
    Delete a listing and its associated location.
    
    Args:
        listing_id (int): ID of the listing to delete
        host_id (int): Host's user ID for verification
        
    Returns:
        bool: Success status
    """
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Verify ownership and get location_id
        cursor.execute('SELECT location_id FROM Listing WHERE listing_id = %s AND host_id = %s',
                      (listing_id, host_id))
        result = cursor.fetchone()
        
        if not result:
            return False
            
        location_id = result[0]
        
        # Start transaction
        cursor.execute('START TRANSACTION')
        
        # Delete the listing
        cursor.execute('DELETE FROM Listing WHERE listing_id = %s', (listing_id,))
        
        # Delete the associated location
        cursor.execute('DELETE FROM Location WHERE location_id = %s', (location_id,))
        
        db.commit()
        return True
    except Exception as e:
        print(f"Error deleting listing: {e}")
        db.rollback()
        return False
    finally:
        cursor.close()

# Search functions
def search_listings(filters=None, page=1, per_page=10):
    """
    Search listings with optional filters and pagination.
    
    Args:
        filters (dict, optional): Search filters (location, work_type, etc.)
        page (int): Page number
        per_page (int): Items per page
        
    Returns:
        tuple: (listings, total_count)
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
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
        
        if filters:
            if filters.get('location'):
                query += ''' AND (loc.city LIKE %s OR loc.country LIKE %s)'''
                search_term = f"%{filters['location']}%"
                params.extend([search_term, search_term])
            
            if filters.get('work_type'):
                query += ''' AND l.work_type LIKE %s'''
                params.append(f"%{filters['work_type']}%")
            
            if filters.get('duration'):
                query += ''' AND l.duration_day <= %s'''
                params.append(filters['duration'])
        
        # Get total count
        count_cursor = db.cursor()
        count_cursor.execute(f"SELECT COUNT(*) FROM ({query}) as count_query", params)
        total_count = count_cursor.fetchone()[0]
        
        # Add pagination
        query += ' LIMIT %s OFFSET %s'
        offset = (page - 1) * per_page
        params.extend([per_page, offset])
        
        cursor.execute(query, params)
        listings = cursor.fetchall()
        
        return listings, total_count
    finally:
        cursor.close()

# Application functions
def create_application(traveler_id, listing_id, introduction):
    """
    Create a new application for a listing.
    
    Args:
        traveler_id (int): Traveler's user ID
        listing_id (int): Listing ID
        introduction (str): Traveler's introduction/message
        
    Returns:
        bool: Success status
    """
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO Application (
                listing_id, traveler_id, introduction, status, date_applied
            ) VALUES (%s, %s, %s, 'pending', NOW())
        ''', (listing_id, traveler_id, introduction))
        
        db.commit()
        return True
    except Exception as e:
        print(f"Error creating application: {e}")
        db.rollback()
        return False
    finally:
        cursor.close()

def update_application_status(application_id, new_status, host_id):
    """
    Update an application's status.
    
    Args:
        application_id (int): Application ID
        new_status (str): New status ('accepted', 'rejected', 'withdrawn')
        host_id (int): Host's user ID for verification
        
    Returns:
        bool: Success status
    """
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute('''
            UPDATE Application a
            JOIN Listing l ON a.listing_id = l.listing_id
            SET a.status = %s,
                a.last_updated = NOW()
            WHERE a.application_id = %s
            AND l.host_id = %s
        ''', (new_status, application_id, host_id))
        
        db.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error updating application status: {e}")
        db.rollback()
        return False
    finally:
        cursor.close()