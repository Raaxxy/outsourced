# VA Document Classification System

A FastAPI backend that powers a VA Document Classification System using a modular Strand Agent pipeline. The system processes PDF and image documents through OCR, classification, confidence assessment, and routing.

## 🚀 Features

### Backend Features
- **Modular Strand Pipeline**: Each processing step is a separate, extensible strand
- **OCR Processing**: Converts PDF and image files to text using Tesseract
- **LLM Classification**: Uses Google Gemini 2.5 Pro (default), Groq, or OpenAI to classify document types with confidence scores
- **Smart Routing**: Automatically routes documents to appropriate folders based on confidence
- **RESTful API**: Clean JSON responses for easy frontend integration
- **Error Handling**: Comprehensive error handling and logging throughout the pipeline

### Frontend Features
- **Modern React UI**: Built with React 18, Vite, and Tailwind CSS
- **Drag & Drop Upload**: Easy file selection with drag and drop support
- **Real-time Processing**: Live updates during document processing
- **Beautiful Results Display**: Clean, organized display of classification results
- **Responsive Design**: Works perfectly on desktop and mobile devices
- **Status Indicators**: Visual feedback for processing status and confidence levels

## 📁 Project Structure

```
Document Classification/
├── backend/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_strand.py          # Base class for all strands
│   │   ├── ocr_strand.py           # OCR processing strand
│   │   ├── classification_strand.py # LLM classification strand
│   │   ├── confidence_strand.py    # Confidence assessment strand
│   │   ├── routing_strand.py       # File routing strand
│   │   └── strand_pipeline.py      # Pipeline orchestrator
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── file_ops.py             # File operations utilities
│   │   └── ocr_helpers.py          # OCR and text processing helpers
│   ├── data/
│   │   ├── uploads/                # Temporary uploaded files
│   │   ├── sorted/                 # Auto-processed documents by type
│   │   ├── review/                 # Documents requiring human review
│   │   └── rejected/               # Rejected documents
│   ├── main.py                     # FastAPI application
│   ├── requirements.txt            # Python dependencies
│   └── env_example.txt             # Environment variables template
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 # Main React component
│   │   ├── main.jsx                # React entry point
│   │   └── index.css               # Tailwind CSS styles
│   ├── public/                     # Static assets
│   ├── index.html                  # HTML template
│   ├── tailwind.config.js          # Tailwind configuration
│   ├── postcss.config.js           # PostCSS configuration
│   └── package.json                # Node.js dependencies
├── venv/                           # Python virtual environment
├── start-dev.sh                    # Development startup script
└── README.md
```

## 🛠️ Installation

### Prerequisites

1. **Python 3.8+**
2. **Tesseract OCR**: Required for OCR processing
3. **LLM API Key**: Google Gemini API key (default), Groq, or OpenAI API key

### Install Tesseract

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download from [Tesseract GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

### Setup Python Environment

1. **Clone the repository:**
```bash
git clone <repository-url>
cd "Document Classification"
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

4. **Set up environment variables:**
```bash
cp env_example.txt .env
# Edit .env with your API keys
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# LLM API Keys (Required - at least one)
GOOGLE_API_KEY=your_google_gemini_api_key_here  # Default provider
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Application Settings
LOG_LEVEL=INFO
UPLOAD_DIR=backend/data/uploads
BASE_DATA_PATH=backend/data

# Confidence Thresholds
HIGH_CONFIDENCE_THRESHOLD=0.8
LOW_CONFIDENCE_THRESHOLD=0.6
```

### Strand Configuration

The system uses four main strands in sequence:

1. **OCR Strand**: Extracts text from PDF/images
2. **Classification Strand**: Uses LLM to classify document type
3. **Confidence Strand**: Determines processing route based on confidence
4. **Routing Strand**: Moves files to appropriate directories

## 🚀 Running the Application

### Quick Start (Recommended)

Use the development script to start both backend and frontend:

```bash
./start-dev.sh
```

This will start:
- Backend API at `http://localhost:8000`
- Frontend UI at `http://localhost:5173`
- API documentation at `http://localhost:8000/docs`

### Manual Start

#### Backend Only

```bash
cd backend
python main.py
```

Or using uvicorn directly:

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

#### Frontend Only

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`

### API Documentation

- **Interactive Docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 📡 API Endpoints

### POST `/upload-docs`
Upload and process multiple documents.

**Request:**
- Content-Type: `multipart/form-data`
- Body: Multiple files (PDF, PNG, JPG, JPEG, TIFF, BMP)

**Response:**
```json
{
  "message": "Processed 2 files successfully",
  "processed_files": [
    {
      "filename": "document.pdf",
      "document_type": "medical_record",
      "confidence": 0.95,
      "processing_route": "auto_process",
      "final_path": "backend/data/sorted/medical_record/medical_record_20231201_143022.pdf",
      "extracted_text_length": 1250,
      "classification_reasoning": "Document contains medical terminology and patient information",
      "confidence_decision": "High confidence (0.95) - safe for auto-processing",
      "status": "success"
    }
  ],
  "total_files": 2,
  "successful_files": 1,
  "failed_files": 1
}
```

### GET `/health`
Health check endpoint.

### GET `/pipeline/strands`
Get information about the current strand pipeline.

### GET `/stats`
Get processing statistics and file counts.

## 🔄 Strand Pipeline

### Document Types

The system classifies documents into these categories:

- `medical_record`: Medical records, health reports, doctor notes
- `disability_claim`: Disability benefit applications, claim forms
- `discharge_papers`: Military discharge documents, DD-214 forms
- `prescription`: Medication prescriptions, pharmacy documents
- `appointment`: Medical appointment schedules, appointment confirmations
- `insurance`: Insurance forms, coverage documents
- `personal_info`: Personal information forms, contact updates
- `other`: Any other document type

### Processing Routes

Based on confidence scores:

- **Auto Process** (≥0.8): Documents moved to `sorted/<document_type>/`
- **Human Review** (0.6-0.8): Documents moved to `review/`
- **Rejected** (<0.6): Documents moved to `rejected/`

## 🧪 Testing

### Test with Sample Files

1. **Start the server**
2. **Use the interactive docs** at `http://localhost:8000/docs`
3. **Upload test files** using the `/upload-docs` endpoint
4. **Check results** in the response and file system

### Test File Types

The system supports:
- **PDF files** (`.pdf`)
- **Image files** (`.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp`)

## 🔧 Customization

### Adding New Strands

1. **Create new strand class** inheriting from `Strand`:
```python
from agents.base_strand import Strand

class CustomStrand(Strand):
    def __init__(self):
        super().__init__("custom")
    
    async def run(self, input_data):
        # Your processing logic here
        return input_data
```

2. **Add to pipeline** in `main.py`:
```python
custom_strand = CustomStrand()
strand_pipeline = StrandPipeline([
    ocr_strand,
    classification_strand,
    custom_strand,  # Add your strand
    confidence_strand,
    routing_strand
])
```

### Modifying Confidence Thresholds

Update the `ConfidenceStrand` initialization in `main.py`:

```python
confidence_strand = ConfidenceStrand(
    high_confidence_threshold=0.9,  # Customize thresholds
    low_confidence_threshold=0.7
)
```

## 🐛 Troubleshooting

### Common Issues

1. **Tesseract not found**: Ensure Tesseract is installed and in PATH
2. **API key errors**: Check your `.env` file and API key validity
3. **File permission errors**: Ensure write permissions for data directories
4. **Memory issues**: Large PDFs may require more memory

### Logs

Check the console output for detailed logs. The system logs:
- Strand execution progress
- File processing results
- Error details
- Performance metrics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the API documentation
3. Check the logs for error details
4. Open an issue on GitHub 