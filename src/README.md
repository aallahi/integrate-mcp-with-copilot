# Mergington High School Activities API

A FastAPI application that allows students to view, join, and leave extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- Unregister from activities
- Persist activities and registrations in SQLite

## Getting Started

1. Install the dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Run the application:

   ```
   uvicorn app:app --reload --app-dir src
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister from an activity                                      |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier for now:
   - Email address

The application stores data in `src/data/activities.db`. The database is created and seeded with the sample activities the first time the application starts. Existing activity and participant data is preserved on subsequent starts.

To use a different database location, set `ACTIVITY_DB_PATH` before starting the server:

```powershell
$env:ACTIVITY_DB_PATH = "C:\path\to\activities.db"
uvicorn app:app --reload --app-dir src
```
