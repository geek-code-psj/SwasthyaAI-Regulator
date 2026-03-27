#!/usr/bin/env python
"""Debug script to inspect ValidationResult data"""

import sys
sys.path.insert(0, 'backend')

from backend.enhanced_app import db, ValidationResult, app
import json

with app.app_context():
    # Get the latest validation results
    results = ValidationResult.query.order_by(ValidationResult.id.desc()).limit(5).all()
    
    print(f"Found {len(results)} validation results\n")
    
    for i, result in enumerate(results, 1):
        print(f"\n{'='*60}")
        print(f"Record {i}:")
        print(f"  Submission ID: {result.submission_id}")
        print(f"  Check Type: {result.check_type}")
        print(f"  Status: {result.status}")
        print(f"  Result JSON:")
        try:
            result_data = json.loads(result.result) if isinstance(result.result, str) else result.result
            print(f"    {json.dumps(result_data, indent=4)}")
            print(f"\n  Root keys: {list(result_data.keys()) if isinstance(result_data, dict) else 'Not a dict'}")
        except json.JSONDecodeError as e:
            print(f"    Error parsing JSON: {e}")
            print(f"    Raw: {result.result[:200]}")
