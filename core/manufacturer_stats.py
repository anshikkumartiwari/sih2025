"""
Manufacturer Statistics and Logging Module
Tracks compliance scores by manufacturer with simple list format
"""

import os
import json
import re
from typing import Dict, List, Optional

STAT_DIR = os.path.join("stat")
MANUFACTURER_LOG_FILE = os.path.join(STAT_DIR, "manufacturer_compliance.json")

# Ensure stat directory exists
os.makedirs(STAT_DIR, exist_ok=True)


def normalize_manufacturer_name(name: str) -> str:
    """
    Normalize manufacturer name for comparison
    - Convert to lowercase
    - Remove common business suffixes and punctuation
    """
    if not name:
        return ""
    
    # Convert to lowercase and strip
    normalized = name.lower().strip()
    
    # Remove common business suffixes
    suffixes = [
        'ltd', 'limited', 'inc', 'incorporated', 'corp', 'corporation', 
        'pvt', 'private', 'co', 'company', 'llc', 'llp', 'gmbh'
    ]
    
    for suffix in suffixes:
        # Remove suffix patterns like "ltd.", "ltd,", "ltd "
        normalized = re.sub(rf'\b{suffix}\.?\,?\s*$', '', normalized)
    
    # Remove extra punctuation and whitespace
    normalized = re.sub(r'[,\.\-\(\)]+', ' ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized


def get_first_word(manufacturer_name: str) -> str:
    """
    Extract the first significant word from manufacturer name
    """
    normalized = normalize_manufacturer_name(manufacturer_name)
    words = normalized.split()
    
    # Skip common prefixes like "the", "m/s", "shri", etc.
    skip_words = {'the', 'm/s', 'shri', 'sri', 'mr', 'mrs', 'dr'}
    
    for word in words:
        if word not in skip_words and len(word) > 2:
            return word
    
    # If no significant word found, return first word
    return words[0] if words else ""


def find_similar_manufacturer(manufacturer_name: str, existing_manufacturers: List[str]) -> Optional[str]:
    """
    Find if a similar manufacturer already exists based on first word fuzzy matching
    """
    if not manufacturer_name or not existing_manufacturers:
        return None
    
    target_first_word = get_first_word(manufacturer_name)
    
    # Check for first word match (primary method)
    for existing in existing_manufacturers:
        existing_first_word = get_first_word(existing)
        if target_first_word and existing_first_word and target_first_word == existing_first_word:
            print(f"[DEBUG] First word match found: '{target_first_word}' -> {existing}")
            return existing
    
    return None


def load_manufacturer_logs() -> Dict[str, List[int]]:
    """
    Load existing manufacturer compliance logs from file
    Returns: Dict with manufacturer names as keys and list of scores as values
    """
    try:
        if os.path.exists(MANUFACTURER_LOG_FILE):
            with open(MANUFACTURER_LOG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"[WARN] Failed to load manufacturer logs: {e}")
    
    return {}


def save_manufacturer_logs(logs: Dict[str, List[int]]) -> None:
    """
    Save manufacturer compliance logs to file
    """
    try:
        with open(MANUFACTURER_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
        print(f"[DEBUG] Saved manufacturer logs to {MANUFACTURER_LOG_FILE}")
    except Exception as e:
        print(f"[ERROR] Failed to save manufacturer logs: {e}")


def extract_score_number(compliance_score: str) -> int:
    """
    Extract numerical score from compliance_score string like "3/4" -> 3
    """
    try:
        if "/" in compliance_score:
            numerator = compliance_score.split("/")[0].strip()
            return int(float(numerator))
        else:
            return int(float(compliance_score))
    except:
        return 0


def log_manufacturer_compliance(manufacturer_name: str, compliance_data: Dict) -> None:
    """
    Log compliance score for a manufacturer
    
    Args:
        manufacturer_name: Name of the manufacturer
        compliance_data: Dictionary containing compliance information
                        Expected keys: compliance_score
    """
    if not manufacturer_name:
        print("[WARN] No manufacturer name provided for logging")
        return
    
    # Load existing logs
    logs = load_manufacturer_logs()
    
    # Find if manufacturer already exists (fuzzy match based on first word)
    existing_manufacturers = list(logs.keys())
    similar_manufacturer = find_similar_manufacturer(manufacturer_name, existing_manufacturers)
    
    # Use existing manufacturer key or create new one
    manufacturer_key = similar_manufacturer if similar_manufacturer else manufacturer_name
    
    # Extract score number
    compliance_score = compliance_data.get("compliance_score", "0/0")
    score_number = extract_score_number(compliance_score)
    
    # Initialize or update manufacturer entry
    if manufacturer_key not in logs:
        logs[manufacturer_key] = []
        print(f"[DEBUG] Created new manufacturer log: {manufacturer_key}")
    else:
        print(f"[DEBUG] Adding to existing manufacturer log: {manufacturer_key}")
    
    # Append the score
    logs[manufacturer_key].append(score_number)
    
    # Save updated logs
    save_manufacturer_logs(logs)
    
    # Log summary
    total_scores = len(logs[manufacturer_key])
    avg_score = sum(logs[manufacturer_key]) / total_scores if total_scores > 0 else 0
    print(f"[INFO] Manufacturer '{manufacturer_key}': {total_scores} analyses, avg score: {avg_score:.1f}")


def get_manufacturer_trend_data(manufacturer_name: str) -> Dict:
    """
    Get trend data for a specific manufacturer for graphing
    
    Returns:
        Dictionary with trend data including scores, labels, and statistics
    """
    logs = load_manufacturer_logs()
    
    # Find similar manufacturer
    existing_manufacturers = list(logs.keys())
    similar_manufacturer = find_similar_manufacturer(manufacturer_name, existing_manufacturers)
    manufacturer_key = similar_manufacturer if similar_manufacturer else manufacturer_name
    
    scores = logs.get(manufacturer_key, [])
    
    if not scores:
        return {
            "manufacturer": manufacturer_name,
            "has_data": False,
            "scores": [],
            "labels": [],
            "statistics": {}
        }
    
    # Create labels for each analysis
    labels = [f"Analysis {i+1}" for i in range(len(scores))]
    
    # Calculate statistics
    avg_score = sum(scores) / len(scores)
    min_score = min(scores)
    max_score = max(scores)
    
    # Calculate trend (simple linear trend)
    if len(scores) >= 2:
        # Simple trend calculation: compare last 3 vs first 3 (or all if less)
        recent_count = min(3, len(scores))
        early_count = min(3, len(scores))
        
        recent_avg = sum(scores[-recent_count:]) / recent_count
        early_avg = sum(scores[:early_count]) / early_count
        
        trend = "improving" if recent_avg > early_avg else "declining" if recent_avg < early_avg else "stable"
        trend_percentage = ((recent_avg - early_avg) / early_avg * 100) if early_avg > 0 else 0
    else:
        trend = "stable"
        trend_percentage = 0
    
    return {
        "manufacturer": manufacturer_key,
        "has_data": True,
        "scores": scores,
        "labels": labels,
        "statistics": {
            "total_analyses": len(scores),
            "average_score": round(avg_score, 1),
            "min_score": min_score,
            "max_score": max_score,
            "trend": trend,
            "trend_percentage": round(trend_percentage, 1)
        }
    }


def get_manufacturer_statistics(manufacturer_name: str = None) -> Dict:
    """
    Get statistics for a specific manufacturer or all manufacturers
    """
    logs = load_manufacturer_logs()
    
    if manufacturer_name:
        # Find similar manufacturer
        existing_manufacturers = list(logs.keys())
        similar_manufacturer = find_similar_manufacturer(manufacturer_name, existing_manufacturers)
        manufacturer_key = similar_manufacturer if similar_manufacturer else manufacturer_name
        
        scores = logs.get(manufacturer_key, [])
        if scores:
            return {
                "manufacturer": manufacturer_key,
                "scores": scores,
                "total_analyses": len(scores),
                "average_score": sum(scores) / len(scores),
                "min_score": min(scores),
                "max_score": max(scores)
            }
        else:
            return {"manufacturer": manufacturer_name, "scores": [], "total_analyses": 0}
    
    # Return summary statistics for all manufacturers
    summary = {
        "total_manufacturers": len(logs),
        "total_analyses": sum(len(scores) for scores in logs.values()),
        "manufacturers": {}
    }
    
    for manufacturer, scores in logs.items():
        if scores:
            summary["manufacturers"][manufacturer] = {
                "total_analyses": len(scores),
                "average_score": sum(scores) / len(scores),
                "scores": scores
            }
    
    return summary


# Test function
def test_manufacturer_logging():
    """
    Test the simplified manufacturer logging functionality
    """
    print("Testing simplified manufacturer logging system...")
    
    # Test data
    test_data = [
        ("Kellogg Pvt Ltd", "2/4"),
        ("Kellogg Corp", "3/4"),  # Should match with Kellogg
        ("Sunfeast Pvt Ltd", "4/4"),
        ("Sunfeast Company", "3/4"),  # Should match with Sunfeast
        ("Britannia Industries", "2/4"),
        ("Parle Products", "3/4"),
        ("Sunfeast Ltd", "5/4"),  # Should match with Sunfeast
    ]
    
    for manufacturer, score in test_data:
        print(f"\nTesting: {manufacturer} with score {score}")
        log_manufacturer_compliance(manufacturer, {"compliance_score": score})
    
    # Get statistics
    stats = get_manufacturer_statistics()
    print(f"\nFinal simplified logs:")
    print(json.dumps(load_manufacturer_logs(), indent=2, ensure_ascii=False))
    
    print(f"\nStatistics:")
    print(f"Total manufacturers: {stats['total_manufacturers']}")
    print(f"Total analyses: {stats['total_analyses']}")


if __name__ == "__main__":
    test_manufacturer_logging()