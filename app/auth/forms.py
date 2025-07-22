"""
Authentication Forms Module
==========================

This module defines Flask-WTF forms for user authentication processes,
including login and registration.

Key Form Classes:
----------------
- LoginForm: For user login authentication
- RegistrationForm: For new user account registration

Dependencies:
------------
- Flask-WTF for form handling
- WTForms for form field and validation
- Custom User model for validation

Security Considerations:
----------------------
1. Validates required fields
2. Implements password confirmation
3. Checks for existing usernames during registration
4. Includes CSRF protection (default in FlaskForm)

Maintenance Notes:
-----------------
1. Ensure form validators are comprehensive
2. Update year choices as academic years change
3. Validate and sanitize user inputs server-side
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange, Optional, ValidationError
from app.models import User, School


class LoginForm(FlaskForm):
    """
    Form for user login authentication.

    Fields:
    -------
    first_name : StringField
        User's first name (required)
    last_name : StringField
        User's last name (required)
    password : PasswordField
        User's password (required)
    year : SelectField
        User's current academic year (7-13)
    remember_me : BooleanField
        Option to maintain user session
    submit : SubmitField
        Button to submit login credentials
    """

    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class RegistrationForm(FlaskForm):
    """
    Form for creating a new user account.

    Fields:
    -------
    first_name : StringField
        User's first name (required)
    last_name : StringField
        User's last name (required)
    year : SelectField
        User's current academic year (7-13)
    password : PasswordField
        User's chosen password (required)
    password2 : PasswordField
        Password confirmation (must match password)
    maths_class : StringField
        User's mathematics class (required)
    submit : SubmitField
        Button to submit registration

    Methods:
    --------
    validate_username(first_name, last_name)
        Custom validation to prevent duplicate usernames
    """

    first_name = StringField("First Name", validators=[DataRequired()])
    last_name = StringField("Last Name", validators=[DataRequired()])
    email = StringField('School Email', validators=[DataRequired(), Email()])
    year = SelectField(
        "Year",
        choices=[
            ("7", "7"),
            ("8", "8"),
            ("9", "9"),
            ("10", "10"),
            ("11", "11"),
            ("12", "12"),
            ("13", "13"),
        ],
        validators=[DataRequired()],
    )
    password = PasswordField("Password", validators=[DataRequired()])
    password2 = PasswordField(
        "Repeat Password", validators=[DataRequired(), EqualTo("password")]
    )
    maths_class = StringField("Maths Class", validators=[DataRequired()])
    submit = SubmitField("Register")

    def validate_email(self, email):
        """Custom validation to ensure email is from UCGS"""
        if not email.data.endswith('@uptoncourtgrammar.org.uk'):
            raise ValidationError('You must use your school email address.')
        
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('This email address is already registered.')

class SummerRegistrationForm(FlaskForm):
    """
    Form for summer competition registration.
    
    This form extends the regular registration with school selection
    and competition-specific information.

    Fields:
    -------
    first_name : StringField
        User's first name (required)
    last_name : StringField
        User's last name (required)
    year : SelectField
        User's current academic year (7-13)
    school_id : SelectField
        User's school (required for competition participants)
    password : PasswordField
        User's chosen password (required)
    password2 : PasswordField
        Password confirmation (must match password)
    maths_class : StringField
        User's mathematics class (optional for non-UCGS participants)
    accept_terms : BooleanField
        Agreement to competition terms (required)
    submit : SubmitField
        Button to submit registration
    """

    first_name = StringField("First Name", validators=[DataRequired()])
    last_name = StringField("Last Name", validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    year = SelectField(
        "Year",
        choices=[
            ("7", "7"),
            ("8", "8"),
            ("9", "9"),
            ("10", "10"),
            ("11", "11"),
            ("12", "12"),
            ("13", "13"),
        ],
        validators=[DataRequired()],
    )
    school_id = SelectField(
        "School", 
        coerce=int,
        validators=[DataRequired()],
    )
    password = PasswordField("Password", validators=[DataRequired()])
    password2 = PasswordField(
        "Repeat Password", validators=[DataRequired(), EqualTo("password")]
    )
    accept_terms = BooleanField(
        "I accept the competition terms and conditions", 
        validators=[DataRequired()]
    )
    submit = SubmitField("Register for Summer Competition")

    def __init__(self, *args, **kwargs):
        """
        Initialize the form with dynamic school choices.
        
        Schools are loaded from the database to populate the dropdown.
        """
        super(SummerRegistrationForm, self).__init__(*args, **kwargs)
        from app.models import School
        # Populate school choices from database
        self.school_id.choices = [(0, "-- Select School --")] + [
            (school.id, school.name) for school in School.query.order_by(School.name).all()
        ]

    def validate_email(self, email):
        """Check if email is already registered"""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('This email address is already registered.')
        
        # check if email ends with school domain associated with school they pick
        if self.school_id.data != 0:  # If a school is selected
            school = School.query.get(self.school_id.data)
            if school and not email.data.endswith(school.email_domain):
                raise ValidationError(f'Must be a school domain associated with {school.name}.')

class SummerLoginForm(FlaskForm):
    """
    Form for summer competition login authentication.
    """
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    year = SelectField(
        "Year",
        choices=[
            ("7", "7"),
            ("8", "8"),
            ("9", "9"),
            ("10", "10"),
            ("11", "11"),
            ("12", "12"),
            ("13", "13"),
        ],
        validators=[DataRequired()],
    )
    school_id = SelectField(
        "School", 
        coerce=int,
        validators=[DataRequired()],
        description="Select your school (required for competition participants)"
    )
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the form with dynamic school choices.
        """
        super(SummerLoginForm, self).__init__(*args, **kwargs)
        from app.models import School
        # Populate school choices from database
        self.school_id.choices = [(0, "-- Select School --")] + [
            (school.id, school.name) for school in School.query.order_by(School.name).all()
        ]
