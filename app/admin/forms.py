from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import StringField, SubmitField, BooleanField, SelectField, FileField
from wtforms.validators import DataRequired, Length
from flask_ckeditor import CKEditorField

class ChallengeForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=100)])
    content = CKEditorField('Content', validators=[DataRequired()])
    image = FileField('Image', validators=[FileAllowed(['jpg', 'png', 'gif'])])
    key_stage = SelectField('Key Stage', 
                          choices=[('ks3', 'Key Stage 3'), 
                                 ('ks4', 'Key Stage 4'), 
                                 ('ks5', 'Key Stage 5')],
                          validators=[DataRequired()])
    correct_answer = StringField('Correct Answer', validators=[DataRequired()])
    submit = SubmitField('Create Challenge')
    
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

