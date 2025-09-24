# Vision module
import re
from typing import List, Tuple, Dict

try:
    import easyocr  # type: ignore
except Exception:
    easyocr = None  # lazy import fallback


PATTERNS: Dict[str, str] = {
    "Manufacturer": r"MARKETED\s*BY|MANUFACTURED\s*BY|Manufacturer|Mfg\s*by|Packed\s*by|Importer|Address|MFD\.?\s*BY|ITC\s*LIMITED",
    "Net Weight": r"NET\s*WEIGHT|Net\s*quantity|Net\s*(Wt|Weight).*?\d+\s*(g|kg|ml|l|grams?)",
    "MRP": r"M\.?R\.?P|MRP|Rs\.?\s*\d+|MRP\s*Incl\.?\s*of\s*all\s*taxes",
    "ConsumerCare": r"FOR\s*FEEDBACK|Consumer\s*Care|Customer\s*Care|Helpline|Email|ITC\s*CARES|1800\s*\d+",
    "Date": r"PKD\.?/BATCH|USE\s*BY|(Mfg|Exp|Best\s*Before|Use\s*By).*?\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
    "CountryOfOrigin": r"Country\s*of\s*Origin|Made\s*in|COUNTRY\s*OF\s*ORIGIN",
    "FSSAI": r"FSSAI|Lic\.?\s*No\.?|License|10012031000312|10012012000154|Lic\s*No|FSSAI\s*Lic|Food\s*Safety|Registration|Reg\s*No",
    "Nutritional": r"NUTRITIONAL\s*INFORMATION|Energy|Protein|Carbohydrate|Fat|kcal",
    "Ingredients": r"INGREDIENTS|REFINED\s*WHEAT\s*FLOUR|SUGAR|MILK\s*CHOCO",
    "Numbers": r"\d{10,}|[0-9]{4,}\s*[0-9]{4,}|Lic\s*[0-9]+|No\s*[0-9]+"
}


def _get_reader(languages: List[str] = None):
    if languages is None:
        languages = ["en"]
    if easyocr is None:
        raise RuntimeError("easyocr is not installed. Please add 'easyocr' to requirements and install it.")
    return easyocr.Reader(languages)


def score_image_for_label_text(reader, image_path: str) -> Tuple[int, List[str], str]:
    """Return a score for how likely an image contains declaration text.

    Score = number of matched pattern categories. Also returns matched names and
    normalized extracted text for downstream use.
    """
    try:
        # Check file size first - skip very small images
        import os
        file_size = os.path.getsize(image_path)
        if file_size < 10000:  # Less than 10KB likely low quality
            return 0, [], ""
        
        results = reader.readtext(image_path, detail=0)
        extracted_text = " ".join(results)
        
        # Quality checks on extracted text
        if len(extracted_text.strip()) < 10:  # Too little text
            return 0, [], extracted_text
            
        # Check for readable text quality indicators
        readable_chars = sum(1 for c in extracted_text if c.isalnum() or c in ' .,:₹-/')
        total_chars = len(extracted_text)
        readability_ratio = readable_chars / total_chars if total_chars > 0 else 0
        
        if readability_ratio < 0.5:  # Too much garbled text
            return 0, [], extracted_text
        
        matched = []
        for name, pattern in PATTERNS.items():
            if re.search(pattern, extracted_text, re.IGNORECASE):
                matched.append(name)
        
        # Use raw match count as score; quality bonus is informative only
        final_score = len(matched)
        
        return final_score, matched, extracted_text
    except Exception as e:
        print(f"[DEBUG] OCR scoring failed for {image_path}: {e}")
        return 0, [], ""


def select_best_label_images(image_paths: List[str], min_matches: int = 3, max_images: int = 1) -> Tuple[List[str], Dict[str, dict]]:
    """Filter and rank candidate images containing declarations.

    Returns (selected_image_paths, debug_info_by_path)
    """
    if not image_paths:
        return [], {}

    reader = _get_reader(["en"])  # initialize once
    scored: List[Tuple[str, int, List[str], str]] = []
    debug: Dict[str, dict] = {}
    for p in image_paths:
        try:
            score, matched, text = score_image_for_label_text(reader, p)
            scored.append((p, score, matched, text))
            debug[p] = {"score": score, "matched": matched, "text_preview": text[:200] + "..." if len(text) > 200 else text}
        except Exception as e:
            debug[p] = {"error": str(e)}

    # Sort by score desc, then by path for stability
    scored.sort(key=lambda t: (-t[1], t[0]))
    selected = [p for (p, score, _m, _t) in scored if score >= min_matches][:max_images]
    return selected, debug

