# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a **Legal Metrology Compliance Checker** - a Flask-based web application that analyzes product packaging images from e-commerce platforms to verify compliance with Indian Legal Metrology regulations. The system uses OCR, computer vision, and AI analysis to extract and validate mandatory product information from packaging labels.

## Development Commands

### Setup and Environment
```powershell
# Clone and setup
git clone https://github.com/anshikkumartiwari/sih2025.git
cd sih2025

# Create and activate virtual environment (Windows)
python -m venv .venv
.\.venv\Scripts\Activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```powershell
# Start development server
python app.py

# Development server runs on http://127.0.0.1:5000
# Debug mode is enabled by default
```

### Environment Configuration
```powershell
# Required: Set Gemini API key in .env file
# GEMINI_API_KEY=your_api_key_here

# Load environment variables
# The app uses python-dotenv to automatically load .env
```

### Testing and Debugging
```powershell
# Run single module tests (manual testing approach)
python -c "from core import ocr; print(ocr.extract_fields_from_images(['path/to/test/image.jpg']))"

# Test specific crawlers
python -c "from core.crawlers import amazon; print(amazon.crawl('https://amazon.in/product-url'))"

# Check Gemini API status
python -c "from core import gemini_analysis; print(gemini_analysis.get_gemini_analysis_status())"
```

## Architecture Overview

### High-Level Structure
The application follows a **modular pipeline architecture** where each stage can be developed and tested independently:

1. **Web Interface** (`dashboard/`) - Flask blueprint with templates and static assets
2. **Business Logic** (`core/`) - Modular processing pipeline
3. **Data Storage** (`temp/`) - File-based temporary storage for MVP

### Core Processing Pipeline
The main workflow in `core/master.py` orchestrates these stages:

```
URL Input → Platform Crawler → Image Download → Vision Analysis → OCR Extraction → 
AI Enhancement → Compliance Validation → Historical Tracking → Report Generation
```

### Key Architectural Components

#### 1. Platform Abstraction Layer (`core/crawlers/`)
- Currently supports Amazon (`amazon.py`) with extensible design
- URL routing logic in `master.py` dispatches to appropriate crawler
- Each crawler downloads product images and extracts basic metadata

#### 2. Computer Vision Pipeline (`core/vision.py`)
- Scores and selects best label images using keyword matching
- Filters images to focus OCR processing on relevant packaging labels
- Reduces computational overhead by processing only promising images

#### 3. OCR and Text Processing (`core/ocr.py`)
- Uses EasyOCR for text extraction from packaging images
- Structured field extraction for Legal Metrology requirements
- Handles multiple image formats and orientations

#### 4. AI Enhancement Layer (`core/gemini_analysis.py`)
- Uses Google Gemini API for OCR refinement and validation
- Cross-verification of extracted data against regulatory requirements
- Natural language processing of packaging text

#### 5. Compliance Engine (`core/rules.py`)
- Validates extracted fields against Legal Metrology regulations
- Categorizes missing information as required vs. optional
- Generates compliance scores and recommendations

#### 6. Analytics and Tracking System
- **Manufacturer Tracking** (`core/manufacturer_tracker.py`) - Maintains compliance history per manufacturer
- **Historical Data** (`core/historical_data.py`) - Stores scan results for trend analysis
- **Dashboard Analytics** - Multiple analytics views for compliance trends

### Data Flow Patterns

#### Primary Processing Flow
1. **Input Handling**: URL or direct image upload via web interface
2. **Image Acquisition**: Platform-specific crawlers download product images
3. **Image Filtering**: Vision system scores images for label relevance
4. **Text Extraction**: OCR processes filtered images for text content
5. **AI Enhancement**: Gemini API refines and validates extracted information
6. **Compliance Analysis**: Rules engine validates against regulatory requirements
7. **Data Persistence**: Results stored in JSON format for reporting
8. **Analytics Update**: Manufacturer and historical data updated for tracking

#### Data Merging Strategy
The system prioritizes data sources in this order:
1. **OCR-extracted fields** (highest priority - direct from packaging)
2. **AI-enhanced recommendations** (when OCR misses required fields)
3. **Platform metadata** (lowest priority - supplementary only)

### Key Integration Points

#### Flask Blueprint Architecture
- Main app (`app.py`) registers the dashboard blueprint
- All routes defined in `dashboard/dashboard.py`
- Static files served from `dashboard/static/`
- Templates in `dashboard/templates/`

#### File Storage Strategy
- **Temporary storage** in `temp/` directory (excluded from Git)
- **Image uploads** stored in `temp/uploads/`
- **Processing results** in `temp/output.txt` (JSON format)
- **Analytics data** persisted in JSON files for manufacturer tracking

#### API Integration Points
- **Gemini API** for AI analysis and OCR enhancement
- **EasyOCR** for text extraction from images
- **Playwright** for web scraping (crawler functionality)

## Development Guidelines

### Adding New E-commerce Platforms
1. Create new crawler in `core/crawlers/platform_name.py`
2. Implement `crawl(url)` function returning standardized data structure
3. Add URL detection logic in `master.py` routing
4. Test with platform-specific URLs

### Extending OCR Capabilities
- OCR processing in `core/ocr.py` uses standardized image input
- Field extraction logic maps to Legal Metrology requirements
- Add new field types by extending the field mapping dictionaries

### AI Analysis Enhancement
- Gemini integration in `core/gemini_analysis.py` handles API communication
- Add new analysis types by creating additional analysis functions
- Ensure proper error handling for API failures

### Compliance Rules Modification
- Legal Metrology requirements defined in validation logic
- Required vs. optional field classification in `master.py`
- Update field mappings when regulations change

### Analytics Extensions
- Manufacturer tracking stores compliance history automatically
- Historical data aggregation supports trend analysis
- Add new analytics views by extending dashboard routes

## Important Technical Details

### Environment Dependencies
- **Python 3.8+** required for dependency compatibility
- **Virtual environment** strongly recommended for isolation
- **Gemini API key** required in `.env` for AI analysis features

### File Processing Notes
- Images automatically normalized to JPEG format with corrected orientation
- Multiple image formats supported (PNG, JPEG, WEBP, etc.)
- OCR processing optimized for packaging label text

### Platform-Specific Considerations
- **Windows PowerShell** commands provided (current environment)
- **File paths** use Windows-style backslashes in configuration
- **Environment activation** uses Windows virtual environment syntax

### Error Handling Strategy
- Graceful degradation when AI services are unavailable
- Fallback processing when OCR extraction fails
- Platform-unsupported errors return structured error responses

### Performance Optimization
- Vision system pre-filters images to reduce OCR processing
- Relevant image selection based on keyword matching
- Temporary file cleanup handled automatically

This architecture supports the core mission of automated Legal Metrology compliance checking while maintaining extensibility for additional platforms, regulations, and analysis capabilities.