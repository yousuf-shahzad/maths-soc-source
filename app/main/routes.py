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
    challenges = Challenge.query.order_by(Challenge.date_posted.desc()).all()
    return render_template('main/challenges.html', title='Challenges', challenges=challenges)

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

@bp.route('/challenges/<int:challenge_id>', methods=['GET', 'POST'])
@login_required
def challenge(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    form = AnswerSubmissionForm()
    
    if form.validate_on_submit():
        submission = AnswerSubmission(
            user_id=current_user.id,
            challenge_id=challenge.id,
            answer=form.answer.data,
            submitted_at=datetime.datetime.utcnow()
        )
        
        try:
            db.session.add(submission)
            db.session.commit()
            
            is_correct = form.answer.data.lower().strip() == challenge.correct_answer.lower().strip()
            print(submission.answer)
            submission.is_correct = is_correct
            flash(f'Your answer is {"correct" if is_correct else "incorrect"}!',
                  'success' if is_correct else 'error')
                  
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error: {str(e)}")
            flash('Error submitting answer. Please try again.', 'error')
        
        return redirect(url_for('main.challenge', challenge_id=challenge_id))
    
    return render_template('main/challenge.html', 
                         title=challenge.title,
                         challenge=challenge,
                         form=form)

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