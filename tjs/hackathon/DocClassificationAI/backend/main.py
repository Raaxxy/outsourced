import os
import json
import logging
from typing import List, Dict, Any
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio

# Import our custom modules
from agents.ocr_strand import OCRStrand
from agents.classification_strand import ClassificationStrand
from agents.data_extraction_strand import DataExtractionStrand
from agents.confidence_strand import ConfidenceStrand
from agents.routing_strand import RoutingStrand
from agents.strand_pipeline import StrandPipeline
from utils.file_ops import FileOperations
from utils.ocr_helpers import OCRHelpers



def generate_veteran_summary(extracted_data: Dict[str, Any], document_type: str, filename: str) -> str:
    """Generate a veteran summary from extracted data."""
    
    # Get veteran name
    veteran_name = "Unknown Veteran"
    if extracted_data.get("primary_name"):
        veteran_name = extracted_data["primary_name"]
    elif extracted_data.get("names") and len(extracted_data["names"]) > 0:
        veteran_name = extracted_data["names"][0]
    
    # Start building summary
    summary_lines = [f"**Veteran Summary: {veteran_name}**"]
    
    # Add document type
    doc_type_display = document_type.replace('_', ' ').title()
    summary_lines.append(f"• Document Type: {doc_type_display}")
    
    # Add SSN if available
    if extracted_data.get("ssn"):
        ssn_masked = f"***-**-{extracted_data['ssn'][-4:]}" if len(extracted_data['ssn']) >= 4 else "***-**-****"
        summary_lines.append(f"• SSN: {ssn_masked}")
    
    # Add contact info
    if extracted_data.get("primary_email"):
        summary_lines.append(f"• Email: {extracted_data['primary_email']}")
    
    if extracted_data.get("primary_phone"):
        summary_lines.append(f"• Phone: {extracted_data['primary_phone']}")
    
    # Add disability information
    disability_info = extracted_data.get("disability_info", {})
    if disability_info.get("disability_percentage"):
        summary_lines.append(f"• Disability Rating: {disability_info['disability_percentage']}%")
    
    if disability_info.get("service_connected"):
        summary_lines.append(f"• Service Connected: Yes")
    
    # Add VA forms if present
    if extracted_data.get("va_forms"):
        forms = extracted_data["va_forms"]
        if isinstance(forms, list):
            summary_lines.append(f"• VA Forms: {', '.join(forms)}")
        else:
            summary_lines.append(f"• VA Forms: {forms}")
    
    return "\n".join(summary_lines)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="VA Document Classification System",
    description="A FastAPI backend for VA document classification using modular Strand Agent pipeline",
    version="1.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
file_ops = FileOperations()
ocr_helpers = OCRHelpers()

# Initialize strands
ocr_strand = OCRStrand()
classification_strand = ClassificationStrand(llm_provider="gemini")  # Using Gemini 2.5 Pro for superior performance
data_extraction_strand = DataExtractionStrand()
confidence_strand = ConfidenceStrand()
routing_strand = RoutingStrand()

# Create strand pipeline
strand_pipeline = StrandPipeline([
    ocr_strand,
    classification_strand,
    data_extraction_strand,  # Extract data after classification
    confidence_strand,
    routing_strand
])

# Pydantic models for responses
class DocumentResult(BaseModel):
    filename: str
    document_type: str
    confidence: float
    processing_route: str
    final_path: str
    extracted_text_length: int
    classification_reasoning: str
    confidence_decision: str
    status: str
    veteran_name: str = "Unknown"
    new_filename: str = ""
    extracted_data: Dict[str, Any] = {}
    error: str | None = None

class UploadResponse(BaseModel):
    message: str
    processed_files: List[DocumentResult]
    total_files: int
    successful_files: int
    failed_files: int
    veteran_summary: str | None = None

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "VA Document Classification System API",
        "version": "1.0.0",
        "endpoints": {
            "upload_docs": "/upload-docs",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "VA Document Classification System"}

@app.post("/upload-docs", response_model=UploadResponse)
async def upload_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
):
    """
    Upload and process multiple documents through the strand pipeline.
    
    Args:
        files: List of uploaded files (PDF or images)
        
    Returns:
        Processing results for all files
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    logger.info(f"Processing {len(files)} uploaded files")
    
    processed_files = []
    successful_files = 0
    failed_files = 0
    
    for file in files:
        try:
            # Validate file type
            if not file_ops.validate_file_type(file.filename):
                logger.warning(f"Skipping unsupported file type: {file.filename}")
                failed_files += 1
                processed_files.append(DocumentResult(
                    filename=file.filename,
                    document_type="unsupported",
                    confidence=0.0,
                    processing_route="rejected",
                    final_path="",
                    extracted_text_length=0,
                    classification_reasoning="Unsupported file type",
                    confidence_decision="File type not supported",
                    status="failed",
                    error="Unsupported file type"
                ))
                continue
            
            # Save uploaded file
            file_path = await file_ops.save_uploaded_file(file)
            logger.info(f"Saved file: {file_path}")
            
            # Prepare initial data for pipeline
            initial_data = {
                "file_path": file_path,
                "original_filename": file.filename,
                "file_size_mb": file_ops.get_file_size_mb(file_path)
            }
            
            # Process through strand pipeline
            result = await strand_pipeline.process(initial_data)
            
            # Extract relevant information for response
            document_result = DocumentResult(
                filename=file.filename,
                document_type=result.get("document_type", "unknown"),
                confidence=result.get("confidence", 0.0),
                processing_route=result.get("processing_route", "rejected"),
                final_path=result.get("final_path", ""),
                extracted_text_length=result.get("text_length", 0),
                classification_reasoning=result.get("classification_reasoning", ""),
                confidence_decision=result.get("confidence_decision", ""),
                status="success" if result.get("routing_status") == "success" else "failed",
                veteran_name=result.get("veteran_name_used", "Unknown"),
                new_filename=result.get("new_filename", ""),
                extracted_data=result.get("extracted_data", {}),
                error=result.get("routing_error") if result.get("routing_status") == "failed" else ""
            )
            
            processed_files.append(document_result)
            
            if document_result.status == "success":
                successful_files += 1
            else:
                failed_files += 1
                
            logger.info(f"Processed {file.filename}: {document_result.document_type} "
                       f"(confidence: {document_result.confidence})")
            
        except Exception as e:
            logger.error(f"Error processing {file.filename}: {str(e)}")
            failed_files += 1
            
            processed_files.append(DocumentResult(
                filename=file.filename,
                document_type="unknown",
                confidence=0.0,
                processing_route="rejected",
                final_path="",
                extracted_text_length=0,
                classification_reasoning="Processing error",
                confidence_decision="Document processing failed",
                status="failed",
                error=str(e)
            ))

        # (Keep all the existing file processing code above this point)
    
        # Generate veteran summary for single document uploads
        veteran_summary = None
        if len(files) == 1 and successful_files == 1:
            successful_result = next((f for f in processed_files if f.status == "success"), None)
            if successful_result and successful_result.extracted_data:
                veteran_summary = generate_veteran_summary(
                    successful_result.extracted_data, 
                    successful_result.document_type, 
                    successful_result.filename
                )

        # Create response
        response = UploadResponse(
            message=f"Processed {len(files)} files successfully",
            processed_files=processed_files,
            total_files=len(files),
            successful_files=successful_files,
            failed_files=failed_files,
            veteran_summary=veteran_summary
        )

        logger.info(f"Upload processing completed: {successful_files} successful, {failed_files} failed")

        return response

@app.get("/pipeline/strands")
async def get_pipeline_strands():
    """Get information about the current strand pipeline."""
    return {
        "strands": strand_pipeline.get_strand_names(),
        "total_strands": len(strand_pipeline.strands)
    }

@app.get("/stats")
async def get_processing_stats():
    """Get processing statistics and system information."""
    # Count files in different directories
    sorted_dir = "backend/data/sorted"
    review_dir = "backend/data/review"
    discarded_dir = "backend/data/discarded"
    extracted_data_dir = "backend/data/extracted_data"
    
    def count_files_recursively(directory):
        """Count all files recursively in a directory."""
        if not os.path.exists(directory):
            return 0
        total = 0
        for root, dirs, files in os.walk(directory):
            total += len([f for f in files if os.path.isfile(os.path.join(root, f))])
        return total
    
    def count_veteran_folders(directory):
        """Count veteran folders and files by category."""
        if not os.path.exists(directory):
            return {}
        
        veteran_stats = {}
        category_stats = {}
        
        for veteran_folder in os.listdir(directory):
            veteran_path = os.path.join(directory, veteran_folder)
            if os.path.isdir(veteran_path) and veteran_folder.endswith('_docs'):
                veteran_name = veteran_folder.replace('_docs', '')
                veteran_stats[veteran_name] = {}
                
                # Count files in each category for this veteran
                for category in os.listdir(veteran_path):
                    category_path = os.path.join(veteran_path, category)
                    if os.path.isdir(category_path):
                        file_count = len([f for f in os.listdir(category_path) 
                                        if os.path.isfile(os.path.join(category_path, f))])
                        veteran_stats[veteran_name][category] = file_count
                        
                        # Add to overall category stats
                        if category not in category_stats:
                            category_stats[category] = 0
                        category_stats[category] += file_count
        
        return {"by_veteran": veteran_stats, "by_category": category_stats}
    
    stats = {
        "files_processed": {
            "sorted": count_veteran_folders(sorted_dir),
            "review": count_files_recursively(review_dir),
            "discarded": count_files_recursively(discarded_dir),
            "extracted_data": count_files_recursively(extracted_data_dir)
        },
        "total_files": (
            count_files_recursively(sorted_dir) + 
            count_files_recursively(review_dir) + 
            count_files_recursively(discarded_dir)
        )
    }
    
    return stats

@app.get("/extracted-data")
async def get_extracted_data():
    """Get list of all extracted data files."""
    extracted_data_dir = "backend/data/extracted_data"
    
    if not os.path.exists(extracted_data_dir):
        return {"extracted_data_files": []}
    
    files = []
    for filename in os.listdir(extracted_data_dir):
        if filename.endswith('_data.json'):
            file_path = os.path.join(extracted_data_dir, filename)
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    files.append({
                        "filename": filename,
                        "document_type": data.get("document_type", "unknown"),
                        "extraction_timestamp": data.get("extraction_timestamp", ""),
                        "data_fields": len(data.keys())
                    })
            except Exception as e:
                files.append({
                    "filename": filename,
                    "error": str(e)
                })
    
    return {"extracted_data_files": files}

@app.get("/extracted-data/{filename}")
async def get_extracted_data_file(filename: str):
    """Get specific extracted data file."""
    extracted_data_dir = "backend/data/extracted_data"
    file_path = os.path.join(extracted_data_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 