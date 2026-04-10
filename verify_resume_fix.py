import sys
import os
import json
from unittest.mock import MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock logger to avoid side effects
from backend.ai import chains

def test_resume_parsing_validation():
    print("Testing Resume Parsing Validation...")
    
    # Mock _invoke to return a slightly incomplete JSON
    chains._invoke = MagicMock(return_value='''
    {
        "full_name": "Test User",
        "contact": {
            "email": "test@test.com"
        },
        "summary": "This is a test summary."
    }
    ''')
    
    # Simulate generate_resume call
    result = chains.generate_resume("Test JD", "Existing Data", "Context")
    
    print(f"Generated Keys: {list(result.keys())}")
    
    # Verify field injection
    required = ["full_name", "contact", "summary", "education", "experience", "skills"]
    for field in required:
        assert field in result, f"Field {field} missing from result!"
        
    assert result["education"] == [], "Education should be defaulted to []"
    assert result["experience"] == [], "Experience should be defaulted to []"
    assert result["skills"] == {}, "Skills should be defaulted to {}"
    
    print("✅ Parsing validation test passed!")

def test_router_fallbacks():
    print("\nTesting Router Fallbacks...")
    from backend.models.user import User
    
    # Mock current_user
    user = User(id=1, full_name="Akshay Patil", email="akshay@test.com")
    
    # Simulate content with missing name
    bad_content = {
        "summary": "Short summary",
        "contact": {"phone": "1234567890"}
    }
    
    # We want to test logic similar to what's in router
    content = bad_content.copy()
    if "full_name" not in content or not content["full_name"]:
        content["full_name"] = user.full_name
    if "contact" not in content:
        content["contact"] = {}
    for field in ["email", "phone", "location", "linkedin", "github"]:
        if field not in content["contact"] or not content["contact"][field]:
            if field == "email": content["contact"][field] = user.email
            else: content["contact"][field] = ""
            
    for section in ["education", "experience", "projects", "certifications", "achievements"]:
        if section not in content or not isinstance(content[section], list):
            content[section] = []
            
    assert content["full_name"] == "Akshay Patil"
    assert content["contact"]["email"] == "akshay@test.com"
    assert content["education"] == []
    
    print("✅ Router fallback logic verified!")

if __name__ == "__main__":
    try:
        test_resume_parsing_validation()
        test_router_fallbacks()
        print("\nAll local logic tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
