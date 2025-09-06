"""
Main Routes Module
==================

This module handles all the main user-facing routes.
It is organized into logical sections based on functionality:
- View Routes
- Challenge Routes
- Article and Newsletter Routes
- Leaderboard Routes

Dependencies:
------------
- Flask and related extensions
- SQLAlchemy for database operations
- Custom models and forms using Flask-WTF

Security:
---------
User authentication and registration are handled securely:
1. All sensitive routes require authentication
2. File access is properly sanitized
3. User permissions are checked appropriately
4. Form data is validated before processing

Maintenance Notes:
-----------------
1. Ensure that the database schema is up-to-date with the models.
2. Validate form data before processing it in routes.
3. Keep the user experience simple and user-friendly.
4. Handle errors gracefully and provide helpful messages.
"""

import os
from flask import (
    abort,
    current_app,
    render_template,
    flash,
    redirect,
    send_from_directory,
    url_for,
    request,
)
from flask_login import current_user
import datetime
from typing import Dict
from app import db
from app.models import User
from sqlalchemy.exc import SQLAlchemyError
from app.main import bp
from app.models import (
    Challenge,
    Article,
    LeaderboardEntry,
    AnswerSubmission,
    ChallengeAnswerBox,
    Announcement,
    SummerChallenge,
    SummerLeaderboard,
    SummerSubmission,
    SummerChallengeAnswerBox,
    School,
)
from app.admin.forms import AnswerSubmissionForm


# ============================================================================
# View Routes
# ============================================================================


@bp.route("/")
@bp.route("/home")
def home():
    """
    Render the homepage with recent content filtered by user type.

    Returns:
        Rendered homepage template with recent challenges, articles, leaderboard entries,
        latest newsletter, and latest announcement filtered by user account type.
    """
    try:
        challenges = Challenge.query
        articles = Article.query
        leaderboard_entries = LeaderboardEntry.query
        now = datetime.datetime.now()
        
        # Initialize variables
        recent_challenges = []
        recent_summer_challenges = []
        
        if current_user.is_authenticated:
            is_summer_participant = getattr(current_user, "is_competition_participant", False)
            
            if is_summer_participant:
                # Summer competition users see summer challenges
                recent_summer_challenges = (
                    SummerChallenge.query.filter_by(key_stage=current_user.key_stage)
                    .order_by(SummerChallenge.date_posted.desc())
                    .limit(3)
                    .all()
                )
            else:
                # Regular users see regular challenges
                recent_challenges = (
                    Challenge.query.filter(Challenge.release_at <= now)
                    .order_by(Challenge.date_posted.desc())
                    .limit(3)
                    .all()
                )
        else:
            # Unauthenticated users see a mix or nothing
            recent_challenges = (
                Challenge.query.filter(Challenge.release_at <= now)
                .order_by(Challenge.date_posted.desc())
                .limit(3)
                .all()
            )

        recent_articles = (
            Article.query.filter_by(type="article")
            .order_by(Article.date_posted.desc())
            .limit(3)
            .all()
        )

        latest_newsletter = (
            Article.query.filter_by(type="newsletter")
            .order_by(Article.date_posted.desc())
            .first()
        )

        latest_announcement = Announcement.query.order_by(
            Announcement.date_posted.desc()
        ).first()

        return render_template(
            "index.html",
            challenges=challenges,
            articles=articles,
            leaderboard_entries=leaderboard_entries,
            recent_challenges=recent_challenges,
            recent_summer_challenges=recent_summer_challenges,
            recent_articles=recent_articles,
            latest_newsletter=latest_newsletter,
            latest_announcement=latest_announcement,
        )
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in index route: {str(e)}")
        flash("An error occurred while loading the homepage.", "error")
        return redirect(url_for("main.about"))


@bp.route("/about")
def about():
    """
    Render the about page.

    Returns:
        Rendered about page template.
    """
    return render_template("main/about.html", title="About")


@bp.route("/summer_about")
def summer_about():
    """
    Render the summer competition about page.

    Returns:
        Rendered summer competition about page template.
    """
    return render_template("main/summer_about.html", title="About Summer Competition 2025")


# ============================================================================
# Challenge Routes
# ============================================================================


@bp.route("/challenges")
def challenges():
    """
    List all challenges with pagination, filtered by user account type.

    Query Parameters:
        page (int, optional): Current page number for pagination. Defaults to 1.

    Returns:
        Rendered challenges page template with filtered challenges based on user type.
    """
    page = request.args.get("page", 1, type=int)
    try:
        now = datetime.datetime.now()
        
        # Initialize variables
        challenges_pagination = None
        summer_challenges = []
        
        if current_user.is_authenticated:
            # Check if user is a summer competition participant
            is_summer_participant = getattr(current_user, "is_competition_participant", False)
            
            if is_summer_participant:
                # Summer competition users only see summer challenges
                summer_challenges = SummerChallenge.query.filter_by(
                    key_stage=current_user.key_stage
                ).order_by(SummerChallenge.date_posted.desc()).all()
                
                # No regular challenges for summer participants
                challenges_pagination = Challenge.query.filter(Challenge.id == -1).paginate(
                    page=page, per_page=6, error_out=False
                )
            else:
                # Regular users only see regular challenges
                challenges_pagination = Challenge.query.filter(
                    Challenge.release_at <= now
                ).order_by(Challenge.date_posted.desc()).paginate(
                    page=page, per_page=6, error_out=False
                )
                
                # No summer challenges for regular users
                summer_challenges = []
        else:
            # Unauthenticated users see nothing or redirect to login
            flash("Please log in to view challenges.", "info")
            return redirect(url_for('auth.login'))
            
        return render_template(
            "main/challenges.html",
            challenges=challenges_pagination,
            summer_challenges=summer_challenges
        )
    except SQLAlchemyError as e:
        current_app.logger.error(f"Error loading challenges: {str(e)}")
        flash("Unable to load challenges at this time.", "error")
        return redirect(url_for("main.home"))


def check_submission_count(user_id: int, challenge_id: int, box_id: int) -> int:
    """
    Check how many submissions a user has made for a specific answer box.

    Args:
        user_id (int): The ID of the user.
        challenge_id (int): The ID of the challenge.
        box_id (int): The ID of the answer box.

    Returns:
        int: Number of submissions for the specified user, challenge, and answer box.
    """
    return AnswerSubmission.query.filter_by(
        user_id=user_id, challenge_id=challenge_id, answer_box_id=box_id
    ).count()


def create_submission(
    user_id: int,
    challenge_id: int,
    answer_box: ChallengeAnswerBox,
    submitted_answer: str,
) -> AnswerSubmission:
    """
    Create and save a new submission.

    Args:
        user_id (int): The ID of the user.
        challenge_id (int): The ID of the challenge.
        answer_box (ChallengeAnswerBox): The answer box object.
        submitted_answer (str): The user's submitted answer.

    Returns:
        AnswerSubmission: Created submission object.
    """
    submission = AnswerSubmission(
        user_id=user_id,
        challenge_id=challenge_id,
        answer_box_id=answer_box.id,
        answer=submitted_answer,
        is_correct=answer_box.check_answer(submitted_answer),
    )

    db.session.add(submission)
    db.session.commit()
    return submission


def check_all_answers_correct(challenge: Challenge, user_id: int) -> bool:
    """
    Check if user has correct submissions for all answer boxes in a challenge.

    Args:
        challenge (Challenge): The Challenge object.
        user_id (int): The ID of the user.

    Returns:
        bool: True if all answers are correct, False otherwise.
    """
    answer_boxes = challenge.answer_boxes.all()
    if not answer_boxes:
        return False
        
    return all(
        AnswerSubmission.query.filter_by(
            user_id=user_id,
            challenge_id=challenge.id,
            answer_box_id=box.id,
            is_correct=True,
        ).first()
        is not None
        for box in answer_boxes
    )


def update_leaderboard(user_id: int, score: int, challenge_key_stage: str) -> None:
    """
    Update user's points on the leaderboard for the specific challenge key stage.

    Args:
        user_id (int): The ID of the user.
        score (int): Number of points to add.
        challenge_key_stage (str): The key stage of the challenge being completed.
    """

    user = User.query.get(user_id)
    if not user:
        return
    
    # Look for existing leaderboard entry for this user and challenge key stage
    leaderboard_entry = LeaderboardEntry.query.filter_by(
        user_id=user_id, 
        key_stage=challenge_key_stage
    ).first()

    if leaderboard_entry:
        leaderboard_entry.score += score
    else:
        # Create new entry for this key stage
        leaderboard_entry = LeaderboardEntry(
            user_id=user_id, 
            score=score, 
            key_stage=challenge_key_stage
        )
        db.session.add(leaderboard_entry)

    leaderboard_entry.last_updated = datetime.datetime.now()
    db.session.commit()


def update_summer_leaderboard(user_id: int, school_id: int, points: int) -> None:
    """
    Update user's points on the summer competition leaderboard.

    Args:
        user_id (int): The ID of the user.
        school_id (int): The ID of the user's school.
        points (int): Number of points to add.
    """
    # Look for existing summer leaderboard entry
    summer_entry = SummerLeaderboard.query.filter_by(
        user_id=user_id,
        school_id=school_id
    ).first()

    if summer_entry:
        summer_entry.score += points
        summer_entry.last_updated = datetime.datetime.now()
    else:
        # Create new summer leaderboard entry
        summer_entry = SummerLeaderboard(
            user_id=user_id,
            school_id=school_id,
            score=points,
            last_updated=datetime.datetime.now()
        )
        db.session.add(summer_entry)

    db.session.commit()


def calculate_summer_challenge_points(challenge: SummerChallenge, is_first_correct: bool = False) -> int:
    """
    Calculate points for a summer challenge based on difficulty and timing.

    Args:
        challenge (SummerChallenge): The challenge object.
        is_first_correct (bool): Whether this is the first correct submission for this answer box.

    Returns:
        int: Points to award for this challenge.
    """
    # First person to solve gets 3 points, everyone else gets 1
    if is_first_correct:
        return 3
    else:
        return 1


def handle_submission_result(
    submission: AnswerSubmission, challenge: Challenge, answer_box: ChallengeAnswerBox
) -> None:
    """
    Handle the result of a submission, updating points and showing appropriate messages.
    """
    submission_count = check_submission_count(
        submission.user_id, challenge.id, answer_box.id
    )

    if submission.is_correct:
        flash(f"Correct answer for {answer_box.box_label}!", "success")

        # Check if this submission completes the entire challenge for this user
        user_correct_boxes = AnswerSubmission.query.filter_by(
            user_id=submission.user_id,
            challenge_id=challenge.id,
            is_correct=True
        ).count()
        
        total_boxes = challenge.answer_boxes.count()  # Use .count() instead of len(list())
        
        # If this submission completes the challenge (all boxes correct)
        if user_correct_boxes == total_boxes:  # Remove the +1 since the submission is already saved
            
            # Check if anyone else has completed the entire challenge already
            # We need to check for users who have correct answers for ALL answer boxes
            completed_users_subquery = (
                db.session.query(AnswerSubmission.user_id)
                .filter(
                    AnswerSubmission.challenge_id == challenge.id,
                    AnswerSubmission.is_correct == True,
                    AnswerSubmission.user_id != submission.user_id  # Exclude current user
                )
                .group_by(AnswerSubmission.user_id)
                .having(db.func.count(db.func.distinct(AnswerSubmission.answer_box_id)) == total_boxes)
            )
            
            completed_users_count = completed_users_subquery.count()
            
            # If no one else has completed it yet, this user gets 3 points
            if completed_users_count == 0:
                update_leaderboard(submission.user_id, 3, challenge.key_stage)
                flash("🎉 First to complete the entire challenge! +3 points!", "success")
                
                # Update challenge completion timestamp
                if challenge.first_correct_submission is None:
                    challenge.first_correct_submission = datetime.datetime.now()
                    db.session.commit()
            else:
                # Someone else completed it first, this user gets 1 point
                update_leaderboard(submission.user_id, 1, challenge.key_stage)
                flash("Challenge completed! +1 point!", "success")
        else:
            # Just answered one part correctly, but not completing the whole challenge yet
            flash("Correct! Keep going to complete the challenge!", "success")
            # No points awarded until entire challenge is completed

    else:
        remaining = 3 - submission_count
        flash(
            f"Incorrect answer for {answer_box.box_label}. {remaining} attempts remaining.",
            "error",
        )

@bp.route("/challenges/<int:challenge_id>", methods=["GET", "POST"])
def challenge(challenge_id: int):
    """
    Display a specific challenge and handle answer submissions.
    Only accessible to regular users (non-summer competition participants).
    """
    challenge = Challenge.query.get_or_404(challenge_id)
    
    # Check user authentication and account type
    if not current_user.is_authenticated:
        flash("Please log in to access challenges.", "error")
        return redirect(url_for('auth.login'))
    
    # Block summer competition participants from accessing regular challenges
    if getattr(current_user, "is_competition_participant", False):
        flash("Summer competition participants can only access competition challenges.", "error")
        return redirect(url_for('main.challenges'))
    
    # Check if challenge is released to the public
    if not current_user.is_admin:
        now = datetime.datetime.now()
        if challenge.release_at and challenge.release_at > now:
            flash("This challenge is not yet available.", "error")
            return redirect(url_for('main.challenges'))
    
    # Check if challenge is locked
    if challenge.is_locked and not current_user.is_admin:
        # Still show the challenge but don't allow submissions
        pass
    
    forms = {}
    submissions = {}

    # Create forms and get submissions only if user is authenticated
    if current_user.is_authenticated:
        for answer_box in challenge.answer_boxes.all():
            forms[answer_box.id] = AnswerSubmissionForm()
            submissions[answer_box.id] = (
                AnswerSubmission.query.filter_by(
                    user_id=current_user.id,
                    challenge_id=challenge_id,
                    answer_box_id=answer_box.id,
                )
                .order_by(AnswerSubmission.submitted_at.desc())
                .all()
            )

        # Handle submission if the form is submitted and challenge is not locked
        if request.method == "POST" and (not challenge.is_locked or current_user.is_admin):
            return handle_challenge_submission(challenge, forms)

    all_correct = current_user.is_authenticated and check_all_answers_correct(
        challenge, current_user.id
    )

    return render_template(
        "main/challenge.html",
        challenge=challenge,
        forms=forms if current_user.is_authenticated else None,
        submissions=submissions,
        attempts_remaining=3,
        all_correct=all_correct,
    )

@bp.route("/summer_challenge/<int:challenge_id>", methods=["GET", "POST"])
def summer_challenge(challenge_id: int):
    """
    Display a specific summer challenge and handle answer submissions.
    Only accessible to summer competition participants.
    """
    challenge = SummerChallenge.query.get_or_404(challenge_id)
    
    # Check user authentication and account type
    if not current_user.is_authenticated:
        flash("Please log in to access summer challenges.", "error")
        return redirect(url_for('auth.login'))
    
    # Block regular users from accessing summer challenges
    if not getattr(current_user, "is_competition_participant", False):
        flash("Only summer competition participants can access these challenges.", "error")
        return redirect(url_for('main.challenges'))
    
    # Check if user's key stage matches the challenge
    if current_user.key_stage != challenge.key_stage:
        flash(f"This summer challenge is for {challenge.key_stage} students only. You are registered for {current_user.key_stage}.", "error")
        return redirect(url_for("main.challenges"))
    
    forms = {}
    submissions = {}

    # Only allow answer submission if user is a summer participant, challenge is not locked, and user's key stage matches
    can_submit = (
        current_user.is_authenticated
        and getattr(current_user, "is_competition_participant", False)
        and current_user.school_id is not None
        and not challenge.is_locked
        and current_user.key_stage == challenge.key_stage
    )

    if current_user.is_authenticated:
        # Create forms and get submissions for each answer box
        for answer_box in challenge.answer_boxes.all():  # Add .all() here
            forms[answer_box.id] = AnswerSubmissionForm()
            submissions[answer_box.id] = (
                SummerSubmission.query.filter_by(
                    user_id=current_user.id,
                    challenge_id=challenge_id,
                    answer_box_id=answer_box.id,
                )
                .order_by(SummerSubmission.submitted_at.desc())
                .all()
            )

        # Handle submission if the form is submitted and allowed
        if request.method == "POST" and can_submit:
            return handle_summer_challenge_submission(challenge, forms)

    # Check if all answers are correct for this user
    all_correct = (
        current_user.is_authenticated
        and len(challenge.answer_boxes.all()) > 0  # Add .all() here
        and all(
            SummerSubmission.query.filter_by(
                user_id=current_user.id,
                challenge_id=challenge.id,
                answer_box_id=box.id,
                is_correct=True,
            ).first()
            is not None
            for box in challenge.answer_boxes.all()  # Add .all() here
        )
    )

    return render_template(
        "main/summer_challenge.html",
        challenge=challenge,
        forms=forms if current_user.is_authenticated else None,
        submissions=submissions,
        attempts_remaining=3,
        all_correct=all_correct,
        can_submit=can_submit,
    )


def handle_challenge_submission(challenge: Challenge, forms: Dict) -> redirect:
    """
    Process a challenge submission.

    Args:
        challenge (Challenge): The Challenge object.
        forms (Dict): Dictionary of forms for each answer box.

    Returns:
        Redirect: Response redirecting back to the challenge page.

    Notes:
        - Validates form submission
        - Checks remaining attempts
        - Creates and handles submission result
    """
    box_id = int(request.form.get("answer_box_id"))
    form = forms[box_id]

    if not form.validate_on_submit():
        flash("Invalid submission.", "error")
        return redirect(url_for("main.challenge", challenge_id=challenge.id))

    answer_box = ChallengeAnswerBox.query.get_or_404(box_id)
    submission_count = check_submission_count(current_user.id, challenge.id, box_id)

    if submission_count >= 3 and not has_correct_submission(
        current_user.id, challenge.id
    ):
        flash("You have reached the maximum attempts for this part.", "error")
        return redirect(url_for("main.challenge", challenge_id=challenge.id))

    submission = create_submission(
        current_user.id, challenge.id, answer_box, form.answer.data
    )

    handle_submission_result(submission, challenge, answer_box)
    return redirect(url_for("main.challenge", challenge_id=challenge.id))


def handle_summer_challenge_submission(challenge: SummerChallenge, forms: Dict) -> redirect:
    """
    Process a summer challenge submission.
    """
    box_id = int(request.form.get("answer_box_id"))
    form = forms[box_id]

    if not form.validate_on_submit():
        flash("Invalid submission.", "error")
        return redirect(url_for("main.summer_challenge", challenge_id=challenge.id))

    answer_box = SummerChallengeAnswerBox.query.get_or_404(box_id)
    
    # Check submission count for this specific answer box
    submission_count = SummerSubmission.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge.id,
        answer_box_id=box_id,
    ).count()

    if submission_count >= 3:
        flash("You have reached the maximum attempts for this part.", "error")
        return redirect(url_for("main.summer_challenge", challenge_id=challenge.id))

    # Check if answer is correct
    is_correct = answer_box.check_answer(form.answer.data)
    
    # Calculate points awarded
    points_awarded = 0
    if is_correct:
        # Check if this will complete the entire challenge for this user
        user_correct_boxes = SummerSubmission.query.filter_by(
            user_id=current_user.id,
            challenge_id=challenge.id,
            is_correct=True
        ).count()
        
        total_boxes = len(list(challenge.answer_boxes))
        
        # If this submission will complete the challenge (all boxes correct)
        if user_correct_boxes + 1 == total_boxes:
            # Check if anyone else has completed the entire challenge already
            completed_users = db.session.query(SummerSubmission.user_id).filter(
                SummerSubmission.challenge_id == challenge.id,
                SummerSubmission.is_correct == True
            ).group_by(SummerSubmission.user_id).having(
                db.func.count(SummerSubmission.answer_box_id) == total_boxes
            ).count()
            
            # If no one has completed it yet, this user gets 3 points
            is_first_to_complete = (completed_users == 0)
            points_awarded = calculate_summer_challenge_points(challenge, is_first_to_complete)
        else:
            # Just answering one part correctly, but not completing the whole challenge
            points_awarded = 0  # No points until the whole challenge is completed

    # Create the submission
    submission = SummerSubmission(
        user_id=current_user.id,
        challenge_id=challenge.id,
        school_id=current_user.school_id,
        answer_box_id=answer_box.id,
        answer=form.answer.data,
        is_correct=is_correct,
        submitted_at=datetime.datetime.now(),
        points_awarded=points_awarded,
    )

    try:
        db.session.add(submission)
        db.session.commit()

        handle_summer_submission_result(submission, challenge, answer_box)
        
        if points_awarded > 0:
            update_summer_leaderboard(current_user.id, current_user.school_id, points_awarded)

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error saving summer submission: {str(e)}")
        flash("Error saving submission. Please try again.", "error")

    return redirect(url_for("main.summer_challenge", challenge_id=challenge.id))


def handle_summer_submission_result(
    submission: SummerSubmission, 
    challenge: SummerChallenge, 
    answer_box: SummerChallengeAnswerBox
) -> None:
    """
    Handle the result of a summer submission, showing appropriate messages.

    Args:
        submission (SummerSubmission): The SummerSubmission object.
        challenge (SummerChallenge): The SummerChallenge object.
        answer_box (SummerChallengeAnswerBox): The SummerChallengeAnswerBox object.

    Notes:
        - Flashes success message for correct answers with points earned
        - Shows remaining attempts for incorrect answers
        - Checks if challenge is fully completed
    """
    submission_count = SummerSubmission.query.filter_by(
        user_id=submission.user_id, 
        challenge_id=challenge.id, 
        answer_box_id=answer_box.id
    ).count()

    if submission.is_correct:
        points_msg = f" (+{submission.points_awarded} points)" if submission.points_awarded > 0 else ""
        flash(f"Correct answer for {answer_box.box_label}!{points_msg}", "success")

        # Check if all parts are now correct for this user
        all_correct = all(
            SummerSubmission.query.filter_by(
                user_id=submission.user_id,
                challenge_id=challenge.id,
                answer_box_id=box.id,
                is_correct=True,
            ).first() is not None
            for box in challenge.answer_boxes
        )
        
        if all_correct:
            flash(f"🎉 Challenge completed! Well done!", "success")
    else:
        remaining = 3 - submission_count
        flash(
            f"Incorrect answer for {answer_box.box_label}. {remaining} attempts remaining.",
            "error",
        )


@bp.route("/articles")
def articles():
    """
    List all articles.

    Returns:
        Rendered articles page template with all articles sorted by most recent.
    """
    articles = (
        Article.query.filter_by(type="article")
        .order_by(Article.date_posted.desc())
        .all()
    )
    return render_template("main/articles.html", title="Articles", articles=articles)


@bp.route("/newsletters/<path:filename>")
def serve_newsletter(filename):
    """
    Serve a newsletter file from the uploads directory.

    Args:
        filename (str): Name of the newsletter file to serve.

    Returns:
        Sent newsletter file from the uploads directory.
    """
    return send_from_directory(
        os.path.join(current_app.config["UPLOAD_FOLDER"], "newsletters"), filename
    )


def check_user_submission_count(user_id, challenge_id):
    """
    Check the total number of submissions for a user in a specific challenge.

    Args:
        user_id: The ID of the user.
        challenge_id: The ID of the challenge.

    Returns:
        int: Total number of submissions for the user in the challenge.
    """
    return AnswerSubmission.query.filter_by(
        user_id=user_id, challenge_id=challenge_id
    ).count()


def has_correct_submission(user_id, challenge_id):
    """
    Check if a user has a correct submission for a specific challenge.

    Args:
        user_id: The ID of the user.
        challenge_id: The ID of the challenge.

    Returns:
        bool: True if the user has a correct submission, False otherwise.
    """
    return (
        AnswerSubmission.query.filter_by(
            user_id=user_id, challenge_id=challenge_id, is_correct=True
        ).first()
        is not None
    )


@bp.route("/newsletters")
def newsletters():
    """
    List all newsletters.

    Returns:
        Rendered newsletters page template with all newsletters sorted by most recent.
    """
    newsletters = (
        Article.query.filter_by(type="newsletter")
        .order_by(Article.date_posted.desc())
        .all()
    )
    return render_template(
        "main/newsletters.html", title="Newsletters", articles=newsletters
    )


@bp.route("/newsletter/<int:id>")
def newsletter(id):
    """
    Display a specific newsletter.

    Args:
        id (int): The ID of the newsletter.

    Returns:
        Rendered newsletter detail page.

    Raises:
        404 Error: If the article is not a newsletter.
    """
    article = Article.query.get_or_404(id)
    if article.type != "newsletter":
        abort(404)
    return render_template("main/newsletter.html", article=article)


@bp.route("/article/<int:id>")
def article(id):
    """
    Display a specific article.

    Args:
        id (int): The ID of the article.

    Returns:
        Rendered article detail page.

    Raises:
        404 Error: If the article is not an article type.
    """
    article = Article.query.get_or_404(id)
    if article.type != "article":
        abort(404)
    return render_template("main/article.html", title=article.title, article=article)


@bp.route("/leaderboard")
def leaderboard():
    """
    Display leaderboards separated by key stages.
    """
    from sqlalchemy import func
    
    # Fix case sensitivity - use lowercase key stages
    ks3_entries = (
        LeaderboardEntry.query.join(User)
        .filter(LeaderboardEntry.key_stage == 'ks3')  # Changed to lowercase
        .order_by(LeaderboardEntry.score.desc())
        .limit(20)
        .all()
    )
    
    ks4_entries = (
        LeaderboardEntry.query.join(User)
        .filter(LeaderboardEntry.key_stage == 'ks4')  # Changed to lowercase
        .order_by(LeaderboardEntry.score.desc())
        .limit(20)
        .all()
    )
    
    ks5_entries = (
        LeaderboardEntry.query.join(User)
        .filter(LeaderboardEntry.key_stage == 'ks5')  # Changed to lowercase
        .order_by(LeaderboardEntry.score.desc())
        .limit(20)
        .all()
    )
    
    # Recent activity from challenge submissions and leaderboard updates
    recent_activity = []
    
    # Get recent challenge submissions
    try:
        recent_submissions = (
            AnswerSubmission.query
            .join(User)
            .join(ChallengeAnswerBox)
            .join(Challenge, ChallengeAnswerBox.challenge_id == Challenge.id)
            .filter(AnswerSubmission.is_correct == True)
            .order_by(AnswerSubmission.submitted_at.desc())
            .limit(10)
            .all()
        )
        
        for submission in recent_submissions:
            recent_activity.append({
                'type': 'challenge_completed',
                'title': f"{submission.user.full_name} solved a challenge",
                'description': f'Completed "{submission.answer_box.challenge.title}"',
                'timestamp': submission.submitted_at,
                'points': 1  # Regular points for individual answers
            })
    except Exception as e:
        current_app.logger.error(f"Error loading recent submissions: {str(e)}")
    
    # Get recent leaderboard updates
    try:
        recent_entries = (
            LeaderboardEntry.query
            .join(User)
            .filter(LeaderboardEntry.last_updated.isnot(None))
            .order_by(LeaderboardEntry.last_updated.desc())
            .limit(8)
            .all()
        )
        
        for entry in recent_entries:
            recent_activity.append({
                'type': 'points_awarded',
                'title': f"{entry.user.full_name} earned points",
                'description': f'Achieved {entry.score} total points in {entry.key_stage.upper()}',
                'timestamp': entry.last_updated,
                'points': None
            })
    except Exception as e:
        current_app.logger.error(f"Error loading recent entries: {str(e)}")
    
    # Sort by timestamp and limit
    recent_activity = sorted(recent_activity, key=lambda x: x['timestamp'] or datetime.datetime.min, reverse=True)[:15]
    
    # Competition statistics for regular competition
    stats = {
        'ks3_participants': LeaderboardEntry.query.filter_by(key_stage='ks3').count(),
        'ks4_participants': LeaderboardEntry.query.filter_by(key_stage='ks4').count(),
        'ks5_participants': LeaderboardEntry.query.filter_by(key_stage='ks5').count(),
        'total_points_awarded': db.session.query(func.sum(LeaderboardEntry.score)).scalar() or 0,
        'total_challenges': Challenge.query.count(),
        'total_submissions': AnswerSubmission.query.count() if AnswerSubmission.query.first() else 0
    }
    
    return render_template(
        "main/leaderboard.html", 
        title="Overall Leaderboard",
        ks3_entries=ks3_entries,
        ks4_entries=ks4_entries,
        ks5_entries=ks5_entries,
        recent_activity=recent_activity,
        stats=stats
    )

@bp.route("/summer_leaderboard")
def summer_leaderboard():
    """
    Display summer competition leaderboards separated by key stages.

    Returns:
        Rendered summer leaderboard page with:
        - Key stage separated leaderboards (KS3, KS4, KS5)
        - School leaderboard by key stage
        - Recent activity
        
    Notes:
        - Shows top performers by key stage for fair competition
        - Updates in real-time based on summer submissions
        - Includes school rankings separated by key stage
    """
    from sqlalchemy import func
    
    # Key Stage 3 Leaderboard (Years 7-8)
    ks3_leaders = (
        SummerLeaderboard.query
        .join(User)
        .join(School, User.school_id == School.id)
        .filter(User.key_stage == 'KS3')
        .order_by(SummerLeaderboard.score.desc())
        .limit(15)
        .all()
    )
    
    # Key Stage 4 Leaderboard (Years 9-11)
    ks4_leaders = (
        SummerLeaderboard.query
        .join(User)
        .join(School, User.school_id == School.id)
        .filter(User.key_stage == 'KS4')
        .order_by(SummerLeaderboard.score.desc())
        .limit(15)
        .all()
    )
    
    # Key Stage 5 Leaderboard (Years 12-13)
    ks5_leaders = (
        SummerLeaderboard.query
        .join(User)
        .join(School, User.school_id == School.id)
        .filter(User.key_stage == 'KS5')
        .order_by(SummerLeaderboard.score.desc())
        .limit(15)
        .all()
    )
    
    # School leaderboards by key stage
    ks3_school_leaders = (
        db.session.query(
            School.id,
            School.name,
            func.sum(SummerLeaderboard.score).label('total_score'),
            func.count(SummerLeaderboard.user_id).label('participant_count'),
            func.avg(SummerLeaderboard.score).label('average_score')
        )
        .join(SummerLeaderboard, School.id == SummerLeaderboard.school_id)
        .join(User, SummerLeaderboard.user_id == User.id)
        .filter(User.key_stage == 'KS3')
        .group_by(School.id, School.name)
        .order_by(func.sum(SummerLeaderboard.score).desc())
        .limit(8)
        .all()
    )
    
    ks4_school_leaders = (
        db.session.query(
            School.id,
            School.name,
            func.sum(SummerLeaderboard.score).label('total_score'),
            func.count(SummerLeaderboard.user_id).label('participant_count'),
            func.avg(SummerLeaderboard.score).label('average_score')
        )
        .join(SummerLeaderboard, School.id == SummerLeaderboard.school_id)
        .join(User, SummerLeaderboard.user_id == User.id)
        .filter(User.key_stage == 'KS4')
        .group_by(School.id, School.name)
        .order_by(func.sum(SummerLeaderboard.score).desc())
        .limit(8)
        .all()
    )
    
    ks5_school_leaders = (
        db.session.query(
            School.id,
            School.name,
            func.sum(SummerLeaderboard.score).label('total_score'),
            func.count(SummerLeaderboard.user_id).label('participant_count'),
            func.avg(SummerLeaderboard.score).label('average_score')
        )
        .join(SummerLeaderboard, School.id == SummerLeaderboard.school_id)
        .join(User, SummerLeaderboard.user_id == User.id)
        .filter(User.key_stage == 'KS5')
        .group_by(School.id, School.name)
        .order_by(func.sum(SummerLeaderboard.score).desc())
        .limit(8)
        .all()
    )
    
    # Recent activity - latest submissions with points
    recent_activity = (
        SummerSubmission.query
        .join(User)
        .join(SummerChallenge)
        .join(School, User.school_id == School.id)
        .filter(SummerSubmission.is_correct == True)
        .filter(SummerSubmission.points_awarded > 0)
        .order_by(SummerSubmission.submitted_at.desc())
        .limit(15)
        .all()
    )
    
    # Competition statistics by key stage
    stats = {
        'ks3_participants': SummerLeaderboard.query.join(User).filter(User.key_stage == 'KS3').count(),
        'ks4_participants': SummerLeaderboard.query.join(User).filter(User.key_stage == 'KS4').count(),
        'ks5_participants': SummerLeaderboard.query.join(User).filter(User.key_stage == 'KS5').count(),
        'total_participants': SummerLeaderboard.query.count(),
        'total_schools': db.session.query(SummerLeaderboard.school_id).distinct().count(),
        'total_submissions': SummerSubmission.query.count(),
        'correct_submissions': SummerSubmission.query.filter_by(is_correct=True).count(),
        'total_points_awarded': db.session.query(func.sum(SummerSubmission.points_awarded)).scalar() or 0,
    }
    
    # Calculate active challenges using Python logic since SQL interval syntax varies by database
    from datetime import timedelta
    all_challenges = SummerChallenge.query.all()
    active_count = 0
    for challenge in all_challenges:
        if not challenge.is_locked:  # Use the existing is_locked property
            active_count += 1
    stats['active_challenges'] = active_count
    
    return render_template(
        "main/summer_leaderboard.html",
        title="Summer Competition 2025 Leaderboard",
        ks3_leaders=ks3_leaders,
        ks4_leaders=ks4_leaders,
        ks5_leaders=ks5_leaders,
        ks3_school_leaders=ks3_school_leaders,
        ks4_school_leaders=ks4_school_leaders,
        ks5_school_leaders=ks5_school_leaders,
        recent_activity=recent_activity,
        stats=stats
    )


@bp.route("/privacy_policy")
def privacy_policy():
    """
    Display the privacy policy.

    Returns:
        Rendered privacy policy page.
    """
    return render_template(
        "main/privacy_policy.html",
        title="Privacy Policy",
        current_date=datetime.datetime.now(),
    )
