import sys
import subprocess
from tests.test_integration import run_tests
import importlib

def test_system():
    """Run system tests and display results."""
    print("\n=== Running PDF Processing Tests ===")
    success, output = run_tests()
    print(output)
    
    if success:
        print("\n✅ All tests passed!")
        return True
    else:
        print("\n❌ Some tests failed!")
        return False

def test_dependencies():
    """Test if all required dependencies are installed and working."""
    required_packages = [
        ('streamlit', 'streamlit'),
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('pdfplumber', 'pdfplumber'),
        ('pytesseract', 'pytesseract'),
        ('pdf2image', 'pdf2image'),
        ('cv2', 'opencv-python-headless'),  # cv2 is the import name for opencv
        ('tabula', 'tabula-py'),  # tabula is the import name for tabula-py
        ('fpdf', 'fpdf')
    ]
    
    missing = []
    for import_name, package_name in required_packages:
        try:
            importlib.import_module(import_name)
            print(f"✓ Found {package_name}")
        except ImportError:
            missing.append(package_name)
            print(f"✗ Missing {package_name}")
    
    return missing

if __name__ == "__main__":
    print("=== Running Full Test Suite ===")
    print("\nChecking dependencies...")
    missing_deps = test_dependencies()
    
    if missing_deps:
        print(f"\n❌ Missing dependencies: {', '.join(missing_deps)}")
        print("Please install missing dependencies:")
        print(f"pip install {' '.join(missing_deps)}")
        sys.exit(1)
    
    print("\n✅ All dependencies installed")
    
    # Run system tests
    if not test_system():
        sys.exit(1)
