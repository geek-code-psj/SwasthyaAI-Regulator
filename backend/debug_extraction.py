"""
Debug Form 44 extraction
"""
import sys
sys.path.insert(0, '.')

from enhanced_app import Form44Parser
import re

# Test text
text = "Patient Age: 45\nMore text here to make it longer than 100 characters so the parser accepts it" + " " * 50

print(f"Text length: {len(text)}")
print(f"Text preview: {text[:100]}...")
print(f"\nMin text check: {len(text.strip())} >= 100? {len(text.strip()) >= 100}")

# Try the regex manually
keyword = 'Patient Age'
pattern = rf'(?:^|\n)(?:§|•|-)?\s*{re.escape(keyword)}\s*[:=]\s*([^\n]+?)(?:\n|$)'
print(f"\nPattern: {pattern}")

match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
print(f"Match found: {match is not None}")
if match:
    print(f"Matched value: '{match.group(1)}'")

# Now test with the parser
result = Form44Parser.parse_text(text)
print(f"\nParser result: {result}")
