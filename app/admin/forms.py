from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length
from flask_ckeditor import CKEditorField

class ChallengeForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=100)])
    content = CKEditorField('Content', validators=[DataRequired()])  # Use CKEditorField
    submit = SubmitField('Create Challenge')

class ArticleForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=100)])
    author = StringField('Author', validators=[DataRequired(), Length(min=1, max=100)])
    content = CKEditorField('Content', validators=[DataRequired()])
    type = SelectField('Type', choices=[('article', 'Article'), ('newsletter', 'Newsletter')], validators=[DataRequired()])
    submit = SubmitField('Create')

