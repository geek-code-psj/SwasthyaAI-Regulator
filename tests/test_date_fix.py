"""Test the date parsing fix"""
import sys
sys.path.insert(0, '/root/backend')  # Adjust path as needed

# Test date parsing directly
import re
from datetime import datetime

def parse_ambiguous_date_FIXED(date_str: str) -> str:
    """Fixed version of parse_ambiguous_date"""
    if not date_str or not isinstance(date_str, str):
        return ''
    
    date_str = date_str.strip()
    
    # Already in YYYY-MM-DD format (4-digit year)
    if re.match(r'^\d{4}-\d{1,2}-\d{1,2}$', date_str):
        return date_str
    
    # Already in DD/MM/YYYY format with slashes
    if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_str):
        return date_str
    
    # Pattern: YY-MM-DD or DD-MM-YY (ambiguous 2-digit years with dashes)
    if re.match(r'^\d{2}-\d{1,2}-\d{2}$', date_str):
        parts = date_str.split('-')
        first, middle, last = int(parts[0]), int(parts[1]), int(parts[2])
        
        # Smart detection:
        # Rule 1: If middle > 12, it cannot be a month, invalid
        if middle > 12:
            return date_str  # Invalid format, return as-is
        
        # Rule 2: If last > 31, it cannot be a day, invalid
        if last > 31:
            return date_str  # Invalid format, return as-is
        
        # Rule 3: If first > 31, it cannot be a day, must be year (invalid but handle gracefully)
        if first > 31:
            extracted_year = first
            month = middle
            day = last
        else:
            # Both first and last <= 31, ambiguous
            # DEFAULT to YY-MM-DD as this matches PDF extraction patterns (26-03-10 = 2026-03-10)
            extracted_year = first
            month = middle
            day = last
        
        # Century heuristic: 00-30 → 2000-2030, 31-99 → 1931-1999
        if extracted_year <= 30:
            full_year = 2000 + extracted_year
        else:
            full_year = 1900 + extracted_year
        
        # Validate month/day range
        if 1 <= month <= 12 and 1 <= day <= 31:
            return f"{full_year}-{month:02d}-{day:02d}"
    
    # Pattern: DD-MM-YYYY (dashes with 4-digit year)
    if re.match(r'^\d{1,2}-\d{1,2}-\d{4}$', date_str):
        return date_str.replace('-', '/')
    
    return date_str

# Test cases
test_cases = [
    ('26-03-10', '2026-03-10', 'YY-MM-DD: 26=year, 03=month, 10=day → 2026-03-10'),
    ('26-03-15', '2026-03-15', 'YY-MM-DD: 26=year, 03=month, 15=day → 2026-03-15'),
    ('10-03-26', '2010-03-26', 'YY-MM-DD: 10=year, 03=month, 26=day → 2010-03-26'),
    ('15-03-26', '2015-03-26', 'YY-MM-DD: 15=year, 03=month, 26=day → 2015-03-26'),
    ('2026-03-10', '2026-03-10', 'YYYY-MM-DD format (no conversion needed)'),
    ('10/03/2026', '10/03/2026', 'DD/MM/YYYY format (no conversion needed)'),
]

print("Testing Date Parsing Fix")
print("=" * 80)
all_pass = True

for input_date, expected, description in test_cases:
    result = parse_ambiguous_date_FIXED(input_date)
    passed = result == expected
    all_pass = all_pass and passed
    
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status} | {description}")
    if not passed:
        print(f"       Input: '{input_date}' → Expected: '{expected}', Got: '{result}'")

print("=" * 80)
print(f"Overall: {'ALL TESTS PASS ✓' if all_pass else 'SOME TESTS FAILED ✗'}")
