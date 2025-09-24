# Gemini API integration for enhanced text analysis
import os
import json
from typing import Dict, List, Optional

GEMINI_API_KEY="AIzaSyBwMQ-D_cqHS1qUaML-JRWW15JJJYTzIOs"

try:
    import google.generativeai as genai  # type: ignore
except Exception:
    genai = None


def setup_gemini(api_key: Optional[str] = None) -> bool:
    """Initialize Gemini API with provided or environment key."""
    if genai is None:
        return False
    
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        return False
    
    genai.configure(api_key=key)
    return True


def analyze_packaging_text(text: str, api_key: Optional[str] = None) -> Dict[str, object]:
    """Use Gemini to analyze packaging text for LM compliance with comprehensive cross-verification."""
    if not setup_gemini(api_key):
        return {"error": "Gemini API not available"}
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        You are an expert in Indian Legal Metrology Rules (2011) compliance. Analyze this raw OCR text extracted from a product packaging label and provide comprehensive compliance analysis.

        RAW OCR TEXT:
        "{text}"

        Please perform detailed analysis and return a JSON response with the following structure:

        {{
            "extracted_fields": {{
                "mrp": "₹XX.XX or null if not found",
                "quantity": "XX g/kg/ml with units or null",
                "manufacturer": "Company name and address or null",
                "origin": "Country name or null",
                "support": "Contact email/phone or null",
                "dates": "Manufacturing/expiry dates or null",
                "batch": "Batch/lot number or null",
                "license": "FSSAI license number or null",
                "barcode": "Product barcode or null"
            }},
            "compliance_analysis": {{
                "required_fields_present": {{
                    "mrp": true/false,
                    "quantity": true/false,
                    "manufacturer": true/false,
                    "origin": true/false
                }},
                "optional_fields_present": {{
                    "support": true/false,
                    "dates": true/false,
                    "batch": true/false,
                    "license": true/false,
                    "barcode": true/false
                }},
                "compliance_score": "X/4",
                "total_fields_found": X,
                "missing_required": ["list of missing required fields"],
                "missing_optional": ["list of missing optional fields"]
            }},
            "detailed_analysis": {{
                "text_quality": "Assessment of OCR text quality",
                "field_extraction_confidence": "High/Medium/Low",
                "potential_issues": ["list of potential compliance issues"],
                "recommendations": ["specific recommendations for improvement"],
                "additional_notes": "Any additional observations"
            }},
            "cross_verification": {{
                "ocr_vs_ai_extraction": "Comparison of OCR vs AI extraction",
                "confidence_level": "High/Medium/Low",
                "discrepancies": ["any discrepancies found"],
                "final_recommendation": "Overall compliance assessment"
            }}
        }}

        IMPORTANT INSTRUCTIONS:
        1. Look for patterns like "NET WEIGHT", "MRP", "MARKETED BY", "MANUFACTURED BY", "FSSAI", "Lic. No.", etc.
        2. Extract email addresses, phone numbers (including 1800 numbers), and addresses
        3. Look for batch numbers, manufacturing dates, expiry dates
        4. Identify FSSAI license numbers (usually 14-digit numbers)
        5. Assess text quality and extraction confidence
        6. Provide specific, actionable recommendations
        7. Cross-verify findings with Legal Metrology requirements
        """
        
        response = model.generate_content(prompt)
        
        # Try to parse JSON response
        try:
            result = json.loads(response.text)
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                result = {
                    "error": "Failed to parse Gemini response as JSON",
                    "raw_response": response.text
                }
        
        return result
        
    except Exception as e:
        return {"error": f"Gemini analysis failed: {str(e)}"}


def enhance_ocr_with_gemini(ocr_text: str, api_key: Optional[str] = None) -> Dict[str, object]:
    """Use Gemini to enhance OCR-extracted text analysis."""
    if not setup_gemini(api_key):
        return {"enhanced": False, "reason": "Gemini API not available"}
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        This text was extracted from product packaging via OCR. Clean it up and extract Legal Metrology fields:
        
        "{ocr_text}"
        
        Please:
        1. Fix any OCR errors
        2. Extract structured data for LM compliance
        3. Identify missing required information
        4. Flag potential compliance issues
        
        Return JSON with cleaned text and extracted fields.
        """
        
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        result["enhanced"] = True
        return result
        
    except Exception as e:
        return {"enhanced": False, "reason": f"Gemini enhancement failed: {str(e)}"}


def comprehensive_compliance_analysis(ocr_text: str, ocr_fields: Dict[str, object], api_key: Optional[str] = None) -> Dict[str, object]:
    """Perform comprehensive compliance analysis with cross-verification between OCR and AI extraction."""
    if not setup_gemini(api_key):
        return {"error": "Gemini API not available"}
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        You are an expert in Indian Legal Metrology Rules (2011) compliance. Perform comprehensive analysis comparing OCR extraction with AI-powered field detection.

        RAW OCR TEXT:
        "{ocr_text}"

        OCR EXTRACTED FIELDS:
        {json.dumps(ocr_fields, indent=2)}

        Please provide a comprehensive JSON analysis with the following structure:

        {{
            "ai_extraction": {{
                "mrp": "₹XX.XX or null",
                "quantity": "XX g/kg/ml or null", 
                "manufacturer": "Company details or null",
                "origin": "Country or null",
                "support": "Contact info or null",
                "dates": "Dates or null",
                "batch": "Batch number or null",
                "license": "FSSAI license or null",
                "barcode": "Barcode or null"
            }},
            "comparison_analysis": {{
                "ocr_vs_ai_match": {{
                    "mrp": "Match/Partial/Discrepancy/OCR_Only/AI_Only",
                    "quantity": "Match/Partial/Discrepancy/OCR_Only/AI_Only",
                    "manufacturer": "Match/Partial/Discrepancy/OCR_Only/AI_Only",
                    "origin": "Match/Partial/Discrepancy/OCR_Only/AI_Only",
                    "support": "Match/Partial/Discrepancy/OCR_Only/AI_Only",
                    "dates": "Match/Partial/Discrepancy/OCR_Only/AI_Only",
                    "batch": "Match/Partial/Discrepancy/OCR_Only/AI_Only",
                    "license": "Match/Partial/Discrepancy/OCR_Only/AI_Only",
                    "barcode": "Match/Partial/Discrepancy/OCR_Only/AI_Only"
                }},
                "discrepancies": ["list of specific discrepancies"],
                "confidence_assessment": "High/Medium/Low",
                "recommended_fields": {{
                    "mrp": "final recommended value",
                    "quantity": "final recommended value",
                    "manufacturer": "final recommended value",
                    "origin": "final recommended value",
                    "support": "final recommended value",
                    "dates": "final recommended value",
                    "batch": "final recommended value",
                    "license": "final recommended value",
                    "barcode": "final recommended value"
                }}
            }},
            "compliance_assessment": {{
                "required_fields_status": {{
                    "mrp": "Present/Missing/Unclear",
                    "quantity": "Present/Missing/Unclear", 
                    "manufacturer": "Present/Missing/Unclear",
                    "origin": "Present/Missing/Unclear"
                }},
                "optional_fields_status": {{
                    "support": "Present/Missing/Unclear",
                    "dates": "Present/Missing/Unclear",
                    "batch": "Present/Missing/Unclear",
                    "license": "Present/Missing/Unclear",
                    "barcode": "Present/Missing/Unclear"
                }},
                "final_compliance_score": "X/4",
                "compliance_level": "Excellent/Good/Fair/Poor",
                "missing_required": ["list of missing required fields"],
                "missing_optional": ["list of missing optional fields"]
            }},
            "detailed_insights": {{
                "text_quality_assessment": "Assessment of OCR quality",
                "extraction_challenges": ["specific challenges identified"],
                "field_confidence_scores": {{
                    "mrp": "High/Medium/Low",
                    "quantity": "High/Medium/Low",
                    "manufacturer": "High/Medium/Low",
                    "origin": "High/Medium/Low",
                    "support": "High/Medium/Low",
                    "dates": "High/Medium/Low",
                    "batch": "High/Medium/Low",
                    "license": "High/Medium/Low",
                    "barcode": "High/Medium/Low"
                }},
                "recommendations": ["specific actionable recommendations"],
                "legal_metrology_compliance": "Overall LM compliance assessment"
            }}
        }}

        ANALYSIS GUIDELINES:
        1. Cross-verify OCR extraction with AI analysis
        2. Identify discrepancies and provide confidence levels
        3. Recommend final field values based on best evidence
        4. Assess compliance with Indian Legal Metrology Rules
        5. Provide specific, actionable recommendations
        6. Consider text quality and extraction challenges
        """
        
        response = model.generate_content(prompt)
        
        # Try to parse JSON response
        try:
            result = json.loads(response.text)
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                result = {
                    "error": "Failed to parse Gemini response as JSON",
                    "raw_response": response.text
                }
        
        return result
        
    except Exception as e:
        return {"error": f"Comprehensive analysis failed: {str(e)}"}


def get_gemini_analysis_status() -> Dict[str, bool]:
    """Check if Gemini API is properly configured."""
    return {
        "gemini_available": genai is not None,
        "api_key_set": bool(os.getenv("GEMINI_API_KEY")),
        "ready": setup_gemini()
    }
