import os
from flask import abort, current_app, render_template, flash, redirect, send_from_directory, url_for, request
from flask_login import login_required, current_user
import datetime
from app import db
from app.main import bp
from app.models import Challenge, Article, LeaderboardEntry, AnswerSubmission, ChallengeAnswerBox
from app.admin.forms import AnswerSubmissionForm, AnswerBoxForm

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

@bp.route('/challenges/<int:challenge_id>', methods=['GET', 'POST'])
@login_required
def challenge(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    forms = {}
    submissions = {}
    all_correct = False
    
    # Create a form for each answer box
    for answer_box in challenge.answer_boxes:
        form = AnswerSubmissionForm()
        forms[answer_box.id] = form
        
        # Get existing submissions for this box
        box_submissions = AnswerSubmission.query.filter_by(
            user_id=current_user.id,
            challenge_id=challenge_id,
            answer_box_id=answer_box.id
        ).order_by(AnswerSubmission.submitted_at.desc()).all()
        
        submissions[answer_box.id] = box_submissions
    
    if request.method == 'POST':
        box_id = int(request.form.get('answer_box_id'))
        form = forms[box_id]
        
        if form.validate_on_submit():
            submission_count = AnswerSubmission.query.filter_by(
                user_id=current_user.id,
                challenge_id=challenge_id,
                answer_box_id=box_id
            ).count()
            
            if submission_count >= 3:
                flash(f'You have reached the maximum attempts for this part.', 'error')
                return redirect(url_for('main.challenge', challenge_id=challenge_id))
            
            answer_box = ChallengeAnswerBox.query.get(box_id)
            submission = AnswerSubmission(
                user_id=current_user.id,
                challenge_id=challenge_id,
                answer_box_id=box_id,
                answer=form.answer.data,
                is_correct=form.answer.data.lower().strip() == answer_box.correct_answer.lower().strip()
            )
            
            db.session.add(submission)
            db.session.commit()
            
            # Check if all boxes have correct answers
            all_correct = all(
                AnswerSubmission.query.filter_by(
                    user_id=current_user.id,
                    challenge_id=challenge_id,
                    answer_box_id=box.id,
                    is_correct=True
                ).first() is not None
                for box in challenge.answer_boxes
            )
            
            if submission.is_correct:
                flash(f'Correct answer for {answer_box.box_label}!', 'success')
                if all_correct:
                    flash('Congratulations! You have completed all parts of this challenge! 🎉', 'success')
                    if challenge.first_correct_submission is None:
                        challenge.first_correct_submission = datetime.datetime.utcnow()
                        update_leaderboard(current_user.id, 3)
                        db.session.commit()
                    else:
                        update_leaderboard(current_user.id, 1)

            else:
                remaining = 2 - submission_count
                flash(f'Incorrect answer for {answer_box.box_label}. {remaining} attempts remaining.', 'error')
            
            return redirect(url_for('main.challenge', challenge_id=challenge_id))
    
    return render_template('main/challenge.html',
                         challenge=challenge,
                         forms=forms,
                         submissions=submissions,
                         attempts_remaining=3,
                         all_correct=all_correct)

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