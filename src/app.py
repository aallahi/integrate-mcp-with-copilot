"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from contextlib import closing
import os
from pathlib import Path
import secrets
import sqlite3

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

DEFAULT_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}

DATABASE_PATH = Path(
    os.getenv("ACTIVITY_DB_PATH", current_dir / "data" / "activities.db")
)

staff_bearer = HTTPBearer(auto_error=False)


def require_staff(
    credentials: HTTPAuthorizationCredentials | None = Depends(staff_bearer),
):
    token = os.getenv("STAFF_API_TOKEN")
    if not token:
        raise HTTPException(status_code=503, detail="Staff access is not configured")
    if credentials is None or not secrets.compare_digest(
        credentials.credentials.encode(), token.encode()
    ):
        raise HTTPException(
            status_code=401, detail="Staff authorization required",
            headers={"WWW-Authenticate": "Bearer"},
        )


class VolunteerProfile(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True, str_max_length=4000, extra="forbid"
    )

    name: str = Field(min_length=1, max_length=200)
    email: str = ""
    phone: str = ""
    availability: str = ""
    age_group: str = ""
    program_cycle: str = ""
    interests: str = ""
    talents: str = ""
    notes: str = ""
    photo_consent: bool = False
    newsletter_consent: bool = False


def volunteer_record(row):
    record = dict(row)
    for field in ("photo_consent", "newsletter_consent"):
        record[field] = bool(record[field])
    return record


def get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    with closing(get_connection()) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS activities (
                name TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                schedule TEXT NOT NULL,
                max_participants INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS registrations (
                activity_name TEXT NOT NULL,
                email TEXT NOT NULL,
                PRIMARY KEY (activity_name, email),
                FOREIGN KEY (activity_name) REFERENCES activities(name)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS volunteers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                availability TEXT NOT NULL,
                age_group TEXT NOT NULL,
                program_cycle TEXT NOT NULL,
                interests TEXT NOT NULL,
                talents TEXT NOT NULL,
                notes TEXT NOT NULL,
                photo_consent INTEGER NOT NULL DEFAULT 0,
                newsletter_consent INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS volunteer_assignments (
                activity_name TEXT NOT NULL,
                volunteer_id INTEGER NOT NULL,
                PRIMARY KEY (activity_name, volunteer_id),
                FOREIGN KEY (activity_name) REFERENCES activities(name)
                    ON DELETE CASCADE,
                FOREIGN KEY (volunteer_id) REFERENCES volunteers(id)
                    ON DELETE CASCADE
            );
            """
        )

        activity_count = connection.execute(
            "SELECT COUNT(*) FROM activities"
        ).fetchone()[0]
        if activity_count == 0:
            connection.executemany(
                """
                INSERT INTO activities (name, description, schedule, max_participants)
                VALUES (:name, :description, :schedule, :max_participants)
                """,
                [
                    {
                        "name": name,
                        "description": details["description"],
                        "schedule": details["schedule"],
                        "max_participants": details["max_participants"],
                    }
                    for name, details in DEFAULT_ACTIVITIES.items()
                ],
            )
            connection.executemany(
                """
                INSERT INTO registrations (activity_name, email)
                VALUES (?, ?)
                """,
                [
                    (name, email)
                    for name, details in DEFAULT_ACTIVITIES.items()
                    for email in details["participants"]
                ],
            )
        connection.commit()


def load_activities():
    with closing(get_connection()) as connection:
        activity_rows = connection.execute(
            "SELECT name, description, schedule, max_participants "
            "FROM activities ORDER BY name"
        ).fetchall()
        participant_rows = connection.execute(
            "SELECT activity_name, email FROM registrations ORDER BY email"
        ).fetchall()
        volunteer_rows = connection.execute(
            "SELECT a.activity_name, v.id, v.name FROM volunteer_assignments a "
            "JOIN volunteers v ON v.id = a.volunteer_id ORDER BY v.name, v.id"
        ).fetchall()

    volunteers_by_activity = {}
    for row in volunteer_rows:
        volunteers_by_activity.setdefault(row["activity_name"], []).append(
            {"id": row["id"], "name": row["name"]}
        )
    participants_by_activity = {}
    for row in participant_rows:
        participants_by_activity.setdefault(row["activity_name"], []).append(
            row["email"]
        )

    return {
        row["name"]: {
            "description": row["description"],
            "schedule": row["schedule"],
            "max_participants": row["max_participants"],
            "participants": participants_by_activity.get(row["name"], []),
            "volunteers": volunteers_by_activity.get(row["name"], []),
        }
        for row in activity_rows
    }


initialize_database()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return load_activities()


@app.get("/volunteers", dependencies=[Depends(require_staff)])
def get_volunteers():
    with closing(get_connection()) as connection:
        return [
            volunteer_record(row) for row in connection.execute(
                "SELECT * FROM volunteers ORDER BY name, id"
            )
        ]


@app.post("/volunteers", status_code=201, dependencies=[Depends(require_staff)])
def create_volunteer(profile: VolunteerProfile):
    values = profile.model_dump()
    columns = ", ".join(values)
    placeholders = ", ".join("?" for _ in values)
    with closing(get_connection()) as connection:
        result = connection.execute(
            f"INSERT INTO volunteers ({columns}) VALUES ({placeholders})",
            tuple(values.values()),
        )
        row = connection.execute(
            "SELECT * FROM volunteers WHERE id = ?", (result.lastrowid,)
        ).fetchone()
        connection.commit()
    return volunteer_record(row)


@app.put("/volunteers/{volunteer_id}", dependencies=[Depends(require_staff)])
def update_volunteer(volunteer_id: int, profile: VolunteerProfile):
    values = profile.model_dump()
    fields = ", ".join(f"{field} = ?" for field in values)
    with closing(get_connection()) as connection:
        result = connection.execute(
            f"UPDATE volunteers SET {fields} WHERE id = ?",
            (*values.values(), volunteer_id),
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Volunteer not found")
        row = connection.execute(
            "SELECT * FROM volunteers WHERE id = ?", (volunteer_id,)
        ).fetchone()
        connection.commit()
    return volunteer_record(row)


@app.put(
    "/activities/{activity_name}/volunteers/{volunteer_id}",
    dependencies=[Depends(require_staff)],
)
def assign_volunteer(activity_name: str, volunteer_id: int):
    with closing(get_connection()) as connection:
        if connection.execute(
            "SELECT 1 FROM activities WHERE name = ?", (activity_name,)
        ).fetchone() is None:
            raise HTTPException(status_code=404, detail="Activity not found")
        if connection.execute(
            "SELECT 1 FROM volunteers WHERE id = ?", (volunteer_id,)
        ).fetchone() is None:
            raise HTTPException(status_code=404, detail="Volunteer not found")
        connection.execute(
            "INSERT OR IGNORE INTO volunteer_assignments "
            "(activity_name, volunteer_id) VALUES (?, ?)",
            (activity_name, volunteer_id),
        )
        connection.commit()
    return {"message": f"Volunteer assigned to {activity_name}"}


@app.delete(
    "/activities/{activity_name}/volunteers/{volunteer_id}",
    dependencies=[Depends(require_staff)],
)
def unassign_volunteer(activity_name: str, volunteer_id: int):
    with closing(get_connection()) as connection:
        result = connection.execute(
            "DELETE FROM volunteer_assignments "
            "WHERE activity_name = ? AND volunteer_id = ?",
            (activity_name, volunteer_id),
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Volunteer assignment not found")
        connection.commit()
    return {"message": f"Volunteer removed from {activity_name}"}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    with closing(get_connection()) as connection:
        activity = connection.execute(
            "SELECT max_participants FROM activities WHERE name = ?",
            (activity_name,),
        ).fetchone()
        if activity is None:
            raise HTTPException(status_code=404, detail="Activity not found")

        participant_count = connection.execute(
            "SELECT COUNT(*) FROM registrations WHERE activity_name = ?",
            (activity_name,),
        ).fetchone()[0]
        if participant_count >= activity["max_participants"]:
            raise HTTPException(status_code=400, detail="Activity is full")

        try:
            connection.execute(
                "INSERT INTO registrations (activity_name, email) VALUES (?, ?)",
                (activity_name, email),
            )
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=400,
                detail="Student is already signed up",
            )
        connection.commit()

    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    with closing(get_connection()) as connection:
        activity_exists = connection.execute(
            "SELECT 1 FROM activities WHERE name = ?", (activity_name,)
        ).fetchone()
        if activity_exists is None:
            raise HTTPException(status_code=404, detail="Activity not found")

        result = connection.execute(
            "DELETE FROM registrations WHERE activity_name = ? AND email = ?",
            (activity_name, email),
        )
        if result.rowcount == 0:
            raise HTTPException(
                status_code=400,
                detail="Student is not signed up for this activity",
            )
        connection.commit()

    return {"message": f"Unregistered {email} from {activity_name}"}
