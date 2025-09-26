# Historical Data Storage and Analysis System
import os
import json
import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict

HISTORICAL_DATA_DIR = os.path.join("temp", "historical_data")
os.makedirs(HISTORICAL_DATA_DIR, exist_ok=True)

def get_historical_file_path() -> str:
    """Get file path for historical data storage."""
    return os.path.join(HISTORICAL_DATA_DIR, "scan_history.json")

def load_historical_data() -> Dict[str, Any]:
    """Load existing historical data."""
    file_path = get_historical_file_path()
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load historical data: {e}")
    
    # Return default structure for new historical data
    return {
        "total_scans": 0,
        "scan_history": [],
        "statistics": {
            "compliance_distribution": {
                "excellent": 0,  # 90%+
                "good": 0,       # 75-89%
                "fair": 0,       # 50-74%
                "poor": 0        # <50%
            },
            "field_compliance": {
                "required_fields": {
                    "mrp": {"present": 0, "missing": 0, "percentage": 0.0},
                    "quantity": {"present": 0, "missing": 0, "percentage": 0.0},
                    "manufacturer": {"present": 0, "missing": 0, "percentage": 0.0},
                    "origin": {"present": 0, "missing": 0, "percentage": 0.0}
                },
                "optional_fields": {
                    "support": {"present": 0, "missing": 0, "percentage": 0.0},
                    "dates": {"present": 0, "missing": 0, "percentage": 0.0},
                    "batch": {"present": 0, "missing": 0, "percentage": 0.0},
                    "license": {"present": 0, "missing": 0, "percentage": 0.0},
                    "barcode": {"present": 0, "missing": 0, "percentage": 0.0}
                }
            },
            "manufacturer_stats": {},
            "category_stats": {},
            "trends": {
                "daily_scans": {},
                "weekly_compliance": {},
                "monthly_analysis": {}
            }
        },
        "last_updated": None
    }

def save_historical_data(historical_data: Dict[str, Any]) -> bool:
    """Save historical data to file."""
    try:
        file_path = get_historical_file_path()
        historical_data["last_updated"] = datetime.datetime.now().isoformat()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(historical_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save historical data: {e}")
        return False

def categorize_compliance_score(score: float) -> str:
    """Categorize compliance score into performance levels."""
    if score >= 0.9:
        return "excellent"
    elif score >= 0.75:
        return "good"
    elif score >= 0.5:
        return "fair"
    else:
        return "poor"

def categorize_product_type(title: str, manufacturer: str = "") -> str:
    """Categorize product based on title and manufacturer."""
    title_lower = title.lower()
    manufacturer_lower = manufacturer.lower()
    
    # Food & Beverages
    if any(word in title_lower for word in ["food", "snack", "biscuit", "chocolate", "drink", "beverage", "juice", "milk", "yogurt", "cheese", "bread", "cereal", "spice", "oil", "sauce", "pickle", "jam", "honey", "tea", "coffee"]):
        return "Food & Beverages"
    
    # Pharmaceuticals
    elif any(word in title_lower for word in ["medicine", "tablet", "capsule", "syrup", "cream", "ointment", "injection", "drops", "powder", "gel", "lotion", "supplement", "vitamin", "calcium", "protein", "multivitamin"]):
        return "Pharmaceuticals"
    
    # Cosmetics & Personal Care
    elif any(word in title_lower for word in ["cosmetic", "cream", "lotion", "shampoo", "soap", "beauty", "makeup", "lipstick", "foundation", "perfume", "deodorant", "toothpaste", "brush", "comb", "razor", "skincare", "face", "body", "hair"]):
        return "Cosmetics & Personal Care"
    
    # Electronics
    elif any(word in title_lower for word in ["electronic", "phone", "charger", "cable", "device", "battery", "headphone", "speaker", "camera", "laptop", "tablet", "watch", "remote", "adapter", "usb", "bluetooth"]):
        return "Electronics"
    
    # Textiles & Clothing
    elif any(word in title_lower for word in ["clothing", "shirt", "dress", "fabric", "textile", "saree", "kurta", "jeans", "trouser", "jacket", "sweater", "sock", "underwear", "towel", "bedding", "curtain"]):
        return "Textiles & Clothing"
    
    # Home & Kitchen
    elif any(word in title_lower for word in ["kitchen", "cookware", "utensil", "plate", "bowl", "cup", "glass", "bottle", "container", "storage", "cleaning", "detergent", "soap", "brush", "mop", "broom"]):
        return "Home & Kitchen"
    
    # Automotive
    elif any(word in title_lower for word in ["car", "auto", "vehicle", "tire", "oil", "fuel", "battery", "engine", "brake", "clutch", "gear", "motor", "bike", "scooter"]):
        return "Automotive"
    
    # Books & Stationery
    elif any(word in title_lower for word in ["book", "notebook", "pen", "pencil", "paper", "stationery", "calculator", "ruler", "eraser", "sharpener", "folder", "file"]):
        return "Books & Stationery"
    
    # Sports & Fitness
    elif any(word in title_lower for word in ["sport", "fitness", "gym", "exercise", "yoga", "running", "football", "cricket", "tennis", "badminton", "basketball", "volleyball", "equipment", "gear"]):
        return "Sports & Fitness"
    
    # Toys & Games
    elif any(word in title_lower for word in ["toy", "game", "puzzle", "doll", "action", "figure", "board", "card", "video", "console", "controller", "play", "fun"]):
        return "Toys & Games"
    
    else:
        return "General Products"

def store_scan_data(compliance_data: Dict[str, Any]) -> Dict[str, Any]:
    """Store complete scan data in historical records."""
    historical_data = load_historical_data()
    
    # Extract key information
    scan_id = f"scan_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{historical_data['total_scans'] + 1}"
    timestamp = datetime.datetime.now().isoformat()
    
    # Calculate compliance score
    compliance_summary = compliance_data.get("compliance_summary", {})
    required_present = compliance_summary.get("required_present", 0)
    required_total = compliance_summary.get("required_total", 4)
    compliance_score = required_present / required_total if required_total > 0 else 0
    
    # Create comprehensive scan record
    scan_record = {
        "scan_id": scan_id,
        "timestamp": timestamp,
        "product_info": {
            "title": compliance_data.get("title", "Unknown Product"),
            "url": compliance_data.get("url", ""),
            "manufacturer": compliance_data.get("manufacturer", "Unknown"),
            "origin": compliance_data.get("origin", "Unknown"),
            "mrp": compliance_data.get("mrp", ""),
            "quantity": compliance_data.get("quantity", ""),
            "category": categorize_product_type(
                compliance_data.get("title", ""), 
                compliance_data.get("manufacturer", "")
            )
        },
        "compliance_data": {
            "score": compliance_score,
            "level": categorize_compliance_score(compliance_score),
            "required_present": required_present,
            "required_total": required_total,
            "compliance_summary": compliance_summary,
            "compliance": compliance_data.get("compliance", {}),
            "missing_fields": compliance_data.get("missing_fields", []),
            "warnings": compliance_data.get("warnings", [])
        },
        "technical_data": {
            "images_count": len(compliance_data.get("images", [])),
            "ocr_text_length": len(compliance_data.get("ocr", {}).get("extracted_text", "")),
            "vision_selected": len(compliance_data.get("vision", {}).get("selected", [])),
            "gemini_analysis": compliance_data.get("gemini_analysis", {}),
            "gemini_comprehensive": compliance_data.get("gemini_comprehensive", {}),
            "manufacturer_analytics": compliance_data.get("manufacturer_analytics", {}),
            "product_details": compliance_data.get("product_details", {})
        },
        "extracted_fields": {
            "mrp": compliance_data.get("mrp"),
            "quantity": compliance_data.get("quantity"),
            "manufacturer": compliance_data.get("manufacturer"),
            "origin": compliance_data.get("origin"),
            "support": compliance_data.get("support"),
            "dates": compliance_data.get("dates"),
            "batch": compliance_data.get("batch"),
            "license": compliance_data.get("license"),
            "barcode": compliance_data.get("barcode")
        }
    }
    
    # Add to history
    historical_data["scan_history"].append(scan_record)
    historical_data["total_scans"] += 1
    
    # Update statistics
    update_statistics(historical_data, scan_record)
    
    # Keep only last 1000 scans to prevent file bloat
    if len(historical_data["scan_history"]) > 1000:
        historical_data["scan_history"] = historical_data["scan_history"][-1000:]
    
    # Save updated data
    save_historical_data(historical_data)
    
    return historical_data

def update_statistics(historical_data: Dict[str, Any], scan_record: Dict[str, Any]) -> None:
    """Update comprehensive statistics based on new scan."""
    stats = historical_data["statistics"]
    compliance_data = scan_record["compliance_data"]
    product_info = scan_record["product_info"]
    extracted_fields = scan_record["extracted_fields"]
    
    # Update compliance distribution
    compliance_level = compliance_data["level"]
    stats["compliance_distribution"][compliance_level] += 1
    
    # Update field compliance statistics
    required_fields = ["mrp", "quantity", "manufacturer", "origin"]
    optional_fields = ["support", "dates", "batch", "license", "barcode"]
    
    for field in required_fields:
        if extracted_fields.get(field):
            stats["field_compliance"]["required_fields"][field]["present"] += 1
        else:
            stats["field_compliance"]["required_fields"][field]["missing"] += 1
        
        # Update percentage
        total = (stats["field_compliance"]["required_fields"][field]["present"] + 
                stats["field_compliance"]["required_fields"][field]["missing"])
        if total > 0:
            stats["field_compliance"]["required_fields"][field]["percentage"] = (
                stats["field_compliance"]["required_fields"][field]["present"] / total * 100
            )
    
    for field in optional_fields:
        if extracted_fields.get(field):
            stats["field_compliance"]["optional_fields"][field]["present"] += 1
        else:
            stats["field_compliance"]["optional_fields"][field]["missing"] += 1
        
        # Update percentage
        total = (stats["field_compliance"]["optional_fields"][field]["present"] + 
                stats["field_compliance"]["optional_fields"][field]["missing"])
        if total > 0:
            stats["field_compliance"]["optional_fields"][field]["percentage"] = (
                stats["field_compliance"]["optional_fields"][field]["present"] / total * 100
            )
    
    # Update manufacturer statistics
    manufacturer = product_info["manufacturer"]
    if manufacturer not in stats["manufacturer_stats"]:
        stats["manufacturer_stats"][manufacturer] = {
            "total_scans": 0,
            "total_compliance_score": 0.0,
            "average_compliance_score": 0.0,
            "compliance_levels": {"excellent": 0, "good": 0, "fair": 0, "poor": 0},
            "categories": set()
        }
    
    manufacturer_stats = stats["manufacturer_stats"][manufacturer]
    manufacturer_stats["total_scans"] += 1
    manufacturer_stats["total_compliance_score"] += compliance_data["score"]
    manufacturer_stats["average_compliance_score"] = (
        manufacturer_stats["total_compliance_score"] / manufacturer_stats["total_scans"]
    )
    manufacturer_stats["compliance_levels"][compliance_level] += 1
    manufacturer_stats["categories"].add(product_info["category"])
    
    # Convert set to list for JSON serialization
    manufacturer_stats["categories"] = list(manufacturer_stats["categories"])
    
    # Update category statistics
    category = product_info["category"]
    if category not in stats["category_stats"]:
        stats["category_stats"][category] = {
            "total_scans": 0,
            "total_compliance_score": 0.0,
            "average_compliance_score": 0.0,
            "compliance_levels": {"excellent": 0, "good": 0, "fair": 0, "poor": 0},
            "manufacturers": set()
        }
    
    category_stats = stats["category_stats"][category]
    category_stats["total_scans"] += 1
    category_stats["total_compliance_score"] += compliance_data["score"]
    category_stats["average_compliance_score"] = (
        category_stats["total_compliance_score"] / category_stats["total_scans"]
    )
    category_stats["compliance_levels"][compliance_level] += 1
    category_stats["manufacturers"].add(manufacturer)
    
    # Convert set to list for JSON serialization
    category_stats["manufacturers"] = list(category_stats["manufacturers"])
    
    # Update daily trends
    date_key = datetime.datetime.now().strftime("%Y-%m-%d")
    if date_key not in stats["trends"]["daily_scans"]:
        stats["trends"]["daily_scans"][date_key] = 0
    stats["trends"]["daily_scans"][date_key] += 1
    
    # Update weekly compliance trends
    week_key = datetime.datetime.now().strftime("%Y-W%U")
    if week_key not in stats["trends"]["weekly_compliance"]:
        stats["trends"]["weekly_compliance"][week_key] = {
            "total_scans": 0,
            "total_score": 0.0,
            "average_score": 0.0
        }
    
    weekly_stats = stats["trends"]["weekly_compliance"][week_key]
    weekly_stats["total_scans"] += 1
    weekly_stats["total_score"] += compliance_data["score"]
    weekly_stats["average_score"] = weekly_stats["total_score"] / weekly_stats["total_scans"]

def get_historical_analytics() -> Dict[str, Any]:
    """Get comprehensive historical analytics."""
    historical_data = load_historical_data()
    
    if historical_data["total_scans"] == 0:
        return {"error": "No historical data available"}
    
    # Calculate overall statistics
    total_scans = historical_data["total_scans"]
    compliance_dist = historical_data["statistics"]["compliance_distribution"]
    
    # Calculate overall compliance percentage
    excellent_count = compliance_dist["excellent"]
    good_count = compliance_dist["good"]
    fair_count = compliance_dist["fair"]
    poor_count = compliance_dist["poor"]
    
    overall_compliance = (excellent_count + good_count) / total_scans * 100 if total_scans > 0 else 0
    
    # Get recent trends (last 30 days)
    thirty_days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
    recent_scans = [
        scan for scan in historical_data["scan_history"]
        if datetime.datetime.fromisoformat(scan["timestamp"]) >= thirty_days_ago
    ]
    
    recent_avg_score = sum(scan["compliance_data"]["score"] for scan in recent_scans) / len(recent_scans) if recent_scans else 0
    
    # Get top performing manufacturers
    manufacturer_stats = historical_data["statistics"]["manufacturer_stats"]
    top_manufacturers = sorted(
        manufacturer_stats.items(),
        key=lambda x: x[1]["average_compliance_score"],
        reverse=True
    )[:10]
    
    # Get category analysis
    category_stats = historical_data["statistics"]["category_stats"]
    category_analysis = sorted(
        category_stats.items(),
        key=lambda x: x[1]["average_compliance_score"],
        reverse=True
    )
    
    # Get daily scan trends (last 30 days)
    daily_trends = {}
    for i in range(30):
        date = (datetime.datetime.now() - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        daily_trends[date] = historical_data["statistics"]["trends"]["daily_scans"].get(date, 0)
    
    return {
        "overview": {
            "total_scans": total_scans,
            "overall_compliance_percentage": overall_compliance,
            "recent_avg_score": recent_avg_score,
            "compliance_distribution": compliance_dist,
            "last_updated": historical_data.get("last_updated")
        },
        "field_analysis": historical_data["statistics"]["field_compliance"],
        "manufacturer_analysis": {
            "top_performers": top_manufacturers,
            "total_manufacturers": len(manufacturer_stats),
            "manufacturer_stats": manufacturer_stats
        },
        "category_analysis": {
            "categories": category_analysis,
            "total_categories": len(category_stats)
        },
        "trends": {
            "daily_scans": daily_trends,
            "weekly_compliance": historical_data["statistics"]["trends"]["weekly_compliance"]
        },
        "recent_scans": recent_scans[-10:] if recent_scans else []
    }

def get_scan_history(limit: int = 50, manufacturer: str = None, category: str = None) -> List[Dict[str, Any]]:
    """Get filtered scan history."""
    historical_data = load_historical_data()
    scans = historical_data["scan_history"]
    
    # Apply filters
    if manufacturer:
        scans = [scan for scan in scans if scan["product_info"]["manufacturer"].lower() == manufacturer.lower()]
    
    if category:
        scans = [scan for scan in scans if scan["product_info"]["category"] == category]
    
    # Return most recent scans
    return scans[-limit:] if limit else scans

def export_historical_data(format: str = "json") -> str:
    """Export historical data in specified format."""
    historical_data = load_historical_data()
    
    if format.lower() == "json":
        return json.dumps(historical_data, indent=2, ensure_ascii=False)
    elif format.lower() == "csv":
        # Convert to CSV format
        import csv
        import io
        
        output = io.StringIO()
        if historical_data["scan_history"]:
            fieldnames = [
                "scan_id", "timestamp", "title", "manufacturer", "category", 
                "compliance_score", "compliance_level", "mrp", "quantity", 
                "origin", "missing_fields_count", "warnings_count"
            ]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for scan in historical_data["scan_history"]:
                row = {
                    "scan_id": scan["scan_id"],
                    "timestamp": scan["timestamp"],
                    "title": scan["product_info"]["title"],
                    "manufacturer": scan["product_info"]["manufacturer"],
                    "category": scan["product_info"]["category"],
                    "compliance_score": scan["compliance_data"]["score"],
                    "compliance_level": scan["compliance_data"]["level"],
                    "mrp": scan["extracted_fields"].get("mrp", ""),
                    "quantity": scan["extracted_fields"].get("quantity", ""),
                    "origin": scan["extracted_fields"].get("origin", ""),
                    "missing_fields_count": len(scan["compliance_data"]["missing_fields"]),
                    "warnings_count": len(scan["compliance_data"]["warnings"])
                }
                writer.writerow(row)
        
        return output.getvalue()
    else:
        return "Unsupported format. Use 'json' or 'csv'."
