import easyocr
import sys

def check_language(lang):
    """Try to initialize a reader with the given language."""
    try:
        print(f"Testing language: {lang}...")
        # Use English as the primary language for stability
        reader = easyocr.Reader(['en', lang])
        print(f"✓ Language '{lang}' is supported")
        return True
    except ValueError as e:
        print(f"✗ Language '{lang}' is not supported: {str(e)}")
        return False
    except Exception as e:
        print(f"! Error testing language '{lang}': {str(e)}")
        return False

def check_single_language(lang):
    """Try to initialize a reader with just one language."""
    try:
        print(f"Testing single language: {lang}...")
        reader = easyocr.Reader([lang])
        print(f"✓ Language '{lang}' is supported as a single language")
        return True
    except ValueError as e:
        print(f"✗ Language '{lang}' is not supported as a single language: {str(e)}")
        return False
    except Exception as e:
        print(f"! Error testing language '{lang}' as single: {str(e)}")
        return False

def main():
    # Common language codes to test
    languages_to_test = [
        'en',    # English
        'ar',    # Arabic
        'bg',    # Bulgarian
        'cs',    # Czech
        'da',    # Danish
        'de',    # German
        'el',    # Greek
        'es',    # Spanish
        'fa',    # Persian
        'fi',    # Finnish
        'fr',    # French
        'he',    # Hebrew
        'hi',    # Hindi
        'hr',    # Croatian
        'hu',    # Hungarian
        'id',    # Indonesian
        'it',    # Italian
        'ja',    # Japanese
        'ko',    # Korean
        'nl',    # Dutch
        'no',    # Norwegian
        'pl',    # Polish
        'pt',    # Portuguese
        'ro',    # Romanian
        'ru',    # Russian
        'sk',    # Slovak
        'sl',    # Slovenian
        'sv',    # Swedish
        'th',    # Thai
        'tr',    # Turkish
        'uk',    # Ukrainian
        'vi',    # Vietnamese
        'zh',    # Chinese (Simplified)
        'zh_tra' # Chinese (Traditional)
    ]
    
    # Check if a specific language was requested
    if len(sys.argv) > 1:
        lang = sys.argv[1]
        check_single_language(lang)
        return
    
    # Otherwise, test all languages
    print("Testing all languages with EasyOCR...")
    print("-" * 50)
    
    supported = []
    unsupported = []
    
    for lang in languages_to_test:
        if check_language(lang):
            supported.append(lang)
        else:
            unsupported.append(lang)
    
    print("\nSupported languages:")
    for lang in supported:
        print(f"- {lang}")
    
    print("\nUnsupported languages:")
    for lang in unsupported:
        print(f"- {lang}")

if __name__ == "__main__":
    main() 