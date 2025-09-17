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
- Announcement Management

Dependencies:
------------
- Flask and related extensions
- SQLAlchemy for database operations
- Werkzeug for file operations
- Custom models and forms using Flask-WTF

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
from datetime import timedelta
import string
import random
from functools import wraps
from io import BytesIO
from werkzeug.utils import secure_filename
from flask import (
    render_template,
    flash,
    redirect,
    url_for,
    request,
    send_from_directory,
    current_app,
    send_file,
    jsonify,
)
from flask_login import login_required, current_user
from flask_ckeditor import upload_success, upload_fail
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import cast, String

from app import db
from app.admin import bp
from app.models import (
    Article,
    Challenge,
    User,
    AnswerSubmission,
    Announcement,
    ChallengeAnswerBox,
    LeaderboardEntry,
    School,
    SummerChallenge,
    SummerChallengeAnswerBox,
    SummerLeaderboard,
    SummerSubmission
)
from app.admin.forms import (
    ChallengeForm,
    ArticleForm,
    AnswerSubmissionForm,
    LeaderboardEntryForm,
    EditUserForm,
    CreateUserForm,
    AnnouncementForm,
    SchoolForm,
    SummerChallengeForm,
    SummerLeaderboardEntryForm,
    AnswerBoxForm
)

# ============================================================================
# Utility Functions
# ============================================================================


def admin_required(f):
    """Decorator to check if user has admin privileges"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash("You do not have permission to access this page.")
            return redirect(url_for("main.home"))
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
    create_date = create_date.strftime("%Y-%m-%d")
    challenge_path = os.path.join(
        current_app.config["UPLOAD_FOLDER"], f"challenge_{create_date}"
    )
    challenge_responses = os.path.join(challenge_path, "responses/")
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
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def get_key_stage(year):
    """
    Determines key stage based on year group

    Args:
        year: str year group

    Returns:
        str: Key stage (KS3, KS4, or KS5)
    """
    if year in ["7", "8"]:
        return "KS3"
    elif year in ["9", "10", "11"]:
        return "KS4"
    elif year in ["12", "13"]:
        return "KS5"
    return None


# ============================================================================
# Base Admin Routes
# ============================================================================


@bp.route("/admin")
@login_required
@admin_required
def admin_index():
    """Admin dashboard homepage"""
    now = datetime.datetime.now()
    
    # Get statistics for dashboard
    total_challenges = Challenge.query.count()
    released_challenges = Challenge.query.filter(Challenge.release_at <= now).count()
    unreleased_challenges = Challenge.query.filter(Challenge.release_at > now).count()
    
    stats = {
        'total_challenges': total_challenges,
        'released_challenges': released_challenges,
        'unreleased_challenges': unreleased_challenges,
        'total_users': User.query.count(),
        'total_articles': Article.query.count()
    }
    
    return render_template("admin/index.html", title="Admin Dashboard", stats=stats)


@bp.route("/admin/math-engine-tester")
@login_required
@admin_required
def math_engine_tester():
    """
    Math engine testing interface for administrators.
    
    Provides a web interface to test mathematical expression equivalence
    and normalization functionality.
    
    Returns:
        Rendered math engine tester template
    """
    return render_template("admin/math_engine_tester.html", title="Math Engine Tester")


# ============================================================================
# Article Management Routes
# ============================================================================


@bp.route("/admin/articles/create", methods=["GET", "POST"])
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
                date_posted=datetime.datetime.now(),
            )

            if form.file.data:
                newsletter_path = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], "newsletters"
                )
                os.makedirs(newsletter_path, exist_ok=True)

                checking_id = article.date_posted.strftime("%Y_%m")
                filename = f"newsletter_{checking_id}_{form.file.data.filename}"
                article.file_url = handle_file_upload(
                    form.file.data, newsletter_path, filename
                )

            db.session.add(article)
            db.session.commit()
            flash(f"{form.type.data.capitalize()} created successfully.")
            return redirect(url_for("admin.manage_articles"))

        except (IOError, SQLAlchemyError) as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating article: {str(e)}")
            flash("Error creating article. Please try again.")

    return render_template(
        "admin/create_article.html", title="Create Article/Newsletter", form=form
    )


@bp.route("/admin/articles")
@login_required
@admin_required
def manage_articles():
    """Lists all articles for management"""
    articles = Article.query.order_by(Article.date_posted.desc()).all()
    return render_template(
        "admin/manage_articles.html",
        title="Manage Articles and Newsletters",
        articles=articles,
    )


@bp.route("/admin/articles/edit/<int:article_id>", methods=["GET", "POST"])
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
                    current_app.config["UPLOAD_FOLDER"], "newsletters"
                )
                os.makedirs(newsletter_path, exist_ok=True)

                if article.file_url:
                    try:
                        os.remove(os.path.join(newsletter_path, article.file_url))
                    except OSError:
                        pass

                filename = f"newsletter_{article.date_posted.strftime('%Y_%m')}_{form.file.data.filename}"
                article.file_url = handle_file_upload(
                    form.file.data, newsletter_path, filename
                )

            db.session.commit()
            flash(f"{article.type.capitalize()} updated successfully.")
            return redirect(url_for("admin.manage_articles"))

        except (IOError, SQLAlchemyError) as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating article: {str(e)}")
            flash("Error updating article. Please try again.")

    # Pre-populate form
    if request.method == "GET":
        form.title.data = article.title
        form.content.data = article.content
        form.author.data = article.named_creator
        form.type.data = article.type

    return render_template(
        "admin/edit_article.html",
        title=f"Edit {article.type.capitalize()}",
        form=form,
        article=article,
    )


@bp.route("/admin/articles/delete/<int:article_id>")
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
                current_app.config["UPLOAD_FOLDER"], "newsletters", article.file_url
            )
            try:
                os.remove(file_path)
            except OSError as e:
                current_app.logger.warning(
                    f"Could not delete file: {file_path} - {str(e)}"
                )

        db.session.delete(article)
        db.session.commit()
        flash(f"{article.type.capitalize()} deleted successfully.")

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting article: {str(e)}")
        flash("Error deleting article. Please try again.")

    return redirect(url_for("admin.manage_articles"))


# ============================================================================
# Challenge Management Routes
# ============================================================================


@bp.route("/challenges/<int:challenge_id>", methods=["GET", "POST"])
@login_required
def view_challenge(challenge_id):
    """
    Displays a challenge and handles answer submissions
    Only shows challenges that have been released or if user is admin
    """
    challenge = Challenge.query.get_or_404(challenge_id)
    
    # Check if challenge is released (unless user is admin)
    if not current_user.is_admin and challenge.release_at and challenge.release_at > datetime.datetime.now():
        flash("This challenge is not yet available.")
        return redirect(url_for("main.challenges"))
    
    form = AnswerSubmissionForm()

    # Handle form submission - COPY EXACT LOGIC FROM SUMMER CHALLENGES
    if form.validate_on_submit():
        # Check if challenge is locked - if so, don't allow submissions
        if challenge.is_locked and not current_user.is_admin:
            flash("This challenge is locked. No more submissions are allowed.")
            return redirect(url_for("admin.view_challenge", challenge_id=challenge_id))
            
        try:
            answer_box_id = request.form.get("answer_box_id")
            answer_box = ChallengeAnswerBox.query.get_or_404(answer_box_id)
            
            # Check if user already has a correct submission for this box
            existing_correct = AnswerSubmission.query.filter_by(
                user_id=current_user.id,
                answer_box_id=answer_box_id,
                is_correct=True
            ).first()
            
            if existing_correct:
                flash("You have already correctly answered this part.")
                return redirect(url_for("admin.view_challenge", challenge_id=challenge_id))
            
            # Create new submission
            submission = AnswerSubmission(
                user_id=current_user.id,
                challenge_id=challenge_id,
                answer_box_id=answer_box_id,
                answer=form.answer.data,
                is_correct=(form.answer.data.strip() == answer_box.correct_answer.strip())
            )
            
            db.session.add(submission)
            db.session.commit()
            
            if submission.is_correct:
                flash("Correct! Well done!")
            else:
                flash("Incorrect. Try again!")

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error submitting answer: {str(e)}")
            flash("Error submitting answer. Please try again.")

        return redirect(url_for("admin.view_challenge", challenge_id=challenge_id))

    # Get user's previous submissions and organize by answer box
    submissions = {}
    forms = {}
    
    for answer_box in challenge.answer_boxes:
        user_submissions = AnswerSubmission.query.filter_by(
            user_id=current_user.id,
            answer_box_id=answer_box.id
        ).order_by(AnswerSubmission.submitted_at.desc()).all()
        
        submissions[answer_box.id] = user_submissions
        forms[answer_box.id] = AnswerSubmissionForm()

    # Check if all parts are correct
    all_correct = all(
        any(sub.is_correct for sub in submissions.get(box.id, []))
        for box in challenge.answer_boxes
    )

    return render_template(
        "main/challenge.html", 
        title=challenge.title, 
        challenge=challenge, 
        form=form,
        forms=forms,
        submissions=submissions,
        all_correct=all_correct
    )


@bp.route("/admin/challenges/create", methods=["GET", "POST"])
@login_required
@admin_required
def create_challenge():
    form = ChallengeForm()
    if form.validate_on_submit():
        try:
            # Set release_at to now if not specified
            release_at = form.release_at.data if form.release_at.data else datetime.datetime.now()
            
            challenge = Challenge(
                title=form.title.data,
                content=form.content.data,
                key_stage=form.key_stage.data,
                date_posted=datetime.datetime.now(),
                release_at=release_at,
                lock_after_hours=form.lock_after_hours.data  # Add this
            )

            # Handle image upload
            if form.image.data:
                folder_path = create_challenge_folder(challenge.date_posted)
                filename = handle_file_upload(
                    form.image.data, folder_path, form.image.data.filename
                )
                challenge.file_url = filename

            db.session.add(challenge)
            db.session.flush()  # Get the ID

            # Handle answer boxes
            for box_data in form.answer_boxes.data:
                if box_data["box_label"] and box_data["correct_answer"]:
                    answer_box = ChallengeAnswerBox(
                        challenge_id=challenge.id,
                        box_label=box_data["box_label"],
                        correct_answer=box_data["correct_answer"],
                        order=int(box_data["order"]) if box_data["order"] else 1,
                    )
                    db.session.add(answer_box)

            db.session.commit()
            
            # Provide feedback about release and lock timing
            if release_at <= datetime.datetime.now():
                if form.lock_after_hours.data:
                    flash(f"Challenge created and published! It will automatically lock after {form.lock_after_hours.data} hours.")
                else:
                    flash("Challenge created and published immediately!")
            else:
                if form.lock_after_hours.data:
                    flash(f"Challenge scheduled for release on {release_at.strftime('%B %d, %Y at %I:%M %p')} and will lock after {form.lock_after_hours.data} hours!")
                else:
                    flash(f"Challenge scheduled for release on {release_at.strftime('%B %d, %Y at %I:%M %p')}!")
            
            return redirect(url_for("admin.manage_challenges"))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating challenge: {str(e)}")
            flash("Error creating challenge. Please try again.")

    return render_template(
        "admin/create_challenge.html", title="Create Challenge", form=form
    )

@bp.route("/admin/challenges/toggle_lock/<int:challenge_id>", methods=["POST"])
@login_required
@admin_required
def toggle_challenge_lock(challenge_id):
    """Toggle manual lock status for a challenge"""
    challenge = Challenge.query.get_or_404(challenge_id)
    
    try:
        challenge.is_manually_locked = not challenge.is_manually_locked
        db.session.commit()
        
        if challenge.is_manually_locked:
            flash(f"Challenge '{challenge.title}' has been manually locked. Answers are now revealed.")
        else:
            flash(f"Challenge '{challenge.title}' has been unlocked. Students can submit answers again.")
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error toggling challenge lock: {str(e)}")
        flash("Error updating challenge lock status.")
    
    return redirect(url_for("admin.manage_challenges"))

@bp.route("/admin/challenges/edit/<int:challenge_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_challenge(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    form = ChallengeForm(obj=challenge)

    if form.validate_on_submit():
        try:
            challenge.title = form.title.data
            challenge.content = form.content.data
            challenge.key_stage = form.key_stage.data
            
            # Update release time and lock settings
            if form.release_at.data:
                challenge.release_at = form.release_at.data
            challenge.lock_after_hours = form.lock_after_hours.data

            # Handle image upload
            if form.image.data:
                folder_path = create_challenge_folder(challenge.date_posted)
                filename = handle_file_upload(
                    form.image.data, folder_path, form.image.data.filename
                )
                challenge.file_url = filename

            # Manage answer boxes
            existing_boxes = list(challenge.answer_boxes.order_by(ChallengeAnswerBox.order))
            used_box_ids = set()

            for index, box_form in enumerate(form.answer_boxes):
                # Skip empty box forms
                if not box_form.box_label.data or not box_form.correct_answer.data:
                    continue
                    
                if index < len(existing_boxes):
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
                        order=int(box_form.order.data) if box_form.order.data else index,
                    )
                    db.session.add(new_box)

            # Delete unused boxes (those without submissions)
            for box in existing_boxes:
                if box.id not in used_box_ids:
                    if box.submissions.count() == 0:
                        db.session.delete(box)
                    # Note: Boxes with submissions are preserved to maintain data integrity

            db.session.commit()
            flash("Challenge updated successfully.")
            return redirect(url_for("admin.manage_challenges"))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating challenge: {str(e)}")
            flash("Error updating challenge. Please try again.")

    # Pre-populate form with existing answer boxes on GET request
    if request.method == "GET":
        form.title.data = challenge.title
        form.content.data = challenge.content
        form.key_stage.data = challenge.key_stage
        form.release_at.data = challenge.release_at
        form.lock_after_hours.data = challenge.lock_after_hours
        
        # Add current answer boxes
        form.answer_boxes.entries = []
        for box in sorted(challenge.answer_boxes, key=lambda x: x.order or 0):
            form.answer_boxes.append_entry(
                {
                    "box_label": box.box_label,
                    "correct_answer": box.correct_answer,
                    "order": str(box.order) if box.order is not None else "",
                }
            )

    return render_template(
        "admin/edit_challenge.html", title="Edit Challenge", form=form, challenge=challenge
    )


@bp.route("/static/uploads/<path:id>")
def uploaded_files(id):
    """
    Serves uploaded challenge files securely

    Args:
        id: Challenge ID to retrieve file for
    """
    challenge = Challenge.query.get_or_404(id)
    date_posted = challenge.date_posted.strftime("%Y-%m-%d")
    filename = challenge.file_url
    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"], f"challenge_{date_posted}/{filename}"
    )


@bp.route("/admin/upload", methods=["POST"])
@login_required
@admin_required
def upload():
    """
    Handles file uploads for CKEditor integration

    Returns:
        dict: Upload success/failure response for CKEditor
    """
    f = request.files.get("upload")
    if not f:
        return upload_fail(message="No file uploaded.")

    extension = f.filename.split(".")[-1].lower()
    if extension not in ["jpg", "jpeg", "png", "gif"]:
        return upload_fail(message="Image files only (jpg, jpeg, png, gif).")

    try:
        filename = handle_file_upload(
            f, current_app.config["UPLOAD_FOLDER"], f.filename
        )
        file_url = url_for("uploaded_files", filename=filename)
        return upload_success(file_url, filename=filename)
    except IOError as e:
        current_app.logger.error(f"Upload error: {str(e)}")
        return upload_fail(message="Error saving file.")


@bp.route("/admin/challenges")
@login_required
@admin_required
def manage_challenges():
    """Lists all challenges for management, showing both released and unreleased"""
    now = datetime.datetime.now()
    released_challenges = Challenge.query.filter(Challenge.release_at <= now).order_by(Challenge.date_posted.desc()).all()
    unreleased_challenges = Challenge.query.filter(Challenge.release_at > now).order_by(Challenge.release_at.asc()).all()
    return render_template(
        "admin/manage_challenges.html", 
        title="Manage Challenges", 
        released_challenges=released_challenges,
        unreleased_challenges=unreleased_challenges
    )


@bp.route("/admin/challenges/delete/<int:challenge_id>")
@login_required
@admin_required
def delete_challenge(challenge_id):
    """
    Deletes a challenge and associated files/submissions

    Args:
        challenge_id: int ID of challenge to delete
    """
    challenge = Challenge.query.get_or_404(challenge_id)
    chall_posted = challenge.date_posted.strftime("%Y-%m-%d")

    try:
        # Delete challenge file if exists
        if challenge.file_url:
            file_path = os.path.join(
                current_app.config["UPLOAD_FOLDER"],
                f"challenge_{chall_posted}",
                challenge.file_url,
            )
            try:
                os.remove(file_path)
            except OSError as e:
                current_app.logger.warning(
                    f"Could not delete file: {file_path} - {str(e)}"
                )

        # Delete challenge folder if exists
        folder_path = os.path.join(
            current_app.config["UPLOAD_FOLDER"], f"challenge_{chall_posted}"
        )
        try:
            if os.path.exists(folder_path):
                if not os.listdir(folder_path):  # Only remove if empty
                    os.rmdir(folder_path)
                else:
                    current_app.logger.warning(
                        f"Folder not empty, skipping deletion: {folder_path}"
                    )
        except OSError as e:
            current_app.logger.warning(
                f"Could not delete folder: {folder_path} - {str(e)}"
            )

        # Delete all submissions
        AnswerSubmission.query.filter_by(challenge_id=challenge_id).delete()

        # Delete challenge
        db.session.delete(challenge)
        db.session.commit()
        flash("Challenge deleted successfully.")

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting challenge: {str(e)}")
        flash("Error deleting challenge. Please try again.")

    return redirect(url_for("admin.manage_challenges"))


# ============================================================================
# User Management Routes
# ============================================================================


@bp.route("/admin/manage_users")
@login_required
@admin_required
def manage_users():
    """Enhanced user management with search, filtering, and pagination"""
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    search = request.args.get('search', '', type=str)
    key_stage_filter = request.args.get('key_stage', '', type=str)
    year_filter = request.args.get('year', '', type=str)
    user_type_filter = request.args.get('user_type', '', type=str)
    admin_filter = request.args.get('admin_status', '', type=str)
    
    # Ensure per_page is within reasonable limits
    per_page = min(per_page, 100)  # Max 100 users per page
    
    # Start with base query
    query = User.query
    
    # Apply search filter
    if search:
        search_clean = search.strip()
        search_term = f"%{search_clean}%"
        # Optimise: if purely digits, allow direct equality OR pattern match
        id_filter = []
        if search_clean.isdigit():
            try:
                id_val = int(search_clean)
                id_filter.append(User.id == id_val)
            except ValueError:
                pass
        id_filter.append(cast(User.id, String).like(search_term))
        query = query.filter(
            db.or_(
                User.full_name.ilike(search_term),
                User.email.ilike(search_term),
                User.maths_class.ilike(search_term),
                db.or_(*id_filter)
            )
        )
    
    # Apply key stage filter
    if key_stage_filter and key_stage_filter != 'all':
        query = query.filter(User.key_stage == key_stage_filter)
    
    # Apply year filter
    if year_filter and year_filter != 'all':
        try:
            year_int = int(year_filter)
            query = query.filter(User.year == year_int)
        except ValueError:
            pass
    
    # Apply user type filter
    if user_type_filter and user_type_filter != 'all':
        if user_type_filter == 'competition':
            query = query.filter(User.is_competition_participant == True)
        elif user_type_filter == 'regular':
            query = query.filter(User.is_competition_participant == False)
    
    # Apply admin status filter
    if admin_filter and admin_filter != 'all':
        if admin_filter == 'admin':
            query = query.filter(User.is_admin == True)
        elif admin_filter == 'user':
            query = query.filter(User.is_admin == False)
    
    # Add ordering
    query = query.order_by(User.full_name.asc())
    
    # Execute paginated query
    users_pagination = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # Get statistics for dashboard
    total_users = User.query.count()
    admin_users = User.query.filter(User.is_admin == True).count()
    competition_users = User.query.filter(User.is_competition_participant == True).count()
    
    # Get unique values for filter dropdowns
    available_years = db.session.query(User.year).distinct().filter(User.year.isnot(None)).order_by(User.year).all()
    available_years = [year[0] for year in available_years]
    
    available_key_stages = db.session.query(User.key_stage).distinct().order_by(User.key_stage).all()
    available_key_stages = [ks[0] for ks in available_key_stages]
    
    return render_template(
        "admin/manage_users.html", 
        title="Manage Users",
        users=users_pagination.items,
        pagination=users_pagination,
        total_users=total_users,
        admin_users=admin_users,
        competition_users=competition_users,
        regular_users=total_users - competition_users,
        available_years=available_years,
        available_key_stages=available_key_stages,
        current_filters={
            'search': search,
            'key_stage': key_stage_filter,
            'year': year_filter,
            'user_type': user_type_filter,
            'admin_status': admin_filter,
            'per_page': per_page
        }
    )

@bp.route("/admin/users/search")
@login_required
@admin_required
def users_search():
    """AJAX endpoint for dynamic user search.
    Safe for Postgres (casts integer ID), clamps limits, guards against abuse.
    """
    try:
        query = request.args.get('q', '', type=str)
        limit = request.args.get('limit', 10, type=int)
        # Clamp limit to prevent large scans
        if limit < 1:
            limit = 1
        limit = min(limit, 50)

        # Allow single-character queries only if they are numeric (ID lookup); otherwise require length >=2
        if not query:
            return jsonify({'users': []})
        trimmed = query.strip()
        if len(trimmed) < 2 and not trimmed.isdigit():
            return jsonify({'users': []})

        # Replace original variable usage with trimmed to avoid re-strip calls
        query = trimmed

        search_clean = query
        search_term = f"%{search_clean}%"

        id_clauses = []
        if search_clean.isdigit():
            try:
                id_clauses.append(User.id == int(search_clean))
            except ValueError:
                pass
        id_clauses.append(cast(User.id, String).like(search_term))

        users = User.query.filter(
            db.or_(
                User.full_name.ilike(search_term),
                User.email.ilike(search_term),
                User.maths_class.ilike(search_term),
                db.or_(*id_clauses)
            )
        ).limit(limit).all()

        user_data = []
        for user in users:
            # Some legacy user records or test fixtures may lack date_joined
            date_joined_val = getattr(user, 'date_joined', None)
            if date_joined_val is not None:
                try:
                    date_joined_str = date_joined_val.strftime('%Y-%m-%d')
                except Exception:
                    date_joined_str = None
            else:
                date_joined_str = None
            user_data.append({
                'id': user.id,
                'full_name': user.full_name,
                'email': user.email,
                'maths_class': user.maths_class,
                'key_stage': user.key_stage,
                'year': user.year,
                'is_admin': user.is_admin,
                'is_competition_participant': user.is_competition_participant,
                'date_joined': date_joined_str
            })
        return jsonify({'users': user_data})
    except SQLAlchemyError as e:
        current_app.logger.error(f"User search DB error: {e}")
        return jsonify({'error': 'Search failed'}), 500
    except Exception as e:
        current_app.logger.error(f"User search unexpected error: {e}")
        return jsonify({'error': 'Unexpected error'}), 500

@bp.route("/admin/users/bulk-action", methods=["POST"])
@login_required
@admin_required
def users_bulk_action():
    """Handle bulk actions on users"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    action = data.get('action')
    user_ids = data.get('user_ids', [])
    
    if not action or not user_ids:
        return jsonify({'success': False, 'error': 'Action and user IDs required'}), 400
    
    try:
        users = User.query.filter(User.id.in_(user_ids)).all()
        
        if action == 'promote_admin':
            for user in users:
                if not user.is_admin:  # Don't demote current admin accidentally
                    user.is_admin = True
            db.session.commit()
            return jsonify({'success': True, 'message': f'Promoted {len(users)} users to admin'})
        
        elif action == 'demote_admin':
            # Prevent demoting the current user
            current_user_id = current_user.id
            users_to_demote = [user for user in users if user.id != current_user_id and user.is_admin]
            
            for user in users_to_demote:
                user.is_admin = False
            db.session.commit()
            return jsonify({'success': True, 'message': f'Demoted {len(users_to_demote)} users from admin'})
        
        elif action == 'mark_competition':
            for user in users:
                user.is_competition_participant = True
            db.session.commit()
            return jsonify({'success': True, 'message': f'Marked {len(users)} users as competition participants'})
        
        elif action == 'unmark_competition':
            for user in users:
                user.is_competition_participant = False
            db.session.commit()
            return jsonify({'success': True, 'message': f'Unmarked {len(users)} users from competition'})
        
        elif action == 'delete':
            # Safety check - don't delete current user
            users_to_delete = [user for user in users if user.id != current_user.id]
            
            for user in users_to_delete:
                db.session.delete(user)
            db.session.commit()
            return jsonify({'success': True, 'message': f'Deleted {len(users_to_delete)} users'})
        
        else:
            return jsonify({'success': False, 'error': 'Invalid action'}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route("/admin/users/stats")
@login_required  
@admin_required
def users_stats():
    """Get user statistics for dashboard widgets"""
    total_users = User.query.count()
    admin_users = User.query.filter(User.is_admin == True).count()
    competition_users = User.query.filter(User.is_competition_participant == True).count()
    
    # Users by key stage
    key_stage_stats = db.session.query(
        User.key_stage, 
        db.func.count(User.id)
    ).group_by(User.key_stage).all()
    
    # Users by year
    year_stats = db.session.query(
        User.year,
        db.func.count(User.id)
    ).group_by(User.year).order_by(User.year).all()
    
    # Recent registrations (last 30 days)
    thirty_days_ago = datetime.datetime.now() - timedelta(days=30)
    recent_users = User.query.filter(User.date_joined >= thirty_days_ago).count()
    
    return jsonify({
        'total_users': total_users,
        'admin_users': admin_users,
        'competition_users': competition_users,
        'regular_users': total_users - competition_users,
        'recent_users': recent_users,
        'key_stage_breakdown': dict(key_stage_stats),
        'year_breakdown': dict(year_stats)
    })


@bp.route("/admin/manage_users/create", methods=["GET", "POST"])
@login_required
@admin_required
def create_user():
    """Creates a new user account"""
    form = CreateUserForm()

    if form.validate_on_submit():
        try:
            key_stage = get_key_stage(form.year.data)
            first_name, last_name = (
                form.first_name.data.strip(),
                form.last_name.data.strip(),
            )
            if " " in first_name or " " in last_name:
                flash("Please remove any whitespace from your name.")
                return redirect(url_for("admin.create_user"))

            full_name = f"{first_name} {last_name}"
            
            # Handle school assignment for competition participants
            school_id = None
            if form.is_competition_participant.data:
                if form.school_id.data and form.school_id.data != 0:
                    school_id = form.school_id.data
                else:
                    flash("Please select a school for summer competition participants.")
                    return redirect(url_for("admin.create_user"))
            
            user = User(
                full_name=full_name,
                email=form.email.data.strip().lower(),
                year=form.year.data,
                key_stage=key_stage,
                maths_class=form.maths_class.data if not form.is_competition_participant.data else None,
                is_admin=form.is_admin.data,
                is_competition_participant=form.is_competition_participant.data,
                school_id=school_id,
            )
            user.set_password(form.password.data)

            db.session.add(user)
            db.session.commit()
            flash("User created successfully.")
            return redirect(url_for("admin.manage_users"))

        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Integrity error creating user: {str(e)}")
            if "email" in str(e).lower():
                flash("Error: A user with this email address already exists.")
            else:
                flash("Error creating user: Duplicate data detected.")
        
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating user: {str(e)}")
            flash(
                "Error creating user. Please try again. If the problem persists, contact admin."
            )

    else:
        if form.errors:
            print(form.errors)

    return render_template("admin/create_user.html", title="Create User", form=form)


@bp.route("/admin/manage_users/edit/<int:user_id>", methods=["GET", "POST"])
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
    first_name, last_name = user.full_name.split(" ", 1)

    # Populate the form with the split names and other user data
    form = EditUserForm(
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        email=user.email,
        year=user.year,
        maths_class=user.maths_class,
        is_competition_participant=user.is_competition_participant,
        school_id=user.school_id if user.school_id else 0,
    )

    if form.validate_on_submit():
        try:
            key_stage = get_key_stage(form.year.data)
            first_name, last_name = (
                form.first_name.data.strip(),
                form.last_name.data.strip(),
            )
            if " " in first_name or " " in last_name:
                flash("Please remove any whitespace from your name.")
                return redirect(url_for("admin.edit_user", user_id=user_id))

            # Handle school assignment for competition participants
            school_id = None
            if form.is_competition_participant.data:
                if form.school_id.data and form.school_id.data != 0:
                    school_id = form.school_id.data
                else:
                    flash("Please select a school for summer competition participants.")
                    return redirect(url_for("admin.edit_user", user_id=user_id))

            user.full_name = f"{first_name} {last_name}"
            user.email = form.email.data.strip().lower()
            user.year = form.year.data
            user.key_stage = key_stage
            user.maths_class = form.maths_class.data if not form.is_competition_participant.data else None
            user.is_competition_participant = form.is_competition_participant.data
            user.school_id = school_id

            db.session.commit()
            flash("User updated successfully.")
            return redirect(url_for("admin.manage_users"))

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating user: {str(e)}")
            flash("Error updating user. Please try again.")

    return render_template(
        "admin/edit_user.html", title="Edit User", form=form, user=user
    )


@bp.route("/admin/manage_users/delete/<int:user_id>")
@login_required
@admin_required
def delete_user(user_id):
    """
    Deletes a user and associated data

    Args:
        user_id: int ID of user to delete
    """
    if current_user.id == user_id:
        flash("You cannot delete your own account.")
        return redirect(url_for("admin.manage_users"))

    try:
        user = User.query.get_or_404(user_id)

        # Delete associated data
        LeaderboardEntry.query.filter_by(user_id=user.id).delete()
        Article.query.filter_by(user_id=user.id).delete()
        AnswerSubmission.query.filter_by(user_id=user.id).delete()
        SummerLeaderboard.query.filter_by(user_id=user.id).delete()
        SummerSubmission.query.filter_by(user_id=user.id).delete()

        # Delete user
        db.session.delete(user)
        db.session.commit()
        flash("User and associated data deleted successfully.")

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting user: {str(e)}")
        flash("Error deleting user and associated data.")

    return redirect(url_for("admin.manage_users"))


@bp.route("/admin/toggle_admin/<int:user_id>")
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
        flash(f"Admin status for {user.full_name} has been toggled.")

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error toggling admin status: {str(e)}")
        flash("Error updating admin status.")

    return redirect(url_for("admin.manage_users"))


@bp.route("/admin/manage_users/reset_password/<int:user_id>")
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
        flash(f"Password for {user.full_name} has been reset to: {password}")

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error resetting password: {str(e)}")
        flash("Error resetting password.")

    return redirect(url_for("admin.manage_users"))


# ============================================================================
# Leaderboard Management Routes
# ============================================================================


@bp.route("/admin/manage_leaderboard")
@login_required
@admin_required
def manage_leaderboard():
    """
    Displays leaderboard management interface with key stage statistics
    """
    from app.models import LeaderboardEntry, User
    
    try:
        leaderboard = (
            LeaderboardEntry.query.join(User)
            .order_by(LeaderboardEntry.key_stage, LeaderboardEntry.score.desc())
            .all()
        )

        ks3_count = LeaderboardEntry.query.filter_by(key_stage='KS3').count()
        ks4_count = LeaderboardEntry.query.filter_by(key_stage='KS4').count() 
        ks5_count = LeaderboardEntry.query.filter_by(key_stage='KS5').count()

        # Get unique users across all key stages
        unique_users = db.session.query(LeaderboardEntry.user_id).distinct().count()

        stats = {
            "total_entries": LeaderboardEntry.query.count(),
            "unique_participants": unique_users,
            "highest_score": db.session.query(
                db.func.max(LeaderboardEntry.score)
            ).scalar()
            or 0,
            "average_score": db.session.query(
                db.func.avg(LeaderboardEntry.score)
            ).scalar()
            or 0,
        }

        export_enabled = current_app.config.get("ENABLE_LEADERBOARD_EXPORT", True)

        return render_template(
            "admin/manage_leaderboard.html",
            title="Manage Leaderboard",
            leaderboard=leaderboard,
            total_entries=stats["total_entries"],
            unique_participants=stats["unique_participants"],
            highest_score=stats["highest_score"],
            average_score=stats["average_score"],
            ks3_count=ks3_count,
            ks4_count=ks4_count,
            ks5_count=ks5_count,
            export_enabled=export_enabled,
        )

    except SQLAlchemyError as e:
        current_app.logger.error(f"Error loading leaderboard: {str(e)}")
        flash("Error loading leaderboard data.")
        return redirect(url_for("admin.admin_index"))


@bp.route("/admin/leaderboard/export")
@login_required
@admin_required
def export_leaderboard():
    """
    Exports leaderboard data to CSV file
    """
    try:
        # Get sorted leaderboard entries grouped by key stage
        leaderboard = (
            LeaderboardEntry.query.join(User)
            .order_by(LeaderboardEntry.key_stage, LeaderboardEntry.score.desc())
            .all()
        )

        # Create CSV data
        csv_data = "User ID,Name,Year,Class,Key Stage,Score,Last Updated\n"
        for entry in leaderboard:
            csv_data += f"{entry.user_id},{entry.user.full_name},{entry.user.year},{entry.user.maths_class},{entry.key_stage},{entry.score},{entry.last_updated}\n"

        # Create file
        file = BytesIO()
        file.write(csv_data.encode())
        file.seek(0)

        return send_file(
            file,
            as_attachment=True,
            attachment_filename="leaderboard_export.csv",
            mimetype="text/csv",
        )

    except SQLAlchemyError as e:
        current_app.logger.error(f"Error exporting leaderboard: {str(e)}")
        flash("Error exporting leaderboard data.")
        return redirect(url_for("admin.manage_leaderboard"))


@bp.route("/admin/leaderboard/edit/<int:entry_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_leaderboard_entry(entry_id):
    """
    Edits a leaderboard entry with key stage selection

    Args:
        entry_id: int ID of entry to edit
    """
    from app.admin.forms import LeaderboardEntryForm
    from app.models import User, LeaderboardEntry
    import datetime
    
    entry = LeaderboardEntry.query.get_or_404(entry_id)
    form = LeaderboardEntryForm(obj=entry)
    form.user_id.choices = [(user.id, user.full_name) for user in User.query.all()]

    if form.validate_on_submit():
        try:
            # Check if changing user/key_stage combination would create duplicate
            if (entry.user_id != form.user_id.data or entry.key_stage != form.key_stage.data):
                existing_entry = LeaderboardEntry.query.filter_by(
                    user_id=form.user_id.data, 
                    key_stage=form.key_stage.data
                ).first()
                
                if existing_entry and existing_entry.id != entry.id:
                    flash(f'User already has an entry for {form.key_stage.data}. Please edit that entry instead.', 'error')
                    return render_template(
                        "admin/edit_leaderboard_entry.html",
                        title="Edit Leaderboard Entry",
                        form=form,
                        entry=entry,
                    )

            entry.user_id = form.user_id.data
            entry.score = form.score.data
            entry.key_stage = form.key_stage.data
            entry.last_updated = datetime.datetime.now()
            
            db.session.commit()
            flash('Leaderboard entry updated successfully!', 'success')
            return redirect(url_for('admin.manage_leaderboard'))

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating leaderboard entry: {str(e)}")
            flash("Error updating leaderboard entry. Please try again.")

    return render_template(
        "admin/edit_leaderboard_entry.html",
        title="Edit Leaderboard Entry",
        form=form,
        entry=entry,
    )


@bp.route("/admin/leaderboard/create", methods=["GET", "POST"])
@login_required
@admin_required
def create_leaderboard_entry():
    """
    Creates a new leaderboard entry with key stage selection
    """
    from app.admin.forms import LeaderboardEntryForm
    from app.models import User, LeaderboardEntry
    import datetime
    
    form = LeaderboardEntryForm()
    form.user_id.choices = [(user.id, user.full_name) for user in User.query.all()]
    
    if form.validate_on_submit():
        try:
            # Check if user already has entry for this key stage
            existing_entry = LeaderboardEntry.query.filter_by(
                user_id=form.user_id.data, 
                key_stage=form.key_stage.data
            ).first()
            
            if existing_entry:
                flash(f'User already has a leaderboard entry for {form.key_stage.data}. Please edit the existing entry.', 'error')
                return redirect(url_for('admin.edit_leaderboard_entry', entry_id=existing_entry.id))
            
            entry = LeaderboardEntry(
                user_id=form.user_id.data,
                score=form.score.data,
                key_stage=form.key_stage.data,
                last_updated=datetime.datetime.now()
            )
            
            db.session.add(entry)
            db.session.commit()
            flash('Leaderboard entry created successfully!', 'success')
            return redirect(url_for('admin.manage_leaderboard'))
            
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating leaderboard entry: {str(e)}")
            flash("Error creating leaderboard entry. Please try again.")
    
    return render_template(
        "admin/create_leaderboard_entry.html",
        title="Create Leaderboard Entry",
        form=form,
    )


@bp.route("/admin/leaderboard/delete/<int:entry_id>")
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
        flash(f"Leaderboard entry for {entry.user.full_name} ({entry.key_stage}) deleted successfully.")
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting entry: {str(e)}")
        flash("Error deleting leaderboard entry.")
    return redirect(url_for("admin.manage_leaderboard"))


@bp.route("/admin/leaderboard/reset")
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
        flash("All leaderboard entries reset successfully.")
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error resetting leaderboard: {str(e)}")
        flash("Error resetting leaderboard.")
    return redirect(url_for("admin.manage_leaderboard"))


@bp.route("/admin/leaderboard/update")
@login_required
@admin_required
def update_leaderboard():
    """
    Updates the leaderboard with new scores based on challenge submissions

    Notes:
    - Calculates scores based on challenge submissions grouped by key stage
    - Updates existing entries or creates new ones
    - A user can have multiple entries (one per key stage they've completed challenges for)
    """
    try:
        # Clear existing leaderboard
        LeaderboardEntry.query.delete()
        
        # Get all users and their submissions
        users = User.query.all()
        
        for user in users:
            # Group submissions by challenge key stage
            key_stage_scores = {}
            
            for submission in user.submissions:
                if submission.is_correct:
                    challenge = Challenge.query.get(submission.challenge_id)
                    if challenge:
                        challenge_ks = challenge.key_stage
                        if challenge_ks not in key_stage_scores:
                            key_stage_scores[challenge_ks] = 0
                        key_stage_scores[challenge_ks] += 1
            
            # Create leaderboard entries for each key stage the user has points in
            for key_stage, score in key_stage_scores.items():
                if score > 0:  # Only create entries for users with points
                    entry = LeaderboardEntry(
                        user_id=user.id, 
                        score=score, 
                        key_stage=key_stage,
                        last_updated=datetime.datetime.now()
                    )
                    db.session.add(entry)
        
        db.session.commit()
        flash("Leaderboard updated successfully based on challenge submissions.")
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating leaderboard: {str(e)}")
        flash("Error updating leaderboard.")
    return redirect(url_for("admin.manage_leaderboard"))


# ============================================================================
# Announcement Management Routes
# ============================================================================


@bp.route("/admin/announcements")
@login_required
@admin_required
def manage_announcements():
    """
    Displays announcement management interface
    """
    announcements = Announcement.query.order_by(Announcement.date_posted.desc()).all()
    return render_template(
        "admin/manage_announcements.html",
        title="Manage Announcements",
        announcements=announcements,
    )


@bp.route("/admin/announcements/create", methods=["GET", "POST"])
@login_required
@admin_required
def create_announcement():
    """
    Creates a new announcement
    """
    form = AnnouncementForm()
    if form.validate_on_submit():
        try:
            announcement = Announcement(
                title=form.title.data,
                content=form.content.data,
                date_posted=datetime.datetime.now(),
            )
            db.session.add(announcement)
            db.session.commit()
            flash("Announcement created successfully.")
            return redirect(url_for("admin.manage_announcements"))
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating announcement: {str(e)}")
            flash("Error creating announcement. Please try again.")
    return render_template(
        "admin/create_announcement.html", title="Create Announcement", form=form
    )


@bp.route("/admin/announcements/edit/<int:announcement_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_announcement(announcement_id):
    """
    Edits an existing announcement

    Args:
        announcement_id: int ID of announcement to edit
    """
    announcement = Announcement.query.get_or_404(announcement_id)
    form = AnnouncementForm(obj=announcement)
    if form.validate_on_submit():
        try:
            announcement.title = form.title.data
            announcement.content = form.content.data
            db.session.commit()
            flash("Announcement updated successfully.")
            return redirect(url_for("admin.manage_announcements"))
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating announcement: {str(e)}")
            flash("Error updating announcement. Please try again.")
    return render_template(
        "admin/edit_announcement.html",
        title="Edit Announcement",
        form=form,
        announcement=announcement,
    )


@bp.route("/admin/announcements/delete/<int:announcement_id>")
@login_required
@admin_required
def delete_announcement(announcement_id):
    """
    Deletes an announcement

    Args:
        announcement_id: int ID of announcement to delete
    """
    announcement = Announcement.query.get_or_404(announcement_id)
    try:
        db.session.delete(announcement)
        db.session.commit()
        flash("Announcement deleted successfully.")
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting announcement: {str(e)}")
        flash("Error deleting announcement. Please try again.")
    return redirect(url_for("admin.manage_announcements"))

# ============================================================================
# Summer Challenge Management Routes
# ============================================================================

@bp.route("/admin/summer_competition")
@login_required
@admin_required
def manage_summer_competition():
    return render_template("admin/manage_summer_competition.html", title="Manage Summer Competition")

@bp.route("/admin/manage_summer_challenges", methods=["GET", "POST"])
@login_required
@admin_required
def manage_summer_challenges():
    """Lists all summer challenges for management, showing both released and unreleased"""
    now = datetime.datetime.now()
    released_challenges = SummerChallenge.query.filter(SummerChallenge.release_at <= now).order_by(SummerChallenge.date_posted.desc()).all()
    unreleased_challenges = SummerChallenge.query.filter(SummerChallenge.release_at > now).order_by(SummerChallenge.release_at.asc()).all()
    return render_template(
        "admin/manage_summer_challenges.html", 
        released_challenges=released_challenges,
        unreleased_challenges=unreleased_challenges
    )

@bp.route("/admin/summer_challenges/toggle_lock/<int:challenge_id>", methods=["POST"])
@login_required
@admin_required
def toggle_summer_challenge_lock(challenge_id):
    """Toggle manual lock status for a summer challenge"""
    challenge = SummerChallenge.query.get_or_404(challenge_id)
    
    try:
        challenge.is_manually_locked = not challenge.is_manually_locked
        db.session.commit()
        
        status = "locked" if challenge.is_manually_locked else "unlocked"
        flash(f"Summer Challenge '{challenge.title}' has been {status}.", "success")
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error toggling lock status: {str(e)}")
        flash("Error updating lock status. Please try again.", "error")
    
    return redirect(url_for("admin.manage_summer_challenges"))

@bp.route("/admin/summer_challenges/create", methods=["GET", "POST"])
@login_required
@admin_required
def create_summer_challenge():
    form = SummerChallengeForm()
    if form.validate_on_submit():
        try:
            # Use the datetime from the form, or current time if blank
            release_at = form.release_at.data or datetime.datetime.now()
            challenge = SummerChallenge(
                title=form.title.data,
                content=form.content.data,
                key_stage=form.key_stage.data,
                duration_hours=form.duration_hours.data,
                date_posted=datetime.datetime.now(),
                release_at=release_at,
            )
            
            # Handle image upload if provided
            if form.image.data:
                challenge_folder = create_challenge_folder(challenge.date_posted)
                try:
                    filename = handle_file_upload(
                        form.image.data, challenge_folder, form.image.data.filename
                    )
                    challenge.file_url = filename
                except IOError as e:
                    current_app.logger.error(f"File save error: {str(e)}")
                    flash("Error saving the image file. Please try again.", "error")
                    return render_template("admin/create_summer_challenge.html", form=form)
            
            # Add challenge to get ID
            db.session.add(challenge)
            db.session.flush()
            
            # Create answer boxes
            for box_form in form.answer_boxes:
                answer_box = SummerChallengeAnswerBox(
                    challenge_id=challenge.id,
                    box_label=box_form.box_label.data,
                    correct_answer=box_form.correct_answer.data,
                    order=int(box_form.order.data) if box_form.order.data else 0,
                )
                db.session.add(answer_box)
            
            db.session.commit()
            flash("Summer Challenge created successfully.", "success")
            return redirect(url_for("admin.manage_summer_challenges"))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating summer challenge: {str(e)}")
            flash("Error creating summer challenge. Please try again.", "error")
            
    return render_template("admin/create_summer_challenge.html", form=form)

@bp.route("/admin/summer_challenges/edit/<int:challenge_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_summer_challenge(challenge_id):
    challenge = SummerChallenge.query.get_or_404(challenge_id)
    form = SummerChallengeForm(obj=challenge)
    
    if form.validate_on_submit():
        try:
            challenge.title = form.title.data
            challenge.content = form.content.data
            challenge.key_stage = form.key_stage.data
            challenge.duration_hours = form.duration_hours.data
            
            # Update release time if provided
            if form.release_at.data:
                challenge.release_at = form.release_at.data
            
            # Handle image upload if provided
            if form.image.data:
                challenge_folder = create_challenge_folder(challenge.date_posted)
                filename = handle_file_upload(
                    form.image.data, challenge_folder, form.image.data.filename
                )
                challenge.file_url = filename
            
            # Manage answer boxes
            existing_boxes = list(challenge.answer_boxes.order_by(SummerChallengeAnswerBox.order))
            used_box_ids = set()
            
            for index, box_form in enumerate(form.answer_boxes):
                # Skip empty box forms
                if not box_form.box_label.data or not box_form.correct_answer.data:
                    continue
                    
                if index < len(existing_boxes):
                    # Update existing box
                    box = existing_boxes[index]
                    box.box_label = box_form.box_label.data
                    box.correct_answer = box_form.correct_answer.data
                    box.order = int(box_form.order.data) if box_form.order.data else index
                    used_box_ids.add(box.id)
                else:
                    # Create new box
                    new_box = SummerChallengeAnswerBox(
                        challenge_id=challenge.id,
                        box_label=box_form.box_label.data,
                        correct_answer=box_form.correct_answer.data,
                        order=int(box_form.order.data) if box_form.order.data else index,
                    )
                    db.session.add(new_box)
            
            # Delete unused boxes (those with submissions should be archived, but for simplicity we'll delete)
            for box in existing_boxes:
                if box.id not in used_box_ids:
                    if box.submissions.count() == 0:
                        db.session.delete(box)
                    # Note: Could implement archiving for boxes with submissions if needed
            
            db.session.commit()
            flash("Summer Challenge updated successfully.", "success")
            return redirect(url_for("admin.manage_summer_challenges"))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating summer challenge: {str(e)}")
            flash("Error updating summer challenge. Please try again.", "error")
    
    # Pre-populate form with existing answer boxes on GET request
    if request.method == "GET":
        form.title.data = challenge.title
        form.content.data = challenge.content
        form.key_stage.data = challenge.key_stage
        form.duration_hours.data = challenge.duration_hours
        form.release_at.data = challenge.release_at
        
        # Add current answer boxes
        form.answer_boxes.entries = []
        for box in sorted(challenge.answer_boxes, key=lambda x: x.order or 0):
            form.answer_boxes.append_entry(
                {
                    "box_label": box.box_label,
                    "correct_answer": box.correct_answer,
                    "order": str(box.order) if box.order is not None else "",
                }
            )
    
    return render_template("admin/edit_summer_challenge.html", form=form, challenge=challenge)

@bp.route("/admin/summer_challenges/delete/<int:challenge_id>", methods=["POST"])
@login_required
@admin_required
def delete_summer_challenge(challenge_id):
    challenge = SummerChallenge.query.get_or_404(challenge_id)
    db.session.delete(challenge)
    db.session.commit()
    flash("Summer Challenge deleted.", "success")
    return redirect(url_for("admin.manage_summer_challenges"))

@bp.route("/admin/manage_schools", methods=["GET", "POST"])
@login_required
@admin_required
def manage_schools():
    form = SchoolForm()
    schools = School.query.order_by(School.name).all()
    if form.validate_on_submit():
        school = School(
            name=form.name.data.strip(),
            email_domain=form.email_domain.data.strip() or None,
            address=form.address.data.strip() or None,
        )
        db.session.add(school)
        db.session.commit()
        flash("School added successfully.", "success")
        return redirect(url_for("admin.manage_schools"))
    return render_template("admin/manage_schools.html", title="Manage Schools", form=form, schools=schools)

@bp.route("/admin/manage_schools/edit/<int:school_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_school(school_id):
    school = School.query.get_or_404(school_id)
    form = SchoolForm(obj=school)
    if form.validate_on_submit():
        school.name = form.name.data.strip()
        school.email_domain = form.email_domain.data.strip() or None
        school.address = form.address.data.strip() or None
        db.session.commit()
        flash("School updated successfully.", "success")
        return redirect(url_for("admin.manage_schools"))
    return render_template("admin/edit_school.html", title="Edit School", form=form, school=school)

@bp.route("/admin/manage_schools/delete/<int:school_id>", methods=["POST"])
@login_required
@admin_required
def delete_school(school_id):
    school = School.query.get_or_404(school_id)
    db.session.delete(school)
    db.session.commit()
    flash("School deleted successfully.", "success")
    return redirect(url_for("admin.manage_schools"))


# ============================================================================
# Summer Leaderboard Management Routes
# ============================================================================


@bp.route("/admin/manage_summer_leaderboard")
@login_required
@admin_required
def manage_summer_leaderboard():
    """Enhanced summer leaderboard management with search, filtering, and pagination"""
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '', type=str)
    key_stage_filter = request.args.get('key_stage', '', type=str)
    school_filter = request.args.get('school_id', '', type=str)
    sort_by = request.args.get('sort_by', 'score', type=str)
    sort_order = request.args.get('sort_order', 'desc', type=str)
    
    # Ensure per_page is within reasonable limits
    per_page = min(per_page, 100)
    
    # Start with base query
    query = SummerLeaderboard.query.join(User).join(School)
    
    # Apply search filter
    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            db.or_(
                User.full_name.ilike(search_term),
                School.name.ilike(search_term),
                User.id.like(search_term)
            )
        )
    
    # Apply key stage filter
    if key_stage_filter and key_stage_filter != 'all':
        query = query.filter(User.key_stage == key_stage_filter)
    
    # Apply school filter
    if school_filter and school_filter != 'all':
        try:
            school_id = int(school_filter)
            query = query.filter(SummerLeaderboard.school_id == school_id)
        except ValueError:
            pass
    
    # Apply sorting
    if sort_by == 'name':
        if sort_order == 'asc':
            query = query.order_by(User.full_name.asc())
        else:
            query = query.order_by(User.full_name.desc())
    elif sort_by == 'school':
        if sort_order == 'asc':
            query = query.order_by(School.name.asc())
        else:
            query = query.order_by(School.name.desc())
    elif sort_by == 'key_stage':
        if sort_order == 'asc':
            query = query.order_by(User.key_stage.asc())
        else:
            query = query.order_by(User.key_stage.desc())
    else:  # Default to score
        if sort_order == 'asc':
            query = query.order_by(SummerLeaderboard.score.asc())
        else:
            query = query.order_by(SummerLeaderboard.score.desc())
    
    # Execute paginated query
    leaderboard_pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    # Calculate comprehensive statistics
    stats = calculate_summer_leaderboard_stats()
    
    # Ensure stats has all required keys with default values
    if not stats:
        stats = {
            'total_entries': 0,
            'unique_participants': 0,
            'participating_schools': 0,
            'max_score': 0,
            'min_score': 0,
            'avg_score': 0,
            'average_score': 0,
            'total_score': 0,
            'key_stage_breakdown': {},
            'school_performance': [],
            'top_performers': []
        }
    
    # Get available schools and key stages for filters
    available_schools = db.session.query(School).order_by(School.name).all()
    available_key_stages = db.session.query(User.key_stage).join(SummerLeaderboard).distinct().order_by(User.key_stage).all()
    available_key_stages = [ks[0] for ks in available_key_stages if ks[0]]
    
    return render_template(
        "admin/manage_summer_leaderboard.html",
        title="Manage Summer Leaderboard",
        summer_leaderboard=leaderboard_pagination.items,
        pagination=leaderboard_pagination,
        stats=stats,
        available_schools=available_schools,
        available_key_stages=available_key_stages,
        current_filters={
            'search': search,
            'key_stage': key_stage_filter,
            'school_id': school_filter,
            'sort_by': sort_by,
            'sort_order': sort_order,
            'per_page': per_page
        }
    )


def calculate_summer_leaderboard_stats():
    """Calculate comprehensive summer leaderboard statistics"""
    try:
        # Basic counts
        total_entries = SummerLeaderboard.query.count()
        if total_entries == 0:
            return {
                'total_entries': 0,
                'unique_participants': 0,
                'participating_schools': 0,
                'max_score': 0,
                'min_score': 0,
                'avg_score': 0,
                'average_score': 0,
                'total_score': 0,
                'key_stage_breakdown': {},
                'school_performance': [],
                'top_performers': []
            }
            
        unique_users = db.session.query(SummerLeaderboard.user_id).distinct().count()
        unique_schools = db.session.query(SummerLeaderboard.school_id).distinct().count()
        
        # Score statistics
        score_stats = db.session.query(
            db.func.max(SummerLeaderboard.score).label('max_score'),
            db.func.min(SummerLeaderboard.score).label('min_score'),
            db.func.avg(SummerLeaderboard.score).label('avg_score'),
            db.func.sum(SummerLeaderboard.score).label('total_score')
        ).first()
        
        # Key stage breakdown
        ks_stats = db.session.query(
            User.key_stage,
            db.func.count(SummerLeaderboard.id).label('count'),
            db.func.avg(SummerLeaderboard.score).label('avg_score'),
            db.func.max(SummerLeaderboard.score).label('max_score')
        ).join(User, SummerLeaderboard.user_id == User.id).group_by(User.key_stage).all()
        
        # School performance (top 10)
        school_stats = db.session.query(
            School.name,
            School.id,
            db.func.count(SummerLeaderboard.id).label('participant_count'),
            db.func.avg(SummerLeaderboard.score).label('avg_score'),
            db.func.sum(SummerLeaderboard.score).label('total_score'),
            db.func.max(SummerLeaderboard.score).label('best_score')
        ).join(School, SummerLeaderboard.school_id == School.id).group_by(
            School.id, School.name
        ).order_by(db.func.sum(SummerLeaderboard.score).desc()).limit(10).all()
        
        # Top performers (top 10)
        top_performers = db.session.query(
            User.full_name,
            User.key_stage,
            School.name.label('school_name'),
            SummerLeaderboard.score
        ).join(User, SummerLeaderboard.user_id == User.id).join(
            School, SummerLeaderboard.school_id == School.id
        ).order_by(SummerLeaderboard.score.desc()).limit(10).all()
        
        return {
            'total_entries': total_entries,
            'unique_participants': unique_users,
            'participating_schools': unique_schools,
            'max_score': score_stats.max_score or 0,
            'min_score': score_stats.min_score or 0,
            'avg_score': round(float(score_stats.avg_score), 2) if score_stats.avg_score else 0,
            'average_score': round(float(score_stats.avg_score), 2) if score_stats.avg_score else 0,  # Template compatibility
            'total_score': score_stats.total_score or 0,
            'key_stage_breakdown': {ks.key_stage: {
                'count': ks.count,
                'avg_score': round(float(ks.avg_score), 2) if ks.avg_score else 0,
                'max_score': ks.max_score or 0
            } for ks in ks_stats},
            'school_performance': [{
                'name': school.name,
                'id': school.id,
                'participants': school.participant_count,
                'avg_score': round(float(school.avg_score), 2) if school.avg_score else 0,
                'total_score': school.total_score or 0,
                'best_score': school.best_score or 0
            } for school in school_stats],
            'top_performers': [{
                'name': performer.full_name,
                'key_stage': performer.key_stage,
                'school': performer.school_name,
                'score': performer.score
            } for performer in top_performers]
        }
    except SQLAlchemyError as e:
        current_app.logger.error(f"Error calculating stats: {str(e)}")
        return {}


@bp.route("/admin/summer_leaderboard/search")
@login_required
@admin_required
def summer_leaderboard_search():
    """AJAX endpoint for dynamic summer leaderboard search (safe casting & limits)"""
    try:
        query = request.args.get('q', '', type=str)
        limit = request.args.get('limit', 10, type=int)
        if limit < 1:
            limit = 1
        limit = min(limit, 50)

        if not query or len(query.strip()) < 2:
            return jsonify({'entries': []})

        search_clean = query.strip()
        search_term = f"%{search_clean}%"
        id_clauses = []
        if search_clean.isdigit():
            try:
                id_clauses.append(User.id == int(search_clean))
            except ValueError:
                pass
        id_clauses.append(cast(User.id, String).like(search_term))

        entries = db.session.query(
            SummerLeaderboard,
            User.full_name,
            School.name.label('school_name')
        ).join(User).join(School).filter(
            db.or_(
                User.full_name.ilike(search_term),
                School.name.ilike(search_term),
                db.or_(*id_clauses)
            )
        ).limit(limit).all()

        entry_data = [
            {
                'id': entry.id,
                'user_name': user_name,
                'school_name': school_name,
                'score': entry.score,
                'last_updated': entry.last_updated.strftime('%Y-%m-%d %H:%M') if entry.last_updated else None
            }
            for entry, user_name, school_name in entries
        ]
        return jsonify({'entries': entry_data})
    except SQLAlchemyError as e:
        current_app.logger.error(f"Summer leaderboard search DB error: {e}")
        return jsonify({'error': 'Search failed'}), 500
    except Exception as e:
        current_app.logger.error(f"Summer leaderboard search unexpected error: {e}")
        return jsonify({'error': 'Unexpected error'}), 500


@bp.route("/admin/summer_leaderboard/bulk-action", methods=["POST"])
@login_required
@admin_required
def summer_leaderboard_bulk_action():
    """Handle bulk actions on summer leaderboard entries"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    action = data.get('action')
    entry_ids = data.get('entry_ids', [])
    
    if not action or not entry_ids:
        return jsonify({'success': False, 'error': 'Action and entry IDs required'}), 400
    
    try:
        entries = SummerLeaderboard.query.filter(SummerLeaderboard.id.in_(entry_ids)).all()
        
        if action == 'delete':
            for entry in entries:
                db.session.delete(entry)
            db.session.commit()
            return jsonify({'success': True, 'message': f'Deleted {len(entries)} entries'})
              
        elif action == 'reset_scores':
            for entry in entries:
                entry.score = 0
                entry.last_updated = datetime.datetime.now()
            db.session.commit()
            return jsonify({'success': True, 'message': f'Reset scores for {len(entries)} entries'})
        
        else:
            return jsonify({'success': False, 'error': 'Invalid action'}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route("/admin/summer_leaderboard/stats")
@login_required
@admin_required
def summer_leaderboard_stats():
    """Get detailed summer leaderboard statistics for dashboard widgets"""
    try:
        stats = calculate_summer_leaderboard_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route("/admin/summer_leaderboard/export")
@login_required
@admin_required
def export_summer_leaderboard():
    """Enhanced export with filtering options"""
    # Get filter parameters
    format_type = request.args.get('format', 'csv', type=str)
    key_stage_filter = request.args.get('key_stage', '', type=str)
    school_filter = request.args.get('school_id', '', type=str)
    min_score = request.args.get('min_score', type=int)
    max_score = request.args.get('max_score', type=int)
    
    try:
        # Build query with filters
        query = SummerLeaderboard.query.join(User).join(School)
        
        if key_stage_filter and key_stage_filter != 'all':
            query = query.filter(User.key_stage == key_stage_filter)
        
        if school_filter and school_filter != 'all':
            try:
                school_id = int(school_filter)
                query = query.filter(SummerLeaderboard.school_id == school_id)
            except ValueError:
                pass
        
        if min_score is not None:
            query = query.filter(SummerLeaderboard.score >= min_score)
        
        if max_score is not None:
            query = query.filter(SummerLeaderboard.score <= max_score)
        
        # Order by score (highest first)
        entries = query.order_by(SummerLeaderboard.score.desc()).all()
        
        if format_type == 'json':
            # Export as JSON
            data = []
            for entry in entries:
                data.append({
                    'user_id': entry.user_id,
                    'name': entry.user.full_name,
                    'year': entry.user.year,
                    'key_stage': entry.user.key_stage,
                    'school': entry.school.name,
                    'school_id': entry.school_id,
                    'score': entry.score,
                    'last_updated': entry.last_updated.isoformat() if entry.last_updated else None,
                    'rank': data.__len__() + 1
                })
            
            file = BytesIO()
            file.write(jsonify(data).get_data())
            file.seek(0)
            
            return send_file(
                file,
                as_attachment=True,
                attachment_filename=f"summer_leaderboard_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mimetype="application/json",
            )
        
        else:
            # Export as CSV (default)
            csv_data = "Rank,User ID,Name,Year,Key Stage,School,Score,Last Updated,Date Exported\n"
            for rank, entry in enumerate(entries, 1):
                csv_data += f"{rank},{entry.user_id},{entry.user.full_name},{entry.user.year},{entry.user.key_stage},{entry.school.name},{entry.score},{entry.last_updated},{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            file = BytesIO()
            file.write(csv_data.encode())
            file.seek(0)
            
            return send_file(
                file,
                as_attachment=True,
                attachment_filename=f"summer_leaderboard_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mimetype="text/csv",
            )

    except SQLAlchemyError as e:
        current_app.logger.error(f"Error exporting summer leaderboard: {str(e)}")
        flash("Error exporting summer leaderboard data.", "error")
        return redirect(url_for("admin.manage_summer_leaderboard"))


@bp.route("/admin/summer_leaderboard/school_rankings")
@login_required
@admin_required
def summer_school_rankings():
    """Display school rankings and performance analytics"""
    try:
        # Check if we have any data
        total_entries = SummerLeaderboard.query.count()
        if total_entries == 0:
            flash("No summer leaderboard data available for school rankings.", "info")
            return redirect(url_for("admin.manage_summer_leaderboard"))
        
        # Calculate school rankings
        school_rankings = db.session.query(
            School.id,
            School.name,
            db.func.count(SummerLeaderboard.id).label('participant_count'),
            db.func.sum(SummerLeaderboard.score).label('total_score'),
            db.func.avg(SummerLeaderboard.score).label('avg_score'),
            db.func.max(SummerLeaderboard.score).label('best_score'),
            db.func.min(SummerLeaderboard.score).label('lowest_score')
        ).join(SummerLeaderboard).group_by(School.id, School.name).order_by(
            db.func.sum(SummerLeaderboard.score).desc()
        ).all()
        
        # Key stage performance by school
        ks_performance = db.session.query(
            School.name.label('school_name'),
            User.key_stage,
            db.func.count(SummerLeaderboard.id).label('count'),
            db.func.avg(SummerLeaderboard.score).label('avg_score')
        ).join(SummerLeaderboard).join(User).group_by(
            School.id, School.name, User.key_stage
        ).order_by(School.name, User.key_stage).all()
        
        # Total participation stats
        total_competition_users = User.query.filter(User.is_competition_participant == True).count()
        participating_users = db.session.query(SummerLeaderboard.user_id).distinct().count()
        participation_rate = (participating_users / total_competition_users * 100) if total_competition_users > 0 else 0
        
        school_data = {
            'rankings': school_rankings,
            'ks_performance': ks_performance,
            'total_competition_users': total_competition_users,
            'participating_users': participating_users,
            'participation_rate': round(participation_rate, 1)
        }
        
        return render_template(
            "admin/manage_summer_leaderboard.html",
            title="Summer Competition School Rankings",
            school_data=school_data,
            show_school_rankings=True
        )
        
    except SQLAlchemyError as e:
        current_app.logger.error(f"Error loading school rankings: {str(e)}")
        flash("Error loading school rankings.", "error")
        return redirect(url_for("admin.manage_summer_leaderboard"))


@bp.route("/admin/summer_leaderboard/analytics")
@login_required
@admin_required
def summer_leaderboard_analytics():
    """Advanced analytics and insights for summer competition"""
    try:
        # Check if we have any data first
        total_entries = SummerLeaderboard.query.count()
        if total_entries == 0:
            flash("No summer leaderboard data available for analytics.", "info")
            return redirect(url_for("admin.manage_summer_leaderboard"))
        
        # Performance trends - score distribution
        score_distribution = db.session.query(
            SummerLeaderboard.score,
            db.func.count(SummerLeaderboard.id).label('count')
        ).group_by(SummerLeaderboard.score).order_by(SummerLeaderboard.score).all()
        
        # Top performers analysis
        top_10_percent_count = max(1, total_entries // 10)
        top_performers = db.session.query(
            SummerLeaderboard, User, School
        ).join(User).join(School).order_by(
            SummerLeaderboard.score.desc()
        ).limit(top_10_percent_count).all()
        
        # Participation by key stage
        ks_participation = db.session.query(
            User.key_stage,
            db.func.count(SummerLeaderboard.id).label('participants'),
            db.func.avg(SummerLeaderboard.score).label('avg_score'),
            db.func.max(SummerLeaderboard.score).label('max_score'),
            db.func.min(SummerLeaderboard.score).label('min_score')
        ).join(SummerLeaderboard).group_by(User.key_stage).all()
        
        # Recent activity (last 7 days)
        week_ago = datetime.datetime.now() - timedelta(days=7)
        recent_updates = db.session.query(
            SummerLeaderboard, User, School
        ).join(User).join(School).filter(
            SummerLeaderboard.last_updated >= week_ago
        ).order_by(SummerLeaderboard.last_updated.desc()).limit(20).all()
        
        # School performance summary
        school_performance = db.session.query(
            School.name,
            db.func.count(SummerLeaderboard.id).label('participant_count'),
            db.func.avg(SummerLeaderboard.score).label('avg_score'),
            db.func.sum(SummerLeaderboard.score).label('total_score')
        ).join(SummerLeaderboard).group_by(School.id, School.name).order_by(
            db.func.sum(SummerLeaderboard.score).desc()
        ).limit(10).all()
        
        # Calculate some basic statistics
        score_stats = db.session.query(
            db.func.avg(SummerLeaderboard.score).label('avg_score'),
            db.func.max(SummerLeaderboard.score).label('max_score'),
            db.func.min(SummerLeaderboard.score).label('min_score')
        ).first()
        
        analytics_data = {
            'total_entries': total_entries,
            'score_distribution': [(score, count) for score, count in score_distribution],
            'top_performers': [(entry, user, school) for entry, user, school in top_performers],
            'ks_participation': ks_participation,
            'recent_updates': recent_updates,
            'school_performance': school_performance,
            'score_stats': score_stats
        }
        
        return render_template(
            "admin/manage_summer_leaderboard.html",
            title="Summer Competition Analytics",
            analytics_data=analytics_data,
            show_analytics=True
        )
        
    except SQLAlchemyError as e:
        current_app.logger.error(f"Error loading analytics: {str(e)}")
        flash("Error loading analytics data.", "error")
        return redirect(url_for("admin.manage_summer_leaderboard"))


@bp.route("/admin/summer_leaderboard/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_summer_leaderboard_entry():
    """Enhanced add summer leaderboard entry with validation"""
    form = SummerLeaderboardEntryForm()
    
    # Only show competition participants in the dropdown
    competition_users = User.query.filter(User.is_competition_participant == True).order_by(User.full_name).all()
    form.user_id.choices = [(user.id, f"{user.full_name} ({user.key_stage}) - {user.school.name if user.school else 'No School'}") for user in competition_users]
    form.school_id.choices = [(school.id, school.name) for school in School.query.order_by(School.name).all()]

    if form.validate_on_submit():
        try:
            # Check if user already has a summer leaderboard entry
            existing_entry = SummerLeaderboard.query.filter_by(user_id=form.user_id.data).first()
            
            if existing_entry:
                flash(f'User already has a summer leaderboard entry with score {existing_entry.score}. Please edit the existing entry instead.', 'error')
                return redirect(url_for('admin.edit_summer_leaderboard_entry', entry_id=existing_entry.id))

            # Validate that user is actually assigned to the selected school
            user = User.query.get(form.user_id.data)
            if user.school_id != form.school_id.data:
                flash(f'Warning: User {user.full_name} is assigned to {user.school.name if user.school else "No School"} but you selected {School.query.get(form.school_id.data).name}', 'warning')

            entry = SummerLeaderboard(
                user_id=form.user_id.data,
                school_id=form.school_id.data,
                score=form.score.data,
                last_updated=datetime.datetime.now()
            )
            
            db.session.add(entry)
            db.session.commit()
            
            # Log the action
            current_app.logger.info(f"Admin {current_user.full_name} added summer leaderboard entry for user {user.full_name} with score {form.score.data}")
            flash(f'Summer leaderboard entry added successfully for {user.full_name}!', 'success')
            return redirect(url_for('admin.manage_summer_leaderboard'))

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding summer leaderboard entry: {str(e)}")
            flash("Error adding summer leaderboard entry. Please try again.", "error")

    return render_template(
        "admin/add_summer_leaderboard_entry.html",
        title="Add Summer Leaderboard Entry",
        form=form,
    )


@bp.route("/admin/summer_leaderboard/edit/<int:entry_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_summer_leaderboard_entry(entry_id):
    """Enhanced edit summer leaderboard entry with history tracking"""
    entry = SummerLeaderboard.query.get_or_404(entry_id)
    original_score = entry.score
    form = SummerLeaderboardEntryForm(obj=entry)
    
    # Only show competition participants
    competition_users = User.query.filter(User.is_competition_participant == True).order_by(User.full_name).all()
    form.user_id.choices = [(user.id, f"{user.full_name} ({user.key_stage}) - {user.school.name if user.school else 'No School'}") for user in competition_users]
    form.school_id.choices = [(school.id, school.name) for school in School.query.order_by(School.name).all()]

    if form.validate_on_submit():
        try:
            # Check if changing user would create duplicate
            if entry.user_id != form.user_id.data:
                existing_entry = SummerLeaderboard.query.filter_by(user_id=form.user_id.data).first()
                
                if existing_entry and existing_entry.id != entry.id:
                    flash(f'User already has a summer leaderboard entry. Please edit that entry instead.', 'error')
                    return redirect(url_for('admin.edit_summer_leaderboard_entry', entry_id=existing_entry.id))

            # Track changes for logging
            changes = []
            if entry.user_id != form.user_id.data:
                old_user = User.query.get(entry.user_id)
                new_user = User.query.get(form.user_id.data)
                changes.append(f"User: {old_user.full_name} → {new_user.full_name}")
            
            if entry.school_id != form.school_id.data:
                old_school = School.query.get(entry.school_id)
                new_school = School.query.get(form.school_id.data)
                changes.append(f"School: {old_school.name} → {new_school.name}")
            
            if entry.score != form.score.data:
                changes.append(f"Score: {entry.score} → {form.score.data}")

            # Update entry
            entry.user_id = form.user_id.data
            entry.school_id = form.school_id.data
            entry.score = form.score.data
            entry.last_updated = datetime.datetime.now()
            
            db.session.commit()
            
            # Log the changes
            if changes:
                change_log = ", ".join(changes)
                current_app.logger.info(f"Admin {current_user.full_name} updated summer leaderboard entry {entry_id}: {change_log}")
                flash(f'Summer leaderboard entry updated successfully! Changes: {change_log}', 'success')
            else:
                flash('No changes detected.', 'info')
                
            return redirect(url_for('admin.manage_summer_leaderboard'))

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating summer leaderboard entry: {str(e)}")
            flash("Error updating summer leaderboard entry. Please try again.", "error")

    return render_template(
        "admin/edit_summer_leaderboard_entry.html",
        title="Edit Summer Leaderboard Entry",
        form=form,
        entry=entry,
    )


@bp.route("/admin/summer_leaderboard/delete/<int:entry_id>", methods=["POST"])
@login_required
@admin_required
def delete_summer_leaderboard_entry(entry_id):
    """
    Delete a summer leaderboard entry

    Args:
        entry_id: int ID of entry to delete
    """
    try:
        entry = SummerLeaderboard.query.get_or_404(entry_id)
        user_name = entry.user.full_name
        
        db.session.delete(entry)
        db.session.commit()
        
        flash(f'Summer leaderboard entry for {user_name} deleted successfully!', 'success')
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting summer leaderboard entry: {str(e)}")
        flash("Error deleting summer leaderboard entry. Please try again.", "error")
    
    return redirect(url_for('admin.manage_summer_leaderboard'))


@bp.route("/admin/summer_leaderboard/reset", methods=["POST"])
@login_required
@admin_required
def reset_summer_leaderboard():
    """
    Reset all summer leaderboard scores to zero (for new competition periods)
    """
    try:
        # Update all entries to score 0
        updated_count = SummerLeaderboard.query.update({
            SummerLeaderboard.score: 0,
            SummerLeaderboard.last_updated: datetime.datetime.now()
        })
        
        db.session.commit()
        flash(f'Summer leaderboard reset successfully! {updated_count} entries updated.', 'success')
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error resetting summer leaderboard: {str(e)}")
        flash("Error resetting summer leaderboard. Please try again.", "error")
    
    return redirect(url_for('admin.manage_summer_leaderboard'))

# ! ERROR HANDLERS


@bp.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template("errors/500.html"), 500
