"""
Profile Forms Module
===================

This module defines Flask-WTF forms for user profile management,
specifically password change functionality.

Key Form Classes:
----------------
- ChangePasswordForm: For updating user passwords

Dependencies:
------------
- Flask-WTF for form handling
- WTForms for form field and validation

Security Considerations:
----------------------
1. Validates required fields
2. Requires current password for change
3. Includes CSRF protection (default in FlaskForm)

Maintenance Notes:
-----------------
1. Ensure form validators are comprehensive
2. Validate and sanitize user inputs server-side
3. Add additional password strength validation if needed
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class ChangePasswordForm(FlaskForm):
    """
    Form for changing user account password.

    Fields:
    -------
    current_password : StringField
        User's current password (required)
    new_password : StringField
        User's chosen new password (required)
    confirm_password : StringField
        Confirmation of new password (required)
    submit : SubmitField
        Button to submit password change

    Notes:
    ------
    Additional password validation should be implemented 
    in the route handling this form to ensure:
    1. Current password is correct
    2. New password meets complexity requirements
    3. New password is different from current password
    """
    current_password = StringField(
        'Current Password', validators=[DataRequired()])
    new_password = StringField('New Password', validators=[DataRequired()])
    confirm_password = StringField(
        'Confirm New Password', validators=[DataRequired()])
    submit = SubmitField('Change Password')