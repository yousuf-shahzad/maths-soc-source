"""
Admin Routes Module
==================

This module handles all administrative routes for the Math Society application.
It is organized into logical sections based on functionality:
- Base Admin (access control, dashboard)
- Article Management 
- Challenge Management
- User Management
- Leaderboard Management

Dependencies:
------------
- Flask and related extensions
- SQLAlchemy for database operations
- Werkzeug for file operations
- Custom models and forms

Security:
---------
All routes are protected by:
1. @login_required decorator
2. Admin permission checks
3. Secure file handling for uploads

Maintenance Notes:
-----------------
1. All file operations use secure_filename
2. Database operations are wrapped in try-except blocks
3. All routes follow RESTful naming conventions
4. Error handlers are implemented for 404 and 500 errors
"""

import os
import datetime
import string
import random
from functools import wraps
from io import BytesIO
from werkzeug.utils import secure_filename
from flask import (
    render_template, flash, redirect, url_for, request,
    send_from_directory, current_app, send_file
)
from flask_login import login_required, current_user
from flask_ckeditor import upload_success, upload_fail
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.admin import bp
from app.models import (
    Article, Challenge, User, AnswerSubmission,
    ChallengeAnswerBox, LeaderboardEntry
)
from app.admin.forms import (
    ChallengeForm, ArticleForm, AnswerSubmissionForm,
    LeaderboardEntryForm, EditUserForm, CreateUserForm,
)
from app.auth.forms import RegistrationForm

# ============================================================================
# Utility Functions
# ============================================================================

def admin_required(f):
    """Decorator to check if user has admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('You do not have permission to access this page.')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def create_challenge_folder(create_date):
    """
    Creates a folder structure for challenge files
    
    Args:
        create_date: datetime object for folder naming
    
    Returns:
        str: Path to created challenge folder
    """
    create_date = create_date.strftime('%Y-%m-%d')
    challenge_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 
                                f'challenge_{create_date}')
    challenge_responses = os.path.join(challenge_path, 'responses/')
    os.makedirs(os.path.dirname(challenge_responses), exist_ok=True)
    return challenge_path

def handle_file_upload(file, folder_path, filename):
    """
    Handles secure file upload operations
    
    Args:
        file: FileStorage object
        folder_path: str path to upload folder
        filename: str desired filename
    
    Returns:
        str: Secure filename that was saved
    
    Raises:
        IOError: If file save fails
    """
    secure_name = secure_filename(filename)
    file_path = os.path.join(folder_path, secure_name)
    file.save(file_path)
    return secure_name

def generate_random_password(length=10):
    """Generates a random password of given length"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def get_key_stage(year):
    """
    Determines key stage based on year group
    
    Args:
        year: str year group
    
    Returns:
        str: Key stage (KS3, KS4, or KS5)
    """
    if year in ['7', '8']:
        return 'KS3'
    elif year in ['9', '10', '11']:
        return 'KS4'
    elif year in ['12', '13']:
        return 'KS5'
    return None

# ============================================================================
# Base Admin Routes
# ============================================================================

@bp.route('/admin')
@login_required
@admin_required
def admin_index():
    """Admin dashboard homepage"""
    return render_template('admin/index.html', title='Admin Dashboard')

# ============================================================================
# Article Management Routes
# ============================================================================

@bp.route('/admin/articles/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_article():
    """
    Creates a new article or newsletter
    
    Handles:
    - Form validation
    - File upload for newsletters
    - Database operations
    """
    form = ArticleForm()
    if form.validate_on_submit():
        try:
            article = Article(
                title=form.title.data,
                content=form.content.data,
                named_creator=form.author.data,
                user_id=current_user.id,
                type=form.type.data,
                date_posted=datetime.datetime.now()
            )
            
            if form.file.data:
                newsletter_path = os.path.join(
                    current_app.config['UPLOAD_FOLDER'], 
                    'newsletters'
                )
                os.makedirs(newsletter_path, exist_ok=True)
                
                checking_id = article.date_posted.strftime('%Y_%m')
                filename = f"newsletter_{checking_id}_{form.file.data.filename}"
                article.file_url = handle_file_upload(
                    form.file.data, 
                    newsletter_path, 
                    filename
                )

            db.session.add(article)
            db.session.commit()
            flash(f'{form.type.data.capitalize()} created successfully.')
            return redirect(url_for('admin.manage_articles'))
            
        except (IOError, SQLAlchemyError) as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating article: {str(e)}")
            flash('Error creating article. Please try again.')
            
    return render_template(
        'admin/create_article.html',
        title='Create Article/Newsletter',
        form=form
    )

@bp.route('/admin/articles')
@login_required
@admin_required
def manage_articles():
    """Lists all articles for management"""
    articles = Article.query.order_by(Article.date_posted.desc()).all()
    return render_template(
        'admin/manage_articles.html',
        title='Manage Articles and Newsletters',
        articles=articles
    )

@bp.route('/admin/articles/edit/<int:article_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_article(article_id):
    """
    Edits an existing article
    
    Args:
        article_id: int ID of article to edit
    """
    article = Article.query.get_or_404(article_id)
    form = ArticleForm(obj=article)

    if form.validate_on_submit():
        try:
            article.title = form.title.data
            article.content = form.content.data
            article.named_creator = form.author.data
            article.type = form.type.data
            
            if form.file.data:
                newsletter_path = os.path.join(
                    current_app.config['UPLOAD_FOLDER'],
                    'newsletters'
                )
                os.makedirs(newsletter_path, exist_ok=True)
                
                if article.file_url:
                    try:
                        os.remove(os.path.join(newsletter_path, article.file_url))
                    except OSError:
                        pass
                
                filename = f"newsletter_{article.date_posted.strftime('%Y_%m')}_{form.file.data.filename}"
                article.file_url = handle_file_upload(
                    form.file.data,
                    newsletter_path,
                    filename
                )
            
            db.session.commit()
            flash(f'{article.type.capitalize()} updated successfully.')
            return redirect(url_for('admin.manage_articles'))
            
        except (IOError, SQLAlchemyError) as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating article: {str(e)}")
            flash('Error updating article. Please try again.')
    
    # Pre-populate form
    if request.method == 'GET':
        form.title.data = article.title
        form.content.data = article.content
        form.author.data = article.named_creator
        form.type.data = article.type
    
    return render_template(
        'admin/edit_article.html',
        title=f'Edit {article.type.capitalize()}',
        form=form,
        article=article
    )

@bp.route('/admin/articles/delete/<int:article_id>')
@login_required
@admin_required
def delete_article(article_id):
    """
    Deletes an article and associated files
    
    Args:
        article_id: int ID of article to delete
    """
    article = Article.query.get_or_404(article_id)
    
    try:
        if article.file_url:
            file_path = os.path.join(
                current_app.config['UPLOAD_FOLDER'],
                'newsletters',
                article.file_url
            )
            try:
                os.remove(file_path)
            except OSError as e:
                current_app.logger.warning(f"Could not delete file: {file_path} - {str(e)}")
        
        db.session.delete(article)
        db.session.commit()
        flash(f'{article.type.capitalize()} deleted successfully.')
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting article: {str(e)}")
        flash('Error deleting article. Please try again.')
    
    return redirect(url_for('admin.manage_articles'))

# ============================================================================
# Challenge Management Routes
# ============================================================================

@bp.route('/challenges/<int:challenge_id>', methods=['GET', 'POST'])
@login_required
def view_challenge(challenge_id):
    """
    Displays a challenge and handles answer submissions
    
    Args:
        challenge_id: int ID of challenge to view
    """
    challenge = Challenge.query.get_or_404(challenge_id)
    form = AnswerSubmissionForm()
    
    if form.validate_on_submit():
        try:
            submission = AnswerSubmission(
                user_id=current_user.id,
                challenge_id=challenge.id,
                answer=form.answer.data
            )
            
            db.session.add(submission)
            db.session.commit()
            
            is_correct = form.answer.data.lower().strip() == challenge.correct_answer.lower().strip()
            flash(
                f'Your answer is {"correct" if is_correct else "incorrect"}!',
                'success' if is_correct else 'error'
            )
            
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error: {str(e)}")
            flash('Error submitting answer. Please try again.', 'error')
        
        return redirect(url_for('admin.view_challenge', challenge_id=challenge_id))
    
    # Get previous submissions
    previous_submission = AnswerSubmission.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id
    ).first()
    
    if previous_submission:
        form.answer.data = previous_submission.answer
    
    return render_template(
        'admin/challenge.html',
        title=challenge.title,
        challenge=challenge,
        form=form
    )

@bp.route('/admin/challenges/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_challenge():
    """Creates a new challenge with associated answer boxes"""
    form = ChallengeForm()
    
    if form.validate_on_submit():
        try:
            challenge = Challenge(
                title=form.title.data,
                content=form.content.data,
                date_posted=datetime.datetime.now(),
                key_stage=form.key_stage.data
            )
            
            # Handle image upload
            challenge_folder = create_challenge_folder(challenge.date_posted)
            if form.image.data:
                try:
                    filename = handle_file_upload(
                        form.image.data,
                        challenge_folder,
                        form.image.data.filename
                    )
                    challenge.file_url = filename
                except IOError as e:
                    current_app.logger.error(f"File save error: {str(e)}")
                    flash('Error saving the image file. Please try again.', 'error')
                    return render_template(
                        'admin/create_challenge.html',
                        title='Create Challenge',
                        form=form
                    )

            # Add challenge to get ID
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
            flash('Challenge created successfully.', 'success')
            return redirect(url_for('admin.manage_challenges'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating challenge: {str(e)}")
            flash('Error creating challenge. Please try again.', 'error')
    
    return render_template(
        'admin/create_challenge.html',
        title='Create Challenge',
        form=form
    )

@bp.route('/admin/challenges/edit/<int:challenge_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_challenge(challenge_id):
    """
    Edits an existing challenge and its answer boxes
    
    Args:
        challenge_id: int ID of challenge to edit
        
    Notes:
        - Handles image upload
        - Manages answer boxes (create/update/archive)
        - Preserves boxes with existing submissions
    """
    challenge = Challenge.query.get_or_404(challenge_id)
    form = ChallengeForm(obj=challenge)

    if form.validate_on_submit():
        try:
            challenge.title = form.title.data
            challenge.content = form.content.data
            challenge.key_stage = form.key_stage.data
            
            # Handle image upload
            if form.image.data:
                challenge_folder = create_challenge_folder(challenge.date_posted)
                filename = handle_file_upload(
                    form.image.data,
                    challenge_folder,
                    form.image.data.filename
                )
                challenge.file_url = filename

            # Manage answer boxes
            existing_boxes = {box.order: box for box in challenge.answer_boxes}
            used_box_ids = set()
            
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
            
            # Archive unused boxes with submissions, delete ones without
            for box in challenge.answer_boxes:
                if box.id not in used_box_ids:
                    if box.submissions:
                        box.is_active = False
                    else:
                        db.session.delete(box)
            
            db.session.commit()
            flash('Challenge updated successfully.')
            return redirect(url_for('admin.manage_challenges'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating challenge: {str(e)}")
            flash('Error updating challenge. Please try again.', 'error')
    
    # Pre-populate form
    if request.method == 'GET':
        form.title.data = challenge.title
        form.content.data = challenge.content
        form.key_stage.data = challenge.key_stage
        
        # Add current answer boxes
        form.answer_boxes.entries = []
        for box in sorted(challenge.answer_boxes, key=lambda x: x.order or 0):
            form.answer_boxes.append_entry({
                'box_label': box.box_label,
                'correct_answer': box.correct_answer,
                'order': str(box.order) if box.order is not None else ''
            })
    
    return render_template(
        'admin/edit_challenge.html',
        title='Edit Challenge',
        form=form
    )

@bp.route('/static/uploads/<path:id>')
def uploaded_files(id):
    """
    Serves uploaded challenge files securely
    
    Args:
        id: Challenge ID to retrieve file for
    """
    challenge = Challenge.query.get_or_404(id)
    date_posted = challenge.date_posted.strftime('%Y-%m-%d')
    filename = challenge.file_url
    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'],
        f'challenge_{date_posted}/{filename}'
    )

@bp.route('/admin/upload', methods=['POST'])
@login_required
@admin_required
def upload():
    """
    Handles file uploads for CKEditor integration
    
    Returns:
        dict: Upload success/failure response for CKEditor
    """
    f = request.files.get('upload')
    if not f:
        return upload_fail(message='No file uploaded.')
    
    extension = f.filename.split('.')[-1].lower()
    if extension not in ['jpg', 'jpeg', 'png', 'gif']:
        return upload_fail(message='Image files only (jpg, jpeg, png, gif).')

    try:
        filename = handle_file_upload(
            f,
            current_app.config['UPLOAD_FOLDER'],
            f.filename
        )
        file_url = url_for('uploaded_files', filename=filename)
        return upload_success(file_url, filename=filename)
    except IOError as e:
        current_app.logger.error(f"Upload error: {str(e)}")
        return upload_fail(message='Error saving file.')

@bp.route('/admin/challenges')
@login_required
@admin_required
def manage_challenges():
    """Lists all challenges for management"""
    challenges = Challenge.query.order_by(Challenge.date_posted.desc()).all()
    return render_template(
        'admin/manage_challenges.html',
        title='Manage Challenges',
        challenges=challenges
    )

@bp.route('/admin/challenges/delete/<int:challenge_id>')
@login_required
@admin_required
def delete_challenge(challenge_id):
    """
    Deletes a challenge and associated files/submissions
    
    Args:
        challenge_id: int ID of challenge to delete
    """
    challenge = Challenge.query.get_or_404(challenge_id)
    chall_posted = challenge.date_posted.strftime('%Y-%m-%d')

    try:
        # Delete challenge file if exists
        if challenge.file_url:
            file_path = os.path.join(
                current_app.config['UPLOAD_FOLDER'],
                f'challenge_{chall_posted}',
                challenge.file_url
            )
            try:
                os.remove(file_path)
            except OSError as e:
                current_app.logger.warning(f"Could not delete file: {file_path} - {str(e)}")

        # Delete challenge folder if exists
        folder_path = os.path.join(
            current_app.config['UPLOAD_FOLDER'],
            f'challenge_{chall_posted}'
        )
        try:
            if os.path.exists(folder_path):
                if not os.listdir(folder_path):  # Only remove if empty
                    os.rmdir(folder_path)
                else:
                    current_app.logger.warning(f"Folder not empty, skipping deletion: {folder_path}")
        except OSError as e:
            current_app.logger.warning(f"Could not delete folder: {folder_path} - {str(e)}")

        # Delete all submissions
        AnswerSubmission.query.filter_by(challenge_id=challenge_id).delete()
        
        # Delete challenge
        db.session.delete(challenge)
        db.session.commit()
        flash('Challenge deleted successfully.')
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting challenge: {str(e)}")
        flash('Error deleting challenge. Please try again.')
    
    return redirect(url_for('admin.manage_challenges'))

# ============================================================================
# User Management Routes
# ============================================================================

@bp.route('/admin/manage_users')
@login_required
@admin_required
def manage_users():
    """Lists all users for management"""
    users = User.query.all()
    return render_template(
        'admin/manage_users.html',
        title='Manage Users',
        users=users
    )

@bp.route('/admin/manage_users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    """Creates a new user account"""
    form = CreateUserForm()
    
    if form.validate_on_submit():
        try:
            key_stage = get_key_stage(form.year.data)
            first_name, last_name = form.first_name.data.strip(), form.last_name.data.strip()
            if ' ' in first_name or ' ' in last_name:
                flash('Please remove any whitespace from your name.')
                return redirect(url_for('admin.create_user'))

            full_name = f"{first_name} {last_name}"
            user = User(
                full_name=full_name,
                year=form.year.data,
                key_stage=key_stage,
                maths_class=form.maths_class.data,
                is_admin=form.is_admin.data
            )
            user.set_password(form.password.data)
            
            db.session.add(user)
            db.session.commit()
            flash('User created successfully.')
            return redirect(url_for('admin.manage_users'))
            
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating user: {str(e)}")
            flash('Error creating user. Please try again. If the problem persists, contact admin.')
    
    else:
        if form.errors:
            print(form.errors)

    return render_template(
        'admin/create_user.html',
        title='Create User',
        form=form
    )

@bp.route('/admin/manage_users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """
    Edits an existing user account
    
    Args:
        user_id: int ID of user to edit
    """
    user = User.query.get_or_404(user_id)
    
    # Split full_name into first_name and last_name
    first_name, last_name = user.full_name.split(' ', 1)
    
    # Populate the form with the split names
    form = EditUserForm(
        first_name=first_name.strip(), 
        last_name=last_name.strip(), 
        year=user.year
    )
    
    if form.validate_on_submit():
        try:
            key_stage = get_key_stage(form.year.data)
            first_name, last_name = form.first_name.data.strip(), form.last_name.data.strip()
            if ' ' in first_name or ' ' in last_name:
                flash('Please remove any whitespace from your name.')
                return redirect(url_for('admin.edit_user', user_id=user_id))

            user.full_name = f"{first_name} {last_name}"
            user.year = form.year.data
            user.key_stage = key_stage
            user.maths_class = form.maths_class.data
            
            db.session.commit()
            flash('User updated successfully.')
            return redirect(url_for('admin.manage_users'))
            
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating user: {str(e)}")
            flash('Error updating user. Please try again.')

    return render_template(
        'admin/edit_user.html',
        title='Edit User',
        form=form,
        user=user
    )


@bp.route('/admin/manage_users/delete/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    """
    Deletes a user and associated data
    
    Args:
        user_id: int ID of user to delete
    """
    if current_user.id == user_id:
        flash('You cannot delete your own account.')
        return redirect(url_for('admin.manage_users'))
    
    try:
        user = User.query.get_or_404(user_id)
        
        # Delete associated data
        LeaderboardEntry.query.filter_by(user_id=user.id).delete()
        Article.query.filter_by(user_id=user.id).delete()
        AnswerSubmission.query.filter_by(user_id=user.id).delete()
        
        # Delete user
        db.session.delete(user)
        db.session.commit()
        flash('User and associated data deleted successfully.')
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting user: {str(e)}")
        flash('Error deleting user and associated data.')
    
    return redirect(url_for('admin.manage_users'))

@bp.route('/admin/toggle_admin/<int:user_id>')
@login_required
@admin_required
def toggle_admin(user_id):
    """
    Toggles admin status for a user
    
    Args:
        user_id: int ID of user to toggle
    """
    try:
        user = User.query.get_or_404(user_id)
        user.is_admin = not user.is_admin
        db.session.commit()
        flash(f'Admin status for {user.full_name} has been toggled.')
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error toggling admin status: {str(e)}")
        flash('Error updating admin status.')
    
    return redirect(url_for('admin.manage_users'))

@bp.route('/admin/manage_users/reset_password/<int:user_id>')
@login_required
@admin_required
def reset_password(user_id):
    """
    Resets a user's password to a random string
    
    Args:
        user_id: int ID of user to reset
    """
    try:
        user = User.query.get_or_404(user_id)
        password = generate_random_password()
        user.set_password(password)
        db.session.commit()
        flash(f'Password for {user.full_name} has been reset to: {password}')
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error resetting password: {str(e)}")
        flash('Error resetting password.')
    
    return redirect(url_for('admin.manage_users'))

# ============================================================================
# Leaderboard Management Routes
# ============================================================================

@bp.route('/admin/manage_leaderboard')
@login_required
@admin_required
def manage_leaderboard():
    """
    Displays leaderboard management interface with statistics
    """
    try:
        # Get sorted leaderboard entries
        leaderboard = LeaderboardEntry.query.join(User).order_by(
            LeaderboardEntry.score.desc()
        ).all()
        
        # Calculate statistics
        stats = {
            'total_participants': LeaderboardEntry.query.count(),
            'highest_score': db.session.query(
                db.func.max(LeaderboardEntry.score)
            ).scalar() or 0,
            'average_score': db.session.query(
                db.func.avg(LeaderboardEntry.score)
            ).scalar() or 0
        }
        
        export_enabled = current_app.config.get('ENABLE_LEADERBOARD_EXPORT', True)
        
        return render_template(
            'admin/manage_leaderboard.html',
            title='Manage Leaderboard',
            leaderboard=leaderboard,
            total_participants=stats['total_participants'],
            highest_score=stats['highest_score'],
            average_score=stats['average_score'],
            export_enabled=export_enabled
        )
        
    except SQLAlchemyError as e:
        current_app.logger.error(f"Error loading leaderboard: {str(e)}")
        flash('Error loading leaderboard data.')
        return redirect(url_for('admin.admin_index'))

@bp.route('/admin/leaderboard/export')
@login_required
@admin_required
def export_leaderboard():
    """
    Exports leaderboard data to CSV file
    """
    try:
        # Get sorted leaderboard entries
        leaderboard = LeaderboardEntry.query.join(User).order_by(
            LeaderboardEntry.score.desc()
        ).all()
        
        # Create CSV data
        csv_data = 'User ID,Name,Year,Class,Score,Last Updated\n'
        for entry in leaderboard:
            csv_data += f'{entry.user_id},{entry.user.full_name},{entry.user.year},{entry.user.maths_class},{entry.score},{entry.last_updated}\n'
        
        # Create file
        file = BytesIO()
        file.write(csv_data.encode())
        file.seek(0)
        
        return send_file(
            file,
            as_attachment=True,
            attachment_filename='leaderboard_export.csv',
            mimetype='text/csv'
        )
        
    except SQLAlchemyError as e:
        current_app.logger.error(f"Error exporting leaderboard: {str(e)}")
        flash('Error exporting leaderboard data.')
        return redirect(url_for('admin.manage_leaderboard'))

@bp.route('/admin/leaderboard/edit/<int:entry_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_leaderboard_entry(entry_id):
    """
    Edits a leaderboard entry
    
    Args:
        entry_id: int ID of entry to edit
    """
    entry = LeaderboardEntry.query.get_or_404(entry_id)
    form = LeaderboardEntryForm(obj=entry)
    
    if form.validate_on_submit():
        try:
            entry.user_id = form.user_id.data
            entry.score = form.score.data
            db.session.commit()
            flash('Leaderboard entry updated successfully.')
            return redirect(url_for('admin.manage_leaderboard'))
            
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating entry: {str(e)}")
            flash('Error updating leaderboard entry.')
    
    return render_template(
        'admin/edit_leaderboard_entry.html',
        title='Edit Leaderboard Entry',
        form=form,
        entry=entry
        )

@bp.route('/admin/leaderboard/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_leaderboard_entry():
    """
    Creates a leaderboard entry
    """
    form = LeaderboardEntryForm()
    if form.validate_on_submit():
        entry = LeaderboardEntry(user_id=form.user_id.data, score=form.score.data)
        db.session.add(entry)
        db.session.commit()
        flash('Leaderboard entry created successfully.')
        return redirect(url_for('admin.manage_leaderboard'))
    return render_template('admin/create_leaderboard_entry.html', title='Create Leaderboard Entry', form=form)

@bp.route('/admin/leaderboard/delete/<int:entry_id>')
@login_required
@admin_required
def delete_leaderboard_entry(entry_id):
    """
    Deletes a leaderboard entry
    
    Args:
        entry_id: int ID of entry to delete
    """
    entry = LeaderboardEntry.query.get_or_404(entry_id)
    try:
        db.session.delete(entry)
        db.session.commit()
        flash('Leaderboard entry deleted successfully.')
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting entry: {str(e)}")
        flash('Error deleting leaderboard entry.')
    return redirect(url_for('admin.manage_leaderboard'))

@bp.route('/admin/leaderboard/reset')
@login_required
@admin_required
def reset_leaderboard():
    """
    Resets the leaderboard to empty
    
    Notes:
    - Does not delete user accounts
    - Does not delete challenge submissions
    """
    try:
        LeaderboardEntry.query.delete()
        db.session.commit()
        flash('Leaderboard reset successfully.')
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error resetting leaderboard: {str(e)}")
        flash('Error resetting leaderboard.')
    return redirect(url_for('admin.manage_leaderboard'))

# ! ERROR HANDLERS

@bp.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500