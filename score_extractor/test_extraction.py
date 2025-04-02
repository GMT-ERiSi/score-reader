import os
import sys
import json
import base64
from dotenv import load_dotenv

# Import the function from the main module
from score_extractor import extract_scores_from_image

# Load environment variables from .env file
load_dotenv()

def test_with_file(image_path):
    """Test the score extraction with a file path"""
    print(f"Testing extraction with image: {image_path}")
    try:
        result = extract_scores_from_image(image_path)
        print("\nExtracted data:")
        print(json.dumps(result, indent=2))
        print("\nSuccess!")
        return result
    except Exception as e:
        print(f"\nError: {str(e)}")
        return None

def test_with_folder(folder_path):
    """Process all image files in a folder"""
    print(f"Processing all images in folder: {folder_path}")
    
    supported_extensions = ['.jpg', '.jpeg', '.png']
    results = {}
    
    for filename in os.listdir(folder_path):
        if any(filename.lower().endswith(ext) for ext in supported_extensions):
            file_path = os.path.join(folder_path, filename)
            print(f"\nProcessing: {filename}")
            try:
                result = extract_scores_from_image(file_path)
                results[filename] = result
                print(f"Successfully processed {filename}")
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
    
    # Save all results to a JSON file
    output_path = os.path.join(folder_path, "extraction_results.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nAll results saved to: {output_path}")
    return results

if __name__ == "__main__":
    # Check if API key is set
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable is not set")
        print("Set it by running: export ANTHROPIC_API_KEY=your-api-key-here")
        print("Or make sure your .env file contains: ANTHROPIC_API_KEY=your-api-key-here")
        sys.exit(1)
    
    # Default Screenshots folder in project root
    default_screenshots_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Screenshots")
    
    # Simple command line interface
    if len(sys.argv) < 2:
        # Check if Screenshots folder exists
        if os.path.isdir(default_screenshots_folder):
            print(f"No path specified. Using default Screenshots folder: {default_screenshots_folder}")
            test_with_folder(default_screenshots_folder)
        else:
            print("Usage:")
            print("  python -m score_extractor.test_extraction <image_path>")
            print("  python -m score_extractor.test_extraction --folder <folder_path>")
            print(f"\nDefault Screenshots folder not found at: {default_screenshots_folder}")
            sys.exit(1)
    elif sys.argv[1] == "--folder" and len(sys.argv) >= 3:
        test_with_folder(sys.argv[2])
    elif sys.argv[1] == "--screenshots":
        # Use the default Screenshots folder
        if os.path.isdir(default_screenshots_folder):
            print(f"Using Screenshots folder: {default_screenshots_folder}")
            test_with_folder(default_screenshots_folder)
        else:
            print(f"Error: Screenshots folder not found at: {default_screenshots_folder}")
            sys.exit(1)
    else:
        test_with_file(sys.argv[1])