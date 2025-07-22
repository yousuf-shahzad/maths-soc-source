from app.database import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import datetime
from flask import current_app
import os


class User(UserMixin, db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    year = db.Column(db.Integer)
    maths_class = db.Column(db.String(100))
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    key_stage = db.Column(db.String(3), nullable=False, index=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=True, index=True)
    is_competition_participant = db.Column(db.Boolean, default=False, nullable=False)
    
    # Relationships with proper lazy loading
    submissions = db.relationship(
        "AnswerSubmission", 
        back_populates="user", 
        lazy="dynamic", 
        cascade="all, delete-orphan"
    )
    articles = db.relationship(
        "Article", 
        back_populates="author", 
        lazy="dynamic", 
        cascade="all, save-update"
    )

    def set_password(self, password):
        """Hash and set user password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password against stored hash."""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.full_name} ({self.key_stage})>'


class Challenge(db.Model):
    __tablename__ = "challenge"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, index=True)
    file_url = db.Column(db.String(100))
    key_stage = db.Column(db.String(3), nullable=False, index=True)
    first_correct_submission = db.Column(db.DateTime)
    release_at = db.Column(db.DateTime, nullable=True, index=True)
    is_manually_locked = db.Column(db.Boolean, default=False, nullable=False)
    lock_after_hours = db.Column(db.Integer, nullable=True)
    
    # Relationships
    answer_boxes = db.relationship(
        "ChallengeAnswerBox", 
        back_populates="challenge", 
        lazy="dynamic", 
        cascade="all, save-update",
        order_by="ChallengeAnswerBox.order"
    )
    submissions = db.relationship(
        "AnswerSubmission", 
        back_populates="challenge", 
        lazy="dynamic"
    )
    
    @property
    def is_locked(self):
        """Check if challenge is locked (manually or by time) - exactly like summer challenges"""
        from datetime import datetime, timedelta
        
        # Check manual lock first
        if self.is_manually_locked:
            return True
            
        # Check automatic time-based lock
        if self.lock_after_hours and self.release_at:
            lock_time = self.release_at + timedelta(hours=self.lock_after_hours)
            return datetime.now() > lock_time
            
        return False
    
    def __repr__(self):
        return f'<Challenge {self.title} ({self.key_stage})>'


class ChallengeAnswerBox(db.Model):
    __tablename__ = "challenge_answer_box"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenge.id"), nullable=False, index=True)
    box_label = db.Column(db.String(100), nullable=False)  # e.g., "Part A", "Step 1", etc.
    correct_answer = db.Column(db.String(100), nullable=False)
    order = db.Column(db.Integer, nullable=False)  # To maintain box order
    
    # Relationships
    challenge = db.relationship("Challenge", back_populates="answer_boxes")
    submissions = db.relationship(
        "AnswerSubmission", 
        back_populates="answer_box", 
        lazy="dynamic"
    )
    
    # Composite index for better query performance
    __table_args__ = (
        db.Index('ix_challenge_answer_box_challenge_order', 'challenge_id', 'order'),
    )
    
    def __repr__(self):
        return f'<ChallengeAnswerBox {self.box_label} for Challenge {self.challenge_id}>'


class AnswerSubmission(db.Model):
    __tablename__ = "answer_submission"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenge.id"), nullable=False, index=True)
    answer_box_id = db.Column(
        db.Integer, 
        db.ForeignKey("challenge_answer_box.id"), 
        nullable=False, 
        index=True
    )
    answer = db.Column(db.String(100), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=True)
    submitted_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, index=True)
    
    # Relationships
    user = db.relationship("User", back_populates="submissions")
    challenge = db.relationship("Challenge", back_populates="submissions")
    answer_box = db.relationship("ChallengeAnswerBox", back_populates="submissions")
    
    # Composite indexes for common query patterns
    __table_args__ = (
        db.Index('ix_answer_submission_user_challenge', 'user_id', 'challenge_id'),
        db.Index('ix_answer_submission_challenge_submitted', 'challenge_id', 'submitted_at'),
    )
    
    def __repr__(self):
        return f'<AnswerSubmission User:{self.user_id} Challenge:{self.challenge_id}>'


class Article(db.Model):
    __tablename__ = "article"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, index=True)
    file_url = db.Column(db.String(255))  # This will store the PDF file path
    content = db.Column(db.Text, nullable=False)
    named_creator = db.Column(db.String(100), nullable=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    type = db.Column(db.String(20), default="article", nullable=False, index=True)
    
    # Relationships
    author = db.relationship("User", back_populates="articles")

    @property
    def pdf_path(self):
        """Get the full path to the PDF file for newsletters."""
        if self.file_url and self.type == "newsletter":
            return os.path.join(
                current_app.config["UPLOAD_FOLDER"], "newsletters", self.file_url
            )
        return None
    
    def __repr__(self):
        return f'<Article {self.title} ({self.type})>'


class LeaderboardEntry(db.Model):
    __tablename__ = "leaderboard_entry"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    score = db.Column(db.Integer, default=0, nullable=False)
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, index=True)
    key_stage = db.Column(db.String(3), nullable=False, index=True)
    
    # Relationships
    user = db.relationship(
        "User", 
        backref=db.backref("leaderboard_entries", cascade="all, delete-orphan")
    )
    
    # Composite index for leaderboard queries
    __table_args__ = (
        db.Index('ix_leaderboard_entry_key_stage_score', 'key_stage', 'score'),
    )
    
    def __repr__(self):
        return f'<LeaderboardEntry User:{self.user_id} Score:{self.score} ({self.key_stage})>'


class Announcement(db.Model):
    __tablename__ = "announcement"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, index=True)
    
    def __repr__(self):
        return f'<Announcement {self.title}>'


class School(db.Model):
    __tablename__ = "school"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    email_domain = db.Column(db.String(100), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    date_joined = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False)
    
    # Relationships
    users = db.relationship('User', backref='school', lazy='dynamic')
    
    def __repr__(self):
        return f'<School {self.name}>'


class SummerChallenge(db.Model):
    __tablename__ = "summer_challenge"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False)
    duration_hours = db.Column(db.Integer, default=24, nullable=False)
    file_url = db.Column(db.String(100))
    key_stage = db.Column(db.String(3), nullable=False, index=True)
    is_manually_locked = db.Column(db.Boolean, default=False, nullable=False)  # Add this field
    release_at = db.Column(db.DateTime, nullable=True, index=True)
    
    # Relationships
    answer_boxes = db.relationship(
        'SummerChallengeAnswerBox', 
        back_populates='challenge', 
        lazy='dynamic', 
        cascade='all, delete-orphan',
        order_by="SummerChallengeAnswerBox.order"
    )
    submissions = db.relationship(
        'SummerSubmission', 
        back_populates='challenge', 
        lazy='dynamic'
    )
    
    def __repr__(self):
        return f'<SummerChallenge {self.title}>'

    @property
    def is_locked(self):
        from datetime import timedelta
        # Check manual lock first, then time-based lock
        return (self.is_manually_locked or 
                datetime.datetime.now() > self.date_posted + timedelta(hours=self.duration_hours))

    @property
    def lock_reason(self):
        from datetime import timedelta
        """Returns the reason why the challenge is locked"""
        if self.is_manually_locked:
            return "manually_locked"
        elif datetime.datetime.now() > self.date_posted + timedelta(hours=self.duration_hours):
            return "time_expired"
        return None


class SummerChallengeAnswerBox(db.Model):
    __tablename__ = "summer_challenge_answer_box"
    
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('summer_challenge.id'), nullable=False, index=True)
    box_label = db.Column(db.String(100), nullable=False)
    correct_answer = db.Column(db.String(100), nullable=False)
    order = db.Column(db.Integer, nullable=False)
    
    # Relationships
    challenge = db.relationship('SummerChallenge', back_populates='answer_boxes')
    submissions = db.relationship(
        'SummerSubmission', 
        back_populates='answer_box', 
        lazy='dynamic'
    )
    
    # Composite index for ordering
    __table_args__ = (
        db.Index('ix_summer_answer_box_challenge_order', 'challenge_id', 'order'),
    )
    
    def __repr__(self):
        return f'<SummerChallengeAnswerBox {self.box_label} for Challenge {self.challenge_id}>'


class SummerSubmission(db.Model):
    __tablename__ = "summer_submission"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False, index=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('summer_challenge.id'), nullable=False, index=True)
    answer_box_id = db.Column(
        db.Integer, 
        db.ForeignKey('summer_challenge_answer_box.id'), 
        nullable=False, 
        index=True
    )
    answer = db.Column(db.String(100), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False, index=True)
    points_awarded = db.Column(db.Integer, default=0, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('summer_submissions', lazy='dynamic'))
    school = db.relationship('School', backref=db.backref('summer_submissions', lazy='dynamic'))
    challenge = db.relationship('SummerChallenge', back_populates='submissions')
    answer_box = db.relationship('SummerChallengeAnswerBox', back_populates='submissions')
    
    # Composite indexes for common queries
    __table_args__ = (
        db.Index('ix_summer_submission_user_challenge', 'user_id', 'challenge_id'),
        db.Index('ix_summer_submission_school_points', 'school_id', 'points_awarded'),
    )
    
    def __repr__(self):
        return f'<SummerSubmission User:{self.user_id} Challenge:{self.challenge_id} Points:{self.points_awarded}>'


class SummerLeaderboard(db.Model):
    __tablename__ = "summer_leaderboard"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False, index=True)
    score = db.Column(db.Integer, default=0, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.datetime.now, nullable=False, index=True)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('summer_leaderboard_entries', lazy='dynamic'))
    school = db.relationship('School', backref=db.backref('leaderboard_entries', lazy='dynamic'))
    
    # Composite indexes for leaderboard queries
    __table_args__ = (
        db.Index('ix_summer_leaderboard_school_score', 'school_id', 'score'),
        db.Index('ix_summer_leaderboard_score', 'score'),
    )
    
    def __repr__(self):
        return f'<SummerLeaderboard User:{self.user_id} School:{self.school_id} Score:{self.score}>'