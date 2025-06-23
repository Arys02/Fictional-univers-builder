# Fictional Universe Builder

## Overview
The Fictional Universe Builder is a Flask application that leverages Large Language Models to create rich, detailed fictional universes for role-playing games. It uses Ollama to run LLMs locally, and stores generated content in a SQLite database, allowing users to build and explore their created universes through a web interface.

## Project Structure
```
poc-dockerized
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
├── README.md                    # Project documentation
├── WIKI.md                      # Detailed database documentation
├── generate_db_diagram.py       # Database diagram generator
└── db_stats.py                  # Database statistics and reports
```


## Prerequisites
- Docker and Docker Compose
- 4+ GB of RAM for running the LLM
- GPU acceleration (optional but recommended for better performance)

## Installation and Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd poc-dockerized
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

## Documentation Tools

### Database Documentation
The project includes several tools for documenting and analyzing the database:

#### 1. Generate Database Diagram
Create a visual representation of the database schema:
```bash
docker-compose exec web python generate_db_diagram.py
```
This generates:
- A Mermaid ER diagram
- A flow diagram showing table relationships
- Detailed table documentation
- JSON schema export

#### 2. Database Statistics
Generate comprehensive reports about your database:
```bash
docker-compose exec web python db_stats.py
```
This provides:
- Record counts per table
- Universe details with element counts
- Recent activity logs
- File size information

#### 3. Detailed Wiki Documentation
For complete database documentation, see:
- `WIKI.md` - Comprehensive database schema documentation
- `database_diagram.md` - Auto-generated diagrams (after running generate_db_diagram.py)
- `database_report.md` - Auto-generated statistics (after running db_stats.py)

## Wiki - Database Schema Documentation

### Overview
The application uses a SQLite database to store all generated fictional universe content. The database is designed with a hierarchical structure where each universe contains multiple related entities.

### Database Schema

#### 1. Table: `univers`
The main table that stores the core universe information.

```sql
CREATE TABLE univers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    created_at TIMESTAMP
);
```

**Fields:**
- `id`: Unique identifier for the universe (auto-increment)
- `name`: Name of the fictional universe
- `description`: Detailed description of the universe
- `created_at`: Timestamp when the universe was created

#### 2. Table: `faction`
Stores factions within each universe.

```sql
CREATE TABLE faction (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    univers_id INTEGER,
    created_at TIMESTAMP
);
```

**Fields:**
- `id`: Unique identifier for the faction (auto-increment)
- `name`: Name of the faction
- `description`: Detailed description of the faction
- `univers_id`: Foreign key reference to the parent universe
- `created_at`: Timestamp when the faction was created

#### 3. Table: `location`
Stores locations within each universe.

```sql
CREATE TABLE location (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    univers_id INTEGER,
    created_at TIMESTAMP
);
```

**Fields:**
- `id`: Unique identifier for the location (auto-increment)
- `name`: Name of the location
- `description`: Detailed description of the location
- `univers_id`: Foreign key reference to the parent universe
- `created_at`: Timestamp when the location was created

#### 4. Table: `culture`
Stores cultures within each universe.

```sql
CREATE TABLE culture (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    univers_id INTEGER,
    created_at TIMESTAMP
);
```

**Fields:**
- `id`: Unique identifier for the culture (auto-increment)
- `name`: Name of the culture
- `description`: Detailed description of the culture
- `univers_id`: Foreign key reference to the parent universe
- `created_at`: Timestamp when the culture was created

#### 5. Table: `personnages`
Stores characters within each universe.

```sql
CREATE TABLE personnages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    univers_id INTEGER,
    created_at TIMESTAMP,
    FOREIGN KEY (univers_id) REFERENCES univers (id)
);
```

**Fields:**
- `id`: Unique identifier for the character (auto-increment)
- `name`: Name of the character (required)
- `description`: Detailed description of the character (required)
- `univers_id`: Foreign key reference to the parent universe
- `created_at`: Timestamp when the character was created

#### 6. Table: `objets`
Stores objects/items within each universe.

```sql
CREATE TABLE objets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    univers_id INTEGER,
    created_at TIMESTAMP,
    FOREIGN KEY (univers_id) REFERENCES univers (id)
);
```

**Fields:**
- `id`: Unique identifier for the object (auto-increment)
- `name`: Name of the object (required)
- `description`: Detailed description of the object (required)
- `univers_id`: Foreign key reference to the parent universe
- `created_at`: Timestamp when the object was created

#### 7. Table: `prompt_answers`
Stores the interaction history between users and the LLM.

```sql
CREATE TABLE prompt_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt TEXT NOT NULL,
    response TEXT NOT NULL,
    univers_id INTEGER,
    created_at TIMESTAMP,
    FOREIGN KEY (univers_id) REFERENCES univers (id)
);
```

**Fields:**
- `id`: Unique identifier for the prompt-answer pair (auto-increment)
- `prompt`: The user's original prompt (required)
- `response`: The LLM's response (required)
- `univers_id`: Foreign key reference to the related universe (optional)
- `created_at`: Timestamp when the interaction occurred

### Database Relationships

```
univers (1) ←→ (N) faction
univers (1) ←→ (N) location
univers (1) ←→ (N) culture
univers (1) ←→ (N) personnages
univers (1) ←→ (N) objets
univers (1) ←→ (N) prompt_answers
```

**Key Points:**
- Each universe can have multiple factions, locations, cultures, characters, and objects
- All child entities are linked to their parent universe via the `univers_id` foreign key
- The `prompt_answers` table stores the conversation history and can be optionally linked to a specific universe
- All tables include timestamps for tracking creation dates

### Database Management

#### Initialization
The database is automatically initialized when running:
```bash
docker-compose exec web python init_db.py
```

#### Database Location
The SQLite database file is located at:
```
poc-dockerized/database.db
```

#### Backup and Maintenance
- The database file is included in the Docker volume mounts
- Regular backups are recommended for production use
- The database can be reset by deleting the `database.db` file and re-running the initialization script

### Data Flow
1. User submits a prompt through the web interface
2. The LLM generates content based on the prompt
3. The application parses the LLM response and extracts structured data
4. Data is stored in the appropriate tables with proper foreign key relationships
5. Users can browse and explore the generated content through the Wiki interface

