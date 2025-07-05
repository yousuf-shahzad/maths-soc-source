import pytest
from sqlalchemy.exc import IntegrityError
from app.database import db
from datetime import datetime
from app.models import User, Challenge, ChallengeAnswerBox, AnswerSubmission, Article, LeaderboardEntry

class TestDatabaseOperations:
    def test_database_connection(self, app):
        """Test basic database connection"""
        with app.app_context():
            try:
                # Simple query to test connection
                user_count = User.query.count()
                assert isinstance(user_count, int)
            except Exception as e:
                pytest.fail(f"Database connection failed: {str(e)}")

    def test_transaction_commit(self, app):
        """Test database transaction commit"""
        with app.app_context():
            # Create a new user
            new_user = User(
                full_name='Transaction Test User',
                year=11,
                maths_class='Test Class',
                key_stage='KS4'
            )
            new_user.set_password('testpassword')
            
            db.session.add(new_user)
            db.session.commit()

            # Verify user was committed
            retrieved_user = User.query.filter_by(full_name='Transaction Test User').first()
            assert retrieved_user is not None
            assert retrieved_user.check_password('testpassword')

    def test_complex_relationship_creation(self, app):
        """Test creating complex relationships between models"""
        with app.app_context():
            # Create a user
            user = User(
                full_name='Relationship Test User',
                year=12,
                maths_class='Advanced Maths',
                key_stage='KS5'
            )
            user.set_password('complextest')
            
            # Create a challenge
            challenge = Challenge(
                title='Complex Relationship Challenge',
                content='Test challenge content',
                key_stage='KS5'
            )
            
            # Create answer boxes
            answer_box1 = ChallengeAnswerBox(
                challenge=challenge,
                box_label='Part A',
                correct_answer='42',
                order=1
            )
            
            # Create a submission
            submission = AnswerSubmission(
                user=user,
                challenge=challenge,
                answer_box=answer_box1,
                answer='42',
                is_correct=True
            )
            
            # Create a leaderboard entry
            leaderboard_entry = LeaderboardEntry(
                user=user,
                score=100,
                last_updated=datetime.now(),
                key_stage='KS5'
            )
            
            # Add all to session and commit
            db.session.add_all([user, challenge, answer_box1, submission, leaderboard_entry])
            db.session.commit()
            
            # Verify relationships
            assert len(user.submissions) == 1
            assert user.submissions[0] == submission
            assert len(user.leaderboard_entries) == 1
            assert challenge.submissions[0] == submission

    def test_cascade_delete(self, app, test_user):
        """Test cascade delete functionality"""
        with app.app_context():
            # Create a user with an article
            article = Article(
                title='Math Insights', 
                content='Interesting math article', 
                named_creator='Admin',
                type='article',
                user_id=test_user.id,
                date_posted=datetime.now()
                )

            
            db.session.add(article)
            db.session.commit()
            
            # Store the article ID before deletion
            article_id = article.id
            
            # Delete the user (which should cascade to articles)
            db.session.delete(test_user)
            db.session.commit()
            
            # Verify article is deleted
            deleted_article = Article.query.get(article_id)
            assert deleted_article is None

    def test_database_performance(self, app):
        """Basic performance test for database queries"""
        with app.app_context():
            # Create multiple users
            users = [
                User(
                    full_name=f'Performance Test User {i}',
                    year=10,
                    maths_class=f'Class {i}',
                    key_stage='KS4'
                ) for i in range(100)
            ]
            
            db.session.add_all(users)
            db.session.commit()
            
            # Time a bulk query
            import time
            start_time = time.time()
            all_users = User.query.filter(User.key_stage == 'KS4').all()
            query_time = time.time() - start_time
            
            assert len(all_users) > 0
            assert query_time < 1.0, f"Query took too long: {query_time} seconds"

    def test_database_rollback(self, app):
        """Test session rollback functionality"""
        with app.app_context():
            # Start a transaction
            user = User(
                full_name='Rollback Test User',
                year=11,
                maths_class='Test Class',
                key_stage='KS4'
            )
            user.set_password('rollbacktest')
            
            db.session.add(user)
            
            # Simulate an error condition
            try:
                # This would normally raise an error
                db.session.flush()
                # Simulate an error
                raise ValueError("Simulated error")
            except ValueError:
                # Rollback the session
                db.session.rollback()
            
            # Verify no user was added
            retrieved_user = User.query.filter_by(full_name='Rollback Test User').first()
            assert retrieved_user is None