"""
REST API routes backed by SQL Server.
"""
from datetime import date
from decimal import Decimal

from flask import Blueprint, jsonify, request, session

from database import get_connection, row_to_dict, rows_to_dicts

api_bp = Blueprint("api", __name__, url_prefix="/api")

VALID_DAYS = {
    "MONDAY",
    "TUESDAY",
    "WEDNESDAY",
    "THURSDAY",
    "FRIDAY",
    "SATURDAY",
    "SUNDAY",
}


def _json_error(message, status_code):
    """
    Return a consistent JSON error response.
    """
    return jsonify({"error": message}), status_code


def _payload():
    """
    Read JSON request data safely.
    """
    return request.get_json(silent=True) or {}


def _clean_text(value):
    """
    Normalize short text submitted to the API.
    """
    return str(value or "").strip()


def _positive_int(value):
    """
    Convert a value to a positive integer, or return None.
    """
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    if number <= 0:
        return None
    return number


def _non_negative_decimal(value):
    """
    Convert a value to a non-negative Decimal, or return None.
    """
    try:
        number = Decimal(str(value))
    except Exception:
        return None
    if number < 0:
        return None
    return number


def _api_user_id():
    """
    Return the logged-in REST API user id from session.
    """
    return session.get("api_user_id")


def _require_api_user():
    """
    Return user id or a login-required response.
    """
    user_id = _api_user_id()
    if user_id is None:
        return None, _json_error("Login required.", 401)
    return user_id, None


def _get_owned_routine(cursor, user_id, routine_id):
    """
    Return a routine only when it belongs to the logged-in user.
    """
    cursor.execute(
        """
        SELECT RoutineId AS id, Name AS name, CreatedAt AS createdAt
        FROM Routines
        WHERE RoutineId = ? AND UserId = ?
        """,
        routine_id,
        user_id,
    )
    return row_to_dict(cursor, cursor.fetchone())


def _get_owned_exercise(cursor, user_id, exercise_id):
    """
    Return an exercise only when its routine belongs to the logged-in user.
    """
    cursor.execute(
        """
        SELECT
            e.ExerciseId AS id,
            e.RoutineId AS routineId,
            e.Name AS name,
            e.Sets AS sets
        FROM Exercises e
        INNER JOIN Routines r ON r.RoutineId = e.RoutineId
        WHERE e.ExerciseId = ? AND r.UserId = ?
        """,
        exercise_id,
        user_id,
    )
    return row_to_dict(cursor, cursor.fetchone())


@api_bp.route("/health")
def health():
    """
    Check that the API process is running.
    """
    return jsonify({"status": "ok"})


@api_bp.route("/auth/login", methods=["POST"])
def api_login():
    """
    Login by username. Creates the user when it does not exist.
    """
    username = _clean_text(_payload().get("username"))
    if not username:
        return _json_error("Username is required.", 400)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT UserId AS id, Username AS username, XPPoints AS xpPoints
            FROM Users
            WHERE Username = ?
            """,
            username,
        )
        user = row_to_dict(cursor, cursor.fetchone())

        if user is None:
            cursor.execute("INSERT INTO Users (Username) VALUES (?)", username)
            cursor.execute(
                """
                SELECT UserId AS id, Username AS username, XPPoints AS xpPoints
                FROM Users
                WHERE Username = ?
                """,
                username,
            )
            user = row_to_dict(cursor, cursor.fetchone())
            conn.commit()

    session["api_user_id"] = user["id"]
    session["api_username"] = user["username"]
    return jsonify({"user": user})


@api_bp.route("/auth/logout", methods=["POST"])
def api_logout():
    """
    Logout the REST API user.
    """
    session.pop("api_user_id", None)
    session.pop("api_username", None)
    return jsonify({"message": "Logged out."})


@api_bp.route("/users/me")
def current_user():
    """
    Return the current API user profile.
    """
    user_id, error = _require_api_user()
    if error:
        return error

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT UserId AS id, Username AS username, XPPoints AS xpPoints
            FROM Users
            WHERE UserId = ?
            """,
            user_id,
        )
        user = row_to_dict(cursor, cursor.fetchone())

    if user is None:
        return _json_error("User not found.", 404)
    return jsonify({"user": user})


@api_bp.route("/routines", methods=["GET"])
def list_routines():
    """
    List routines for the logged-in user.
    """
    user_id, error = _require_api_user()
    if error:
        return error

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT RoutineId AS id, Name AS name, CreatedAt AS createdAt
            FROM Routines
            WHERE UserId = ?
            ORDER BY CreatedAt DESC
            """,
            user_id,
        )
        routines = rows_to_dicts(cursor)

    return jsonify({"routines": routines})


@api_bp.route("/routines", methods=["POST"])
def create_routine():
    """
    Create a routine for the logged-in user.
    """
    user_id, error = _require_api_user()
    if error:
        return error

    name = _clean_text(_payload().get("name"))
    if not name:
        return _json_error("Routine name is required.", 400)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM Routines WHERE UserId = ? AND Name = ?",
            user_id,
            name,
        )
        if cursor.fetchone():
            return _json_error("Routine already exists.", 409)

        cursor.execute(
            "INSERT INTO Routines (UserId, Name) VALUES (?, ?)",
            user_id,
            name,
        )
        cursor.execute(
            """
            SELECT TOP 1 RoutineId AS id, Name AS name, CreatedAt AS createdAt
            FROM Routines
            WHERE UserId = ? AND Name = ?
            ORDER BY RoutineId DESC
            """,
            user_id,
            name,
        )
        routine = row_to_dict(cursor, cursor.fetchone())
        conn.commit()

    return jsonify({"routine": routine}), 201


@api_bp.route("/routines/<int:routine_id>", methods=["GET"])
def get_routine(routine_id):
    """
    Return one routine and its exercises.
    """
    user_id, error = _require_api_user()
    if error:
        return error

    with get_connection() as conn:
        cursor = conn.cursor()
        routine = _get_owned_routine(cursor, user_id, routine_id)
        if routine is None:
            return _json_error("Routine not found.", 404)

        cursor.execute(
            """
            SELECT ExerciseId AS id, Name AS name, Sets AS sets
            FROM Exercises
            WHERE RoutineId = ?
            ORDER BY ExerciseId
            """,
            routine_id,
        )
        routine["exercises"] = rows_to_dicts(cursor)

    return jsonify({"routine": routine})


@api_bp.route("/routines/<int:routine_id>", methods=["PUT"])
def update_routine(routine_id):
    """
    Rename one routine.
    """
    user_id, error = _require_api_user()
    if error:
        return error

    name = _clean_text(_payload().get("name"))
    if not name:
        return _json_error("Routine name is required.", 400)

    with get_connection() as conn:
        cursor = conn.cursor()
        routine = _get_owned_routine(cursor, user_id, routine_id)
        if routine is None:
            return _json_error("Routine not found.", 404)

        cursor.execute(
            """
            SELECT 1 FROM Routines
            WHERE UserId = ? AND Name = ? AND RoutineId <> ?
            """,
            user_id,
            name,
            routine_id,
        )
        if cursor.fetchone():
            return _json_error("Routine already exists.", 409)

        cursor.execute(
            "UPDATE Routines SET Name = ? WHERE RoutineId = ?",
            name,
            routine_id,
        )
        conn.commit()

    return jsonify({"routine": {"id": routine_id, "name": name}})


@api_bp.route("/routines/<int:routine_id>", methods=["DELETE"])
def delete_routine(routine_id):
    """
    Delete one routine and its exercises.
    """
    user_id, error = _require_api_user()
    if error:
        return error

    with get_connection() as conn:
        cursor = conn.cursor()
        routine = _get_owned_routine(cursor, user_id, routine_id)
        if routine is None:
            return _json_error("Routine not found.", 404)

        cursor.execute("DELETE FROM Routines WHERE RoutineId = ?", routine_id)
        conn.commit()

    return jsonify({"message": "Routine deleted."})


@api_bp.route("/routines/<int:routine_id>/exercises", methods=["GET"])
def list_exercises(routine_id):
    """
    List exercises in one routine.
    """
    user_id, error = _require_api_user()
    if error:
        return error

    with get_connection() as conn:
        cursor = conn.cursor()
        if _get_owned_routine(cursor, user_id, routine_id) is None:
            return _json_error("Routine not found.", 404)

        cursor.execute(
            """
            SELECT ExerciseId AS id, Name AS name, Sets AS sets
            FROM Exercises
            WHERE RoutineId = ?
            ORDER BY ExerciseId
            """,
            routine_id,
        )
        exercises = rows_to_dicts(cursor)

    return jsonify({"exercises": exercises})


@api_bp.route("/routines/<int:routine_id>/exercises", methods=["POST"])
def create_exercise(routine_id):
    """
    Create an exercise in one routine.
    """
    user_id, error = _require_api_user()
    if error:
        return error

    data = _payload()
    name = _clean_text(data.get("name"))
    sets = _positive_int(data.get("sets"))
    if not name:
        return _json_error("Exercise name is required.", 400)
    if sets is None:
        return _json_error("Sets must be a positive integer.", 400)

    with get_connection() as conn:
        cursor = conn.cursor()
        if _get_owned_routine(cursor, user_id, routine_id) is None:
            return _json_error("Routine not found.", 404)

        cursor.execute(
            "SELECT 1 FROM Exercises WHERE RoutineId = ? AND Name = ?",
            routine_id,
            name,
        )
        if cursor.fetchone():
            return _json_error("Exercise already exists.", 409)

        cursor.execute(
            "INSERT INTO Exercises (RoutineId, Name, Sets) VALUES (?, ?, ?)",
            routine_id,
            name,
            sets,
        )
        cursor.execute(
            """
            SELECT TOP 1 ExerciseId AS id, Name AS name, Sets AS sets
            FROM Exercises
            WHERE RoutineId = ? AND Name = ?
            ORDER BY ExerciseId DESC
            """,
            routine_id,
            name,
        )
        exercise = row_to_dict(cursor, cursor.fetchone())
        conn.commit()

    return jsonify({"exercise": exercise}), 201


@api_bp.route("/exercises/<int:exercise_id>", methods=["PUT"])
def update_exercise(exercise_id):
    """
    Update one exercise.
    """
    user_id, error = _require_api_user()
    if error:
        return error

    data = _payload()
    name = _clean_text(data.get("name"))
    sets = _positive_int(data.get("sets"))
    if not name:
        return _json_error("Exercise name is required.", 400)
    if sets is None:
        return _json_error("Sets must be a positive integer.", 400)

    with get_connection() as conn:
        cursor = conn.cursor()
        exercise = _get_owned_exercise(cursor, user_id, exercise_id)
        if exercise is None:
            return _json_error("Exercise not found.", 404)

        cursor.execute(
            """
            SELECT 1 FROM Exercises
            WHERE RoutineId = ? AND Name = ? AND ExerciseId <> ?
            """,
            exercise["routineId"],
            name,
            exercise_id,
        )
        if cursor.fetchone():
            return _json_error("Exercise already exists.", 409)

        cursor.execute(
            "UPDATE Exercises SET Name = ?, Sets = ? WHERE ExerciseId = ?",
            name,
            sets,
            exercise_id,
        )
        conn.commit()

    return jsonify(
        {
            "exercise": {
                "id": exercise_id,
                "routineId": exercise["routineId"],
                "name": name,
                "sets": sets,
            }
        }
    )


@api_bp.route("/exercises/<int:exercise_id>", methods=["DELETE"])
def delete_exercise(exercise_id):
    """
    Delete one exercise.
    """
    user_id, error = _require_api_user()
    if error:
        return error

    with get_connection() as conn:
        cursor = conn.cursor()
        if _get_owned_exercise(cursor, user_id, exercise_id) is None:
            return _json_error("Exercise not found.", 404)

        cursor.execute("DELETE FROM Exercises WHERE ExerciseId = ?", exercise_id)
        conn.commit()

    return jsonify({"message": "Exercise deleted."})


@api_bp.route("/workout-days", methods=["GET"])
def get_workout_days():
    """
    Return selected workout days.
    """
    user_id, error = _require_api_user()
    if error:
        return error

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DayName AS day
            FROM WorkoutDays
            WHERE UserId = ?
            ORDER BY DayName
            """,
            user_id,
        )
        days = [row["day"] for row in rows_to_dicts(cursor)]

    return jsonify({"workoutDays": days})


@api_bp.route("/workout-days", methods=["PUT"])
def update_workout_days():
    """
    Replace selected workout days.
    """
    user_id, error = _require_api_user()
    if error:
        return error

    days = _payload().get("days", [])
    if not isinstance(days, list):
        return _json_error("Days must be a list.", 400)

    normalized_days = {_clean_text(day).upper() for day in days}
    if not normalized_days.issubset(VALID_DAYS):
        return _json_error("One or more workout days are invalid.", 400)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM WorkoutDays WHERE UserId = ?", user_id)
        for day_name in sorted(normalized_days):
            cursor.execute(
                "INSERT INTO WorkoutDays (UserId, DayName) VALUES (?, ?)",
                user_id,
                day_name,
            )
        conn.commit()

    return jsonify({"workoutDays": sorted(normalized_days)})


@api_bp.route("/workout-logs", methods=["GET"])
def list_workout_logs():
    """
    Return workout log summaries.
    """
    user_id, error = _require_api_user()
    if error:
        return error

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                wl.WorkoutLogId AS id,
                wl.RoutineId AS routineId,
                r.Name AS routineName,
                wl.PerformedOn AS performedOn,
                COUNT(wls.WorkoutLogSetId) AS setCount
            FROM WorkoutLogs wl
            INNER JOIN Routines r ON r.RoutineId = wl.RoutineId
            LEFT JOIN WorkoutLogSets wls
                ON wls.WorkoutLogId = wl.WorkoutLogId
            WHERE wl.UserId = ?
            GROUP BY wl.WorkoutLogId, wl.RoutineId, r.Name, wl.PerformedOn
            ORDER BY wl.PerformedOn DESC, wl.WorkoutLogId DESC
            """,
            user_id,
        )
        logs = rows_to_dicts(cursor)

    return jsonify({"workoutLogs": logs})


@api_bp.route("/workout-logs", methods=["POST"])
def create_workout_log():
    """
    Create a workout log with set weights.

    Expected JSON:
        {
            "routineId": 1,
            "performedOn": "2026-05-13",
            "sets": [
                {"exerciseId": 1, "setNumber": 1, "weight": 100}
            ]
        }
    """
    user_id, error = _require_api_user()
    if error:
        return error

    data = _payload()
    routine_id = _positive_int(data.get("routineId"))
    if routine_id is None:
        return _json_error("routineId is required.", 400)

    performed_on = _clean_text(data.get("performedOn")) or date.today().isoformat()
    try:
        date.fromisoformat(performed_on)
    except ValueError:
        return _json_error("performedOn must be YYYY-MM-DD.", 400)

    sets = data.get("sets", [])
    if not isinstance(sets, list) or not sets:
        return _json_error("sets must be a non-empty list.", 400)

    with get_connection() as conn:
        cursor = conn.cursor()
        if _get_owned_routine(cursor, user_id, routine_id) is None:
            return _json_error("Routine not found.", 404)

        cleaned_sets = []
        for item in sets:
            exercise_id = _positive_int(item.get("exerciseId"))
            set_number = _positive_int(item.get("setNumber"))
            weight = _non_negative_decimal(item.get("weight"))
            if exercise_id is None or set_number is None or weight is None:
                return _json_error("Each set needs exerciseId, setNumber, and weight.", 400)

            exercise = _get_owned_exercise(cursor, user_id, exercise_id)
            if exercise is None or exercise["routineId"] != routine_id:
                return _json_error("Exercise does not belong to this routine.", 400)

            cleaned_sets.append((exercise_id, set_number, weight))

        cursor.execute(
            """
            INSERT INTO WorkoutLogs (UserId, RoutineId, PerformedOn)
            VALUES (?, ?, ?)
            """,
            user_id,
            routine_id,
            performed_on,
        )
        cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT) AS id")
        workout_log_id = row_to_dict(cursor, cursor.fetchone())["id"]

        for exercise_id, set_number, weight in cleaned_sets:
            cursor.execute(
                """
                INSERT INTO WorkoutLogSets
                    (WorkoutLogId, ExerciseId, SetNumber, Weight)
                VALUES (?, ?, ?, ?)
                """,
                workout_log_id,
                exercise_id,
                set_number,
                weight,
            )

        cursor.execute(
            "UPDATE Users SET XPPoints = XPPoints + 100 WHERE UserId = ?",
            user_id,
        )
        conn.commit()

    return jsonify({"workoutLog": {"id": workout_log_id}}), 201


@api_bp.route("/personal-records", methods=["GET"])
def personal_records():
    """
    Return the highest logged weight for each exercise.
    """
    user_id, error = _require_api_user()
    if error:
        return error

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                e.ExerciseId AS exerciseId,
                e.Name AS exerciseName,
                MAX(wls.Weight) AS maxWeight
            FROM Exercises e
            INNER JOIN Routines r ON r.RoutineId = e.RoutineId
            INNER JOIN WorkoutLogSets wls ON wls.ExerciseId = e.ExerciseId
            WHERE r.UserId = ?
            GROUP BY e.ExerciseId, e.Name
            ORDER BY maxWeight DESC
            """,
            user_id,
        )
        records = rows_to_dicts(cursor)

    return jsonify({"personalRecords": records})
