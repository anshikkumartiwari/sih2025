# Manufacturer Compliance Tracking System
import os
import json
import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict

MANUFACTURER_DATA_DIR = os.path.join("temp", "manufacturer_data")
os.makedirs(MANUFACTURER_DATA_DIR, exist_ok=True)

def normalize_manufacturer_name(name: str) -> str:
    """Normalize manufacturer name for consistent storage."""
    if not name:
        return "Unknown"
    
    # Clean and normalize the name
    normalized = name.strip().title()
    
    # Remove common suffixes and prefixes
    suffixes = ["Ltd", "Limited", "Pvt", "Private", "Inc", "Corp", "Corporation", "Co", "Company"]
    for suffix in suffixes:
        if normalized.endswith(f" {suffix}"):
            normalized = normalized[:-len(f" {suffix}")]
    
    return normalized

def get_manufacturer_file_path(manufacturer_name: str) -> str:
    """Get file path for manufacturer data."""
    safe_name = manufacturer_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
    return os.path.join(MANUFACTURER_DATA_DIR, f"{safe_name}.json")

def load_manufacturer_data(manufacturer_name: str) -> Dict[str, Any]:
    """Load existing manufacturer data."""
    file_path = get_manufacturer_file_path(manufacturer_name)
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load manufacturer data for {manufacturer_name}: {e}")
    
    # Return default structure for new manufacturer
    return {
        "manufacturer_name": manufacturer_name,
        "total_products": 0,
        "compliance_history": [],
        "compliance_stats": {
            "total_scans": 0,
            "compliant_scans": 0,
            "non_compliant_scans": 0,
            "average_compliance_score": 0.0,
            "required_fields_compliance": {
                "mrp": {"present": 0, "missing": 0, "percentage": 0.0},
                "quantity": {"present": 0, "missing": 0, "percentage": 0.0},
                "manufacturer": {"present": 0, "missing": 0, "percentage": 0.0},
                "origin": {"present": 0, "missing": 0, "percentage": 0.0}
            },
            "optional_fields_compliance": {
                "support": {"present": 0, "missing": 0, "percentage": 0.0},
                "dates": {"present": 0, "missing": 0, "percentage": 0.0},
                "batch": {"present": 0, "missing": 0, "percentage": 0.0},
                "license": {"present": 0, "missing": 0, "percentage": 0.0},
                "barcode": {"present": 0, "missing": 0, "percentage": 0.0}
            }
        },
        "product_categories": {},
        "recent_products": [],
        "last_updated": None
    }

def save_manufacturer_data(manufacturer_data: Dict[str, Any]) -> bool:
    """Save manufacturer data to file."""
    try:
        file_path = get_manufacturer_file_path(manufacturer_data["manufacturer_name"])
        manufacturer_data["last_updated"] = datetime.datetime.now().isoformat()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(manufacturer_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save manufacturer data: {e}")
        return False

def categorize_product(compliance_data: Dict[str, Any]) -> str:
    """Categorize product based on compliance data."""
    # Extract product information for categorization
    title = compliance_data.get("title", "").lower()
    manufacturer = compliance_data.get("manufacturer", "").lower()
    
    # Basic categorization logic - can be enhanced
    if any(word in title for word in ["food", "snack", "biscuit", "chocolate", "drink", "beverage"]):
        return "Food & Beverages"
    elif any(word in title for word in ["medicine", "tablet", "capsule", "syrup", "cream", "ointment"]):
        return "Pharmaceuticals"
    elif any(word in title for word in ["cosmetic", "cream", "lotion", "shampoo", "soap", "beauty"]):
        return "Cosmetics"
    elif any(word in title for word in ["electronic", "phone", "charger", "cable", "device"]):
        return "Electronics"
    elif any(word in title for word in ["clothing", "shirt", "dress", "fabric", "textile"]):
        return "Textiles"
    else:
        return "General Products"

def update_manufacturer_compliance(compliance_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update manufacturer compliance data with new product scan."""
    manufacturer_name = compliance_data.get("manufacturer", "Unknown")
    normalized_name = normalize_manufacturer_name(manufacturer_name)
    
    # Load existing data
    manufacturer_data = load_manufacturer_data(normalized_name)
    
    # Update basic stats
    manufacturer_data["total_products"] += 1
    manufacturer_data["compliance_stats"]["total_scans"] += 1
    
    # Extract compliance information
    compliance = compliance_data.get("compliance", {})
    compliance_summary = compliance_data.get("compliance_summary", {})
    
    # Calculate compliance score
    required_present = compliance_summary.get("required_present", 0)
    required_total = compliance_summary.get("required_total", 4)
    compliance_score = required_present / required_total if required_total > 0 else 0
    
    # Update compliance history
    compliance_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "product_title": compliance_data.get("title", "Unknown Product"),
        "compliance_score": compliance_score,
        "required_fields_present": required_present,
        "required_fields_total": required_total,
        "missing_fields": compliance_data.get("missing_fields", []),
        "warnings": compliance_data.get("warnings", []),
        "url": compliance_data.get("url", ""),
        "category": categorize_product(compliance_data)
    }
    
    manufacturer_data["compliance_history"].append(compliance_entry)
    
    # Keep only last 100 entries to prevent file bloat
    if len(manufacturer_data["compliance_history"]) > 100:
        manufacturer_data["compliance_history"] = manufacturer_data["compliance_history"][-100:]
    
    # Update compliance statistics
    if compliance_score >= 0.75:  # 75% or higher compliance
        manufacturer_data["compliance_stats"]["compliant_scans"] += 1
    else:
        manufacturer_data["compliance_stats"]["non_compliant_scans"] += 1
    
    # Update average compliance score
    total_scans = manufacturer_data["compliance_stats"]["total_scans"]
    current_avg = manufacturer_data["compliance_stats"]["average_compliance_score"]
    manufacturer_data["compliance_stats"]["average_compliance_score"] = (
        (current_avg * (total_scans - 1) + compliance_score) / total_scans
    )
    
    # Update field-specific compliance stats
    required_fields = ["mrp", "quantity", "manufacturer", "origin"]
    optional_fields = ["support", "dates", "batch", "license", "barcode"]
    
    for field in required_fields:
        if compliance.get(field, False):
            manufacturer_data["compliance_stats"]["required_fields_compliance"][field]["present"] += 1
        else:
            manufacturer_data["compliance_stats"]["required_fields_compliance"][field]["missing"] += 1
        
        # Update percentage
        total = (manufacturer_data["compliance_stats"]["required_fields_compliance"][field]["present"] + 
                manufacturer_data["compliance_stats"]["required_fields_compliance"][field]["missing"])
        if total > 0:
            manufacturer_data["compliance_stats"]["required_fields_compliance"][field]["percentage"] = (
                manufacturer_data["compliance_stats"]["required_fields_compliance"][field]["present"] / total * 100
            )
    
    for field in optional_fields:
        if compliance.get(field, False):
            manufacturer_data["compliance_stats"]["optional_fields_compliance"][field]["present"] += 1
        else:
            manufacturer_data["compliance_stats"]["optional_fields_compliance"][field]["missing"] += 1
        
        # Update percentage
        total = (manufacturer_data["compliance_stats"]["optional_fields_compliance"][field]["present"] + 
                manufacturer_data["compliance_stats"]["optional_fields_compliance"][field]["missing"])
        if total > 0:
            manufacturer_data["compliance_stats"]["optional_fields_compliance"][field]["percentage"] = (
                manufacturer_data["compliance_stats"]["optional_fields_compliance"][field]["present"] / total * 100
            )
    
    # Update product categories
    category = categorize_product(compliance_data)
    if category not in manufacturer_data["product_categories"]:
        manufacturer_data["product_categories"][category] = {
            "total_products": 0,
            "compliant_products": 0,
            "average_compliance_score": 0.0
        }
    
    manufacturer_data["product_categories"][category]["total_products"] += 1
    if compliance_score >= 0.75:
        manufacturer_data["product_categories"][category]["compliant_products"] += 1
    
    # Update category average compliance score
    cat_total = manufacturer_data["product_categories"][category]["total_products"]
    cat_current_avg = manufacturer_data["product_categories"][category]["average_compliance_score"]
    manufacturer_data["product_categories"][category]["average_compliance_score"] = (
        (cat_current_avg * (cat_total - 1) + compliance_score) / cat_total
    )
    
    # Update recent products (keep last 10)
    recent_product = {
        "title": compliance_data.get("title", "Unknown Product"),
        "compliance_score": compliance_score,
        "timestamp": datetime.datetime.now().isoformat(),
        "category": category,
        "url": compliance_data.get("url", "")
    }
    
    manufacturer_data["recent_products"].insert(0, recent_product)
    if len(manufacturer_data["recent_products"]) > 10:
        manufacturer_data["recent_products"] = manufacturer_data["recent_products"][:10]
    
    # Save updated data
    save_manufacturer_data(manufacturer_data)
    
    return manufacturer_data

def get_all_manufacturers() -> List[Dict[str, Any]]:
    """Get list of all manufacturers with basic stats."""
    manufacturers = []
    
    for filename in os.listdir(MANUFACTURER_DATA_DIR):
        if filename.endswith('.json'):
            manufacturer_name = filename[:-5].replace("_", " ")
            try:
                data = load_manufacturer_data(manufacturer_name)
                manufacturers.append({
                    "name": manufacturer_name,
                    "total_products": data["total_products"],
                    "average_compliance_score": data["compliance_stats"]["average_compliance_score"],
                    "total_scans": data["compliance_stats"]["total_scans"],
                    "last_updated": data.get("last_updated"),
                    "categories": list(data["product_categories"].keys())
                })
            except Exception as e:
                print(f"[ERROR] Failed to load manufacturer {manufacturer_name}: {e}")
    
    # Sort by total products (most active first)
    manufacturers.sort(key=lambda x: x["total_products"], reverse=True)
    return manufacturers

def get_manufacturer_analytics(manufacturer_name: str) -> Dict[str, Any]:
    """Get detailed analytics for a specific manufacturer."""
    normalized_name = normalize_manufacturer_name(manufacturer_name)
    data = load_manufacturer_data(normalized_name)
    
    if data["total_products"] == 0:
        return {"error": "No data found for this manufacturer"}
    
    # Calculate trends (last 30 days vs previous 30 days)
    now = datetime.datetime.now()
    thirty_days_ago = now - datetime.timedelta(days=30)
    sixty_days_ago = now - datetime.timedelta(days=60)
    
    recent_scans = [
        entry for entry in data["compliance_history"]
        if datetime.datetime.fromisoformat(entry["timestamp"]) >= thirty_days_ago
    ]
    
    previous_scans = [
        entry for entry in data["compliance_history"]
        if (datetime.datetime.fromisoformat(entry["timestamp"]) >= sixty_days_ago and
            datetime.datetime.fromisoformat(entry["timestamp"]) < thirty_days_ago)
    ]
    
    recent_avg = sum(entry["compliance_score"] for entry in recent_scans) / len(recent_scans) if recent_scans else 0
    previous_avg = sum(entry["compliance_score"] for entry in previous_scans) / len(previous_scans) if previous_scans else 0
    
    trend = "improving" if recent_avg > previous_avg else "declining" if recent_avg < previous_avg else "stable"
    
    # Calculate compliance level
    avg_score = data["compliance_stats"]["average_compliance_score"]
    if avg_score >= 0.9:
        compliance_level = "Excellent"
    elif avg_score >= 0.75:
        compliance_level = "Good"
    elif avg_score >= 0.5:
        compliance_level = "Fair"
    else:
        compliance_level = "Poor"
    
    return {
        "manufacturer_name": normalized_name,
        "basic_stats": {
            "total_products": data["total_products"],
            "total_scans": data["compliance_stats"]["total_scans"],
            "compliant_scans": data["compliance_stats"]["compliant_scans"],
            "non_compliant_scans": data["compliance_stats"]["non_compliant_scans"],
            "average_compliance_score": avg_score,
            "compliance_level": compliance_level
        },
        "field_compliance": {
            "required_fields": data["compliance_stats"]["required_fields_compliance"],
            "optional_fields": data["compliance_stats"]["optional_fields_compliance"]
        },
        "product_categories": data["product_categories"],
        "recent_products": data["recent_products"],
        "trends": {
            "recent_period_avg": recent_avg,
            "previous_period_avg": previous_avg,
            "trend_direction": trend,
            "recent_scans_count": len(recent_scans),
            "previous_scans_count": len(previous_scans)
        },
        "last_updated": data.get("last_updated")
    }

def get_manufacturer_comparison() -> Dict[str, Any]:
    """Get comparative analysis of all manufacturers."""
    manufacturers = get_all_manufacturers()
    
    if not manufacturers:
        return {"error": "No manufacturer data available"}
    
    # Calculate industry averages
    total_products = sum(m["total_products"] for m in manufacturers)
    avg_compliance = sum(m["average_compliance_score"] for m in manufacturers) / len(manufacturers)
    
    # Find top and bottom performers
    top_performers = sorted(manufacturers, key=lambda x: x["average_compliance_score"], reverse=True)[:5]
    bottom_performers = sorted(manufacturers, key=lambda x: x["average_compliance_score"])[:5]
    most_active = sorted(manufacturers, key=lambda x: x["total_products"], reverse=True)[:5]
    
    # Calculate compliance distribution
    excellent = len([m for m in manufacturers if m["average_compliance_score"] >= 0.9])
    good = len([m for m in manufacturers if 0.75 <= m["average_compliance_score"] < 0.9])
    fair = len([m for m in manufacturers if 0.5 <= m["average_compliance_score"] < 0.75])
    poor = len([m for m in manufacturers if m["average_compliance_score"] < 0.5])
    
    return {
        "industry_overview": {
            "total_manufacturers": len(manufacturers),
            "total_products_scanned": total_products,
            "industry_average_compliance": avg_compliance,
            "compliance_distribution": {
                "excellent": excellent,
                "good": good,
                "fair": fair,
                "poor": poor
            }
        },
        "top_performers": top_performers,
        "bottom_performers": bottom_performers,
        "most_active": most_active,
        "all_manufacturers": manufacturers
    }
