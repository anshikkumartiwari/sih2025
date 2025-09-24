from core.crawlers import amazon
from core import vision, ocr
from core import gemini_analysis

def process_product(url: str):
    if any(domain in url.lower() for domain in ["amazon", "amzn.in"]):
        data = amazon.crawl(url)
        # Collect downloaded images
        images = data.get("images") or []

        # Score/select best label images for debugging/visibility, but do OCR on relevant images only
        selected, debug = vision.select_best_label_images(images, min_matches=1, max_images=5)
        data["vision"] = {"selected": selected, "scoring": debug}

        # Run OCR only on images that have at least one keyword match
        relevant_images = [img for img in images if debug.get(img, {}).get("score", 0) >= 1]
        if not relevant_images:
            # Fallback to all images if none have keywords
            relevant_images = images
            print(f"[DEBUG] No images with keywords found, using all {len(images)} images for OCR")
        else:
            print(f"[DEBUG] Using {len(relevant_images)} relevant images (with keywords) for OCR")
        
        ocr_result = ocr.extract_fields_from_images(relevant_images)
        data["ocr"] = ocr_result
        
        # Merge OCR fields (prioritize OCR over DOM extraction)
        for key in ["mrp", "quantity", "manufacturer", "origin", "support", "dates", "batch", "license", "barcode"]:
            if ocr_result.get("fields", {}).get(key):
                data[key] = ocr_result["fields"][key]
                print(f"[DEBUG] Merged OCR field {key}: {ocr_result['fields'][key]}")
        
        # Re-run compliance analysis with merged data to ensure accuracy
        merged_fields = {key: data.get(key) for key in ["mrp", "quantity", "manufacturer", "origin", "support", "dates", "batch", "license", "barcode"]}
        print(f"[DEBUG] Merged fields for compliance check: {merged_fields}")
        
        # Update compliance analysis with actual merged data
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
        
        # Check required fields with merged data
        for field, label in required_fields.items():
            present = bool(merged_fields.get(field))
            compliance[field] = present
            if not present:
                missing.append(label)
        
        # Check optional fields with merged data
        for field, label in optional_fields.items():
            present = bool(merged_fields.get(field))
            compliance[field] = present
            if not present:
                warnings.append(f"Optional: {label}")
        
        # Additional validation rules
        if merged_fields.get("mrp"):
            try:
                mrp_val = float(str(merged_fields["mrp"]).replace("₹", "").replace(",", ""))
                if mrp_val <= 0:
                    warnings.append("MRP should be positive")
            except:
                warnings.append("MRP format may be invalid")
        
        if merged_fields.get("quantity"):
            qty_str = str(merged_fields["quantity"]).lower()
            if not any(unit in qty_str for unit in ["g", "kg", "ml", "l", "pcs", "pack"]):
                warnings.append("Quantity unit may be missing or invalid")
        
        # Update compliance summary with merged data
        compliance_summary = {
            "total_fields_found": len([f for f in merged_fields.values() if f]),
            "required_present": len([f for f in required_fields.keys() if compliance.get(f)]),
            "required_total": len(required_fields),
            "compliance_score": f"{len([f for f in required_fields.keys() if compliance.get(f)])}/{len(required_fields)}"
        }
        
        # Add comprehensive compliance analysis baseline
        data["compliance"] = compliance
        data["missing_fields"] = missing
        data["warnings"] = warnings
        data["compliance_summary"] = compliance_summary
        
        print(f"[DEBUG] Compliance analysis results:")
        print(f"[DEBUG] - Compliance status: {compliance}")
        print(f"[DEBUG] - Missing fields: {missing}")
        print(f"[DEBUG] - Warnings: {warnings}")
        print(f"[DEBUG] - Compliance summary: {compliance_summary}")
        
        # Enhanced Gemini Analysis with Cross-Verification and OCR refinement
        raw_text = ocr_result.get("extracted_text", "")
        if raw_text:
            gemini_status = gemini_analysis.get_gemini_analysis_status()
            data["gemini_status"] = gemini_status
            
            if gemini_status["ready"]:
                try:
                    # Step 1: Ask Gemini to clean/refine OCR text (spelling/grammar correction)
                    enhanced = gemini_analysis.enhance_ocr_with_gemini(raw_text)
                    data["gemini_enhanced"] = enhanced
                    effective_text = enhanced.get("cleaned_text") if enhanced.get("enhanced") and enhanced.get("cleaned_text") else raw_text

                    # Step 2: Basic Gemini extraction on refined text
                    gemini_basic = gemini_analysis.analyze_packaging_text(effective_text)
                    data["gemini_analysis"] = gemini_basic
                    
                    # Step 3: Comprehensive cross-verification analysis
                    comprehensive_analysis = gemini_analysis.comprehensive_compliance_analysis(
                        effective_text,
                        merged_fields
                    )
                    data["gemini_comprehensive"] = comprehensive_analysis
                    
                    # Merge Gemini recommendations with OCR results where OCR missed
                    if comprehensive_analysis.get("comparison_analysis", {}).get("recommended_fields"):
                        recommended = comprehensive_analysis["comparison_analysis"]["recommended_fields"]
                        print(f"[DEBUG] Gemini recommended fields: {recommended}")
                        for field, value in recommended.items():
                            if value and value != "null" and not merged_fields.get(field):
                                data[field] = value
                                merged_fields[field] = value  # Update merged_fields for consistency
                                print(f"[DEBUG] Updated {field} with Gemini recommendation: {value}")
                        
                        # Re-run compliance analysis with updated merged_fields
                        updated_compliance = {}
                        updated_missing = []
                        updated_warnings = []
                        
                        # Check required fields with updated merged data
                        for field, label in required_fields.items():
                            present = bool(merged_fields.get(field))
                            updated_compliance[field] = present
                            if not present:
                                updated_missing.append(label)
                        
                        # Check optional fields with updated merged data
                        for field, label in optional_fields.items():
                            present = bool(merged_fields.get(field))
                            updated_compliance[field] = present
                            if not present:
                                updated_warnings.append(f"Optional: {label}")
                        
                        # Update compliance summary with updated merged data
                        updated_compliance_summary = {
                            "total_fields_found": len([f for f in merged_fields.values() if f]),
                            "required_present": len([f for f in required_fields.keys() if updated_compliance.get(f)]),
                            "required_total": len(required_fields),
                            "compliance_score": f"{len([f for f in required_fields.keys() if updated_compliance.get(f)])}/{len(required_fields)}"
                        }
                        
                        # Update data with corrected compliance analysis
                        data["compliance"] = updated_compliance
                        data["missing_fields"] = updated_missing
                        data["warnings"] = updated_warnings
                        data["compliance_summary"] = updated_compliance_summary
                    
                    # Update compliance analysis with Gemini insights
                    if comprehensive_analysis.get("compliance_assessment"):
                        gemini_compliance = comprehensive_analysis["compliance_assessment"]
                        if gemini_compliance.get("final_compliance_score"):
                            data["compliance_summary"]["compliance_score"] = gemini_compliance["final_compliance_score"]
                        if gemini_compliance.get("missing_required"):
                            # Only update if we don't already have updated missing fields from recommendations
                            if not comprehensive_analysis.get("comparison_analysis", {}).get("recommended_fields"):
                                data["missing_fields"] = gemini_compliance["missing_required"]
                        if gemini_compliance.get("missing_optional"):
                            # Only update if we don't already have updated warnings from recommendations
                            if not comprehensive_analysis.get("comparison_analysis", {}).get("recommended_fields"):
                                data["warnings"] = gemini_compliance["missing_optional"]
                            
                except Exception as e:
                    data["gemini_analysis"] = {"error": f"Gemini analysis failed: {str(e)}"}
                    data["gemini_comprehensive"] = {"error": f"Comprehensive analysis failed: {str(e)}"}
        
        return data
    return {"error": "Unsupported platform"}