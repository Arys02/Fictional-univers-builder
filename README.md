# Fictional Universe Builder

## Overview
The Fictional Universe Builder is a comprehensive platform for creating rich, detailed fictional universes for role-playing games. It consists of two main components:

1. **Cloud Application** - A Flask web application with RAG (Retrieval-Augmented Generation) capabilities
2. **LLM Core** - A modular framework for training and experimenting with language models

The system uses Ollama to run LLMs locally, stores generated content in a SQLite database, and provides advanced features like semantic search and database querying through natural language.

The app is running on GCP and is available at https://fictional-universe-web-1069829401679.europe-west1.run.app

## Project Structure
```
Fictional-univers-builder/
├── cloud/                          # Web application with RAG capabilities
│   ├── app/
│   │   ├── app.py                  # Main Flask application
│   │   ├── llm_call.py             # LLM interaction module
│   │   ├── rag.py                  # RAG (Retrieval-Augmented Generation) module
│   │   ├── init_db.py              # Database initialization
│   │   ├── drop_tables.py          # Database cleanup utilities
│   │   ├── db_path.py              # Database path configuration
│   │   └── templates/              # Flask templates directory
│   │       ├── base.html           # Base template
│   │       ├── prompt.html         # Main prompt interface
│   │       ├── rag.html            # RAG query interface
│   │       ├── wiki_home.html      # Wiki home page
│   │       ├── wiki_table.html     # Data table display
│   │       └── wiki_universe.html  # Universe detail view
│   ├── Dockerfile                  # Docker configuration
│   ├── docker-compose.yml          # Docker Compose setup
│   ├── requirements.txt            # Python dependencies
│   ├── cloudbuild.yaml             # Google Cloud Build configuration
│   └── docs/                       # Deployment documentation
├── llm_core/                       # LLM training and experimentation framework
│   ├── src/
│   │   ├── models/                 # Model implementations
│   │   │   ├── gpt.py              # GPT model wrapper
│   │   │   └── gpt2.py             # GPT-2 model implementation
│   │   ├── training/               # Training framework
│   │   │   ├── train.py            # Training script
│   │   │   ├── trainer.py          # Training utilities
│   │   │   └── config/             # Training configurations
│   │   ├── tokenizer/              # Tokenizer implementations
│   │   ├── data/                   # Data processing utilities
│   │   ├── utils/                  # Utility functions
│   │   └── notebook/               # Jupyter notebooks for experimentation
│   ├── mlflow_root/                # MLflow experiment tracking
│   ├── data/                       # Training data
│   ├── config.py                   # Configuration management
│   └── requirements.txt            # LLM core dependencies
├── venv/                           # Python virtual environment
├── LICENSE                         # Project license
└── README.md                       # This file
```

## Key Features

### Cloud Application
- **Interactive Universe Creation**: Generate fictional universes through natural language prompts
- **RAG (Retrieval-Augmented Generation)**: Query your universe database using natural language
- **Semantic Search**: Find relevant information across all universe elements
- **Database Management**: Visual interface for exploring and managing generated content
- **Multi-Model Support**: Support for different LLM models including custom implementations

### LLM Core Framework
- **Modular Architecture**: Extensible framework for different model types
- **Training Pipeline**: Complete training infrastructure with MLflow tracking
- **Tokenizer Support**: Multiple tokenizer implementations
- **Experiment Management**: Jupyter notebooks for model experimentation
- **Configuration Management**: Flexible configuration system

## Prerequisites
- Docker and Docker Compose
- 4+ GB of RAM for running the LLM
- GPU acceleration (optional but recommended for better performance)
- Python 3.8+ (for local development)

## Installation and Setup
FOLLOW THESE STEPS TO RUN LOCALLY, SOME CHANGES NEED TO BE DONE TO RUN.

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Fictional-univers-builder
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

### 3. Build and Start the Docker Application
Go to the db_path.py file, uncomment the "return 'cloud/database.db'" and comment "return db_path" because one is used for the cloud deployment and the other for a local run
```bash
cd cloud
docker-compose up --build
```

### 4. Initialize the Database
DO ONLY THIS IF YOU DONT ALREADY HAVE THE database.db FILE
In a new terminal, while the Docker containers are running:
```bash
docker-compose exec web python init_db.py
```

### 5. Download the LLM Model
In a new terminal, while the Docker containers are running:
```bash
docker exec -it cloud-ollama-1 ollama pull llama3.2
docker exec -it cloud-ollama-1 ollama pull gemma2
```

This will download the Llama 3.2 model (approximately 4-5 GB). The download may take 5-20 minutes depending on your internet connection.

### 6. Access the Application
Once everything is set up, access the application at:
```
http://localhost:5000
```

## Usage

### Generate a New Universe
1. Navigate to the main page at http://localhost:5000
2. Enter a prompt describing the universe you want to create (e.g., "Create a cyberpunk universe with magic elements")
3. Click "Submit" and wait for the LLM to generate your universe
4. Once generation is complete, click "Parse and Save" to store it in the database

### Query Your Universe with RAG
1. Click on "RAG Query" in the navigation
2. Select the universe you want to query
3. Ask questions in natural language about your universe
4. The system will search through all universe elements and provide relevant answers

### Browse Generated Content
1. Click on "Wiki Browser" in the navigation
2. View and explore all your created universes and their components
3. Navigate through different tables (factions, locations, cultures, characters, objects)

### LLM Core Development
For working with the LLM training framework:

```bash
cd llm_core
pip install -r requirements.txt

# Start MLflow for experiment tracking
cd mlflow_root
mlflow ui
```

## Advanced Features

### RAG (Retrieval-Augmented Generation)
The RAG system allows you to:
- Query your universe database using natural language
- Get semantic search results across all universe elements
- Generate SQL queries for database updates
- Maintain conversation context for complex queries

### Semantic Search
- Uses sentence transformers for embedding generation
- FAISS index for fast similarity search
- Configurable similarity thresholds
- Caching for improved performance

### Database Management
- Automatic parsing of LLM responses into structured data
- Foreign key relationships between universe elements
- Timestamp tracking for all entries
- Backup and maintenance utilities

## Database Schema

### Core Tables
- **univers**: Main universe information
- **faction**: Factions within universes
- **location**: Locations within universes
- **culture**: Cultures within universes
- **personnages**: Characters within universes
- **objets**: Objects/items within universes
- **prompt_answers**: Conversation history

### Relationships
```
univers (1) ←→ (N) faction
univers (1) ←→ (N) location
univers (1) ←→ (N) culture
univers (1) ←→ (N) personnages
univers (1) ←→ (N) objets
univers (1) ←→ (N) prompt_answers
```

## Development

### Cloud Application Development
```bash
cd cloud
# For local development without Docker
pip install -r requirements.txt
python app/app.py
```

### LLM Core Development
```bash
cd llm_core
pip install -r requirements.txt

# Run training experiments
python src/training/train.py

# Start MLflow UI
cd mlflow_root
mlflow ui
```

### Adding New Models
1. Create a new model implementation in `llm_core/src/models/`
2. Update the training configuration in `llm_core/src/training/config/`
3. Add model-specific requirements to `llm_core/requirements.txt`

## Deployment

### Cloud Deployment
The project includes Google Cloud Build configuration:
```bash
cd cloud
# Deploy to Google Cloud Run
gcloud builds submit --config cloudbuild.yaml
```

### Local Production
```bash
cd cloud
docker-compose -f docker-compose.prod.yml up --build
```

## Troubleshooting

### Common Issues
1. **Port conflicts**: Ensure ports 5000 and 11434 are available
2. **Memory issues**: Increase Docker memory allocation for LLM models
3. **GPU access**: Ensure NVIDIA Docker runtime is installed for GPU acceleration
4. **Database errors**: Run `python drop_tables.py` followed by `python init_db.py` to reset

### Performance Optimization
- Use GPU acceleration when available
- Adjust similarity thresholds in RAG configuration
- Monitor memory usage during large universe generation
- Use caching for frequently accessed data

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License
This project is licensed under the MIT License - see the LICENSE file for details.

