"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
import secrets
import time

if __package__:
    from .auth import verify_teacher_credentials
else:
    from auth import verify_teacher_credentials

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

SESSION_COOKIE_NAME = "teacher_session"
SESSION_DURATION_SECONDS = 8 * 60 * 60
teacher_sessions = {}


class TeacherLogin(BaseModel):
    username: str
    password: str


def get_teacher_session(request: Request):
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    session = teacher_sessions.get(session_id)
    if session is None:
        return None

    if session["expires_at"] <= time.time():
        teacher_sessions.pop(session_id, None)
        return None

    return session["username"]


def require_teacher(request: Request):
    username = get_teacher_session(request)
    if username is None:
        raise HTTPException(status_code=401, detail="Teacher login required")
    return username


@app.post("/auth/login")
def teacher_login(credentials: TeacherLogin, response: Response):
    try:
        is_valid = verify_teacher_credentials(credentials.username, credentials.password)
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Teacher accounts are unavailable") from None

    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    now = time.time()
    for session_id, session in list(teacher_sessions.items()):
        if session["expires_at"] <= now:
            teacher_sessions.pop(session_id, None)

    session_id = secrets.token_urlsafe(32)
    teacher_sessions[session_id] = {
        "username": credentials.username.strip(),
        "expires_at": now + SESSION_DURATION_SECONDS,
    }
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        max_age=SESSION_DURATION_SECONDS,
        httponly=True,
        samesite="lax",
        secure=os.getenv("COOKIE_SECURE", "").lower() in {"1", "true", "yes"},
        path="/",
    )
    return {"username": credentials.username.strip()}


@app.get("/auth/session")
def get_auth_session(request: Request):
    username = get_teacher_session(request)
    if username is None:
        raise HTTPException(status_code=401, detail="Teacher login required")
    return {"username": username}


@app.post("/auth/logout")
def teacher_logout(request: Request, response: Response):
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    teacher_sessions.pop(session_id, None)
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return {"message": "Logged out"}

# In-memory activity database
activities = {
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


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, request: Request, email: str):
    """Sign up a student for an activity"""
    require_teacher(request)

    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, request: Request, email: str):
    """Unregister a student from an activity"""
    require_teacher(request)

    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
