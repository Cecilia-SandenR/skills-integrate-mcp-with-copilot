# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Teachers can register and unregister students after logging in
- Students can view activities and participant lists without logging in

## Teacher Accounts

Create or update a teacher account from the repository root:

```
python src/manage_teachers.py teacher-username
```

The command prompts for a password (at least 12 characters) and stores a salted PBKDF2 hash in `src/teachers.json`. That file is ignored by Git; `src/teachers.example.json` shows its format. Teacher sessions expire after eight hours. Set `COOKIE_SECURE=true` when serving the app over HTTPS.

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/auth/login`                                                      | Start a teacher session                                             |
| GET    | `/auth/session`                                                    | Get the current teacher session                                     |
| POST   | `/auth/logout`                                                     | End the current teacher session                                     |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Register a student (teacher session required)                       |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister a student (teacher session required)                  |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
