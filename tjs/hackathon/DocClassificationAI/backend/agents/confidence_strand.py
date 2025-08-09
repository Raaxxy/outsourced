from typing import Dict, Any
from .base_strand import Strand

class ConfidenceStrand(Strand):
    """
    Confidence Strand: Decides if document goes to human review or auto-processing.
    """
    
    def __init__(self, high_confidence_threshold: float = 0.8, low_confidence_threshold: float = 0.6):
        super().__init__("confidence")
        self.high_confidence_threshold = high_confidence_threshold
        self.low_confidence_threshold = low_confidence_threshold
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate that confidence and document_type exist in input_data."""
        return ("confidence" in input_data and 
                "document_type" in input_data and 
                input_data["document_type"] != "unknown")
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine processing route based on confidence score.
        
        Args:
            input_data: Dictionary containing 'confidence' and 'document_type'
            
        Returns:
            Dictionary with processing decision
        """
        confidence = input_data["confidence"]
        document_type = input_data["document_type"]
        
        # Determine processing route
        if confidence >= self.high_confidence_threshold:
            processing_route = "auto_process"
            decision_reason = f"High confidence ({confidence:.2f}) - safe for auto-processing"
        elif confidence >= self.low_confidence_threshold:
            processing_route = "human_review"
            decision_reason = f"Medium confidence ({confidence:.2f}) - requires human review"
        else:
            processing_route = "rejected"
            decision_reason = f"Low confidence ({confidence:.2f}) - document discarded"
        
        # Add confidence decision to input_data
        input_data["processing_route"] = processing_route
        input_data["confidence_decision"] = decision_reason
        input_data["confidence_status"] = "success"
        
        # Additional metadata for routing
        input_data["requires_review"] = processing_route == "human_review"
        input_data["is_rejected"] = processing_route == "rejected"
        input_data["is_auto_processed"] = processing_route == "auto_process"
        input_data["is_discarded"] = confidence < 0.7  # Below 70% confidence
        
        self.logger.info(f"Confidence decision: {processing_route} - {decision_reason}")
        
        return input_data 