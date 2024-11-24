"""
Main Routes Module

This module handles all the main user-facing routes of the application including:
- Homepage and navigation
- Challenge viewing and submission
- Article and newsletter management
- Leaderboard functionality

Security:
- All sensitive routes require authentication
- File access is properly sanitized
- User permissions are checked appropriately

Dependencies:
- Flask-Login for user authentication
- SQLAlchemy for database operations
- WTForms for form handling
"""

import os
from flask import abort, current_app, render_template, flash, redirect, send_from_directory, url_for, request
from flask_login import login_required, current_user
import datetime
from typing import Dict, List
from app import db
from sqlalchemy.exc import SQLAlchemyError
from app.main import bp
from app.models import Challenge, Article, LeaderboardEntry, AnswerSubmission, ChallengeAnswerBox
from app.admin.forms import AnswerSubmissionForm, AnswerBoxForm


# ============================================================================
# View Routes
# ============================================================================

@bp.route('/')
@bp.route('/index')
def index():
    """Homepage route showing recent content and top performers."""
    try:
        challenges = Challenge.query
        articles = Article.query
        leaderboard_entries = LeaderboardEntry.query
        recent_challenges = Challenge.query.order_by(
                Challenge.date_posted.desc()
            ).limit(3).all()
            
        recent_articles = Article.query.filter_by(
            type='article'
        ).order_by(Article.date_posted.desc()).limit(3).all()
        
        top_performers = LeaderboardEntry.query.order_by(
            LeaderboardEntry.score.desc()
        ).limit(5).all()
        
        latest_newsletter = Article.query.filter_by(
            type='newsletter'
        ).order_by(Article.date_posted.desc()).first()
        return render_template('index.html',
                            challenges=challenges,
                            articles=articles,
                            leaderboard_entries=leaderboard_entries,
                            recent_challenges=recent_challenges,
                            recent_articles=recent_articles,
                            top_performers=top_performers,
                            latest_newsletter=latest_newsletter)
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in index route: {str(e)}")
        flash("An error occurred while loading the homepage.", "error")
        return redirect(url_for('main.about'))

@bp.route('/about')
def about():
    """About page route."""
    return render_template('main/about.html', title='About')

# ============================================================================
# Challenge Routes
# ============================================================================

@bp.route('/challenges')
def challenges():
    """List all challenges with pagination."""
    page = request.args.get('page', 1, type=int)
    try:
        challenges_pagination = Challenge.query.order_by(
            Challenge.date_posted.desc()
        ).paginate(page=page, per_page=6, error_out=False)
        
        return render_template('main/challenges.html', 
                             challenges=challenges_pagination)
    except SQLAlchemyError as e:
        current_app.logger.error(f"Error loading challenges: {str(e)}")
        flash("Unable to load challenges at this time.", "error")
        return redirect(url_for('main.index'))

def check_submission_count(user_id: int, challenge_id: int, box_id: int) -> int:
    """
    Check how many submissions a user has made for a specific answer box.
    
    Args:
        user_id: The ID of the user
        challenge_id: The ID of the challenge
        box_id: The ID of the answer box
        
    Returns:
        Number of submissions
    """
    return AnswerSubmission.query.filter_by(
        user_id=user_id,
        challenge_id=challenge_id,
        answer_box_id=box_id
    ).count()

def create_submission(user_id: int, challenge_id: int, 
                     answer_box: ChallengeAnswerBox, 
                     submitted_answer: str) -> AnswerSubmission:
    """
    Create and save a new submission.
    
    Args:
        user_id: The ID of the user
        challenge_id: The ID of the challenge
        answer_box: The answer box object
        submitted_answer: The user's submitted answer
        
    Returns:
        Created AnswerSubmission object
    """
    submission = AnswerSubmission(
        user_id=user_id,
        challenge_id=challenge_id,
        answer_box_id=answer_box.id,
        answer=submitted_answer,
        is_correct=submitted_answer.lower().strip() == answer_box.correct_answer.lower().strip()
    )
    
    db.session.add(submission)
    db.session.commit()
    return submission

def check_all_answers_correct(challenge: Challenge, user_id: int) -> bool:
    """
    Check if user has correct submissions for all answer boxes in a challenge.
    
    Args:
        challenge: The Challenge object
        user_id: The ID of the user
        
    Returns:
        True if all answers are correct, False otherwise
    """
    return all(
        AnswerSubmission.query.filter_by(
            user_id=user_id,
            challenge_id=challenge.id,
            answer_box_id=box.id,
            is_correct=True
        ).first() is not None
        for box in challenge.answer_boxes
    )

def update_leaderboard(user_id: int, points: int) -> None:
    """
    Update user's points on the leaderboard.
    
    Args:
        user_id: The ID of the user
        points: Number of points to add
    """
    leaderboard_entry = LeaderboardEntry.query.filter_by(user_id=user_id).first()
    
    if leaderboard_entry:
        leaderboard_entry.points += points
    else:
        leaderboard_entry = LeaderboardEntry(user_id=user_id, points=points)
        db.session.add(leaderboard_entry)
    
    db.session.commit()

def handle_submission_result(submission: AnswerSubmission, 
                           challenge: Challenge,
                           answer_box: ChallengeAnswerBox) -> None:
    """
    Handle the result of a submission, updating points and showing appropriate messages.
    
    Args:
        submission: The AnswerSubmission object
        challenge: The Challenge object
        answer_box: The ChallengeAnswerBox object
    """
    submission_count = check_submission_count(
        submission.user_id, challenge.id, answer_box.id
    )
    
    if submission.is_correct:
        flash(f'Correct answer for {answer_box.box_label}!', 'success')
        
        # Check if all parts are now correct
        if check_all_answers_correct(challenge, submission.user_id):
            flash('Congratulations! You have completed all parts of this challenge! 🎉', 'success')
            
            # Award bonus points for first correct solution
            if challenge.first_correct_submission is None:
                challenge.first_correct_submission = datetime.datetime.utcnow()
                update_leaderboard(submission.user_id, 3)  # First solution bonus
            else:
                update_leaderboard(submission.user_id, 1)  # Regular completion points
            
            db.session.commit()
    else:
        remaining = 3 - submission_count
        flash(f'Incorrect answer for {answer_box.box_label}. {remaining} attempts remaining.', 'error')

@bp.route('/challenges/<int:challenge_id>', methods=['GET', 'POST'])
@login_required
def challenge(challenge_id: int):
    """
    Display and handle submissions for a specific challenge.
    
    Args:
        challenge_id: The ID of the challenge to display
        
    Returns:
        Rendered challenge template or redirect
    """
    challenge = Challenge.query.get_or_404(challenge_id)
    forms = {}
    submissions = {}
    
    # Create forms and get submissions for each answer box
    for answer_box in challenge.answer_boxes:
        forms[answer_box.id] = AnswerSubmissionForm()
        submissions[answer_box.id] = AnswerSubmission.query.filter_by(
            user_id=current_user.id,
            challenge_id=challenge_id,
            answer_box_id=answer_box.id
        ).order_by(AnswerSubmission.submitted_at.desc()).all()
    
    if request.method == 'POST':
        return handle_challenge_submission(challenge, forms)
    
    all_correct = check_all_answers_correct(challenge, current_user.id)
    
    return render_template('main/challenge.html',
                         challenge=challenge,
                         forms=forms,
                         submissions=submissions,
                         attempts_remaining=3,
                         all_correct=all_correct)

def handle_challenge_submission(challenge: Challenge, forms: Dict) -> redirect:
    """
    Process a challenge submission.
    
    Args:
        challenge: The Challenge object
        forms: Dictionary of forms for each answer box
        
    Returns:
        Redirect response
    """
    box_id = int(request.form.get('answer_box_id'))
    form = forms[box_id]
    
    if not form.validate_on_submit():
        flash("Invalid submission.", "error")
        return redirect(url_for('main.challenge', challenge_id=challenge.id))
    
    answer_box = ChallengeAnswerBox.query.get_or_404(box_id)
    submission_count = check_submission_count(
        current_user.id, challenge.id, box_id
    )
    
    if submission_count >= 3 and not has_correct_submission(current_user.id, challenge.id):
        flash('You have reached the maximum attempts for this part.', 'error')
        return redirect(url_for('main.challenge', challenge_id=challenge.id))
    
    submission = create_submission(
        current_user.id, challenge.id, 
        answer_box, form.answer.data
    )
    
    handle_submission_result(submission, challenge, answer_box)
    return redirect(url_for('main.challenge', challenge_id=challenge.id))

@bp.route('/articles')
def articles():
    articles = Article.query.filter_by(type='article').order_by(Article.date_posted.desc()).all()
    return render_template('main/articles.html', title='Articles', articles=articles)

@bp.route('/newsletters/<path:filename>')
def serve_newsletter(filename):
    return send_from_directory(
        os.path.join(current_app.config['UPLOAD_FOLDER'], 'newsletters'),
        filename
    )

def update_leaderboard(user_id, score):
    entry = LeaderboardEntry.query.filter_by(user_id=user_id).first()
    if entry is None:
        entry = LeaderboardEntry(user_id=user_id, score=score)
        db.session.add(entry)
    else:
        entry.score += score
    entry.last_updated = datetime.datetime.utcnow()
    db.session.commit()

def check_user_submission_count(user_id, challenge_id):
    return AnswerSubmission.query.filter_by(user_id=user_id, challenge_id=challenge_id).count()

def has_correct_submission(user_id, challenge_id):
    return AnswerSubmission.query.filter_by(
        user_id=user_id,
        challenge_id=challenge_id,
        is_correct=True
    ).first() is not None

@bp.route('/newsletters')
def newsletters():
    newsletters = Article.query.filter_by(type='newsletter').order_by(Article.date_posted.desc()).all()
    return render_template('main/newsletters.html', title='Newsletters', articles=newsletters)

@bp.route('/newsletter/<int:id>')
def newsletter(id):
    article = Article.query.get_or_404(id)
    if article.type != 'newsletter':
        abort(404)
    return render_template('main/newsletter.html', article=article)

@bp.route('/article/<int:id>')
def article(id):
    article = Article.query.get_or_404(id)
    return render_template('main/article.html', title=article.title, article=article)

@bp.route('/leaderboard')
def leaderboard():
    entries = LeaderboardEntry.query.order_by(LeaderboardEntry.score.desc()).limit(10).all()
    return render_template('main/leaderboard.html', title='Leaderboard', entries=entries)