# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

OJ-RAG is a comprehensive document analysis and management application for job offers, CVs, and associated documents. It combines a Python Flask backend with a modern JavaScript frontend, featuring AI integration for document analysis and a modular architecture.

## Quick Start Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv .venv
# Windows activation
.venv\Scripts\activate
# Install dependencies
pip install -r requirements.txt
npm install
```

### Running the Application
```bash
# Main launcher (recommended - handles venv activation)
python launcher.py

# Direct backend launch
python backend/app.py

# Local services (runs on port 5005)
python backend/app_local.py
```

### Testing
```bash
# Run all tests
npm run test:all

# Frontend tests only
npm test
npm run test:watch    # Watch mode
npm run test:coverage # With coverage

# Backend tests only
npm run test:backend
npm run test:backend:coverage

# Use provided scripts
scripts\run_tests.bat
scripts\run_tests_coverage.bat
```

### Development Tools
```bash
# Start HTTP server for frontend development
npm start

# Lint and format (if configured)
# Check specific module tests
python -m pytest tests/backend/test_cy_mistral.py -v
```

## Architecture Overview

### Modular Backend Structure
The application uses a modular architecture based on "cy" modules:

- **cy_routes.py**: Main application routes and core functionality
- **cy_app_config.py**: Centralized configuration management
- **cy_data_layer.py**: Data access and management layer
- **cy_security.py**: Security validation and file handling

### Module Organization (cy1-cy6)
- **cy1**: File exploration and navigation (local file explorer, navigation, filters)
- **cy2**: Image processing and analysis (metadata extraction, analysis, marking)
- **cy3**: AI prompt management and database operations (announcements, AI interactions)
- **cy4**: General analysis (job offer/CV correlation, text extraction, PDF generation)
- **cy5**: Configuration management (columns, filters, personalization)
- **cy6**: Integration and automation (scripts, batch processing, migrations)

### Frontend Architecture
- **Modular JavaScript**: Components organized by functionality (cy_Panel.js, cy_State.js, etc.)
- **State Management**: Centralized state handling via cy_State.js
- **UI Components**: Panels, dialogs, tables with consistent styling

### AI Integration
- **Mistral API**: Document analysis and classification
- **OpenAI API**: Alternative AI processing
- **Automatic Classification**: Uses `.clas` instruction files for document categorization

## Development Workflow

### Configuration Management
- **config.json**: Main application configuration
- **constants.json**: Shared constants (located in backend/config/)
- **.data.json**: Per-folder data files for document metadata
- **.conf**: Tab configuration
- **.cols**: Column configuration

### File Structure Conventions
- Job offer documents: `{folder}_ANNONCE.pdf`
- CVs: `{folder}_CyrilSauret.docx/pdf`
- Cover letters: `{folder}_BA.docx/pdf`
- Data files: `.data.json` (metadata for each folder)

### Testing Strategy
- **Frontend**: Jest with jsdom for DOM testing
- **Backend**: Pytest with coverage reporting
- **Fixtures**: Shared test data and mocks
- **Coverage targets**: Frontend >80%, Backend >85%

### Key API Endpoints
- `/read_annonces_json`: Load document listings with metadata
- `/save_annonces_json`: Save document metadata
- `/get_constants`: Retrieve application constants
- `/run_general_analyse`: Trigger AI analysis with specific folder number
- `/upload_doc`: Handle document uploads with validation

### Security Considerations
- File upload validation via SecurityValidator
- Filename sanitization using secure_filename
- File size limits (16MB max)
- Allowed file extensions: .pdf, .docx, .json, .txt, .csv

### Local Services Architecture
The application runs multiple services:
- **Main app** (port 5000): Primary Flask application
- **Local services** (port 5005): File explorer and prompt table interfaces

### AI Analysis Workflow
1. Documents are automatically detected in folders
2. Text extraction from PDFs using PyPDF2
3. AI classification using instructions from `.clas` files
4. Results stored in `.data.json` files per folder
5. Metadata includes enterprise, job description, location, and URLs

## Common Development Tasks

### Adding New AI Analysis Features
- Modify `cy_mistral.py` for new AI integrations
- Update `cy4_general_analyse.py` for analysis workflows
- Add new prompt templates in `backend/prompts.json`

### Extending the Frontend
- Add new components following the cy_* naming convention
- Update cy_State.js for state management
- Extend cy_Panel.js for UI interactions

### Database Operations
- Use cy_data_layer.py for data access patterns
- Annonce management via AnnonceManager class
- Configuration management via ConfigManager class

### File Processing
- Document conversion handled by cy4_pdf_functions.py
- Image processing via cy2_* modules
- File caching through cy_file_manager.py

## Environment Variables
- `ANNONCES_FILE_DIR`: Root directory for document processing
- `SUIVI_DIR`: Directory for tracking CSV files
- `MISTRAL_API_KEY`: API key for Mistral AI integration
- `OPENAI_API_KEY`: API key for OpenAI integration (optional)
