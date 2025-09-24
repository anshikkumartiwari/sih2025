# Ocr module
import re
from typing import Dict, List

try:
    import easyocr  # type: ignore
except Exception:
    easyocr = None

# Optional CV imports for preprocessing
try:
    import cv2  # type: ignore
    import numpy as np  # type: ignore
except Exception:
    cv2 = None
    np = None


FIELD_REGEX: Dict[str, str] = {
    "mrp": r"(?:M\.?R\.?P|MRP|Maximum\s*Retail\s*Price|MRP\s*Incl\.?\s*of\s*all\s*taxes)\s*[:₹Rs\.\s]*([0-9]+(?:\.[0-9]{1,2})?)",
    "quantity": r"(?:NET\s*WEIGHT|Net\s*Quantity|Net\s*Wt|Net\s*Weight|Quantity|Weight)\s*[:.]*\s*(\d+(?:\.\d+)?)\s*(g|kg|ml|l|L|pcs?|pack|pieces?|grams?)",
    "manufacturer": r"(?:MARKETED\s*BY|MANUFACTURED\s*BY|Manufacturer|Mfg\s*by|Packed\s*by|Packer|Importer|MFD\.?\s*BY)\s*:?\s*([^,\n]+(?:LIMITED|LTD|PVT|PRIVATE|CORP|CORPORATION)?[^,\n]*)",
    "origin": r"(?:Country\s*of\s*Origin|Made\s*in|Origin|COUNTRY\s*OF\s*ORIGIN)\s*:?\s*([^,\n]+)",
    "support": r"(?:FOR\s*FEEDBACK|Consumer\s*Care|Customer\s*Care|Helpline|Email|Phone|Contact|ITC\s*CARES)\s*:?\s*([^,\n@]+@[^,\n]+|[^,\n]*\d{10,}[^,\n]*)",
    "dates": r"(?:PKD\.?/BATCH|USE\s*BY|Mfg|Exp|Best\s*Before|Use\s*By|Manufacturing|Expiry|PACKED|BATCH)\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|[A-Z0-9]+)",
    "batch": r"(?:PKD\.?/BATCH|Batch|Lot|BATCH)\s*:?\s*([A-Z0-9]+)",
    "license": r"(?:FSSAI|License|Lic\.?|Lic\.?\s*No\.?|Lic\s*No|FSSAI\s*Lic|Food\s*Safety|Registration|Reg\s*No)\s*:?\s*([0-9]+)",
    "barcode": r"(?:Barcode|EAN|UPC|QR\s*Code)\s*:?\s*([0-9]+)",
    # Additional patterns for specific data we can see
    "net_weight_detailed": r"NET\s*WEIGHT:\s*(\d+(?:\.\d+)?)\s*(g|kg|ml|l|L|pcs?|pack|pieces?|grams?)\s*\((\d+)\s*PACKS?\s*X\s*(\d+(?:\.\d+)?)\s*(g|kg|ml|l|L|pcs?|pack|pieces?|grams?)\)",
    "fssai_license": r"(?:Lic\.?\s*No\.?|Lic\s*No|FSSAI\s*Lic|Food\s*Safety)\s*:?\s*([0-9]+)",
    "contact_email": r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
    "contact_phone": r"(1800\s*\d{3}\s*\d{3}\s*\d{3}|\d{10,})",
    "address": r"(?:MARKETED\s*BY|MFD\.?\s*BY)\s*[^:]*:\s*([^,\n]+(?:LIMITED|LTD)[^,\n]*)",
    # Edge cases for FSSAI and license numbers
    "fssai_edge_cases": r"(?:FSSAI|Lic|License|Reg|Registration)\s*:?\s*([0-9]{8,})",
    "long_numbers": r"([0-9]{10,})",  # Any 10+ digit number
    "license_variants": r"(?:Lic\.?\s*No\.?\s*|Lic\s*No\s*|License\s*No\.?\s*|Reg\.?\s*No\.?\s*)([0-9]+)",
    "near_fssai": r"(?:FSSAI|Food\s*Safety)\s*[^0-9]*([0-9]{8,})",  # Numbers near FSSAI keywords
}


def _reader():
    if easyocr is None:
        raise RuntimeError("easyocr is not installed. Please add 'easyocr' to requirements and install it.")
    return easyocr.Reader(["en"])  # init English reader


def _preprocess_image(path: str):
    """Return multiple preprocessed variants for better OCR, or [] if CV is unavailable."""
    if cv2 is None or np is None:
        return []
    try:
        img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            return []
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # CLAHE for contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        eq = clahe.apply(gray)
        # Denoise then sharpen
        den = cv2.bilateralFilter(eq, d=7, sigmaColor=75, sigmaSpace=75)
        # Unsharp mask
        blur = cv2.GaussianBlur(den, (0, 0), 2.0)
        sharp = cv2.addWeighted(den, 1.6, blur, -0.6, 0)
        # Adaptive threshold variant
        thr = cv2.adaptiveThreshold(eq, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 15)
        # Scale up variant
        h, w = sharp.shape[:2]
        scale2 = cv2.resize(sharp, (int(w * 1.5), int(h * 1.5)), interpolation=cv2.INTER_CUBIC)
        return [sharp, thr, scale2]
    except Exception:
        return []


def _extract_fssai_numbers(text: str) -> List[str]:
    """Extract potential FSSAI numbers using multiple strategies."""
    candidates = []
    
    # Strategy 1: Direct FSSAI patterns
    fssai_patterns = [
        r"FSSAI\s*:?\s*([0-9]+)",
        r"Lic\.?\s*No\.?\s*:?\s*([0-9]+)",
        r"License\s*No\.?\s*:?\s*([0-9]+)",
        r"Food\s*Safety\s*:?\s*([0-9]+)",
        r"Registration\s*No\.?\s*:?\s*([0-9]+)",
    ]
    
    for pattern in fssai_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        candidates.extend(matches)
    
    # Strategy 2: Look for numbers near FSSAI keywords (within 50 chars)
    fssai_context = re.finditer(r"FSSAI|Lic|License|Food\s*Safety|Registration", text, re.IGNORECASE)
    for match in fssai_context:
        start = max(0, match.start() - 25)
        end = min(len(text), match.end() + 25)
        context = text[start:end]
        numbers = re.findall(r"([0-9]{8,})", context)
        candidates.extend(numbers)
    
    # Strategy 3: Find all 8+ digit numbers and check context
    long_numbers = re.findall(r"([0-9]{8,})", text)
    for num in long_numbers:
        # Find the position of this number in text
        pos = text.find(num)
        if pos != -1:
            # Check 50 chars before and after for FSSAI-related keywords
            start = max(0, pos - 50)
            end = min(len(text), pos + len(num) + 50)
            context = text[start:end]
            if re.search(r"FSSAI|Lic|License|Food\s*Safety|Registration", context, re.IGNORECASE):
                candidates.append(num)
    
    # Remove duplicates and return
    return list(set(candidates))


def extract_fields_from_images(image_paths: List[str]) -> Dict[str, object]:
    """Run OCR on given images and extract LM-relevant fields using regexes.

    Returns a dictionary with extracted fields and comprehensive compliance analysis.
    """
    if not image_paths:
        return {"extracted_text": "", "fields": {}, "compliance": {}, "missing": [], "warnings": []}

    reader = _reader()
    texts: List[str] = []
    for p in image_paths:
        try:
            # Check file size first
            import os
            if os.path.getsize(p) < 10000:  # Skip very small files
                print(f"[DEBUG] Skipping small image for OCR: {p}")
                continue
            
            # Run OCR on original
            results = reader.readtext(p, detail=1)
            variants_text: List[str] = []
            for (bbox, text, confidence) in results:
                if confidence >= 0.25:
                    variants_text.append(text)
            
            # Run OCR on preprocessed variants
            for variant in _preprocess_image(p):
                try:
                    v_results = reader.readtext(variant, detail=1)
                    for (_b, v_text, v_conf) in v_results:
                        if v_conf >= 0.25:
                            variants_text.append(v_text)
                except Exception:
                    continue
            
            if variants_text:
                joined = " \n".join(variants_text)
                texts.append(joined)
                print(f"[DEBUG] OCR extracted {len(variants_text)} text blocks from {p} (with preprocessing)")
        except Exception as e:
            print(f"[DEBUG] OCR failed for {p}: {e}")
            continue

    merged = " \n".join(texts)
    print(f"[DEBUG] Total OCR text length: {len(merged)} characters")
    print(f"[DEBUG] OCR text preview: {merged[:500]}...")
    
    fields: Dict[str, object] = {}

    # Clean and normalize text for better matching
    cleaned_text = re.sub(r'\s+', ' ', merged)  # Normalize whitespace
    cleaned_text = re.sub(r'[^\w\s₹.,:/-]', ' ', cleaned_text)  # Remove special chars except essential ones
    
    # Extract with regex patterns - prioritize FSSAI/license detection
    fssai_candidates = []
    
    for key, regex in FIELD_REGEX.items():
        # Try both original and cleaned text
        for text_source in [merged, cleaned_text]:
            m = re.search(regex, text_source, re.IGNORECASE)
            if m:
                if key in ("mrp",):
                    fields[key] = f"₹{m.group(1)}"
                elif key in ("quantity",):
                    fields[key] = f"{m.group(1)} {m.group(2)}".strip()
                elif key in ("net_weight_detailed",):
                    # Extract detailed net weight info
                    total_weight = f"{m.group(1)} {m.group(2)}"
                    packs = m.group(3)
                    pack_weight = f"{m.group(4)} {m.group(5)}"
                    fields["quantity"] = f"{total_weight} ({packs} PACKS X {pack_weight})"
                elif key in ("dates",):
                    fields[key] = {"label": m.group(1), "date": m.group(2)}
                elif key in ("contact_email",):
                    fields["support"] = m.group(1)
                elif key in ("contact_phone",):
                    if "support" not in fields:
                        fields["support"] = m.group(1)
                    else:
                        fields["support"] += f", {m.group(1)}"
                elif key in ("fssai_license", "fssai_edge_cases", "license_variants", "near_fssai"):
                    # Collect all FSSAI/license candidates
                    fssai_candidates.append(m.group(1).strip())
                elif key in ("long_numbers",):
                    # Check if this long number could be FSSAI (8+ digits)
                    num = m.group(1).strip()
                    if len(num) >= 8:
                        fssai_candidates.append(num)
                elif key in ("address",):
                    if "manufacturer" not in fields:
                        fields["manufacturer"] = m.group(1)
                else:
                    fields[key] = m.group(1).strip() if m.groups() else m.group(0).strip()
                print(f"[DEBUG] Extracted {key}: {fields.get(key, 'N/A')}")
                break
    
    # Enhanced FSSAI detection using specialized function
    fssai_specialized = _extract_fssai_numbers(merged)
    if fssai_specialized:
        fssai_candidates.extend(fssai_specialized)
        print(f"[DEBUG] Specialized FSSAI detection found: {fssai_specialized}")
    
    # Process FSSAI candidates - pick the most likely one
    if fssai_candidates:
        # Remove duplicates and sort by length (longer numbers more likely to be FSSAI)
        unique_candidates = list(set(fssai_candidates))
        unique_candidates.sort(key=len, reverse=True)
        
        # Prefer 8+ digit numbers for FSSAI
        for candidate in unique_candidates:
            if len(candidate) >= 8:
                fields["license"] = candidate
                print(f"[DEBUG] Selected FSSAI license from candidates: {candidate}")
                break
        else:
            # If no 8+ digit number, take the longest one
            if unique_candidates:
                fields["license"] = unique_candidates[0]
                print(f"[DEBUG] Selected longest candidate as license: {unique_candidates[0]}")
    
    # Additional fallback extractions for common patterns
    if "quantity" not in fields:
        # Try to find any weight/quantity pattern
        weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(g|kg|ml|l|L|pcs?|pack|pieces?|grams?)', merged, re.IGNORECASE)
        if weight_match:
            fields["quantity"] = f"{weight_match.group(1)} {weight_match.group(2)}"
            print(f"[DEBUG] Fallback extracted quantity: {fields['quantity']}")
    
    if "manufacturer" not in fields:
        # Try to find company names
        company_match = re.search(r'(ITC\s*LIMITED|LIMITED|LTD|PVT|PRIVATE|CORP)', merged, re.IGNORECASE)
        if company_match:
            fields["manufacturer"] = company_match.group(0)
            print(f"[DEBUG] Fallback extracted manufacturer: {fields['manufacturer']}")
    
    if "support" not in fields:
        # Try to find email or phone
        email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', merged)
        phone_match = re.search(r'(1800\s*\d{3}\s*\d{3}\s*\d{3})', merged)
        if email_match:
            fields["support"] = email_match.group(1)
        elif phone_match:
            fields["support"] = phone_match.group(1)
        if "support" in fields:
            print(f"[DEBUG] Fallback extracted support: {fields['support']}")

    # Comprehensive compliance analysis
    required_fields = {
        "mrp": "Maximum Retail Price (₹)",
        "quantity": "Net Quantity/Weight", 
        "manufacturer": "Manufacturer/Packer Name",
        "origin": "Country of Origin"
    }
    
    optional_fields = {
        "support": "Consumer Care Contact",
        "dates": "Manufacturing/Expiry Date",
        "batch": "Batch/Lot Number",
        "license": "FSSAI License Number",
        "barcode": "Product Barcode"
    }
    
    compliance = {}
    missing = []
    warnings = []
    
    # Check required fields
    for field, label in required_fields.items():
        present = bool(fields.get(field))
        compliance[field] = present
        if not present:
            missing.append(label)
    
    # Check optional fields
    for field, label in optional_fields.items():
        present = bool(fields.get(field))
        compliance[field] = present
        if not present:
            warnings.append(f"Optional: {label}")
    
    # Additional validation rules
    if fields.get("mrp"):
        try:
            mrp_val = float(str(fields["mrp"]).replace("₹", "").replace(",", ""))
            if mrp_val <= 0:
                warnings.append("MRP should be positive")
        except:
            warnings.append("MRP format may be invalid")
    
    if fields.get("quantity"):
        qty_str = str(fields["quantity"]).lower()
        if not any(unit in qty_str for unit in ["g", "kg", "ml", "l", "pcs", "pack"]):
            warnings.append("Quantity unit may be missing or invalid")
    
    return {
        "extracted_text": merged, 
        "fields": fields, 
        "compliance": compliance,
        "missing": missing,
        "warnings": warnings,
        "summary": {
            "total_fields_found": len([f for f in fields.values() if f]),
            "required_present": len([f for f in required_fields.keys() if compliance.get(f)]),
            "required_total": len(required_fields),
            "compliance_score": f"{len([f for f in required_fields.keys() if compliance.get(f)])}/{len(required_fields)}"
        }
    }

