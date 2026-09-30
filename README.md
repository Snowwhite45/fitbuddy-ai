# FitBuddy – AI Fitness Plan Generator

FitBuddy is a FastAPI + Jinja2 + SQLite application based on the supplied SkillWallet project documentation.

## Architecture

- **Frontend:** HTML/CSS + Jinja2
- **Backend:** FastAPI
- **AI:** Google Gemini through the modern `google-genai` SDK
- **Database:** SQLite + SQLAlchemy
- **Validation:** Pydantic
- **Server:** Uvicorn

The supplied documentation describes Gemini 1.5 Pro for workout generation/feedback and Gemini Flash for nutrition tips. The code keeps these roles separate, but makes model names configurable because Gemini model availability changes over time.

## Features

1. User form: name, user ID, age, weight, goal, intensity.
2. AI-generated 7-day workout plan.
3. Warm-up, main workout, sets/reps/duration, cooldown/recovery.
4. Goal-specific nutrition/recovery tip.
5. Feedback-based plan regeneration.
6. SQLite persistence for users and original/updated plans.
7. Admin view of all users and plans.
8. Delete-user action.
9. HTML pages plus JSON API endpoints.
10. `/docs` Swagger UI.

## Project structure

```text
fitbuddy_ai/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── routes.py
│   ├── database.py
│   ├── schemas.py
│   ├── gemini_client.py
│   ├── gemini_generator.py
│   ├── gemini_flash_generator.py
│   └── updated_plan.py
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── result.html
│   └── all_users.html
├── static/
│   ├── styles.css
│   └── app.js
├── tests/
│   └── test_app.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## VS Code setup – Windows

### 1. Open the project

Extract the ZIP and open the `fitbuddy_ai` folder in VS Code.

### 2. Create a virtual environment

PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Command Prompt:

```cmd
py -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Gemini

Copy `.env.example` to `.env`:

```text
GEMINI_API_KEY=your_real_key
```

Google's current Gemini API documentation recommends the `GEMINI_API_KEY` environment variable and the `google-genai` Python package.

If you leave the key empty, FitBuddy runs in **demo/fallback mode** so you can test the UI and database locally. AI calls will use the deterministic fallback rather than Gemini.

### 5. Start the server

```bash
uvicorn app.main:app --reload
```

Open:

- Home: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs
- Admin view: http://127.0.0.1:8000/view-all-users

The supplied SkillWallet material also specifies local FastAPI access and `/docs`.

## Testing

Run:

```bash
pytest -q
```

The tests force demo mode so they do not require an API key.

## Main routes

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Home form |
| POST | `/generate-workout` | Generate and save a plan |
| POST | `/submit-feedback` | Update a plan from feedback |
| GET | `/view-all-users` | Admin list |
| POST | `/delete-user/{user_id}` | Delete a user |
| GET | `/health` | Health check |
| POST | `/api/generate-workout` | JSON generation API |
| POST | `/api/submit-feedback` | JSON feedback API |
| GET | `/api/users` | JSON admin data |
| GET | `/docs` | FastAPI Swagger docs |

## Important fitness safety note

This is a software project, not a medical system. Generated fitness/nutrition content is informational and should not replace advice from a qualified healthcare or fitness professional. The application prompt asks the model to avoid diagnosis, extreme dieting, unsafe exercise, and medical claims.

## GitHub

After testing:

```bash
git init
git add .
git commit -m "Build FitBuddy AI fitness plan generator"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```
