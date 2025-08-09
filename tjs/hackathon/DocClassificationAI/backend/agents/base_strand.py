from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

class Strand(ABC):
    """
    Base class for all strands in the document processing pipeline.
    Each strand processes input data and returns modified data.
    """
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"strand.{name}")
    
    @abstractmethod
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the strand's processing logic.
        
        Args:
            input_data: Dictionary containing input data from previous strands
            
        Returns:
            Dictionary containing processed data to pass to next strand
        """
        pass
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate that input_data contains required fields for this strand.
        Override in subclasses if needed.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if input is valid, False otherwise
        """
        return True
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method that includes validation and error handling.
        
        Args:
            input_data: Input data from previous strand
            
        Returns:
            Processed data for next strand
        """
        try:
            if not self.validate_input(input_data):
                raise ValueError(f"Invalid input for strand {self.name}")
            
            self.logger.info(f"Starting {self.name} strand")
            result = await self.run(input_data)
            self.logger.info(f"Completed {self.name} strand")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in {self.name} strand: {str(e)}")
            # Add error information to the data
            input_data[f"{self.name}_error"] = str(e)
            input_data[f"{self.name}_status"] = "failed"
            return input_data 