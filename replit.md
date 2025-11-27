# Rivo - Django REST API Project

## Overview

Django REST API for mortgage lead management with chat history, client tracking, and role-based dashboard.

## Project Structure

```
rivo/
├── account/          # User, Role models + login API
├── chat/             # Chat history API
├── client/           # Client CRUD API + stage/assignment logic
├── dashboard/        # Web UI for client management
├── rivo/             # Django settings
├── manage.py
└── requirements.txt
```

## Tech Stack

- Python 3.11, Django 4.2, Django REST Framework
- PostgreSQL (Supabase)
- OpenAI API (Replit AI Integrations)

## API Endpoints

### Auth
- `POST /api/v1/account/login/` - Get token

### Chat
- `POST /api/v1/chat/stream/` - Send message
- `GET /api/v1/chat/history/?session_id=<uuid>` - Get history

### Clients (Token Auth)
- `GET /api/v1/clients/` - List clients
- `POST /api/v1/clients/` - Create client
- `GET /api/v1/clients/<id>/` - Get client
- `PUT /api/v1/clients/<id>/` - Update client (name, email, phone, stage, assign_to)
- `DELETE /api/v1/clients/<id>/` - Delete client

### Dashboard (Session Auth)
- `/dashboard/login/` - Login
- `/dashboard/` - Client list
- `/dashboard/client/<id>/` - Client detail

## Permissions

Uses Django's built-in permissions only:
- `client.view_client` - Can view clients
- `client.change_client` - Can edit, assign, change stage

Assign via Django Admin > Roles > Permissions.

## Client Model Methods

All client workflow logic in one place:
```python
client.set_stage('contacted', changed_by=user)  # Changes stage + creates history
client.assign(assigned_to=csm, assigned_by=user)  # Assigns + deactivates previous
client.initialize(context=ai_summary)  # New client: set stage + create assignment
```

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection (required)
- `SECRET_KEY` - Django secret (required for production)
- `DEBUG` - 'True' or 'False'

## Deployment

```bash
gunicorn --bind=0.0.0.0:5000 --reuse-port rivo.wsgi:application
```
