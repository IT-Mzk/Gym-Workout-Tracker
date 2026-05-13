"""
SQL Server connection helpers for the REST API.
"""
import os


def get_connection():
    """
    Create a SQL Server connection using environment variables.

    Preferred:
        SQLSERVER_CONNECTION_STRING

    Or individual values:
        SQLSERVER_SERVER, SQLSERVER_DATABASE, SQLSERVER_USERNAME,
        SQLSERVER_PASSWORD, SQLSERVER_DRIVER
    """
    try:
        import pyodbc
    except ImportError as exc:
        raise RuntimeError(
            "pyodbc is not installed. Run: pip install -r requirements.txt"
        ) from exc

    connection_string = os.getenv("SQLSERVER_CONNECTION_STRING")
    if connection_string:
        return pyodbc.connect(connection_string)

    server = os.getenv("SQLSERVER_SERVER", "localhost")
    database = os.getenv("SQLSERVER_DATABASE", "GymWorkoutTracker")
    driver = os.getenv("SQLSERVER_DRIVER", "ODBC Driver 18 for SQL Server")
    username = os.getenv("SQLSERVER_USERNAME")
    password = os.getenv("SQLSERVER_PASSWORD")

    parts = [
        f"DRIVER={{{driver}}}",
        f"SERVER={server}",
        f"DATABASE={database}",
        "TrustServerCertificate=yes",
    ]

    if username and password:
        parts.extend([f"UID={username}", f"PWD={password}"])
    else:
        parts.append("Trusted_Connection=yes")

    return pyodbc.connect(";".join(parts))


def row_to_dict(cursor, row):
    """
    Convert one pyodbc row into a dictionary.
    """
    if row is None:
        return None

    columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row))


def rows_to_dicts(cursor):
    """
    Convert all rows from a cursor into dictionaries.
    """
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]
