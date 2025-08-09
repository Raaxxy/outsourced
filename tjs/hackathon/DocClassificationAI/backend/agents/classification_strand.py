import os
import re
from typing import Dict, Any, Optional
from .base_strand import Strand
import groq
import openai
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class ClassificationStrand(Strand):
    """
    Classification Strand: Uses LLM to determine document type and confidence score.
    """
    
    def __init__(self, llm_provider: str = "groq"):
        super().__init__("classification")
        self.llm_provider = llm_provider
        
        # Initialize LLM client
        if llm_provider == "groq":
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY environment variable is required")
            self.client = groq.Groq(api_key=api_key)
        elif llm_provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")
            self.client = openai.OpenAI(api_key=api_key)
        elif llm_provider == "gemini":
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable is required")
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel('gemini-1.5-flash')
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}")
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate that extracted_text exists in input_data."""
        return "extracted_text" in input_data and input_data["extracted_text"].strip()
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify document type using LLM.
        
        Args:
            input_data: Dictionary containing 'extracted_text'
            
        Returns:
            Dictionary with classification results
        """
        extracted_text = input_data["extracted_text"]
        
        try:
            # Truncate text if too long (LLM context limits)
            max_chars = 4000
            if len(extracted_text) > max_chars:
                extracted_text = extracted_text[:max_chars] + "..."
            
            # Classify document
            classification_result = await self._classify_document(extracted_text)
            
            # Add classification results to input_data
            input_data.update(classification_result)
            input_data["classification_status"] = "success"
            
            self.logger.info(f"Classified document as: {classification_result['document_type']} "
                           f"(confidence: {classification_result['confidence']})")
            
            return input_data
            
        except Exception as e:
            self.logger.error(f"Classification failed: {str(e)}")
            input_data["document_type"] = "unknown"
            input_data["confidence"] = 0.0
            input_data["classification_status"] = "failed"
            input_data["classification_error"] = str(e)
            return input_data
    
    async def _classify_document(self, text: str) -> Dict[str, Any]:
        """
        Use LLM to classify document type and extract confidence.
        
        Args:
            text: Extracted text from document
            
        Returns:
            Dictionary with document_type and confidence
        """
        prompt = f"""
        You are an expert VA document classification system. Classify documents with ULTRA-HIGH precision to minimize false positives.

        ## DOCUMENT CATEGORIES WITH PRECISE VA-SPECIFIC DEFINITIONS

        ### 1. RDL (Rating Decision Letter) - FINAL OFFICIAL VA DECISIONS
        **MUST HAVE ALL THREE CORE MARKERS:**
        - **FINALITY LANGUAGE**: "Service connection IS GRANTED", "Service connection IS DENIED", "We have GRANTED", "We have DENIED", "This constitutes the rating decision", "Decision is final"
        - **OFFICIAL VA HEADER**: "Department of Veterans Affairs", "Regional Office", "Veterans Benefits Administration"  
        - **DECISION SPECIFICS**: "Effective date", "Disability rating", "Combined rating", "Schedular rating"
        
        **ADDITIONAL CONFIRMING INDICATORS:**
        - Appeal rights language: "right to appeal", "Board of Veterans' Appeals", "Notice of Disagreement"
        - CFR references: "38 CFR", "Code of Federal Regulations"
        - VA Form references: "Based on VA Form 21-526EZ"
        
        **CRITICAL EXCLUSIONS:**
        - If contains "pending", "under development", "awaiting", "additional evidence needed" → RCS
        - If worksheet/calculation format → RDS
        - If medical provider header → Medical Evidence

        ### 2. RCS (Rating Claim Statement) - ACTIVE/PENDING CLAIMS
        **MUST HAVE BOTH CORE ELEMENTS:**
        - **CLAIM REFERENCE**: "VA File Number", "Claim Number", "C-File", "End Product Code (EP)", "Development ID"
        - **ACTIVE STATUS LANGUAGE**: "under development", "pending decision", "evidence requested", "examination scheduled", "we are processing your claim"
        
        **ADDITIONAL CONFIRMING INDICATORS:**
        - Development actions: "Additional evidence needed", "Medical examination required"
        - Timeline references: "within 60 days", "development period"
        - Request language: "Please provide", "Submit additional"
        - Communication focus: Letters TO veteran about claim status
        
        **DOCUMENT FORMAT CHARACTERISTICS:**
        - Letter format with formal VA correspondence structure
        - Communication-focused (informing veteran of status)
        - Future-oriented language about what will happen next
        
        **CRITICAL EXCLUSIONS:**
        - If contains final decision language → RDL
        - If contains mathematical rating calculations or diagnostic codes → RDS
        - If worksheet/tabular calculation format → RDS
        - If medical provider credentials → Medical Evidence

        ### 3. RDS (Rating Decision Sheet) - INTERNAL VA CALCULATION WORKSHEETS
        **MUST HAVE WORKSHEET FORMAT PLUS CALCULATION ELEMENTS:**
        
        **REQUIRED FORMAT INDICATORS (Must have worksheet characteristics):**
        - **WORKSHEET STRUCTURE**: Tabular layout, calculation grid, or structured data entry format
        - **INTERNAL PROCESSING FORMAT**: Not a formal letter to veteran, but internal VA working document
        - **CALCULATION FOCUS**: Mathematical computations, rating formulas, percentage breakdowns
        
        **REQUIRED CONTENT MARKERS (Must have at least 2):**
        - **DIAGNOSTIC CODES**: "DC 5010", "Diagnostic Code 8045", numbered codes (5000-9999 series)
        - **CFR SCHEDULE REFERENCES**: "38 CFR 4.71", "Rating Schedule", "Schedule for Rating Disabilities"
        - **RATING CALCULATIONS**: Individual percentages, combined rating formulas, schedular ratings
        - **TECHNICAL VA TERMINOLOGY**: "Schedular rating", "Extra-schedular", "TDIU", "Bilateral factor", "Pyramiding"
        
        **ADDITIONAL CONFIRMING INDICATORS:**
        - Mathematical calculations: "40% + (70% of 60%) = 82%"
        - Medical conditions with codes: "Lumbar spine DC 5010 - 40%"
        - Internal processing notes or reviewer comments
        - DBQ summary analysis (not the actual DBQ report)
        - Rating worksheet headers: "Rating Decision Sheet", "Calculation Worksheet"
        
        **CRITICAL DISTINCTIONS FROM RCS:**
        - RDS is CALCULATION-focused (math, percentages, codes)
        - RCS is COMMUNICATION-focused (status updates, requests)
        - RDS has WORKSHEET format (structured data)
        - RCS has LETTER format (narrative communication)
        - RDS is INTERNAL processing document
        - RCS is EXTERNAL communication to veteran
        
        **CRITICAL EXCLUSIONS:**
        - If formal letter header addressing veteran → RCS or RDL
        - If communication about claim status without calculations → RCS
        - If final decision letter with appeal rights → RDL
        - If medical provider credentials and clinical notes → Medical Evidence

        ### 4. Medical Evidence - CLINICAL REPORTS FROM LICENSED PROVIDERS
        **MUST HAVE PROVIDER CREDENTIALS AND CLINICAL DATA:**
        - **PROVIDER IDENTIFICATION**: "Dr.", "MD", "DO", "NP", "PA-C", "License #", "DEA #", "NPI #"
        - **MEDICAL FACILITY**: "Hospital", "Clinic", "Medical Center", letterhead with medical facility name
        - **CLINICAL TERMINOLOGY**: "Diagnosis", "ICD-10", "CPT codes", "Physical examination", "Assessment and Plan"
        - **OBJECTIVE DATA**: Lab values, vital signs, imaging results, test measurements
        
        **SPECIFIC MEDICAL DOCUMENT TYPES:**
        - C&P Examination reports (but only if from medical provider, not VA worksheet)
        - Hospital discharge summaries
        - Radiology reports (MRI, CT, X-ray)
        - Laboratory results
        - Specialist consultation notes
        
        **CRITICAL EXCLUSIONS:**
        - If VA internal worksheet format → RDS  
        - If first-person narrative → Lay Statement
        - If VA decision letter → RDL

        ### 5. Lay Statement - PERSONAL NARRATIVES
        **MUST HAVE FIRST-PERSON NARRATIVE:**
        - **PERSONAL PERSPECTIVE**: "I served", "My condition", "I experienced", "During my time in"
        - **NARRATIVE STYLE**: Story-telling format, chronological personal account
        - **NON-CLINICAL LANGUAGE**: Describes symptoms in lay terms, no medical jargon
        
        **INCLUDES:**
        - Veteran personal statements
        - Buddy statements from fellow service members
        - Family member observations
        - Personal impact statements
        
        **CRITICAL EXCLUSIONS:**
        - If clinical measurements/diagnosis from provider → Medical Evidence
        - If VA official language → RDL/RCS
        - If technical calculation format → RDS

        ### 6. VA Forms - OFFICIAL APPLICATION DOCUMENTS
        **MUST HAVE FORM IDENTIFICATION:**
        - **FORM NUMBERS**: "VA Form 21-526EZ", "Form 10-10EZ", "DD-214", "21-4142", "21-0781"
        - **APPLICATION LANGUAGE**: "Application for", "Request for", form field structure
        - **BLANK/FILLED FORMS**: Both completed and blank official VA forms
        
        **CRITICAL EXCLUSIONS:**
        - If decision about form → RDL
        - If worksheet analyzing form → RDS

        ### 7. Personal Information (Flag for Discard)
        - Government ID cards, driver licenses, passports, birth certificates
        - Social Security cards, state-issued identification
        - Personal financial documents unrelated to VA benefits

        ### 8. Other
        - Unclear/incomplete text
        - Multiple categories equally likely
        - No clear distinguishing markers
        - Confidence below 70%

        ## CLASSIFICATION HIERARCHY (For Tie-Breaking):
        1. RDL (highest priority - final decisions)
        2. RDS (technical worksheets)
        3. RCS (active claims)
        4. Medical Evidence (clinical reports)
        5. VA Forms (applications)
        6. Lay Statement (narratives)
        7. Personal Info (discard)
        8. Other (lowest confidence)

        ## CONFIDENCE SCORING:
        - **95-100%**: Perfect match with all required markers, zero ambiguity
        - **85-94%**: Strong match with most markers, minimal uncertainty
        - **75-84%**: Good match but some ambiguity between categories
        - **70-74%**: Weak but acceptable evidence
        - **<70%**: Insufficient evidence → classify as "Other"

        ## CRITICAL FALSE POSITIVE PREVENTION:
        
        ### SPECIFIC RDS vs RCS DECISION RULES:
        **IF document contains claim references AND calculation elements:**
        1. **CHECK FORMAT**: Is it a worksheet/table OR a formal letter?
           - Worksheet format → RDS
           - Letter format → RCS
        
        2. **CHECK PRIMARY PURPOSE**: Is it for calculation OR communication?
           - Mathematical calculations, diagnostic codes, rating formulas → RDS
           - Status updates, requests, development actions → RCS
        
        3. **CHECK AUDIENCE**: Is it internal VA processing OR communication to veteran?
           - Internal processing document → RDS
           - Letter to veteran → RCS
        
        **EXAMPLES:**
        - "Claim #12345 - DC 5010: 40%, DC 9411: 70%, Combined: 82%" → RDS (calculation focus)
        - "Your claim #12345 is under development, please provide additional evidence" → RCS (communication focus)
        
        ### OTHER CRITICAL DISTINCTIONS:
        - RDL vs RCS: Look for FINALITY ("granted/denied") vs PENDING ("under development") language
        - RDL vs RDS: Look for FORMAL DECISION LETTER vs CALCULATION WORKSHEET format
        - RDS vs Medical Evidence: Look for VA INTERNAL ANALYSIS vs CLINICAL PROVIDER REPORT
        - Medical vs Lay: Look for PROVIDER CREDENTIALS vs PERSONAL NARRATIVE

        ## OUTPUT FORMAT:
        Return ONLY valid JSON:
        {{"category": "<exact_category>", "confidence": <0-100>, "reasoning": "Specific markers found and excluded categories explained"}}

        Document text to classify:
        {text}
        """
        
        try:
            if self.llm_provider == "groq":
                response = self.client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=500
                )
                result_text = response.choices[0].message.content
            elif self.llm_provider == "openai":
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=500
                )
                result_text = response.choices[0].message.content
            elif self.llm_provider == "gemini":
                response = self.client.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,
                        max_output_tokens=500,
                    )
                )
                result_text = response.text
            
            # Parse JSON response
            import json
            import re
            
            # Try to extract JSON from the response (in case LLM adds extra text)
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
            else:
                result = json.loads(result_text)
            
            return {
                "document_type": result.get("category", "unknown"),
                "confidence": float(result.get("confidence", 0.0)) / 100.0,  # Convert 0-100 to 0-1
                "classification_reasoning": result.get("reasoning", "")
            }
            
        except Exception as e:
            self.logger.error(f"LLM classification failed: {str(e)}")
            # Fallback classification based on keywords
            return self._fallback_classification(text)
    
    def _fallback_classification(self, text: str) -> Dict[str, Any]:
        """
        Fallback classification using keyword matching.
        
        Args:
            text: Document text
            
        Returns:
            Dictionary with document_type and confidence
        """
        text_lower = text.lower()
        
        # Enhanced keyword patterns with better RDS vs RCS distinction
        patterns = {
            "rdl": [
                r"service connection is granted", r"service connection is denied",
                r"we have granted", r"we have denied", r"this constitutes the rating decision",
                r"decision is final", r"effective date", r"disability rating", r"combined rating",
                r"right to appeal", r"board of veterans.? appeals", r"notice of disagreement"
            ],
            "rds": [
                # Primary RDS indicators (calculation and worksheet focus)
                r"rating decision sheet", r"calculation worksheet", r"rating worksheet",
                r"dc \d{4}", r"diagnostic code \d{4}", r"schedular rating",
                r"38 cfr 4\.\d+", r"rating schedule", r"combined rating.*?formula",
                r"bilateral factor", r"pyramiding", r"tdiu", r"extra.?schedular",
                r"\d{1,3}% \+ \d{1,3}% of \d{1,3}%", r"individual ratings:",
                # Format indicators
                r"condition.*?dc.*?\d{1,3}%", r"diagnosis.*?rating.*?\d{1,3}%"
            ],
            "rcs": [
                # Communication and status focus (NOT calculation)
                r"your claim.*?is.*?under development", r"pending decision", 
                r"evidence requested", r"examination scheduled", r"we are processing your claim",
                r"additional evidence needed", r"medical examination required",
                r"please provide", r"submit.*?within.*?days", r"development.*?letter",
                r"dear veteran", r"we are writing", r"contact us if you have questions",
                r"remains under development", r"notify you.*?decision", r"current rating.*?increase",
                # Enhanced claim communication patterns
                r"your.*?claim.*?for.*?(?:increased|additional|disability)", 
                r"we will determine.*?(?:rating|increase)", r"requested evidence",
                # Only claim references WITHOUT calculation elements
                r"va file number.*?(?!dc|diagnostic|rating|cfr)", r"claim number.*?(?!dc|diagnostic|rating)",
                r"end product code", r"development id"
            ],
            "medical_evidence": [
                r"dr\.", r"\bmd\b", r"\bdo\b", r"license #", r"dea #", r"npi #",
                r"hospital", r"clinic", r"medical center", r"diagnosis", r"icd-10",
                r"cpt codes", r"physical examination", r"assessment and plan",
                r"mri", r"ct scan", r"x-ray", r"laboratory results"
            ],
            "lay_statement": [
                r"i served", r"my condition", r"i experienced", r"during my time in",
                r"when i was in", r"during my service", r"i remember", r"my injury",
                r"buddy statement", r"fellow service member"
            ],
            "va_forms": [
                r"va form", r"form 21-526ez", r"form 10-10ez", r"dd-214",
                r"21-4142", r"21-0781", r"application for", r"request for"
            ],
            "personal_info": [
                r"driver license", r"passport", r"birth certificate",
                r"social security card", r"state id", r"date of birth"
            ]
        }
        
        # Find best match with RDS vs RCS disambiguation
        best_match = "other"
        best_score = 0
        scores = {}
        
        for doc_type, pattern_list in patterns.items():
            score = 0
            for pattern in pattern_list:
                if re.search(pattern, text_lower):
                    score += 1
            scores[doc_type] = score
            
            if score > best_score:
                best_score = score
                best_match = doc_type
        
        # Apply RDS vs RCS disambiguation rules
        rds_score = scores.get("rds", 0)
        rcs_score = scores.get("rcs", 0)
        
        if rds_score > 0 and rcs_score > 0:
            # Both have matches - apply decision rules
            
            # Check for calculation indicators (strongly favor RDS)
            calculation_indicators = [
                r"dc \d{4}", r"diagnostic code", r"\d{1,3}%.*?\d{1,3}%", 
                r"schedular rating", r"combined rating.*?formula", r"38 cfr"
            ]
            has_calculations = any(re.search(pattern, text_lower) for pattern in calculation_indicators)
            
            # Check for communication indicators (strongly favor RCS) 
            communication_indicators = [
                r"dear", r"we are writing", r"please provide", r"your claim.*?is",
                r"submit.*?within", r"examination scheduled"
            ]
            has_communication = any(re.search(pattern, text_lower) for pattern in communication_indicators)
            
            # Apply decision rules
            if has_calculations and not has_communication:
                best_match = "rds"
                best_score = rds_score + 2  # Boost for calculation focus
            elif has_communication and not has_calculations:
                best_match = "rcs" 
                best_score = rcs_score + 2  # Boost for communication focus
            elif rds_score > rcs_score:
                best_match = "rds"
            else:
                best_match = "rcs"
                best_match = "rcs"
        
        # Calculate confidence based on match score
        confidence = min(70, best_score * 10)  # Cap at 70 for fallback
        
        return {
            "document_type": best_match,
            "confidence": confidence / 100.0,  # Convert to 0-1 scale
            "classification_reasoning": f"Fallback classification: RDS score={rds_score}, RCS score={rcs_score}, chosen={best_match} (total score: {best_score})"
        } 