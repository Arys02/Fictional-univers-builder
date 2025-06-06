# Fictional Universe Builder

## Overview
The Fictional Universe Builder is a Flask application that leverages Large Language Models to create rich, detailed fictional universes for role-playing games. It uses Ollama to run LLMs locally, and stores generated content in a SQLite database, allowing users to build and explore their created universes through a web interface.

## Project Structure
```
fictional-universe-builder
├── app
│   ├── app.py                  # Main Flask application
│   ├── llm_call.py             # LLM interaction module
│   ├── templates               # Flask templates directory
│   │   ├── prompt.html         # Template for the main prompt page
│   │   ├── wiki_home.html      # Template for the wiki home page
│   │   └── wiki_table.html     # Template for displaying data in a table
|   |   |__ base.html           # Template for main aspect
│   └── static                  # Static files (CSS, JS, etc.)
├── Dockerfile                   # Dockerfile for building the application image
├── docker-compose.yml           # Docker Compose configuration
├── requirements.txt             # Python dependencies
├── .dockerignore                # Files to ignore when building the Docker image
└── README.md                    # Project documentation
```


## Prerequisites
- Docker and Docker Compose
- 4+ GB of RAM for running the LLM
- GPU acceleration (optional but recommended for better performance)

## Installation and Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd fictional-universe-builder
```

### 2. Check for Port Conflicts
Ensure ports 5000 and 11434 are not already in use:
```bash
# Windows
netstat -ano | findstr 11434
netstat -ano | findstr 5000

# Linux/macOS
lsof -i :11434
lsof -i :5000
```
If Ollama is already running locally, stop it before proceeding:

```bash
# Windows (using the PID from netstat)
taskkill /PID <PID> /F

# Linux/macOS
pkill ollama
```

### 3. Build and Start the Docker Containers
```bash
docker-compose up --build
```

### 4. Initialize the Database
In a new terminal, while the Docker containers are running:
```bash
docker-compose exec web python init_db.py
```

### 5. Download the LLM Model
In a new terminal, while the Docker containers are running:
``` bash
docker exec -it poc-dockerized-ollama-1 ollama pull llama3.2
```

This will download the Llama 3.2 model (approximately 4-5 GB). The download may take 5-20 minutes depending on your internet connection.

### 6. Access the Application
Once everything is set up, access the application at:
```bash
http://localhost:5000
```
## Usage
### Generate a New Universe
- Navigate to the main page at http://localhost:5000
- Enter a prompt describing the universe you want to create (e.g., "Create a cyberpunk universe with magic elements")
- Click "Submit" and wait for the LLM to generate your universe
- Once generation is complete, click "Parse and Save" to store it in the database

### Browse Generated Content
- Click on "Wiki Browser" in the navigation
- View and explore all your created universes and their components

