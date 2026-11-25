# HelpDesk MVP

A complete helpdesk web application built with **Python (Flask)**, **SQLite** and **Bootstrap 5**, fully containerized with Docker.

## Features

- User registration (`/register`) and login (`/login`) with session management and hashed passwords (Werkzeug).
- Two roles: `client` (default, created via registration) and `support` (admin, created via CLI command or via the support signup key on `/register`).
- Client dashboard (`/dashboard`) listing your own tickets with a "Create New Ticket" button.
- Ticket creation (`/ticket/new`) with title, description, priority (Low / Medium / High) and an optional attachment (PDF / PNG / JPG, max 5 MB) saved to `uploads/`.
- Ticket detail page (`/ticket/<id>`) with attachment link and a comments/replies section.
- Ticket search (`/search?q=...`) by title or description (clients search their own tickets, support searches all).
- Support/admin panel (`/admin`) with an overview of all tickets, inline status changes (Open / In Progress / Closed), ticket assignment to support users, and a mandatory resolution note when closing a ticket (stored as a comment).
- Clients see status and assignee on their dashboard and ticket pages, and can reopen a closed ticket with an explanatory comment.

## Run with Docker (single command)

```bash
docker-compose up --build
```

Then open <http://localhost:5000>.

Uploaded files and the SQLite database are persisted in the named volumes `uploads_data` and `db_data`.

### Create a support (admin) account

Via the CLI (prompts for a password):

```bash
docker compose exec web flask create-support admin admin@example.com
```

Or self-service: set `SUPPORT_SIGNUP_KEY` (e.g. in a `.env` file next to `docker-compose.yml` or as an environment variable) and share it with support staff. Anyone who enters that key in the optional "Support signup key" field on `/register` gets a `support` account. If the variable is unset, the field has no effect and everyone registers as a client.

## Run locally without Docker

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app create-support admin admin@example.com   # optional: support account
python app.py                                            # serves on http://localhost:5000
```

## Project structure

```
app.py                  # entrypoint (python app.py / gunicorn app:app)
helpdesk/
  __init__.py           # app factory, config, CLI commands
  db.py                 # SQLite connection + schema
  models.py             # data-access layer (users, tickets, comments)
  auth.py               # /register, /login, /logout + role decorators
  tickets.py            # dashboard, ticket CRUD views, search, uploads
  admin.py              # /admin panel and status management
templates/              # Bootstrap 5 Jinja2 templates
uploads/                # uploaded attachments (runtime)
data/                   # SQLite database (runtime)
Dockerfile
docker-compose.yml
requirements.txt
```

## Configuration (environment variables)

| Variable         | Default                              | Purpose                     |
|------------------|--------------------------------------|-----------------------------|
| `SECRET_KEY`     | dev placeholder                      | Flask session signing key   |
| `SUPPORT_SIGNUP_KEY` | unset                             | Key that turns /register into a support account |
| `DATABASE_PATH`  | `data/helpdesk.db`                   | SQLite database file        |
| `UPLOAD_FOLDER`  | `uploads/`                           | Attachment storage folder   |

Set `SECRET_KEY` to a strong random value outside local development.
