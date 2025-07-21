"""
Forms Module for Admin Panel
===========================

This module defines Flask-WTF forms used across the application for various
administrative and user interaction purposes.

Key Form Classes:
----------------
- LeaderboardEntryForm: For managing leaderboard entries
- ChallengeForm: For creating and editing challenges
- ArticleForm: For managing article submissions
- UserManagement Forms: For creating and editing user accounts

Dependencies:
------------
- Flask-WTF for form handling
- WTForms for form field and validation
- Flask-CKEditor for rich text editing

Security Considerations:
----------------------
1. Uses DataRequired() validators to ensure critical fields are not empty
2. Implements file type restrictions for uploads
3. Supports nested form validation
4. Includes CSRF protection (default in FlaskForm)

Maintenance Notes:
-----------------
1. Ensure form validators are comprehensive
2. Update choices in SelectFields as needed
3. Validate and sanitize user inputs server-side
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import (
    StringField,
    IntegerField,
    SubmitField,
    BooleanField,
    SelectField,
    FileField,
    FieldList,
    FormField,
)
from wtforms.fields import DateTimeLocalField
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange, Optional
from flask_ckeditor import CKEditorField


class LeaderboardEntryForm(FlaskForm):
    """
    Form for creating and editing leaderboard entries.

    This form allows administrators to manually create or modify leaderboard
    entries, including selecting the appropriate key stage for fair competition.

    Fields:
    -------
    user_id : SelectField
        Dropdown selection of registered users
    score : IntegerField
        User's current point total (minimum 0)
    key_stage : SelectField
        Educational key stage classification:
        - KS3: Years 7-8
        - KS4: Years 9-11  
        - KS5: Years 12-13
    submit : SubmitField
        Button to save the leaderboard entry
    """
    user_id = SelectField('User', coerce=int, validators=[DataRequired()])
    score = IntegerField('Score', validators=[DataRequired(), NumberRange(min=0)])
    key_stage = SelectField('Key Stage', choices=[
        ('KS3', 'Key Stage 3 (Years 7-8)'),
        ('KS4', 'Key Stage 4 (Years 9-11)'),
        ('KS5', 'Key Stage 5 (Years 12-13)')
    ], validators=[DataRequired()])
    submit = SubmitField('Save Entry')


class AnswerBoxForm(FlaskForm):
    """
    Nested form for managing individual answer boxes within a challenge.

    Note:
    -----
    CSRF is disabled for nested forms to prevent validation conflicts.

    Fields:
    -------
    box_label : StringField
        Label for the answer box
    correct_answer : StringField
        The correct answer for this box
    order : StringField
        Optional ordering for multiple answer boxes
    """

    class Meta:
        # Disable CSRF for nested form
        csrf = False

    box_label = StringField("Box Label", validators=[DataRequired()])
    correct_answer = StringField("Correct Answer", validators=[DataRequired()])
    order = StringField("Order")


class ChallengeForm(FlaskForm):
    """
    Form for creating and editing educational challenges.

    Fields:
    -------
    title : StringField
        Challenge title (1-100 characters)
    content : CKEditorField
        Rich text description of the challenge
    image : FileField
        Optional image upload for the challenge
    key_stage : SelectField
        Educational key stage (KS3, KS4, KS5)
    answer_boxes : FieldList
        Dynamic list of answer boxes for the challenge
    submit : SubmitField
        Button to submit the challenge
    """

    title = StringField("Title", validators=[DataRequired(), Length(min=1, max=100)])
    content = CKEditorField("Content", validators=[DataRequired()])
    image = FileField("Image", validators=[FileAllowed(["jpg", "png", "gif"])])
    release_at = DateTimeLocalField("Release Date & Time (leave blank for immediate release)", validators=[Optional()])
    lock_after_hours = IntegerField("Lock after X hours (leave blank for no auto-lock)", validators=[Optional(), NumberRange(min=1, max=8760)])  # Max 1 year
    key_stage = SelectField(
        "Key Stage",
        choices=[
            ("ks3", "Key Stage 3"),
            ("ks4", "Key Stage 4"),
            ("ks5", "Key Stage 5"),
        ],
        validators=[DataRequired()],
    )
    answer_boxes = FieldList(FormField(AnswerBoxForm), min_entries=1)
    submit = SubmitField("Submit Challenge")

class SummerChallengeForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(min=1, max=100)])
    content = CKEditorField("Content", validators=[DataRequired()])
    image = FileField("Image", validators=[FileAllowed(["jpg", "png", "gif"])])
    release_at = DateTimeLocalField("Release Date & Time (leave blank for immediate release)", validators=[Optional()])
    key_stage = SelectField(
        "Key Stage",
        choices=[("KS3", "Key Stage 3"), ("KS4", "Key Stage 4"), ("KS5", "Key Stage 5")],
        validators=[DataRequired()],
    )
    duration_hours = IntegerField("Duration (hours)", validators=[DataRequired(), NumberRange(min=1, max=168)])
    answer_boxes = FieldList(FormField(AnswerBoxForm), min_entries=1)
    submit = SubmitField("Submit Summer Challenge")

class AnswerSubmissionForm(FlaskForm):
    """
    Form for submitting answers to challenges.

    Fields:
    -------
    answer : StringField
        User's submitted answer
    submit : SubmitField
        Button to submit the answer
    """

    answer = StringField("Your Answer", validators=[DataRequired()])
    submit = SubmitField("Submit Answer")


class ArticleForm(FlaskForm):
    """
    Form for creating and managing articles and newsletters.

    Fields:
    -------
    title : StringField
        Article title (1-100 characters)
    author : StringField
        Article author name (1-100 characters)
    content : CKEditorField
        Rich text content of the article
    type : SelectField
        Type of publication (article or newsletter)
    file : FileField
        Optional PDF file upload
    submit : SubmitField
        Button to submit the article
    """

    title = StringField("Title", validators=[DataRequired(), Length(min=1, max=100)])
    author = StringField("Author", validators=[DataRequired(), Length(min=1, max=100)])
    content = CKEditorField("Content", validators=[DataRequired()])
    type = SelectField(
        "Type",
        choices=[("article", "Article"), ("newsletter", "Newsletter")],
        validators=[DataRequired()],
    )
    file = FileField("PDF File", validators=[FileAllowed(["pdf"], "PDF files only!")])
    submit = SubmitField("Submit")


class EditUserForm(FlaskForm):
    """
    Form for editing existing user details.

    Fields:
    -------
    first_name : StringField
        User's first name
    last_name : StringField
        User's last name
    year : SelectField
        User's current academic year (7-13)
    is_competition_participant : BooleanField
        Flag to indicate if user is a summer competition participant
    school_id : SelectField
        School selection for summer competition participants
    maths_class : StringField
        User's mathematics class (for regular users)
    submit : SubmitField
        Button to submit user edits
    """

    first_name = StringField("First Name", validators=[DataRequired()])
    last_name = StringField("Last Name", validators=[DataRequired()])
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
    is_competition_participant = BooleanField("Summer Competition Participant")
    school_id = SelectField("School", coerce=int, validators=[Optional()])
    maths_class = StringField("Maths Class")
    submit = SubmitField("Submit")
    
    def __init__(self, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        from app.models import School
        self.school_id.choices = [(0, 'Select School...')] + [(school.id, school.name) for school in School.query.order_by(School.name).all()]


class CreateUserForm(FlaskForm):
    """
    Form for creating a new user account.

    Fields:
    -------
    first_name : StringField
        User's first name
    last_name : StringField
        User's last name
    password : StringField
        Initial password for the user
    year : SelectField
        User's current academic year (7-13)
    is_admin : BooleanField
        Flag to grant administrative privileges
    is_competition_participant : BooleanField
        Flag to indicate if user is a summer competition participant
    school_id : SelectField
        School selection for summer competition participants
    maths_class : StringField
        User's mathematics class (for regular users)
    submit : SubmitField
        Button to create new user
    """

    first_name = StringField("First Name", validators=[DataRequired()])
    last_name = StringField("Last Name", validators=[DataRequired()])
    password = StringField("Password", validators=[DataRequired()])
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
    is_admin = BooleanField("Admin")
    is_competition_participant = BooleanField("Summer Competition Participant")
    school_id = SelectField("School", coerce=int, validators=[Optional()])
    maths_class = StringField("Maths Class")
    submit = SubmitField("Create User")
    
    def __init__(self, *args, **kwargs):
        super(CreateUserForm, self).__init__(*args, **kwargs)
        from app.models import School
        self.school_id.choices = [(0, 'Select School...')] + [(school.id, school.name) for school in School.query.order_by(School.name).all()]


class AnnouncementForm(FlaskForm):
    """
    Form for creating and publishing announcements.

    Fields:
    -------
    title : StringField
        Announcement title
    content : CKEditorField
        Rich text content of the announcement
    submit : SubmitField
        Button to submit the announcement
    """

    title = StringField("Title", validators=[DataRequired()])
    content = CKEditorField("Content", validators=[DataRequired()])
    submit = SubmitField("Submit")

class SchoolForm(FlaskForm):
    name = StringField("School Name", validators=[DataRequired(), Length(max=100)])
    email_domain = StringField("Email Domain", validators=[Length(max=100)])
    address = StringField("Address", validators=[Length(max=200)])
    submit = SubmitField("Save School")


class SummerLeaderboardEntryForm(FlaskForm):
    """
    Form for creating and editing summer leaderboard entries.

    This form allows administrators to manually create or modify summer competition
    leaderboard entries, linking users to their schools and managing their scores.

    Fields:
    -------
    user_id : SelectField
        Dropdown selection of registered users
    school_id : SelectField  
        Dropdown selection of participating schools
    score : IntegerField
        User's current point total for summer competition (minimum 0)
    submit : SubmitField
        Button to save the summer leaderboard entry
    """
    user_id = SelectField('User', coerce=int, validators=[DataRequired()])
    school_id = SelectField('School', coerce=int, validators=[DataRequired()])
    score = IntegerField('Score', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Save Entry')