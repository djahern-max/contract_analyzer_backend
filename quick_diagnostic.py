#!/usr/bin/env python3
"""
Quick diagnostic to verify your schemas setup
"""

import os
import sys
from pathlib import Path

def check_file_structure():
    """Check if all required files exist"""
    print("🔍 Checking file structure...")
    
    required_files = [
        "schemas/__init__.py",
        "schemas/base.py",
        "schemas/auth.py", 
        "schemas/project.py",
        "schemas/contract.py",
        "routers/contracts.py",
        "routers/projects.py",
        "models/project.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing_files.append(file_path)
    
    return len(missing_files) == 0

def test_imports():
    """Test if imports work"""
    print("\n📦 Testing imports...")
    
    try:
        # Test schemas import
        from schemas.base import SuccessResponse
        print("✅ schemas.base import successful")
        
        from schemas.contract import ContractDetailResponse
        print("✅ schemas.contract import successful")
        
        from schemas.project import ProjectCreate
        print("✅ schemas.project import successful")
        
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def check_schema_content():
    """Check if schema files have content"""
    print("\n📄 Checking schema file contents...")
    
    schema_files = [
        "schemas/__init__.py",
        "schemas/contract.py"
    ]
    
    for file_path in schema_files:
        path = Path(file_path)
        if path.exists():
            content = path.read_text()
            if len(content.strip()) > 50:  # Has substantial content
                print(f"✅ {file_path} has content ({len(content)} chars)")
            else:
                print(f"⚠️  {file_path} seems empty or minimal")
        else:
            print(f"❌ {file_path} doesn't exist")

def check_router_imports():
    """Check if routers can import schemas"""
    print("\n🚀 Testing router imports...")
    
    try:
        # Check if the router file mentions schemas
        contracts_router = Path("routers/contracts.py")
        if contracts_router.exists():
            content = contracts_router.read_text()
            if "from schemas" in content:
                print("✅ routers/contracts.py imports from schemas")
            else:
                print("⚠️  routers/contracts.py doesn't import from schemas")
        else:
            print("❌ routers/contracts.py doesn't exist")
            
        return True
    except Exception as e:
        print(f"❌ Error checking routers: {e}")
        return False

def main():
    """Run all diagnostics"""
    print("🧪 Contract Analyzer Schema Diagnostic\n")
    
    # Check current directory
    current_dir = Path.cwd()
    print(f"📁 Current directory: {current_dir}")
    
    if not Path("main.py").exists():
        print("❌ Not in backend directory! Please run from where main.py is located.")
        return
    
    print("✅ In correct directory (main.py found)\n")
    
    # Run checks
    structure_ok = check_file_structure()
    check_schema_content()
    imports_ok = test_imports()
    router_ok = check_router_imports()
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"   File structure: {'✅' if structure_ok else '❌'}")
    print(f"   Schema imports: {'✅' if imports_ok else '❌'}")
    print(f"   Router setup: {'✅' if router_ok else '❌'}")
    
    if structure_ok and imports_ok and router_ok:
        print("\n🎉 Everything looks good! Your schemas should work.")
        print("\n🚀 Next steps:")
        print("   1. Add job_number to Project model")
        print("   2. Run: alembic revision --autogenerate -m 'Add job_number'")
        print("   3. Run: alembic upgrade head")
        print("   4. Start your server: uvicorn main:app --reload")
    else:
        print("\n⚠️  Some issues found. Please fix them first.")
        
        if not structure_ok:
            print("   - Make sure all schema files are created")
        if not imports_ok:
            print("   - Check schema file syntax and imports")
        if not router_ok:
            print("   - Update routers to import from schemas")

if __name__ == "__main__":
    main()
