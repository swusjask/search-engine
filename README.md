# Information Retrieval Search Engine

A search engine implementation using PyTerrier for information retrieval and Django for the web interface. This project demonstrates learning-to-rank techniques with a user-friendly search interface.

## Features

- Full-text search using PyTerrier
- Learning-to-rank implementation for better search results
- Document viewing functionality
- Docker support for easy deployment

## Prerequisites

- Python 3.9
- Docker and Docker Compose
- Git

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/search-engine-ir.git
cd search-engine-ir
```

2. Build and run with Docker:
```bash
docker-compose up --build
```

The application will be available at http://localhost:8000

## Development

To run the project in development mode:

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the development server:
```bash
python manage.py runserver
```