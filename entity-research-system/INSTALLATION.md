# Installation Guide

This guide provides instructions for setting up the Entity Research & Risk Assessment System on your local machine or server.

## Prerequisites

- Python 3.10 or higher
- pip (Python package installer)
- PostgreSQL (optional, SQLite is used by default)
- OpenAI API key

## Local Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/entity-research-system.git
cd entity-research-system
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate the virtual environment:

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the root directory with the following variables:

```
OPENAI_API_KEY=your_openai_api_key
SESSION_SECRET=your_session_secret
DATABASE_URL=sqlite:///instance/entity_research.db
```

For PostgreSQL, use a connection string like:
```
DATABASE_URL=postgresql://username:password@localhost:5432/entity_research
```

### 5. Initialize the Database

```bash
python -c "from app import db; db.create_all()"
```

### 6. Run the Application

```bash
python main.py
```

The application will be available at [http://localhost:5000](http://localhost:5000).

## Docker Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/entity-research-system.git
cd entity-research-system
```

### 2. Set Up Environment Variables

Create a `.env` file in the root directory with:

```
OPENAI_API_KEY=your_openai_api_key
```

### 3. Build and Run with Docker Compose

```bash
docker-compose up -d
```

The application will be available at [http://localhost:5000](http://localhost:5000).

## Deploying to Production

### Option 1: Heroku

1. Create a Heroku account and install the Heroku CLI
2. Login to Heroku: `heroku login`
3. Create a new app: `heroku create your-app-name`
4. Add a PostgreSQL database: `heroku addons:create heroku-postgresql:hobby-dev`
5. Set environment variables:
   ```bash
   heroku config:set OPENAI_API_KEY=your_openai_api_key
   heroku config:set SESSION_SECRET=your_session_secret
   ```
6. Deploy to Heroku: `git push heroku main`

### Option 2: Google App Engine

1. Create a Google Cloud account and install the Google Cloud SDK
2. Initialize your project: `gcloud init`
3. Deploy to App Engine: `gcloud app deploy app.yaml`

## Troubleshooting

### Database Connection Issues

- Ensure your PostgreSQL server is running
- Verify the connection string in DATABASE_URL
- Check database user permissions

### OpenAI API Issues

- Verify your API key is valid
- Check your OpenAI account has sufficient credits
- Ensure proper network connectivity

### Application Startup Issues

- Check for error messages in the console
- Verify all dependencies were installed correctly
- Ensure environment variables are set properly

## Updating

To update to the latest version:

```bash
git pull
pip install -r requirements.txt
```

If database schema changes are included, you may need to run migrations or recreate the database.

## Support

If you encounter issues not addressed in this guide, please open an issue on the GitHub repository.