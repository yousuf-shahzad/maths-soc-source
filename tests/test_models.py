import pytest
from datetime import datetime, timedelta
from app.models import User, Challenge, ChallengeAnswerBox, AnswerSubmission, Article, LeaderboardEntry, Announcement
from app.database import db

class TestUserModel:
    def test_user_creation(self, test_user):
        """Test basic user creation and attributes"""
        assert test_user.full_name == 'Test User'
        assert test_user.year == 12
        assert test_user.maths_class == 'Test Class'
        assert test_user.key_stage == 'KS5'
        assert test_user.is_admin is False

    def test_password_hashing(self, test_user):
        """Test password hashing and checking"""
        # Test correct password
        assert test_user.check_password('testpassword') is True
        
        # Test incorrect password
        assert test_user.check_password('wrongpassword') is False

    def test_user_relationships(self, _db):
        """Test relationships with other models"""
        user = User(
            full_name='Another User', 
            year=11, 
            maths_class='Math Class',
            key_stage='KS4'
        )
        user.set_password('anotherpassword')
        
        # Add challenge and submission to test relationships
        challenge = Challenge(
            title='Test Challenge', 
            content='Challenge content',
            key_stage='KS4'
        )
        answer_box = ChallengeAnswerBox(
            challenge=challenge, 
            box_label='Part A', 
            correct_answer='42', 
            order=1
        )
        submission = AnswerSubmission(
            user=user, 
            challenge=challenge, 
            answer_box=answer_box, 
            answer='42'
        )
        
        _db.session.add_all([user, challenge, answer_box, submission])
        _db.session.commit()
        
        assert len(user.submissions) == 1
        assert user.submissions[0] == submission

class TestChallengeModel:
    def test_challenge_creation(self, _db):
        """Test challenge creation and basic attributes"""
        challenge = Challenge(
            title='Math Challenge', 
            content='Solve this tricky problem', 
            key_stage='KS5'
        )
        _db.session.add(challenge)
        _db.session.commit()
        
        assert challenge.title == 'Math Challenge'
        assert challenge.key_stage == 'KS5'
        assert challenge.date_posted is not None
        assert isinstance(challenge.date_posted, datetime)

    def test_challenge_answer_box_relationship(self, _db):
        """Test relationship between Challenge and ChallengeAnswerBox"""
        challenge = Challenge(
            title='Geometry Challenge', 
            content='Solve geometric problems', 
            key_stage='KS4'
        )
        
        answer_box1 = ChallengeAnswerBox(
            challenge=challenge, 
            box_label='Part A', 
            correct_answer='Triangle', 
            order=1
        )
        answer_box2 = ChallengeAnswerBox(
            challenge=challenge, 
            box_label='Part B', 
            correct_answer='Circle', 
            order=2
        )
        
        _db.session.add_all([challenge, answer_box1, answer_box2])
        _db.session.commit()
        
        assert len(challenge.answer_boxes) == 2
        assert {box.box_label for box in challenge.answer_boxes} == {'Part A', 'Part B'}

class TestAnswerSubmissionModel:
    def test_answer_submission_creation(self, _db, test_user):
        """Test creation of answer submission"""
        challenge = Challenge(
            title='Test Challenge', 
            content='Challenge content',
            key_stage='KS5'
        )
        answer_box = ChallengeAnswerBox(
            challenge=challenge, 
            box_label='Part A', 
            correct_answer='42', 
            order=1
        )
        submission = AnswerSubmission(
            user=test_user, 
            challenge=challenge, 
            answer_box=answer_box, 
            answer='42',
            is_correct=True
        )
        
        _db.session.add_all([challenge, answer_box, submission])
        _db.session.commit()
        
        assert submission.user == test_user
        assert submission.challenge == challenge
        assert submission.answer_box == answer_box
        assert submission.is_correct is True
        assert isinstance(submission.submitted_at, datetime)

class TestArticleModel:
    def test_article_creation(self, _db, test_user):
        """Test article creation and attributes"""
        article = Article(
            title='Math Insights', 
            content='Interesting math article', 
            named_creator='Admin',
            type='article',
            user_id=test_user.id,
            date_posted=datetime.now()
        )
        
        _db.session.add(article)
        _db.session.commit()
        
        assert article.title == 'Math Insights'
        assert article.user_id == test_user.id
        assert article.type == 'article'
        assert isinstance(article.date_posted, datetime)


class TestLeaderboardEntryModel:
    def test_leaderboard_entry_creation(self, _db, test_user):
        """Test leaderboard entry creation"""
        leaderboard_entry = LeaderboardEntry(
            user=test_user,
            score=100
        )
        
        _db.session.add(leaderboard_entry)
        _db.session.commit()
        
        assert leaderboard_entry.user == test_user
        assert leaderboard_entry.score == 100
        assert isinstance(leaderboard_entry.last_updated, datetime)

class TestAnnouncementModel:
    def test_announcement_creation(self, _db):
        """Test announcement creation"""
        announcement = Announcement(
            title='Upcoming Event', 
            content='Join our math competition!'
        )
        
        _db.session.add(announcement)
        _db.session.commit()
        
        assert announcement.title == 'Upcoming Event'
        assert isinstance(announcement.date_posted, datetime)