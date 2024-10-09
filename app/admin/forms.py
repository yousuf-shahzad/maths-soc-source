from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length
from flask_ckeditor import CKEditorField

class ChallengeForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=100)])
    content = CKEditorField('Content', validators=[DataRequired()])  # Use CKEditorField
    submit = SubmitField('Create Challenge')

class NewsletterForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=100)])
    content = CKEditorField('Content', validators=[DataRequired()])  # Use CKEditorField
    submit = SubmitField('Create Newsletter')

class ArticleReviewForm(FlaskForm):
    approve = BooleanField('Approve')
    submit = SubmitField('Submit Review')
