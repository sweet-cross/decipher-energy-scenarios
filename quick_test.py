#!/usr/bin/env python3
"""
Quick test for the Swiss Energy Scenarios system
"""

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_basic_imports():
    """Test basic imports work."""
    print("🔧 Testing Basic Imports...")
    
    try:
        from utils.config import config
        print("✅ Configuration import successful")
        
        # Test config validation
        config.validate()
        print("✅ Configuration validation passed")
        print(f"   OpenAI API Key: {'***' + config.openai_api_key[-4:] if config.openai_api_key else 'NOT SET'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic import test failed: {e}")
        return False

def test_data_availability():
    """Test if data is available."""
    print("\n📊 Testing Data Availability...")
    
    data_path = os.path.join(os.path.dirname(__file__), 'data')
    
    if not os.path.exists(data_path):
        print(f"⚠️  Data directory not found at {data_path}")
        return False
        
    synthesis_path = os.path.join(data_path, 'extracted', 'synthesis')
    transformation_path = os.path.join(data_path, 'extracted', 'transformation')
    reports_path = os.path.join(data_path, 'reports')
    
    synthesis_files = len([f for f in os.listdir(synthesis_path) if f.endswith('.csv')]) if os.path.exists(synthesis_path) else 0
    transformation_files = len([f for f in os.listdir(transformation_path) if f.endswith('.csv')]) if os.path.exists(transformation_path) else 0
    report_files = len([f for f in os.listdir(reports_path) if f.endswith('.pdf')]) if os.path.exists(reports_path) else 0
    
    print(f"✅ Data structure check:")
    print(f"   Synthesis CSV files: {synthesis_files}")
    print(f"   Transformation CSV files: {transformation_files}")
    print(f"   PDF reports: {report_files}")
    
    total_files = synthesis_files + transformation_files + report_files
    if total_files > 0:
        print(f"✅ Total data files available: {total_files}")
        return True
    else:
        print("⚠️  No data files found - system will have limited functionality")
        return False

def test_simple_csv_processing():
    """Test simple CSV processing."""
    print("\n📈 Testing CSV Processing...")
    
    synthesis_path = os.path.join(os.path.dirname(__file__), 'data', 'extracted', 'synthesis')
    
    if not os.path.exists(synthesis_path):
        print("⚠️  No synthesis data directory found")
        return False
        
    csv_files = [f for f in os.listdir(synthesis_path) if f.endswith('.csv')]
    
    if not csv_files:
        print("⚠️  No CSV files found")
        return False
    
    try:
        import pandas as pd
        
        # Try to load first CSV file
        sample_file = csv_files[0]
        df = pd.read_csv(os.path.join(synthesis_path, sample_file))
        
        print(f"✅ Successfully loaded sample file: {sample_file}")
        print(f"   Shape: {df.shape}")
        print(f"   Columns: {list(df.columns)}")
        
        # Check for expected columns
        expected_cols = ['variable', 'year', 'value', 'scenario']
        found_cols = [col for col in expected_cols if col in df.columns]
        print(f"   Expected columns found: {found_cols}")
        
        return True
        
    except Exception as e:
        print(f"❌ CSV processing failed: {e}")
        return False

def main():
    """Main test function."""
    print("=" * 80)
    print("🇨🇭 SWISS ENERGY SCENARIOS DECIPHER - QUICK TEST")
    print("=" * 80)
    
    tests_passed = 0
    total_tests = 3
    
    # Run tests
    if test_basic_imports():
        tests_passed += 1
        
    if test_data_availability():
        tests_passed += 1
        
    if test_simple_csv_processing():
        tests_passed += 1
    
    # Results
    print("\n" + "=" * 80)
    print("🏁 QUICK TEST RESULTS")
    print("=" * 80)
    
    if tests_passed == total_tests:
        print("✅ ALL TESTS PASSED!")
        print("\n🚀 System is ready! You can now:")
        print("   1. Run the CLI: source .venv/bin/activate && python main.py")
        print("   2. Run the web app: source .venv/bin/activate && streamlit run streamlit_app.py")
    else:
        print(f"⚠️  {tests_passed}/{total_tests} tests passed")
        print("Some issues detected - system may have limited functionality")
    
    print("=" * 80)

if __name__ == "__main__":
    main()