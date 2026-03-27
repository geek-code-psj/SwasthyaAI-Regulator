# SwasthyaAI Regulator - Test Suite

This directory contains all test files and test fixtures for the SwasthyaAI Regulator project.

## Quick Start

```bash
# Run all validation tests
python run_tests.py

# Or run the detailed validation suite directly
python test_validation_fixes.py

# Run other test files
python test_pipeline.py
python test_comprehensive_pipeline.py
```

## Test Files

### Core Validation Tests
- **`test_validation_fixes.py`** - Comprehensive validation suite with 10 test cases
  - Tests ADR field mapping
  - Tests MD-14 flexible validation
  - Tests full pipeline integration
  - **Status:** 10/10 PASSING

- **`run_tests.py`** - Simple test runner script
  - Executes test_validation_fixes.py
  - Provides summary of fixes

### Integration Tests
- **`test_pipeline.py`** - Complete pipeline validation
  - Submission → Extraction → Processing
  - Tests end-to-end validation flow

- **`test_comprehensive_pipeline.py`** - Comprehensive pipeline testing
- **`test_extraction_*.py`** - Specific extraction tests
- **`test_extraction_fixed.py`** - Fixed extraction tests
- **`test_extraction_quick.py`** - Quick extraction validation

## Fixtures Directory

The `fixtures/` directory contains test data files:

- **`TEST_MD14_BATCH.txt`** - Sample MD-14 batch submission
- **`TEST_ADR_WITH_DATES.txt`** - Sample ADR with dates
- **`COMPLETE_FORM44_TEMPLATE.txt`** - Complete Form 44 template
- **`test_document.txt`** - Generic test document
- **`test_form44_complete.txt`** - Complete Form 44 example

## Test Coverage

### Validation Tests (10 tests)

1. **Date Format Normalization** ✓
   - Tests multiple date format handling
   - YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY support

2. **Field Mapping** ✓
   - Tests MD-14 → ADR field mapping
   - Ensures all required fields mapped correctly

3. **ADR Validation (Valid Data)** ✓
   - Tests complete valid ADR submission
   - Expects PASS status

4. **ADR Validation (Batch Mode)** ✓
   - Tests batch mode with optional reporter_name
   - Expects PASS with >80% completeness

5. **ADR Validation (Missing Field)** ✓
   - Tests missing mandatory field detection
   - Expects FAIL status

6. **MD-14 Validation (Single Record)** ✓
   - Tests valid MD-14 record
   - Expects 100% data quality

7. **MD-14 Validation (Flexible Dates)** ✓
   - Tests multiple date formats
   - DD/MM/YYYY format support

8. **MD-14 Validation (Flexible Enum)** ✓
   - Tests case-insensitive enum matching
   - 'mild', 'Mild', 'MILD' all accepted

9. **MD-14 Batch Validation** ✓
   - Tests multiple records
   - >60% pass threshold

10. **Pipeline Integration** ✓
    - Tests full MD-14 → Normalize → Validate pipeline
    - End-to-end validation workflow

## Running Tests

### Run All Tests
```bash
python run_tests.py
```

### Run Specific Test Suite
```bash
python test_validation_fixes.py
```

### Run Individual Test (from Python)
```python
from test_validation_fixes import test_adr_validation_valid_data
test_adr_validation_valid_data()
```

## Expected Output

```
======================================================================
SWASTHYAAI REGULATOR - VALIDATION FIXES TEST SUITE
======================================================================

[TEST 1] Date Format Normalization
  [PASS]: '2026-03-15' -> '2026-03-15'
  [PASS]: '15/03/2026' -> '15/03/2026'
  [PASS]: '15-03-2026' -> '15/03/2026'

... (more tests)

======================================================================
TEST SUMMARY
======================================================================
[PASS]: test_date_format_normalization
[PASS]: test_field_mapping
[PASS]: test_adr_validation_valid_data
[PASS]: test_adr_validation_batch_mode
[PASS]: test_adr_validation_missing_field
[PASS]: test_md14_validation_single_record
[PASS]: test_md14_validation_flexible_dates
[PASS]: test_md14_validation_flexible_enum
[PASS]: test_md14_batch_validation
[PASS]: test_pipeline_integration

TOTAL: 10/10 tests PASSED
======================================================================
```

## Test Environment Requirements

- Python 3.8+
- Flask (backend)
- SQLAlchemy (database)
- All dependencies in requirements.txt

## Troubleshooting

### ImportError with backend modules
```bash
cd ..  # Go to project root
python tests/test_validation_fixes.py
```

### Encoding errors (Windows)
The test suite automatically handles Unicode encoding. If you see encoding errors:
1. Ensure Python 3.8+ is installed
2. Set PYTHONIOENCODING=utf-8 environment variable
3. Or specify encoding in terminal

### Database errors
Tests use in-memory validation - no database required. If errors occur:
1. Ensure backend modules are in path
2. Check PYTHONPATH includes backend/

## Adding New Tests

To add new tests to the suite:

1. Create a new test function in `test_validation_fixes.py`:
```python
def test_my_new_validation():
    """Test description"""
    # Setup
    # Execute
    # Assert
    # Return boolean
```

2. Add to `run_all_tests()` function in the tests list

3. Run the suite to verify new test is included

## Documentation

For more information about the validation fixes, see:
- `../CLEANUP_AND_FIXES_SUMMARY.md` - Detailed explanation of all fixes
- `../README.md` - Project overview
- `../docs/QUICKSTART.md` - Quick start guide

---

**All tests are designed to verify the validation fixes are working correctly.**
