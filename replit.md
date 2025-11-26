# Rivo - Django REST API Project

## Overview

Rivo is a Django application with database models for chat conversations, user accounts, and client/lead management.

**Currently Implemented:**
- **Chat REST API** - Full CRUD endpoints for chatbot conversation history
- **User/Role Management** - Django Admin interface only (no REST API)
- **Client/Lead Models** - Database schema only (no REST API or admin interface)

Built with Django 4.2.26 and Django REST Framework.

## Project Structure

```
rivo/
├── account/          # User authentication and role management
├── chat/             # Chat history API
├── client/           # Client/lead management
├── rivo/             # Django project settings
├── manage.py         # Django management script
└── requirements.txt  # Python dependencies
```

## Technology Stack

- Python 3.11
- Django 4.2.26
- Django REST Framework 3.14.0
- PostgreSQL database (Supabase)
- Gunicorn (production deployment)

## API Endpoints

### Chat API (Implemented)
- `POST /api/v1/chat/stream/` - Send a message to chat
  - Request: `{"session_id": "uuid", "message": "text", "sender_type": "client|bot"}`
  - Response: Created chat message
  
- `GET /api/v1/chat/history/?session_id=<uuid>` - Get chat history for a session
  - Response: `{"session_id": "uuid", "messages": [...]}`

### Admin Interface
- `/admin/` - Django admin interface
  - User and Role management
  - Chat History management
  - Client management (Clients, Context, Stage History, Assignments)

## Database Models

### Account App
- **User**: Custom user model with email authentication and role support (accessible via Django Admin)
- **Role**: Role-based permission system (accessible via Django Admin)

### Chat App  
- **ChatHistory**: Store chat messages by session (API endpoints available)

### Client App (Models only - no API endpoints yet)
- **Client**: Lead/client information with stage tracking
- **ClientContext**: Additional context data stored as JSON
- **ClientStageHistory**: Track stage transitions
- **ClientAssignment**: Manage client assignments to customer support users

Note: The client models exist in the database but do not have REST API endpoints or admin interface configured yet.

## Development Setup

The project is configured to run on Replit with:
- Django development server on port 5000
- ALLOWED_HOSTS set to accept all hosts (required for Replit proxy)
- CSRF trusted origins configured for Replit domains (HTTP and HTTPS)
- PostgreSQL database (Supabase connection pooler)
- X_FRAME_OPTIONS set to SAMEORIGIN for security

## Environment Variables

The application supports the following environment variables:

- `SECRET_KEY` - Django secret key (required for production)
  - Development fallback: Uses a default insecure key
  - Production: Generate a secure random key and set this variable
  
- `DEBUG` - Enable/disable debug mode (default: 'True')
  - Development: 'True'
  - Production: Set to 'False' for security

- `ALLOWED_HOSTS` - Comma-separated list of allowed hostnames (optional)
  - Development fallback: Accepts all hosts ('*')
  - Production: Set to your deployment domain(s), e.g., 'yourdomain.replit.app,yourdomain.com'

- `DATABASE_URL` - PostgreSQL connection string (required)
  - Currently connected to Supabase PostgreSQL via connection pooler

## Security Notes

**IMPORTANT**: Before deployment, you must:
- Generate a secure SECRET_KEY and set it as an environment variable
- Set DEBUG='False' in production environment
- Set ALLOWED_HOSTS to your specific domain(s) in production
- The default SECRET_KEY in settings.py is for development only
- Do NOT use the default SECRET_KEY in production
- Never commit production secrets to the repository

## Deployment

The project is configured for deployment using:
- Gunicorn WSGI server
- Autoscale deployment target (configured in deployment settings)
- **Required environment variables for production:**
  - `SECRET_KEY` - A secure random string (e.g., generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
  - `DEBUG` - Set to 'False'
  - `ALLOWED_HOSTS` - Your deployment domain(s), comma-separated (e.g., 'yourdomain.replit.app')
- The deployment uses: `gunicorn --bind=0.0.0.0:5000 --reuse-port rivo.wsgi:application`

## Recent Changes

- November 26, 2025: Connected to Supabase PostgreSQL
  - Configured DATABASE_URL with Supabase connection pooler
  - Ran migrations on Supabase database
  - Chat admin already registered

- November 26, 2025: Initial Replit environment setup
  - Configured Django settings for Replit
  - Set up development workflow on port 5000
  - Ran initial database migrations
  - Configured deployment with Gunicorn
