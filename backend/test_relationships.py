#!/usr/bin/env python3
"""
Test script to verify SQLAlchemy relationship warnings are resolved.
"""
import warnings
import sys
import os
from io import StringIO

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def capture_warnings():
    """Capture all warnings to check for SQLAlchemy relationship issues."""
    warning_output = StringIO()
    
    def warning_handler(message, category, filename, lineno, file=None, line=None):
        warning_output.write(f'{category.__name__}: {message}\n')
    
    # Set up warning capture
    old_showwarning = warnings.showwarning
    warnings.showwarning = warning_handler
    
    try:
        # Import models that were causing the relationship conflict
        print("Importing models...")
        from app.models.library import MangaUserLibrary, LibraryCategory
        from app.models.user import User
        from app.models.manga import Manga
        
        print("✅ Models imported successfully")
        
        # Check captured warnings
        warnings_text = warning_output.getvalue()
        
        if 'SAWarning' in warnings_text and 'relationship' in warnings_text:
            print("❌ SQLAlchemy relationship warning still present:")
            print(warnings_text)
            return False
        elif warnings_text:
            print("⚠️  Other warnings found:")
            print(warnings_text)
            return True
        else:
            print("✅ No SQLAlchemy relationship warnings found!")
            return True
            
    except Exception as e:
        print(f"❌ Error importing models: {e}")
        return False
    finally:
        # Restore original warning handler
        warnings.showwarning = old_showwarning

def test_model_relationships():
    """Test that the model relationships are properly defined."""
    try:
        from app.models.library import MangaUserLibrary, LibraryCategory
        
        # Check MangaUserLibrary relationships
        manga_user_lib_relationships = [attr for attr in dir(MangaUserLibrary) if not attr.startswith('_')]
        print(f"MangaUserLibrary relationships: {[r for r in manga_user_lib_relationships if 'relationship' in str(getattr(MangaUserLibrary, r, ''))]}")
        
        # Check LibraryCategory relationships  
        category_relationships = [attr for attr in dir(LibraryCategory) if not attr.startswith('_')]
        print(f"LibraryCategory relationships: {[r for r in category_relationships if 'relationship' in str(getattr(LibraryCategory, r, ''))]}")
        
        # Verify the specific relationships exist
        assert hasattr(MangaUserLibrary, 'categories'), "MangaUserLibrary should have 'categories' relationship"
        assert hasattr(LibraryCategory, 'manga_items'), "LibraryCategory should have 'manga_items' relationship"
        
        print("✅ Model relationships are properly defined")
        return True
        
    except Exception as e:
        print(f"❌ Error testing relationships: {e}")
        return False

if __name__ == "__main__":
    print("Testing SQLAlchemy relationship fix...")
    print("=" * 50)
    
    # Test 1: Check for warnings
    warnings_ok = capture_warnings()
    
    print("\n" + "=" * 50)
    
    # Test 2: Test relationships
    relationships_ok = test_model_relationships()
    
    print("\n" + "=" * 50)
    
    if warnings_ok and relationships_ok:
        print("🎉 All tests passed! SQLAlchemy relationship issue is resolved.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the output above.")
        sys.exit(1)
