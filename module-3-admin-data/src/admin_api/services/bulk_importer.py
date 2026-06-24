# ===========================================
# Bulk Importer Service
# ===========================================

import os
import logging
from typing import Dict, List, Optional
from pathlib import Path
import csv
import json

logger = logging.getLogger(__name__)


class BulkImporter:
    """Bulk import data from CSV, JSON, and other formats"""
    
    def __init__(self):
        self.supported_formats = ['csv', 'json', 'xlsx']
    
    def import_profiles_from_csv(self, file_path: str) -> Dict:
        """Import user profiles from CSV file"""
        profiles = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                required_fields = ['user_id', 'full_name']
                
                for row in reader:
                    # Check required fields
                    missing = [f for f in required_fields if f not in row or not row[f]]
                    if missing:
                        logger.warning(f"Skipping row: missing fields {missing}")
                        continue
                    
                    profile = {
                        "user_id": row['user_id'],
                        "full_name": row['full_name'],
                        "email": row.get('email', ''),
                        "role": row.get('role', 'user'),
                        "is_active": row.get('is_active', 'true').lower() == 'true',
                        "metadata": {}
                    }
                    
                    # Add optional fields
                    for key, value in row.items():
                        if key not in ['user_id', 'full_name', 'email', 'role', 'is_active']:
                            profile["metadata"][key] = value
                    
                    profiles.append(profile)
            
            return {
                "status": "success",
                "imported": len(profiles),
                "profiles": profiles
            }
            
        except Exception as e:
            logger.error(f"Failed to import profiles from CSV: {e}")
            return {
                "status": "error",
                "message": str(e),
                "imported": 0
            }
    
    def import_profiles_from_json(self, file_path: str) -> Dict:
        """Import user profiles from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            profiles = []
            
            if isinstance(data, list):
                for item in data:
                    if 'user_id' in item and 'full_name' in item:
                        profiles.append(item)
            elif isinstance(data, dict) and 'profiles' in data:
                profiles = data['profiles']
            
            return {
                "status": "success",
                "imported": len(profiles),
                "profiles": profiles
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON file: {e}")
            return {
                "status": "error",
                "message": f"Invalid JSON: {str(e)}",
                "imported": 0
            }
        except Exception as e:
            logger.error(f"Failed to import profiles from JSON: {e}")
            return {
                "status": "error",
                "message": str(e),
                "imported": 0
            }
    
    def import_rules_from_csv(self, file_path: str) -> Dict:
        """Import corporate rules from CSV file"""
        rules = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                required_fields = ['name', 'category', 'condition', 'action']
                
                for row in reader:
                    missing = [f for f in required_fields if f not in row or not row[f]]
                    if missing:
                        logger.warning(f"Skipping row: missing fields {missing}")
                        continue
                    
                    rule = {
                        "name": row['name'],
                        "description": row.get('description', ''),
                        "category": row['category'],
                        "role": row.get('role', 'user'),
                        "priority": int(row.get('priority', 2)),
                        "condition": row['condition'],
                        "action": row['action'],
                        "is_active": row.get('is_active', 'true').lower() == 'true'
                    }
                    
                    rules.append(rule)
            
            return {
                "status": "success",
                "imported": len(rules),
                "rules": rules
            }
            
        except Exception as e:
            logger.error(f"Failed to import rules from CSV: {e}")
            return {
                "status": "error",
                "message": str(e),
                "imported": 0
            }
    
    def import_styles_from_json(self, file_path: str) -> Dict:
        """Import artistic styles from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            styles = []
            
            if isinstance(data, list):
                for item in data:
                    if 'name' in item:
                        styles.append(item)
            elif isinstance(data, dict) and 'styles' in data:
                styles = data['styles']
            
            return {
                "status": "success",
                "imported": len(styles),
                "styles": styles
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON file: {e}")
            return {
                "status": "error",
                "message": f"Invalid JSON: {str(e)}",
                "imported": 0
            }
        except Exception as e:
            logger.error(f"Failed to import styles from JSON: {e}")
            return {
                "status": "error",
                "message": str(e),
                "imported": 0
            }
    
    def batch_import(self, directory: str, data_type: str) -> Dict:
        """Batch import data from directory"""
        results = {
            "status": "success",
            "imported": 0,
            "errors": [],
            "files_processed": []
        }
        
        for filename in os.listdir(directory):
            if filename.endswith('.csv') or filename.endswith('.json'):
                file_path = os.path.join(directory, filename)
                
                if data_type == 'profiles':
                    if filename.endswith('.csv'):
                        result = self.import_profiles_from_csv(file_path)
                    else:
                        result = self.import_profiles_from_json(file_path)
                elif data_type == 'rules':
                    result = self.import_rules_from_csv(file_path)
                elif data_type == 'styles':
                    result = self.import_styles_from_json(file_path)
                else:
                    result = {"status": "error", "message": f"Unknown data type: {data_type}"}
                
                results["files_processed"].append(filename)
                
                if result["status"] == "success":
                    results["imported"] += result.get("imported", 0)
                else:
                    results["errors"].append({
                        "file": filename,
                        "error": result.get("message", "Unknown error")
                    })
        
        return results
