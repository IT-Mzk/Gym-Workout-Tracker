"""
Website routing using Flask
"""
import re
from datetime import date
from pathlib import Path

import pandas as pd
from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from modules.dates import Weekday
from modules.profile import User
from modules.workouts import Exercise, Routine
from routes.api_routes import api_bp

app = Flask(__name__)
app.secret_key = "gym-workout-tracker-dev-secret"
app.register_blueprint(api_bp)


def _safe_user_name(user_name):
    """
    Keep usernames compatible with the existing user_data folder layout.
    """
    return re.sub(r"[^A-Za-z0-9_ ]", "", user_name).strip()


def _is_positive_int(value):
    """
    Check if a value is a positive integer.
    """
    try:
        return int(value) > 0
    except (TypeError, ValueError):
        return False


def _is_number(value):
    """
    Check if a value can be converted to a number.
    """
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def _safe_form_label(value):
    """
    Keep routine and exercise names safe before saving them to files.
    """
    return re.sub(r"[^A-Za-z0-9_ ]", "", value).strip()


def _get_routine(current_user, routine_name):
    """
    Return a routine if it exists for the current user.
    """
    return current_user.routines.get(routine_name)


def _current_user():
    """
    Load the currently authenticated user from the Flask session.
    """
    username = session.get("username")
    if not username:
        return None

    try:
        return User.load_user_data(username)
    except FileNotFoundError:
        return User(username)


def _ensure_active_user():
    """
    Return the logged-in user, or None when the visitor is anonymous.
    """
    return _current_user()


def _save_current_user(current_user, export_routines=False):
    """
    Persist the active user's profile and, when needed, routine files.
    """
    current_user.to_json()
    if export_routines:
        current_user.export_routines()


def _login_required_user():
    """
    Return the active user for routes that require authentication.
    """
    current_user = _ensure_active_user()
    if current_user is None:
        return None
    return current_user


def _routine_file_stem(current_user, routine_name):
    """
    Return the path stem used by the existing routine JSON and CSV files.
    """
    user_folder = current_user.name.replace(" ", "_")
    routine_folder = routine_name.replace(" ", "_")
    return f"user_data/{user_folder}/{routine_folder}/{routine_folder}"


def _profile_photo(current_user):
    """
    Return the relative static path for the active user's profile photo.
    """
    pic_path = Path(f"static/img/{current_user.name}_profile_picture.jpg")
    if pic_path.is_file():
        return f"img/{current_user.name}_profile_picture.jpg"
    return "img/default_profile.jpg"


def _slugify(value):
    """
    Convert labels into stable frontend ids.
    """
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "routine"


def _parse_log_date(value):
    """
    Parse ISO log dates when possible.
    """
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def _format_date_label(value):
    """
    Convert stored dates into a compact frontend label.
    """
    parsed = _parse_log_date(value)
    if parsed is None:
        return str(value)
    return parsed.strftime("%b %d")


def _valid_weights(weights):
    """
    Return non-empty, non-NaN weights from a stored workout entry.
    """
    valid = []
    for weight in weights:
        if pd.isna(weight):
            continue
        valid.append(weight)
    return valid


def _coerce_weight(weight):
    """
    Convert logged weights to a number when possible.
    """
    try:
        return float(weight)
    except (TypeError, ValueError):
        return None


def _format_weight(weight):
    """
    Format weight values for frontend display.
    """
    if weight is None:
        return "No record"
    if float(weight).is_integer():
        return f"{int(weight)} lbs"
    return f"{weight:.1f} lbs"


def _exercise_record(exercise):
    """
    Return the numeric personal record for an exercise.
    """
    weights = []
    for _, logged_weights in exercise.history.items():
        for weight in _valid_weights(logged_weights):
            numeric_weight = _coerce_weight(weight)
            if numeric_weight is not None:
                weights.append(numeric_weight)
    if not weights:
        return None
    return max(weights)


def _routine_focus(routine):
    """
    Build a short summary for a routine.
    """
    names = [exercise.name for _, exercise in routine.exercises.items()]
    if not names:
        return "No exercises added yet"
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return f"{names[0]}, {names[1]} and {len(names) - 2} more"


def _routine_volume(routine):
    """
    Return the total planned working sets for a routine.
    """
    total_sets = sum(
        int(exercise.sets) for _, exercise in routine.exercises.items()
    )
    return f"{total_sets} working sets"


def _routine_last_log_label(routine):
    """
    Return the latest workout date for a routine.
    """
    latest_date = None
    for _, exercise in routine.exercises.items():
        for day_label in exercise.history:
            parsed = _parse_log_date(day_label)
            if parsed is not None and (
                latest_date is None or parsed > latest_date
            ):
                latest_date = parsed
    if latest_date is None:
        return "No logs yet"
    return latest_date.strftime("%b %d")


def _selected_workout_days(current_user):
    """
    Return a display-ready list of selected workout days.
    """
    return [
        day.name.capitalize()
        for day, is_selected in current_user.workout_days.items()
        if is_selected
    ]


def _total_exercise_count(current_user):
    """
    Return the total number of exercises across all routines.
    """
    return sum(
        len(routine.exercises) for _, routine in current_user.routines.items()
    )


def _history_entries(current_user):
    """
    Aggregate exercise logs into routine-level history entries.
    """
    entries = []
    for _, routine in current_user.routines.items():
        sessions = {}
        for _, exercise in routine.exercises.items():
            for day_label, logged_weights in exercise.history.items():
                valid_weights = _valid_weights(logged_weights)
                if not valid_weights:
                    continue
                session = sessions.setdefault(
                    day_label,
                    {
                        "exercise_names": set(),
                        "set_count": 0,
                        "sort_date": _parse_log_date(day_label),
                    },
                )
                session["exercise_names"].add(exercise.name)
                session["set_count"] += len(valid_weights)

        for day_label, session in sessions.items():
            exercise_count = len(session["exercise_names"])
            entries.append(
                {
                    "date": _format_date_label(day_label),
                    "routine": routine.name,
                    "note": (
                        f"{exercise_count} exercises logged, "
                        f"{session['set_count']} total sets."
                    ),
                    "sort_date": session["sort_date"] or date.min,
                }
            )

    entries.sort(key=lambda item: item["sort_date"], reverse=True)
    return [
        {
            "date": entry["date"],
            "routine": entry["routine"],
            "note": entry["note"],
        }
        for entry in entries
    ]


def _record_entries(current_user):
    """
    Build a frontend-friendly list of personal records.
    """
    records = []
    for _, routine in current_user.routines.items():
        for _, exercise in routine.exercises.items():
            personal_record = _exercise_record(exercise)
            if personal_record is None:
                continue
            records.append(
                {
                    "label": exercise.name,
                    "value": _format_weight(personal_record),
                    "sort_weight": personal_record,
                }
            )

    records.sort(key=lambda item: item["sort_weight"], reverse=True)
    return [
        {"label": record["label"], "value": record["value"]}
        for record in records[:6]
    ]


def _serialize_routine(routine):
    """
    Serialize a routine for the React demo.
    """
    exercises = [
        {
            "name": exercise.name,
            "sets": int(exercise.sets),
            "record": _format_weight(_exercise_record(exercise)),
        }
        for _, exercise in routine.exercises.items()
    ]
    return {
        "id": _slugify(routine.name),
        "name": routine.name,
        "focus": _routine_focus(routine),
        "volume": _routine_volume(routine),
        "lastLog": _routine_last_log_label(routine),
        "exercises": exercises,
    }


def _frontend_state(current_user):
    """
    Return the full state object used by the React frontend demo.
    """
    workout_days = _selected_workout_days(current_user)
    history = _history_entries(current_user)
    return {
        "user": {
            "name": current_user.name,
            "initials": "".join(
                part[0].upper() for part in current_user.name.split()[:2]
            )
            or current_user.name[:2].upper(),
            "level": current_user.level(),
            "xpCurrent": current_user.xp_points % current_user.XP_PER_LEVEL,
            "xpGoal": current_user.XP_PER_LEVEL,
            "loggedSessions": len(history),
            "weeklyGoal": (
                f"{len(workout_days)} planned sessions"
                if workout_days
                else "Choose workout days"
            ),
        },
        "workoutDays": workout_days,
        "routines": [
            _serialize_routine(routine)
            for _, routine in current_user.routines.items()
        ],
        "records": _record_entries(current_user),
        "history": history[:8],
        "nextWorkout": _next_workout_label(current_user),
        "profilePhoto": _profile_photo(current_user),
    }


def _next_workout_label(current_user):
    """
    Return a human-readable label for the next scheduled workout.
    """
    next_workout_day = current_user.next_workout_day()
    if next_workout_day is None:
        return "No workout day selected yet"
    return next_workout_day.strftime("%A, %b %d")


@app.context_processor
def inject_shell_context():
    """
    Share top-level shell data with authenticated templates.
    """
    current_user = _current_user()
    if current_user is None:
        return {}

    workout_days = _selected_workout_days(current_user)
    return {
        "shell_user_name": current_user.name,
        "shell_user_level": current_user.level(),
        "shell_routine_count": len(current_user.routines),
        "shell_exercise_count": _total_exercise_count(current_user),
        "shell_workout_day_count": len(workout_days),
        "shell_profile_photo": _profile_photo(current_user),
    }


# ----------Login Page-----------#
@app.route("/")
def login():
    """
    Renders login page
    """
    return render_template("login.html")


@app.route("/frontend-demo")
def frontend_demo():
    """
    Serve the React frontend demo.
    """
    current_user = _login_required_user()
    if current_user is None:
        return redirect(url_for("login"))
    return render_template("frontend_demo.html")


@app.route("/api/frontend-demo/state")
def frontend_demo_state():
    """
    Return the current frontend state as JSON.
    """
    current_user = _login_required_user()
    if current_user is None:
        return jsonify({"error": "Login required."}), 401
    return jsonify(_frontend_state(current_user))


@app.route("/api/frontend-demo/routines", methods=["POST"])
def frontend_demo_create_routine():
    """
    Create a routine from the React frontend demo.
    """
    current_user = _login_required_user()
    if current_user is None:
        return jsonify({"error": "Login required."}), 401

    payload = request.get_json(silent=True) or {}
    routine_name = _safe_form_label(str(payload.get("name", "")))

    if not routine_name:
        return jsonify({"error": "Routine name is required."}), 400

    if routine_name in current_user.routines:
        return jsonify({"error": "A routine with that name already exists."}), 409

    current_user.add_routine(Routine(routine_name))
    _save_current_user(current_user, export_routines=True)
    return jsonify(_frontend_state(current_user)), 201


@app.route("/api/frontend-demo/workout-days", methods=["POST"])
def frontend_demo_update_days():
    """
    Update selected workout days from the React frontend demo.
    """
    current_user = _login_required_user()
    if current_user is None:
        return jsonify({"error": "Login required."}), 401

    payload = request.get_json(silent=True) or {}
    workout_days = payload.get("workoutDays", [])

    if not isinstance(workout_days, list):
        return jsonify({"error": "Workout days must be a list."}), 400

    try:
        weekday_members = [Weekday[day.upper()] for day in workout_days]
    except KeyError:
        return jsonify({"error": "One or more workout days are invalid."}), 400

    current_user.set_workout_days(weekday_members)
    _save_current_user(current_user)
    return jsonify(_frontend_state(current_user))


def _try_bridge_api_session(username):
    """
    When a user logs in via Flask, also create or look up their SQL Server
    record so the REST API endpoints are accessible in the same session.
    Silently skipped if SQL Server is not configured.
    """
    try:
        from database import get_connection, row_to_dict  # noqa: PLC0415

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT UserId AS id FROM Users WHERE Username = ?", username
            )
            api_user = row_to_dict(cursor, cursor.fetchone())
            if api_user is None:
                cursor.execute(
                    "INSERT INTO Users (Username) VALUES (?)", username
                )
                conn.commit()
                cursor.execute(
                    "SELECT UserId AS id FROM Users WHERE Username = ?",
                    username,
                )
                api_user = row_to_dict(cursor, cursor.fetchone())
            session["api_user_id"] = api_user["id"]
            session["api_username"] = username
    except Exception:  # noqa: BLE001
        pass


@app.route("/auth", methods=["POST"])
def authenticate():
    """
    Check if user exists in system, create new user if not found
    """
    username = _safe_user_name(request.form.get("username", ""))
    if not username:
        return redirect(url_for("login"))

    try:
        current_user = User.load_user_data(username)
    except FileNotFoundError:
        current_user = User(username)
        _save_current_user(current_user)

    session["username"] = current_user.name
    _try_bridge_api_session(current_user.name)
    return redirect(url_for("home"))

@app.route("/logout")
def logout():
    """
    Clear the active user from the browser session.
    """
    session.pop("username", None)
    session.pop("api_user_id", None)
    session.pop("api_username", None)
    return redirect(url_for("login"))


# --------Home Page ---------#
@app.route("/home")
def home():
    """
    Renders home page
    """
    current_user = _login_required_user()
    if current_user is None:
        return redirect(url_for("login"))

    return render_template(
        "home.html",
        name=current_user.name,
        routine_count=len(current_user.routines),
        exercise_count=_total_exercise_count(current_user),
        workout_day_count=len(_selected_workout_days(current_user)),
        next_workout_day=_next_workout_label(current_user),
        routines_preview=list(current_user.routines.values())[:3],
        level=current_user.level(),
        xp_points=current_user.xp_points,
    )


# --------Profile Page---------#


@app.route("/profile")
def profile():
    """
    Renders profile page
    """
    current_user = _login_required_user()
    if current_user is None:
        return redirect(url_for("login"))

    level = current_user.level()
    level_fraction = current_user.xp_points - 1000 * current_user.level()
    return render_template(
        "profile.html",
        routines=current_user.routines,
        length=len(current_user.routines),
        username=current_user.name,
        photo=_profile_photo(current_user),
        level=level,
        level_fraction=level_fraction,
        progress_percent=round(level_fraction / 10, 1),
        total_exercises=_total_exercise_count(current_user),
        workout_day_count=len(_selected_workout_days(current_user)),
        next_workout_day=_next_workout_label(current_user),
    )


@app.route("/edit-profile")
def edit_profile():
    """
    Renders page where user can upload a profile picture
    """
    current_user = _login_required_user()
    if current_user is None:
        return redirect(url_for("login"))

    return render_template(
        "editprofile.html",
        photo=_profile_photo(current_user),
        username=current_user.name,
    )


@app.route("/upload-successful", methods=["POST"])
def photo_uploaded():
    """
    Uploads photo into system
    """
    current_user = _login_required_user()
    if current_user is None:
        return redirect(url_for("login"))

    if "file" not in request.files:
        return redirect(url_for("edit_profile"))

    uploaded_files = request.files["file"]
    if uploaded_files.filename == "":
        return redirect(url_for("edit_profile"))

    uploaded_files.save(f"static/img/{current_user.name}_profile_picture.jpg")
    return redirect(url_for("profile"))


# @app.route("/username-changed", methods=["GET"])
# def username_changed():
#     """
#     Updates username to new username the user inputted
#     """
#     global username
#     username = request.args.get("new_username")
#     return redirect(url_for("profile"))


@app.route("/profile/<routine>/history")
def routine_history(routine):
    """
    Displays selected routine's .csv file in a html table

    Args:
        routine: String representing name of routine
    """
    current_user = _login_required_user()
    if current_user is None:
        return redirect(url_for("login"))
    if _get_routine(current_user, routine) is None:
        return redirect(url_for("profile"))

    try:
        df = pd.read_csv(f"{_routine_file_stem(current_user, routine)}.csv")
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return redirect(url_for("profile"))

    df = df[df.columns[1:]]
    return render_template(
        "routinehistory.html",
        routine=routine,
        data=df.to_html(index=False, classes="history-data"),
    )


@app.route("/profile/<routine>/PRs")
def personal_records(routine):
    """
    Displays PRs for all exercises in a selected routine

    Args:
        routine: String representing name of routine
    """
    current_user = _login_required_user()
    if current_user is None:
        return redirect(url_for("login"))
    selected_routine = _get_routine(current_user, routine)
    if selected_routine is None:
        return redirect(url_for("profile"))

    exercises = selected_routine.exercises
    return render_template(
        "viewPR.html",
        routine=routine,
        exercises=exercises,
        length=len(exercises),
    )


# ---------Everything that is linked with the Plan page--------- #


@app.route("/plan")
def plan_page():
    """
    Renders page for viewing routines/add new routine
    """
    current_user = _login_required_user()
    if current_user is None:
        return redirect(url_for("login"))

    return render_template(
        "plan.html",
        routines=current_user.routines,
        length=len(current_user.routines),
        total_exercises=_total_exercise_count(current_user),
    )


# ------------- New routine --------------------#


@app.route("/add-routine")
def new_routine():
    """
    Asks user for a routine name, then redirects them to /add-exercise
    """
    current_user = _login_required_user()
    if current_user is None:
        return redirect(url_for("login"))

    return render_template("addroutine.html")


@app.route("/submit-routine")
def submit_routine():
    """
    Adds routine to Routine object
    """
    current_user = _login_required_user()
    if current_user is None:
        return redirect(url_for("login"))

    new_routine_name = _safe_form_label(
        request.args.get("routine-name", "")
    )

    if not new_routine_name:
        return redirect(url_for("new_routine"))

    if new_routine_name in current_user.routines:
        return redirect(url_for("plan_page"))

    current_user.add_routine(Routine(new_routine_name))
    _save_current_user(current_user, export_routines=True)

    return redirect(url_for("add_new_exercise", routine=new_routine_name))



# ------------- Add exercise to routine ------------- #


@app.route("/add-exercise/<routine>")
def add_new_exercise(routine):
    """
    Renders page for adding new exercise

    Args:
        routine: String representing name of routine
    """
    current_user = _login_required_user()
    if current_user is None:
        return redirect(url_for("login"))
    if _get_routine(current_user, routine) is None:
        return redirect(url_for("plan_page"))

    return render_template("addexercise.html", routine_name=routine)


@app.route("/submit-exercise/<routine>")
def submit_exercise(routine):
    """
    Adds new exercise to routine
    Sends user back to add more exercises
    """
    current_user = _login_required_user()
    if current_user is None:
        return redirect(url_for("login"))

    selected_routine = _get_routine(current_user, routine)
    if selected_routine is None:
        return redirect(url_for("plan_page"))

    exercise_name = _safe_form_label(request.args.get("exercise-name", ""))
    sets = request.args.get("sets", "").strip()

    if not exercise_name:
        return redirect(url_for("add_new_exercise", routine=routine))

    if not _is_positive_int(sets):
        return redirect(url_for("add_new_exercise", routine=routine))

    if exercise_name in selected_routine.exercises:
        return redirect(url_for("add_new_exercise", routine=routine))

    selected_routine.add_exercise(Exercise(exercise_name, sets))
    _save_current_user(current_user, export_routines=True)

    return redirect(url_for("add_new_exercise", routine=routine))



# ---------------------Logging-------------------- #


@app.route("/logs/<day>")
def logs_page(day):
    """
    Renders logging page

    Args:
        day: String reprenting what day of the week it is
    """
    current_user = _login_required_user()
    if current_user is None:
        return redirect(url_for("login"))

    return render_template(
        "logs.html",
        day=day,
        routines=current_user.routines,
        length=len(current_user.routines),
    )


@app.route("/logs/<day>/<routine>")
def log_exercise(day, routine):
    """
    Renders page for user to enter weights for each exercise in a routine

    Args:
        day: String reprenting what day of the week it is
        routine: String representing name of routine
    """
    current_user = _login_required_user()
    if current_user is None:
        return redirect(url_for("login"))
    selected_routine = _get_routine(current_user, routine)
    if selected_routine is None:
        return redirect(url_for("logs_page", day=day))

    exercise_dict = selected_routine.exercises
    return render_template(
        "routinelog.html",
        day=day,
        routine=routine,
        inputs=exercise_dict,
        exercise_total=len(exercise_dict),
    )


@app.route("/submit-log/<day>/<routine>", methods=["GET", "POST"])
def submit_log(routine, day):
    """
    Submit weights user entered
    """
    current_user = _login_required_user()
    if current_user is None:
        return redirect(url_for("login"))

    selected_routine = _get_routine(current_user, routine)
    if selected_routine is None:
        return redirect(url_for("logs_page", day=day))

    if request.method == "POST":
        for _, exercise in selected_routine.exercises.items():
            for i in range(int(exercise.sets)):
                weight = request.form.get(f"{exercise.name} {i}", "").strip()

                if not _is_number(weight):
                    return redirect(url_for(
                        "log_exercise",
                        day=day,
                        routine=routine
                    ))

        try:
            selected_routine.load_log(
                f"{_routine_file_stem(current_user, routine)}.csv"
            )
        except FileNotFoundError:
            pass

        try:
            current_user.log_workout(routine_name=routine)
        except (KeyError, ValueError):
            return redirect(
                url_for("log_exercise", day=day, routine=routine)
            )

        _save_current_user(current_user)
        selected_routine.export_log(
            f"{_routine_file_stem(current_user, routine)}.csv"
        )

    return redirect(url_for("gain_xp", day=day))



@app.route("/gainxp/<day>")
def gain_xp(day):
    """
    Renders a page notifying the user that they gained xp

    Args:
        day: String reprenting what day of the week it is
    """
    current_user = _login_required_user()
    if current_user is None:
        return redirect(url_for("login"))

    level = current_user.level()
    level_fraction = current_user.xp_points - 1000 * current_user.level()
    return render_template(
        "gainxp.html",
        day=day,
        level=level,
        level_fraction=level_fraction,
        progress_percent=round(level_fraction / 10, 1),
    )


# -------------------Calendar----------------------#
@app.route("/calendar")
def calendar():
    """
    Renders Calendar page
    """
    current_user = _login_required_user()
    if current_user is None:
        return redirect(url_for("login"))

    days = _selected_workout_days(current_user)
    return render_template(
        "calendar.html",
        workout_days=days,
        length=len(days),
        next_workout_day=_next_workout_label(current_user),
    )


@app.route("/select-days")
def select_days():
    """
    Renders page where user selects workout days
    """
    current_user = _login_required_user()
    if current_user is None:
        return redirect(url_for("login"))

    selected_days = {
        day.name
        for day, is_selected in current_user.workout_days.items()
        if is_selected
    }
    return render_template("selectdays.html", selected_days=selected_days)

@app.route("/submit-days", methods=["GET", "POST"])
def submit_days():
    """
    Fetch user input from /select-days
    """
    current_user = _login_required_user()
    if current_user is None:
        return redirect(url_for("login"))

    if request.method == "POST":
        days = request.form.getlist("day")

        try:
            selected_days = [Weekday[day] for day in days]
        except KeyError:
            return redirect(url_for("select_days"))

        current_user.set_workout_days(selected_days)
        _save_current_user(current_user)

    return redirect(url_for("calendar"))


@app.errorhandler(404)
def page_not_found(error):
    """
    Redirect users when they open a route that does not exist.
    """
    return redirect(url_for("login"))


@app.errorhandler(500)
def internal_error(error):
    """
    Redirect users when an unexpected backend error happens.
    """
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
