from app.database import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
from flask import current_app
import os


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer)
    maths_class = db.Column(db.String(100))
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    key_stage = db.Column(db.String(3), nullable=False, index=True)
    submissions = db.relationship('AnswerSubmission', backref='user', lazy=True,
                                  cascade='all, delete-orphan')
    articles = db.relationship('Article', backref='author', lazy='dynamic',
                               cascade='all, save-update')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False,
                            default=datetime.utcnow)
    file_url = db.Column(db.String(100))
    key_stage = db.Column(db.String(3), nullable=False)
    answer_boxes = db.relationship(
        'ChallengeAnswerBox', backref='challenge', lazy=True, cascade='all, save-update')
    submissions = db.relationship(
        'AnswerSubmission', backref='challenge', lazy=True)
    first_correct_submission = db.Column(db.DateTime)


class ChallengeAnswerBox(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey(
        'challenge.id'), nullable=False)
    # e.g., "Part A", "Step 1", etc.
    box_label = db.Column(db.String(100), nullable=False)
    correct_answer = db.Column(db.String(100), nullable=False)
    order = db.Column(db.Integer, nullable=False)  # To maintain box order
    submissions = db.relationship(
        'AnswerSubmission', backref='answer_box', lazy=True)


class AnswerSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey(
        'challenge.id'), nullable=False)
    answer_box_id = db.Column(db.Integer, db.ForeignKey(
        'challenge_answer_box.id'), nullable=False)
    answer = db.Column(db.String(100), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=True)
    submitted_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow)


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    file_url = db.Column(db.String(255))  # This will store the PDF file path
    content = db.Column(db.Text, nullable=False)
    named_creator = db.Column(db.String(100), nullable=True)
    date_posted = db.Column(db.DateTime, nullable=False,
                            default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(20), default='article', nullable=False)

    @property
    def pdf_path(self):
        if self.file_url and self.type == 'newsletter':
            return os.path.join(current_app.config['UPLOAD_FOLDER'], 'newsletters', self.file_url)
        return None


class LeaderboardEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    score = db.Column(db.Integer, default=0)
    last_updated = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref(
        'leaderboard_entries', cascade='all, delete-orphan'))
    # position = db.Column(db.Integer, nullable=True)


class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False,
                            default=datetime.utcnow)
