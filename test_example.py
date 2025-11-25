"""
Example Test Script for EasyExcel Backend

This script demonstrates how to test the backend API locally.
"""

import requests
import os
from pathlib import Path


# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_FILE_PATH = "test_data/sample.csv"  # Create this file for testing


def create_sample_csv():
    """Create a sample CSV file for testing"""
    test_dir = Path("test_data")
    test_dir.mkdir(exist_ok=True)
    
    csv_content = """Region,Product,Revenue,Quantity,Date
North,Widget A,15000,100,2024-01-15
South,Widget B,22000,150,2024-01-16
East,Widget A,18000,120,2024-01-17
West,Widget C,25000,200,2024-01-18
North,Widget B,19000,130,2024-01-19
South,Widget A,21000,140,2024-01-20
East,Widget C,23000,180,2024-01-21
West,Widget B,24000,190,2024-01-22"""
    
    sample_file = test_dir / "sample.csv"
    sample_file.write_text(csv_content)
    print(f"✓ Created sample CSV: {sample_file}")
    return sample_file


def test_health_endpoint():
    """Test health check endpoint"""
    print("\n1. Testing Health Endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False


def test_process_file(file_path: Path, prompt: str):
    """Test file processing endpoint"""
    print(f"\n2. Testing Process File Endpoint...")
    print(f"   Prompt: {prompt}")
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'text/csv')}
            data = {'prompt': prompt}
            
            response = requests.post(
                f"{API_BASE_URL}/process-file",
                files=files,
                data=data
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✓ Success!")
                print(f"   Processed File: {result.get('processed_file_url')}")
                print(f"   Chart URL: {result.get('chart_url')}")
                print(f"   Summary: {result.get('summary')}")
                print(f"   Action Plan: {result.get('action_plan')}")
                
                # Download processed file if available
                if result.get('processed_file_url'):
                    download_url = f"{API_BASE_URL}{result['processed_file_url']}"
                    download_response = requests.get(download_url)
                    if download_response.status_code == 200:
                        output_file = Path("test_output") / file_path.stem / "_processed.xlsx"
                        output_file.parent.mkdir(exist_ok=True, parents=True)
                        output_file.write_bytes(download_response.content)
                        print(f"   ✓ Downloaded processed file: {output_file}")
                
                # Download chart if available
                if result.get('chart_url'):
                    chart_url = f"{API_BASE_URL}{result['chart_url']}"
                    chart_response = requests.get(chart_url)
                    if chart_response.status_code == 200:
                        chart_file = Path("test_output") / "chart.png"
                        chart_file.parent.mkdir(exist_ok=True, parents=True)
                        chart_file.write_bytes(chart_response.content)
                        print(f"   ✓ Downloaded chart: {chart_file}")
                
                return True
            else:
                print(f"   ✗ Error: {response.json()}")
                return False
                
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("EasyExcel Backend Test Script")
    print("=" * 60)
    
    # Check if API is running
    print("\nChecking if API is running...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        print("✓ API is running!")
    except Exception:
        print("✗ API is not running!")
        print("\nPlease start the API first:")
        print("  cd backend")
        print("  python app.py")
        return
    
    # Create sample file
    sample_file = create_sample_csv()
    
    # Test health endpoint
    if not test_health_endpoint():
        print("\n✗ Health check failed. Exiting.")
        return
    
    # Test various prompts
    test_cases = [
        {
            "prompt": "Group by Region and sum the Revenue",
            "description": "Group by operation with aggregation"
        },
        {
            "prompt": "Clean the data - remove duplicates and fix formatting",
            "description": "Data cleaning operation"
        },
        {
            "prompt": "Show me summary statistics for Revenue and Quantity",
            "description": "Summary statistics"
        },
        {
            "prompt": "Filter rows where Revenue is greater than 20000 and create a bar chart",
            "description": "Filter and chart generation"
        }
    ]
    
    print("\n" + "=" * 60)
    print("Running Test Cases")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {test_case['description']} ---")
        test_process_file(sample_file, test_case['prompt'])
    
    print("\n" + "=" * 60)
    print("Testing Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()








