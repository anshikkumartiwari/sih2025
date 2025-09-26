import re
import json
import os
from paddleocr import PaddleOCR
from transformers import BlipProcessor, BlipForConditionalGeneration, pipeline
from PIL import Image
import torch
from core.gemini_analysis import extract_structured_data

class LegalMetrologyChecker:
    def __init__(self):
        # Initialize OCR
        print("Loading OCR model...")
        self.ocr_reader = PaddleOCR(use_angle_cls=True, lang='en')

        # Vision-language fallback
        print("Loading vision model...")
        self.vl_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        self.vl_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

        # LLM fallback
        self.text_extractor = pipeline("text2text-generation", model="google/flan-t5-base")

        # Regex patterns (expanded)
        self.patterns = {
            "Manufacturer": r"(MARKETED\s*BY[\s\S]*?(?=Net|MRP|FSSAI|$)|MANUFACTURED\s*BY[\s\S]*?(?=Net|MRP|FSSAI|$)|Mfg\.?\s*by[\s\S]*?(?=Net|MRP|FSSAI|$))",
            "Net_Weight": r"(Net\s*(Wt|Weight|Quantity)\s*[:\-]?\s*\d+\.?\d*\s*(g|kg|ml|l|grams?|litres?))",
            "MRP": r"(MRP\s*[:\-]?\s*(₹|Rs\.?|INR)\s*\d+\.?\d*)",
            "Consumer_Care": r"(Customer\s*Care.*?|For\s*feedback.*?|Helpline.*?|Email.*?)(?=Net|MRP|FSSAI|$)",
            "Date": r"((Mfg|Pkd|Exp|Best\s*Before|Use\s*By|PKD)[^:]*[:\-]?\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|Best\s*Before\s*\d+\s*(months?|days?|yrs?))",
            "Country_Of_Origin": r"(Country\s*of\s*Origin.*?|Made\s*in\s*[A-Za-z ]+|Product\s*of\s*[A-Za-z ]+)",
            "FSSAI_License": r"(FSSAI\s*Lic\.?\s*No\.?\s*[:\-]?\s*\d+|Lic\.?\s*No\.?\s*\d+|FSSAI\s*LIC\.?\s*[:\-]?\s*\d+|FSSAILIC\.?N[O0]\s*\d+)",
            "Nutritional": r"(Energy.*?kcal|Protein.*?\d+\.?\d*|Carbohydrate.*?\d+\.?\d|Fat.*?\d+\.?\d|Sugar.*?\d+\.?\d)",
            "Ingredients": r"(INGREDIENTS?[:\-].*?)(?=Allergen|Net|MRP|FSSAI|$)",
            "Allergen_Info": r"(Allergen\s*Information.*?)(?=Net|MRP|FSSAI|$)",
            "Storage": r"(Store\s*in.*?|Keep\s*away.*?|Consume\s*within.*?)(?=Net|MRP|FSSAI|$)",
            "Certifications": r"(ISO\s*\d*|FDA|Incredible\s*India|PRODUCT\s*OF\s*Incredible\s*India)",
            "Claims": r"(High\s*in\s*Protein|Source\s*of\s*Protein|No\s*Trans\s*Fat|Cholesterol\s*Free|Gluten\s*Free|Rich\s*in\s*Fiber)",
            "Serving_Suggestion": r"(Serving\s*Suggestions?.*?|Serving\s*Size.*?)(?=Storage|Allergen|Net|MRP|$)",
            "Numbers": r"\d{6,}"  # generic long numbers (batch, contact, barcode, etc.)
        }

    def clean_text(self, text: str) -> str:
        text = re.sub(r"[^a-zA-Z0-9:/.,\- ]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def extract_with_ocr(self, image_path: str) -> str:
        try:
            results = self.ocr_reader.ocr(image_path, cls=True)
            if results and results[0]:
                extracted_text = " ".join([line[1][0] for line in results[0]])
                return self.clean_text(extracted_text)
        except Exception as e:
            print(f"OCR extraction failed: {e}")
        return ""

    def is_relevant(self, text: str) -> bool:
        matched_items = [name for name, pattern in self.patterns.items() if re.search(pattern, text, re.IGNORECASE)]
        return len(matched_items) >= 2

    def extract_with_vision_model(self, image_path: str) -> str:
        try:
            image = Image.open(image_path).convert('RGB')
            prompt = "describe all text visible on this food package including numbers, dates, and regulatory information"
            inputs = self.vl_processor(image, prompt, return_tensors="pt")
            with torch.no_grad():
                output = self.vl_model.generate(**inputs, max_length=200, num_beams=5)
            return self.vl_processor.decode(output[0], skip_special_tokens=True)
        except Exception as e:
            print(f"Vision model extraction failed: {e}")
            return ""

    def extract_fields_regex(self, text: str) -> dict:
        """Collects all regex matches per field (list of values)."""
        extracted_fields = {}
        for name, pattern in self.patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                flat_matches = [m if isinstance(m, str) else m[0] for m in matches]

                # Special handling for CountryOfOrigin
                if name == "Country_Of_Origin":
                    clean_vals = []
                    for val in flat_matches:
                        country_match = re.search(
                            r"\b(India|USA|United States|UK|England|Germany|France|Italy|China|Japan|Korea|Brazil|Australia)\b",
                            val, re.IGNORECASE
                        )
                        if country_match:
                            clean_vals.append(country_match.group(1).upper())
                        else:
                            clean_vals.append(val)
                    flat_matches = clean_vals

                # Special handling for FSSAI License: merge all numbers into one list
                if name == "FSSAI_License":
                    clean_vals = [re.sub(r"[^\d]", "", val) for val in flat_matches]
                    if "FSSAI_License" in extracted_fields:
                        extracted_fields["FSSAI_License"].extend(clean_vals)
                    else:
                        extracted_fields["FSSAI_License"] = clean_vals
                    # remove duplicates & sort
                    extracted_fields["FSSAI_License"] = sorted(list(set(extracted_fields["FSSAI_License"])))
                    continue

                # Special handling for Numbers (exclude FSSAI License numbers)
                if name == "Numbers":
                    fssai_numbers = []
                    if "FSSAI_License" in extracted_fields:
                        fssai_numbers = extracted_fields["FSSAI_License"]
                    flat_matches = [num for num in flat_matches if num not in fssai_numbers]

                extracted_fields[name] = list(set(flat_matches))  # unique values
        return extracted_fields

    def extract_with_llm(self, text: str, missing_fields: list) -> dict:
        try:
            prompt = f"""
            Extract the following information from this food package text: {', '.join(missing_fields)}
            
            Text: {text}
            
            Return only a JSON object with the requested fields.
            """
            response = self.text_extractor(prompt, max_length=512)[0]['generated_text']
            response = re.sub(r"```json|```", "", response).strip()
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            return json.loads(json_match.group()) if json_match else {}
        except Exception as e:
            print(f"LLM extraction failed: {e}")
            return {}

    def validate_compliance(self, fields: dict) -> dict:
        compliance = {}
        total_fields = len(self.patterns)
        found_fields = 0
        
        for field in self.patterns.keys():
            is_present = bool(fields.get(field))
            compliance[field] = is_present
            if is_present:
                found_fields += 1
        
        # Calculate compliance score
        compliance_score = found_fields / total_fields if total_fields > 0 else 0
        compliance["overall_score"] = compliance_score
        
        return compliance

    def process_image_internal(self, image_path: str) -> dict:
        """Internal processing method with Gemini analysis integration"""
        print(f"[INFO] Starting OCR extraction...")
        ocr_text = self.extract_with_ocr(image_path)
        
        if not self.is_relevant(ocr_text):
            return {"relevant": False, "message": "Irrelevant image. No compliance check done."}

        print(f"[INFO] OCR text extracted: {len(ocr_text)} characters")
        
        # Try Gemini structured extraction first
        print(f"[INFO] Attempting structured analysis with Gemini...")
        try:
            structured_result = extract_structured_data(ocr_text)
            
            if "error" not in structured_result:
                print(f"[INFO] Structured analysis successful!")
                
                # Calculate compliance score based on filled fields
                required_fields = [
                    'product_manufacturer', 'manufacturer_address', 'manufacturer_lic_number',
                    'consumer_care', 'net_quantity', 'mrp', 'manufacture_date', 
                    'expiry_date', 'country_of_origin'
                ]
                
                filled_fields = 0
                for field in required_fields:
                    if field == 'consumer_care':
                        # Check if consumer_care has any contact info
                        care_data = structured_result.get(field, {})
                        if care_data and (care_data.get('contact_email') or care_data.get('contact_number')):
                            filled_fields += 1
                    else:
                        value = structured_result.get(field, '')
                        if value and value.lower() not in ['not found', 'not found on package', 'n/a', '']:
                            filled_fields += 1
                
                compliance_score = filled_fields / len(required_fields)
                
                return {
                    "relevant": True, 
                    "structured_data": structured_result,
                    "compliance_score": compliance_score,
                    "extraction_method": "structured_gemini"
                }
            else:
                print(f"[WARN] Structured analysis failed: {structured_result.get('error')}")
        except Exception as e:
            print(f"[WARN] Structured analysis error: {e}")

        # Fallback to regex-based extraction
        print(f"[INFO] Using fallback regex extraction...")
        extracted_fields = self.extract_fields_regex(ocr_text)

        if len(extracted_fields) < len(self.patterns):
            print("OCR incomplete, trying vision model...")
            vision_text = self.extract_with_vision_model(image_path)
            combined_text = f"{ocr_text}\n{vision_text}" if vision_text else ocr_text
            extracted_fields = self.extract_fields_regex(combined_text)

            missing_fields = [k for k in self.patterns.keys() if k not in extracted_fields]
            if missing_fields:
                print(f"Using LLM for missing fields: {missing_fields}")
                llm_results = self.extract_with_llm(combined_text, missing_fields)
                extracted_fields.update(llm_results)

        compliance = self.validate_compliance(extracted_fields)

        return {"relevant": True, "fields": extracted_fields, "compliance": compliance}


# Global instance for reuse
_checker_instance = None

def get_checker():
    """Get or create a global LegalMetrologyChecker instance"""
    global _checker_instance
    if _checker_instance is None:
        _checker_instance = LegalMetrologyChecker()
    return _checker_instance

def process_image(image_path):
    """
    Main function to extract Legal Metrology compliance data from product images.
    
    Args:
        image_path (str): Path to the image to process
        
    Returns:
        dict: Extracted data and compliance information
    """
    print(f"[INFO] Processing image: {image_path}")
    
    if not os.path.exists(image_path):
        return {
            "image_path": image_path,
            "error": "Image file not found",
            "compliance_score": 0.0
        }
    
    try:
        checker = get_checker()
        result = checker.process_image_internal(image_path)
        
        if not result.get("relevant", False):
            return {
                "image_path": image_path,
                "relevant": False,
                "message": result.get("message", "Image not relevant for compliance checking"),
                "compliance_score": 0.0
            }
        
        # Check if we got structured data
        if result.get("extraction_method") == "structured_gemini" and result.get("structured_data"):
            structured_data = result["structured_data"]
            
            # Create formatted data with structured information
            formatted_data = {
                "image_path": image_path,
                "product_name": structured_data.get("product_manufacturer", "N/A"),
                "manufacturer": structured_data.get("product_manufacturer", "N/A"),
                "net_quantity": structured_data.get("net_quantity", "N/A"),
                "mrp": structured_data.get("mrp", "N/A"),
                "manufacture_date": structured_data.get("manufacture_date", "N/A"),
                "best_before": structured_data.get("expiry_date", "N/A"),
                "country_origin": structured_data.get("country_of_origin", "N/A"),
                "customer_care": f"{structured_data.get('consumer_care', {}).get('contact_email', '')} | {structured_data.get('consumer_care', {}).get('contact_number', '')}".strip(' |'),
                "ingredients": structured_data.get("miscellaneous", {}).get("ingredients", "N/A"),
                "fssai_license": structured_data.get("manufacturer_lic_number", "N/A"),
                "compliance_score": result.get("compliance_score", 0.0),
                "structured_data": structured_data,  # Include the full structured data
                "extraction_method": "structured_gemini",
                "relevant": True
            }
            
            print(f"[INFO] Structured extraction complete. Compliance score: {formatted_data['compliance_score']:.2f}")
            return formatted_data
        
        # Fallback to regex-based extraction format
        fields = result.get("fields", {})
        compliance = result.get("compliance", {})
        
        # Extract key fields for compatibility
        formatted_data = {
            "image_path": image_path,
            "product_name": ", ".join(fields.get("Ingredients", ["N/A"])[:1]),  # Use first ingredient as product name fallback
            "manufacturer": ", ".join(fields.get("Manufacturer", ["N/A"])),
            "net_quantity": ", ".join(fields.get("Net_Weight", ["N/A"])),
            "mrp": ", ".join(fields.get("MRP", ["N/A"])),
            "manufacture_date": ", ".join(fields.get("Date", ["N/A"])),
            "best_before": ", ".join(fields.get("Date", ["N/A"])),  # Same as manufacture date for now
            "country_origin": ", ".join(fields.get("Country_Of_Origin", ["N/A"])),
            "customer_care": ", ".join(fields.get("Consumer_Care", ["N/A"])),
            "ingredients": ", ".join(fields.get("Ingredients", ["N/A"])),
            "fssai_license": ", ".join(fields.get("FSSAI_License", ["N/A"])),
            "nutritional_info": fields.get("Nutritional", ["N/A"]),
            "storage_instructions": ", ".join(fields.get("Storage", ["N/A"])),
            "allergen_info": ", ".join(fields.get("Allergen_Info", ["N/A"])),
            "certifications": ", ".join(fields.get("Certifications", ["N/A"])),
            "compliance_score": compliance.get("overall_score", 0.0),
            "all_extracted_fields": fields,
            "detailed_compliance": compliance,
            "relevant": True
        }
        
        print(f"[INFO] Extraction complete. Compliance score: {formatted_data['compliance_score']:.2f}")
        return formatted_data
        
    except Exception as e:
        print(f"[ERROR] Failed to process image {image_path}: {str(e)}")
        return {
            "image_path": image_path,
            "error": f"Processing failed: {str(e)}",
            "compliance_score": 0.0
        }
