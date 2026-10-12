# Mergington High School Activities API

A FastAPI application that allows students to view, join, and leave extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- Unregister from activities
- Persist activities and registrations in SQLite
- Create and update staff-only volunteer profiles, including availability and preferences
- Assign volunteers to activities, with volunteer rosters separate from students

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
| GET    | `/volunteers` | List complete volunteer profiles (staff only) |
| POST   | `/volunteers` | Create a volunteer profile (staff only) |
| PUT    | `/volunteers/{volunteer_id}` | Replace a volunteer profile (staff only) |
| PUT    | `/activities/{activity_name}/volunteers/{volunteer_id}` | Assign a volunteer; repeated assignments are harmless (staff only) |
| DELETE | `/activities/{activity_name}/volunteers/{volunteer_id}` | Remove a volunteer assignment (staff only) |

## Volunteer Staffing

Before starting the server, set `STAFF_API_TOKEN` to a securely generated secret
(for example, generate one with `python -c "import secrets; print(secrets.token_urlsafe(32))"`).
Share it only with authorized staff and use HTTPS outside local development.
Do not commit the token. Staff access is disabled if this variable is unset.

In the website's **Volunteer Staffing** panel, enter the token to unlock the tools.
Create a profile or select an existing one to edit it, then select a volunteer and
activity to assign or remove staffing. Lock the tools when finished. The token is
kept only in page memory and is not saved in browser storage.

Staff API requests require an `Authorization` header with the `Bearer` scheme
followed by the configured token. Profile JSON contains a required nonblank `name`
(up to 200 characters) and optional `email`, `phone`, `availability`, `age_group`,
`program_cycle`, `interests`, `talents`, and `notes` text fields (up to 4,000
characters each). Availability accepts days, times, or date ranges as free text.
`photo_consent` and `newsletter_consent` are booleans, defaulting to `false`.
Updates replace the profile, so include all fields you wish to keep.

Volunteer profiles and assignments persist in the same SQLite database. Public
activity rosters expose only volunteer IDs and names; contact details, availability,
notes, and preferences are staff-only. Assignments do not consume student places.
This app currently supports activity-level staffing, not individual dated sessions.

## Tests

From the repository root, run `python -m unittest discover -s tests -v`.

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
