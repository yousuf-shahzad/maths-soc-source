import os
from flask import abort, current_app, render_template, flash, redirect, send_from_directory, url_for, request
from flask_login import login_required, current_user
import datetime
from app import db
from app.main import bp
from app.models import Challenge, Article, LeaderboardEntry, AnswerSubmission
from app.admin.forms import AnswerSubmissionForm

@bp.route('/')
@bp.route('/index')
def index():
    return render_template('index.html', title='Home')

@bp.route('/challenges')
def challenges():
    page = request.args.get('page', 1, type=int)
    challenges = Challenge.query.order_by(Challenge.date_posted.desc()).paginate(
        page=page, per_page=6, error_out=False)
    return render_template('main/challenges.html', challenges=challenges)

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

def check_user_submission_count(user_id, challenge_id):
    return AnswerSubmission.query.filter_by(user_id=user_id, challenge_id=challenge_id).count()

def has_correct_submission(user_id, challenge_id):
    return AnswerSubmission.query.filter_by(
        user_id=user_id,
        challenge_id=challenge_id,
        is_correct=True
    ).first() is not None

@bp.route('/challenges/<int:challenge_id>', methods=['GET', 'POST'])
@login_required
def challenge(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    form = AnswerSubmissionForm()
    
    # Check if user has already solved this challenge
    already_solved = has_correct_submission(current_user.id, challenge_id)
    
    # Check submission count before processing form
    submission_count = check_user_submission_count(current_user.id, challenge_id)
    if submission_count >= 3 and not already_solved:
        flash('You have reached the maximum number of attempts (3) for this challenge.', 'error')
        return render_template('main/challenge.html',
                             title=challenge.title,
                             challenge=challenge,
                             form=form,
                             attempts_remaining=0,
                             already_solved=already_solved)
    
    if form.validate_on_submit():
        submission = AnswerSubmission(
            user_id=current_user.id,
            challenge_id=challenge.id,
            answer=form.answer.data,
            submitted_at=datetime.datetime.utcnow()
        )
        
        try:
            is_correct = form.answer.data.lower().strip() == challenge.correct_answer.lower().strip()
            submission.is_correct = is_correct
            db.session.add(submission)
            db.session.commit()
            
            # Update submission count after successful submission
            new_submission_count = check_user_submission_count(current_user.id, challenge_id)
            attempts_remaining = 3 - new_submission_count
            
            if is_correct:
                message = 'Congratulations! Your answer is correct! You have completed this challenge! 🎉'
            else:
                message = 'Your answer is incorrect.'
                if attempts_remaining > 0:
                    message += f' You have {attempts_remaining} attempts remaining.'
                else:
                    message += ' This was your last attempt.'
                
            flash(message, 'success' if is_correct else 'error')
                  
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error: {str(e)}")
            flash('Error submitting answer. Please try again.', 'error')
        
        return redirect(url_for('main.challenge', challenge_id=challenge_id))
    
    # Calculate attempts remaining for display
    attempts_remaining = 3 - submission_count
    
    # Get user's submissions for this challenge
    submissions = AnswerSubmission.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id
    ).order_by(AnswerSubmission.submitted_at.desc()).all()
    
    return render_template('main/challenge.html', 
                         title=challenge.title,
                         challenge=challenge,
                         form=form,
                         attempts_remaining=attempts_remaining,
                         already_solved=already_solved,
                         submissions=submissions)

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