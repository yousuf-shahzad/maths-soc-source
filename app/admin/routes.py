import os, datetime
from werkzeug.utils import secure_filename
from io import BytesIO
from flask import render_template, flash, redirect, url_for, request, send_from_directory, current_app, send_file
from flask_login import login_required, current_user
from flask_ckeditor import upload_success, upload_fail
import string, random
from app import db
from app.admin import bp
from app.models import Article, Challenge, User, AnswerSubmission, ChallengeAnswerBox, LeaderboardEntry
from app.admin.forms import ChallengeForm, ArticleForm, AnswerSubmissionForm, LeaderboardEntryForm
from app.auth.forms import RegistrationForm

@bp.route('/admin')
@login_required
def admin_index():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    return render_template('admin/index.html', title='Admin Dashboard')

# ! ARTICLE ROUTES

@bp.route('/admin/articles/create', methods=['GET', 'POST'])
@login_required
def create_article():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    
    form = ArticleForm()
    if form.validate_on_submit():
        article = Article(
            title=form.title.data,
            content=form.content.data,
            named_creator=form.author.data,
            user_id=current_user.id,
            type=form.type.data,
            date_posted = datetime.datetime.now(),
        )
        
        if form.file.data:
            # Create newsletters directory if it doesn't exist
            print(form.file.data)
            newsletter_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'newsletters')
            os.makedirs(newsletter_path, exist_ok=True)
            
            # Save PDF file
            checking_id = article.date_posted.strftime('%Y_%m')
            filename = secure_filename(f"newsletter_{checking_id}_{form.file.data.filename}")
            file_path = os.path.join(newsletter_path, filename)
            form.file.data.save(file_path)
            article.file_url = filename

        db.session.add(article)
        db.session.commit()
        flash(f'{form.type.data.capitalize()} created successfully.')
        return redirect(url_for('admin.manage_articles'))
    
    return render_template('admin/create_article.html', title='Create Article/Newsletter', form=form)

@bp.route('/admin/articles')
@login_required
def manage_articles():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    articles = Article.query.order_by(Article.date_posted.desc()).all()
    return render_template('admin/manage_articles.html', title='Manage Articles and Newsletters', articles=articles)

# In admin/routes.py

@bp.route('/admin/articles/edit/<int:article_id>', methods=['GET', 'POST'])
@login_required
def edit_article(article_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    
    article = Article.query.get_or_404(article_id)
    form = ArticleForm(obj=article)

    if form.validate_on_submit():
        article.title = form.title.data
        article.content = form.content.data
        article.named_creator = form.author.data
        article.type = form.type.data
        
        if form.file.data:
            # Create newsletters directory if it doesn't exist
            newsletter_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'newsletters')
            os.makedirs(newsletter_path, exist_ok=True)
            
            # Delete old file if it exists
            if article.file_url:
                old_file_path = os.path.join(newsletter_path, article.file_url)
                try:
                    os.remove(old_file_path)
                except OSError:
                    pass
            
            # Save new PDF file
            filename = secure_filename(f"newsletter_{article.date_posted.strftime('%Y_%m')}_{form.file.data.filename}")
            file_path = os.path.join(newsletter_path, filename)
            form.file.data.save(file_path)
            article.file_url = filename
        
        db.session.commit()
        flash(f'{article.type.capitalize()} updated successfully.')
        return redirect(url_for('admin.manage_articles'))
    
    # Pre-populate the form
    form.title.data = article.title
    form.content.data = article.content
    form.author.data = article.named_creator
    form.type.data = article.type
    
    return render_template('admin/edit_article.html', 
                         title=f'Edit {article.type.capitalize()}', 
                         form=form, 
                         article=article)

@bp.route('/admin/articles/delete/<int:article_id>')
@login_required
def delete_article(article_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    
    article = Article.query.get_or_404(article_id)
    
    # Delete associated PDF file if it exists
    if article.type == 'newsletter' and article.file_url:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 
                                'newsletters', 
                                article.file_url)
        try:
            os.remove(file_path)
        except OSError:
            current_app.logger.warning(f"Could not delete file: {file_path}")
    
    db.session.delete(article)
    db.session.commit()
    
    flash(f'{article.type.capitalize()} deleted successfully.')
    return redirect(url_for('admin.manage_articles'))

# ! CHALLENGE ROUTES

def create_challenge_folder(create_date):
    create_date = create_date.strftime('%Y-%m-%d')
    print(create_date)
    challenge_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f'challenge_{create_date}')
    challenge_responses = os.path.join(challenge_path, 'responses/')
    os.makedirs(os.path.dirname(challenge_responses), exist_ok=True)
    return challenge_path

# Modified route handler
@bp.route('/challenges/<int:challenge_id>', methods=['GET', 'POST'])
@login_required
def view_challenge(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    form = AnswerSubmissionForm()
    
    if form.validate_on_submit():
        submission = AnswerSubmission(
            user_id=current_user.id,
            challenge_id=challenge.id,
            answer=form.answer.data
        )
        
        try:
            db.session.add(submission)
            db.session.commit()
            
            is_correct = form.answer.data.lower().strip() == challenge.correct_answer.lower().strip()
            flash(f'Your answer is {"correct" if is_correct else "incorrect"}!',
                  'success' if is_correct else 'error')
                  
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error: {str(e)}")
            flash('Error submitting answer. Please try again.', 'error')
        
        return redirect(url_for('admin.view_challenge', challenge_id=challenge_id))
    
    # Get previous submissions for this user and challenge
    previous_submission = AnswerSubmission.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id
    ).first()
    
    if previous_submission:
        form.answer.data = previous_submission.answer
    
    return render_template('admin/challenge.html', 
                         title=challenge.title,
                         challenge=challenge,
                         form=form)

@bp.route('/admin/challenges/create', methods=['GET', 'POST'])
@login_required
def create_challenge():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('main.index'))

    form = ChallengeForm()
    if form.validate_on_submit():
        try:
            challenge = Challenge(
                title=form.title.data,
                content=form.content.data,
                date_posted=datetime.datetime.now(),
                key_stage=form.key_stage.data
            )
            
            challenge_folder = create_challenge_folder(challenge.date_posted)
            if form.image.data:
                try:
                    filename = secure_filename(form.image.data.filename)
                    file_path = os.path.join(challenge_folder, filename)
                    form.image.data.save(file_path)
                    challenge.file_url = filename
                except IOError as e:
                    current_app.logger.error(f"File save error: {str(e)}")
                    flash('Error saving the image file. Please try again.', 'error')
                    return render_template('admin/create_challenge.html', title='Create Challenge', form=form)

            # Add challenge first to get the ID
            db.session.add(challenge)
            db.session.flush()

            # Create answer boxes
            for box_form in form.answer_boxes:
                answer_box = ChallengeAnswerBox(
                    challenge_id=challenge.id,
                    box_label=box_form.box_label.data,
                    correct_answer=box_form.correct_answer.data,
                    order=int(box_form.order.data) if box_form.order.data else None
                )
                db.session.add(answer_box)

            db.session.commit()
            flash('Challenge added successfully.', 'success')
            return redirect(url_for('admin.manage_challenges'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating challenge: {str(e)}")
            flash('An error occurred while creating the challenge. Please try again.', 'error')
    else:
        if form.errors:
            print(form.errors)
            flash('Error creating challenge. Please check the form for errors.', 'error')

    return render_template('admin/create_challenge.html', title='Create Challenge', form=form)

@bp.route('/admin/challenges/edit/<int:challenge_id>', methods=['GET', 'POST'])
@login_required
def edit_challenge(challenge_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    
    challenge = Challenge.query.get_or_404(challenge_id)
    form = ChallengeForm(obj=challenge)

    if form.validate_on_submit():
        challenge.title = form.title.data
        challenge.content = form.content.data
        challenge.key_stage = form.key_stage.data
        
        # Handle image upload
        if form.image.data:
            try:
                challenge_folder = create_challenge_folder(challenge.date_posted)
                filename = secure_filename(form.image.data.filename)
                file_path = os.path.join(challenge_folder, filename)
                form.image.data.save(file_path)
                challenge.file_url = filename
            except IOError as e:
                current_app.logger.error(f"File save error: {str(e)}")
                flash('Error saving the image file. Please try again.', 'error')
                return render_template('admin/edit_challenge.html', title='Edit Challenge', form=form)

        # Get existing answer boxes
        existing_boxes = {box.order: box for box in challenge.answer_boxes}
        used_box_ids = set()
        
        # Update or create answer boxes
        for index, box_form in enumerate(form.answer_boxes):
            if index in existing_boxes:
                # Update existing box
                box = existing_boxes[index]
                box.box_label = box_form.box_label.data
                box.correct_answer = box_form.correct_answer.data
                box.order = int(box_form.order.data) if box_form.order.data else index
                used_box_ids.add(box.id)
            else:
                # Create new box
                new_box = ChallengeAnswerBox(
                    challenge_id=challenge.id,
                    box_label=box_form.box_label.data,
                    correct_answer=box_form.correct_answer.data,
                    order=int(box_form.order.data) if box_form.order.data else index
                )
                db.session.add(new_box)
        
        # Delete unused boxes (only those without submissions)
        for box in challenge.answer_boxes:
            if box.id not in used_box_ids:
                # Check if box has submissions
                if not box.submissions:
                    db.session.delete(box)
                else:
                    # Archive the box instead of deleting it
                    box.is_active = False
        
        try:
            db.session.commit()
            flash('Challenge updated successfully.')
            return redirect(url_for('admin.manage_challenges'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error: {str(e)}")
            flash('Error updating the challenge. Please try again.', 'error')
            return render_template('admin/edit_challenge.html', title='Edit Challenge', form=form)
    
    # Pre-populate the form
    if request.method == 'GET':
        form.title.data = challenge.title
        form.content.data = challenge.content
        form.key_stage.data = challenge.key_stage
        
        # Clear existing answer boxes and add current ones
        form.answer_boxes.entries = []
        for box in sorted(challenge.answer_boxes, key=lambda x: x.order or 0):
            form.answer_boxes.append_entry({
                'box_label': box.box_label,
                'correct_answer': box.correct_answer,
                'order': str(box.order) if box.order is not None else ''
            })
        
        if challenge.file_url:
            post_date = challenge.date_posted.strftime('%Y-%m-%d')
            form.file_url = f'challenge_{post_date}/{challenge.file_url}'
        
    return render_template('admin/edit_challenge.html', title='Edit Challenge', form=form)

@bp.route('/static/uploads/<path:id>')
def uploaded_files(id):
    challenge = Challenge.query.get_or_404(id)
    date_posted = challenge.date_posted.strftime('%Y-%m-%d')
    filename = challenge.file_url
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], f'challenge_{date_posted}/{filename}')

@bp.route('/admin/upload', methods=['POST', 'GET'])
@login_required
def upload():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    f = request.files.get('upload')
    if not f:
        return upload_fail(message='No file uploaded.')
    
    extension = f.filename.split('.')[-1].lower()
    if extension not in ['jpg', 'jpeg', 'png', 'gif']:
        return upload_fail(message='Image files only (jpg, jpeg, png, gif).')

    file_path = os.path.join(bp.config['UPLOAD_FOLDER'], f.filename)
    f.save(file_path)

    file_url = url_for('uploaded_files', filename=f.filename)
    return upload_success(file_url, filename=f.filename)

@bp.route('/admin/challenges')
@login_required
def manage_challenges():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    challenges = Challenge.query.order_by(Challenge.date_posted.desc()).all()
    return render_template('admin/manage_challenges.html', title='Manage Challenges', challenges=challenges)
    
@bp.route('/admin/challenges/delete/<int:challenge_id>')
@login_required
def delete_challenge(challenge_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    
    challenge = Challenge.query.get_or_404(challenge_id)

    try:
        filename = challenge.file_url
        os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
    except:
        pass

    try:
        date_posted = challenge.date_posted.strftime('%Y-%m-%d')
        os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], f'challenge_{date_posted}/responses/'))
    except:
        pass

    submissions = AnswerSubmission.query.filter_by(challenge_id=challenge_id).all()
    for submission in submissions:
        db.session.delete(submission)

    db.session.delete(challenge)
    db.session.commit()
    flash('Challenge deleted successfully.')
    return redirect(url_for('admin.manage_challenges'))

# ! USER ROUTES

@bp.route('/admin/toggle_admin/<int:user_id>')
@login_required
def toggle_admin(user_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    flash(f'Admin status for {user.username} has been toggled.')
    return redirect(url_for('admin.manage_users'))

@bp.route('/admin/manage_users')
@login_required
def manage_users():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    users = User.query.all()
    return render_template('admin/manage_users.html', title='Manage Users', users=users)

def generate_random_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

@bp.route('/admin/manage_users/reset_password/<int:user_id>')
@login_required
def reset_password(user_id: int):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    user = User.query.get(user_id)
    random_password = generate_random_password()
    user.set_password(random_password)
    db.session.commit()
    flash(f'Password for {user.username} has been reset to: {random_password}')
    return redirect(url_for('admin.manage_users'))

@bp.route('/admin/manage_users/delete/<int:user_id>')
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    if current_user.id == user_id:
        flash('You cannot delete your own account.')
        return redirect(url_for('admin.manage_users'))
    user = User.query.get_or_404(user_id)
    LeaderboardEntry.query.filter_by(user_id=user.id).delete()
    Article.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    try:
        db.session.commit()
        flash('User and associated data deleted successfully.')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the user.')
        current_app.logger.error(f'Error deleting user: {str(e)}')
    
    return redirect(url_for('admin.manage_users'))

@bp.route('/admin/manage_users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    user = User.query.get_or_404(user_id)
    form = RegistrationForm(obj=user)
    if form.validate_on_submit():
        if form.year.data == '7' or form.year.data == '8' or form.year.data == '9':
            key_stage = 'KS3'
        elif form.year.data == '10' or form.year.data == '11':
            key_stage = 'KS4'
        elif form.year.data == '12' or form.year.data == '13':
            key_stage = 'KS5'
        user.username = form.username.data
        user.year = form.year.data
        user.key_stage = key_stage
        db.session.commit()
        flash('User updated successfully.')
        return redirect(url_for('admin.manage_users'))
    return render_template('admin/edit_user.html', title='Edit User', form=form, user=user)

@bp.route('/admin/manage_users/create', methods=['GET', 'POST'])
@login_required
def create_user():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        if form.year.data == '7' or form.year.data == '8' or form.year.data == '9':
            key_stage = 'KS3'
        elif form.year.data == '10' or form.year.data == '11':
            key_stage = 'KS4'
        elif form.year.data == '12' or form.year.data == '13':
            key_stage = 'KS5'
        user = User(username=form.username.data, year=form.year.data, key_stage=key_stage, is_admin=form.is_admin.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('User created successfully.')
        return redirect(url_for('admin.manage_users'))
    return render_template('admin/create_user.html', title='Create User', form=form)

# ! LEADERBOARD ROUTES

@bp.route('/admin/manage_leaderboard')
@login_required
def manage_leaderboard():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    
    # Get all leaderboard entries ordered by points
    leaderboard = LeaderboardEntry.query.join(User).order_by(LeaderboardEntry.score.desc()).all()
    
    # Calculate statistics
    total_participants = LeaderboardEntry.query.count()
    highest_score = db.session.query(db.func.max(LeaderboardEntry.score)).scalar() or 0
    average_score = db.session.query(db.func.avg(LeaderboardEntry.score)).scalar() or 0
    
    # Get settings from app config
    export_enabled = current_app.config.get('ENABLE_LEADERBOARD_EXPORT', False)
    
    return render_template('admin/manage_leaderboard.html',
                         title='Manage Leaderboard',
                         leaderboard=leaderboard,
                         total_participants=total_participants,
                         highest_score=highest_score,
                         average_score=average_score,
                         export_enabled=export_enabled)

@bp.route('/admin/leaderboard')
@login_required
def leaderboard():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    leaderboard = LeaderboardEntry.query.order_by(LeaderboardEntry.score.desc()).all()
    return render_template('admin/leaderboard.html', title='Leaderboard', leaderboard=leaderboard)

@bp.route('/admin/leaderboard/reset')
@login_required
def reset_leaderboard():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    LeaderboardEntry.query.delete()
    db.session.commit()
    flash('Leaderboard reset successfully.')
    return redirect(url_for('admin.leaderboard'))

@bp.route('/admin/leaderboard/delete/<int:entry_id>')
@login_required
def delete_leaderboard_entry(entry_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    entry = LeaderboardEntry.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    flash('Leaderboard entry deleted successfully.')
    return redirect(url_for('admin.leaderboard'))

@bp.route('/admin/leaderboard/edit/<int:entry_id>', methods
=['GET', 'POST'])
@login_required
def edit_leaderboard_entry(entry_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    entry = LeaderboardEntry.query.get_or_404(entry_id)
    form = LeaderboardEntryForm(obj=entry)
    if form.validate_on_submit():
        entry.user_id = form.user_id.data
        entry.score = form.score.data
        db.session.commit()
        flash('Leaderboard entry updated successfully.')
        return redirect(url_for('admin.leaderboard'))
    return render_template('admin/edit_leaderboard_entry.html', title='Edit Leaderboard Entry', form=form, entry=entry)

@bp.route('/admin/leaderboard/create', methods=['GET', 'POST'])
@login_required
def create_leaderboard_entry():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.index'))
    form = LeaderboardEntryForm()
    if form.validate_on_submit():
        entry = LeaderboardEntry(user_id=form.user_id.data, score=form.score.data)
        db.session.add(entry)
        db.session.commit()
        flash('Leaderboard entry created successfully.')
        return redirect(url_for('admin.leaderboard'))
    return render_template('admin/create_leaderboard_entry.html', title='Create Leaderboard Entry', form=form)

# ! ERROR HANDLERS

@bp.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500
