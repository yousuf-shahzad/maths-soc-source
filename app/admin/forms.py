from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import StringField, SubmitField, BooleanField, SelectField, FileField, FieldList, FormField
from wtforms.validators import DataRequired, Length
from flask_ckeditor import CKEditorField

class LeaderboardEntryForm(FlaskForm):
    user_id = StringField('User ID', validators=[DataRequired()])
    score = StringField('Score', validators=[DataRequired()])
    submit = SubmitField('Submit')
class AnswerBoxForm(FlaskForm):
    class Meta:
        # Disable CSRF for nested form
        csrf = False
        
    box_label = StringField('Box Label', validators=[DataRequired()])
    correct_answer = StringField('Correct Answer', validators=[DataRequired()])
    order = StringField('Order')
class ChallengeForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=100)])
    content = CKEditorField('Content', validators=[DataRequired()])
    image = FileField('Image', validators=[FileAllowed(['jpg', 'png', 'gif'])])
    key_stage = SelectField('Key Stage',
                          choices=[('ks3', 'Key Stage 3'),
                                 ('ks4', 'Key Stage 4'),
                                 ('ks5', 'Key Stage 5')],
                          validators=[DataRequired()])
    answer_boxes = FieldList(FormField(AnswerBoxForm), min_entries=1)
    submit = SubmitField('Submit Challenge')

class AnswerSubmissionForm(FlaskForm):
    answer = StringField('Your Answer', validators=[DataRequired()])
    submit = SubmitField('Submit Answer')

class ArticleForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=100)])
    author = StringField('Author', validators=[DataRequired(), Length(min=1, max=100)])
    content = CKEditorField('Content', validators=[DataRequired()])
    type = SelectField('Type', choices=[('article', 'Article'), ('newsletter', 'Newsletter')], validators=[DataRequired()])
    file = FileField('PDF File', validators=[
        FileAllowed(['pdf'], 'PDF files only!')
    ])
    submit = SubmitField('Submit')

class EditUserForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    year = SelectField('Year', choices=[(7), (8), (9), (10), (11), (12), (13)],validators=[DataRequired()])
    maths_class = StringField('Maths Class', validators=[DataRequired()])
    submit = SubmitField('Submit')

class CreateUserForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    password = StringField('Password', validators=[DataRequired()])
    year = SelectField('Year', choices=[(7), (8), (9), (10), (11), (12), (13)],validators=[DataRequired()])
    is_admin = BooleanField('Admin')
    maths_class = StringField('Maths Class', validators=[DataRequired()])
    submit = SubmitField('Create User')