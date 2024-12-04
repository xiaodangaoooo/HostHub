# app/routes/settings.py
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.utils.db import get_db

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def user_settings():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Get additional user info based on role
        if current_user.role_type == 'host':
            cursor.execute('''
                SELECT h.preferred_language, h.rating
                FROM Host h
                WHERE h.user_id = %s
            ''', (current_user.id,))
            role_info = cursor.fetchone()
        else:  # traveler
            cursor.execute('''
                SELECT t.language_spoken, t.skills, t.availability
                FROM Traveler t
                WHERE t.user_id = %s
            ''', (current_user.id,))
            role_info = cursor.fetchone()

        if request.method == 'POST':
            # Get form data
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            email = request.form.get('email')
            
            # Role-specific data
            if current_user.role_type == 'host':
                preferred_language = request.form.get('preferred_language')
            else:
                language_spoken = request.form.get('language_spoken')
                skills = request.form.get('skills')
                availability = request.form.get('availability')

            try:
                # Update basic user info
                cursor.execute('''
                    UPDATE User 
                    SET first_name = %s, last_name = %s, email = %s
                    WHERE user_id = %s
                ''', (first_name, last_name, email, current_user.id))

                # Update role-specific info
                if current_user.role_type == 'host':
                    cursor.execute('''
                        UPDATE Host
                        SET preferred_language = %s
                        WHERE user_id = %s
                    ''', (preferred_language, current_user.id))
                else:
                    cursor.execute('''
                        UPDATE Traveler
                        SET language_spoken = %s, skills = %s, availability = %s
                        WHERE user_id = %s
                    ''', (language_spoken, skills, availability, current_user.id))

                db.commit()
                flash('Your settings have been updated successfully!', 'success')
                return redirect(url_for('settings.user_settings'))

            except Exception as e:
                db.rollback()
                print(f"Error updating user settings: {e}")
                flash('An error occurred while updating your settings.', 'danger')

        return render_template('settings/settings.html', user=current_user, role_info=role_info)
    finally:
        cursor.close()