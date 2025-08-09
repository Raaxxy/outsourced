from typing import List, Dict, Any
from .base_strand import Strand
import logging

class StrandPipeline:
    """
    Orchestrates the execution of strands in sequence.
    """
    
    def __init__(self, strands: List[Strand]):
        self.strands = strands
        self.logger = logging.getLogger("strand_pipeline")
    
    async def process(self, initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process data through all strands in sequence.
        
        Args:
            initial_data: Initial data to process
            
        Returns:
            Final processed data
        """
        self.logger.info(f"Starting pipeline with {len(self.strands)} strands")
        
        current_data = initial_data.copy()
        
        for i, strand in enumerate(self.strands):
            try:
                self.logger.info(f"Executing strand {i+1}/{len(self.strands)}: {strand.name}")
                
                # Execute strand
                current_data = await strand.execute(current_data)
                
                # Check if strand failed
                if f"{strand.name}_status" in current_data and current_data[f"{strand.name}_status"] == "failed":
                    self.logger.error(f"Strand {strand.name} failed, stopping pipeline")
                    break
                
            except Exception as e:
                self.logger.error(f"Unexpected error in strand {strand.name}: {str(e)}")
                current_data[f"{strand.name}_error"] = str(e)
                current_data[f"{strand.name}_status"] = "failed"
                break
        
        self.logger.info("Pipeline execution completed")
        return current_data
    
    def add_strand(self, strand: Strand):
        """Add a strand to the pipeline."""
        self.strands.append(strand)
    
    def remove_strand(self, strand_name: str):
        """Remove a strand from the pipeline by name."""
        self.strands = [s for s in self.strands if s.name != strand_name]
    
    def get_strand_names(self) -> List[str]:
        """Get list of strand names in the pipeline."""
        return [strand.name for strand in self.strands] 