# Entity Research & Risk Assessment System

A Generative AI-powered system for automated entity research, verification, and risk-scoring from transaction data.

<div align="center">
  <img src="generated-icon.png" alt="Entity Research System" width="180" height="180">
</div>

## Overview

This system helps financial investigators, compliance officers, and researchers to automatically identify, verify, and risk-score various entities (corporations, non-profits, shell companies, and financial intermediaries) from complex transaction data. By leveraging generative AI, the system can significantly reduce manual effort while increasing accuracy in compliance-related research tasks.

## Features

- **AI-Powered Analysis**: Utilizes OpenAI's GPT-4o to analyze entities and identify risk factors
- **Entity Extraction**: Automatically extracts entities from transaction data
- **Risk Scoring**: Calculates risk scores based on various factors including transaction patterns, entity type, and external evidence
- **Network Analysis**: Visualizes relationships between entities to identify hidden connections
- **Evidence Collection**: Gathers evidence from multiple sources to support risk assessments
- **Report Generation**: Creates comprehensive reports for high-risk entities
- **Interactive Dashboard**: Provides an intuitive interface for exploring entity data

## Technologies Used

- **Backend**: Python, Flask, SQLAlchemy
- **Frontend**: Bootstrap CSS, JavaScript, D3.js for visualizations
- **Database**: SQLite/PostgreSQL
- **AI**: OpenAI API integration
- **Data Processing**: Pandas for data manipulation

## Screenshots

*Coming soon*

## Getting Started

### Prerequisites

- Python 3.11 or higher
- OpenAI API key
- PostgreSQL (optional, SQLite is used by default)

### Quick Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/entity-research-system.git
cd entity-research-system
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Set up environment variables
```bash
export OPENAI_API_KEY="your-api-key"
export SESSION_SECRET="your-secret-key"
```

4. Run the application
```bash
python main.py
```

For detailed installation instructions, see [INSTALLATION.md](entity-research-system/INSTALLATION.md).

## Usage

### 1. Uploading Transaction Data

- Navigate to the upload page
- Upload transaction data in CSV, Excel, or JSON format
- The system accepts various data structures and will attempt to standardize them

### 2. Entity Analysis

- The system will automatically extract entities from the data
- AI analysis will gather evidence and calculate risk scores
- View entity details including description, evidence, and risk factors

### 3. Network Visualization

- The entity network visualization shows relationships between entities
- Identify clusters and potential suspicious patterns
- Filter by risk score or entity type

### 4. Report Generation

- Generate comprehensive reports for individual entities or the entire dataset
- Reports include risk assessments, evidence summaries, and recommended actions
- Export reports for sharing with stakeholders

## Development

For information on setting up a development environment and contributing to the project, see [GITHUB_SETUP.md](GITHUB_SETUP.md).

## Deployment

The project includes configuration for deploying to:
- Heroku
- Google App Engine
- Docker containers

Run `python deploy.py --package` to create a deployment package with all the necessary files.

## License

MIT License

## Acknowledgments

- OpenAI for providing the AI models
- D3.js for network visualization capabilities
- Bootstrap for UI components
- The open-source community for various libraries and tools