import os
import sys
import json
import base64
from dotenv import load_dotenv

# Import the functions from the main module
from score_extractor import extract_scores_from_image, extract_scores_from_multiple_images

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

def test_with_multiple_files(image_paths):
    """Test the score extraction with multiple file paths"""
    print(f"Testing extraction with {len(image_paths)} images")
    try:
        results = extract_scores_from_multiple_images(image_paths)
        print("\nExtracted data:")
        print(json.dumps(results, indent=2))
        print("\nSuccess!")
        return results
    except Exception as e:
        print(f"\nError: {str(e)}")
        return None

def test_with_folder(folder_path, batch_size=None):
    """Process all image files in a folder"""
    print(f"Processing all images in folder: {folder_path}")
    
    supported_extensions = ['.jpg', '.jpeg', '.png']
    image_paths = []
    
    for filename in os.listdir(folder_path):
        if any(filename.lower().endswith(ext) for ext in supported_extensions):
            file_path = os.path.join(folder_path, filename)
            image_paths.append(file_path)
    
    print(f"Found {len(image_paths)} images to process")
    
    # If batch_size is specified, process images in batches
    if batch_size and batch_size > 0:
        results = {}
        for i in range(0, len(image_paths), batch_size):
            batch = image_paths[i:i+batch_size]
            print(f"\nProcessing batch {i//batch_size + 1} ({len(batch)} images)")
            batch_results = extract_scores_from_multiple_images(batch)
            results.update(batch_results)
    else:
        # Process all images at once
        results = extract_scores_from_multiple_images(image_paths)
    
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
    
    # Default Screenshots folder at same level as project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parent_dir = os.path.dirname(project_root)
    default_screenshots_folder = os.path.join(parent_dir, "Screenshots")
    
    # Simple command line interface
    if len(sys.argv) < 2:
        # Check if Screenshots folder exists
        if os.path.isdir(default_screenshots_folder):
            print(f"No path specified. Using default Screenshots folder: {default_screenshots_folder}")
            test_with_folder(default_screenshots_folder)
        else:
            print("Usage:")
            print("  python -m score_extractor.test_extraction <image_path>")
            print("  python -m score_extractor.test_extraction --multiple <image_path1> <image_path2> ...")
            print("  python -m score_extractor.test_extraction --folder <folder_path> [--batch-size <size>]")
            print(f"\nDefault Screenshots folder not found at: {default_screenshots_folder}")
            sys.exit(1)
    elif sys.argv[1] == "--multiple" and len(sys.argv) >= 3:
        test_with_multiple_files(sys.argv[2:])
    elif sys.argv[1] == "--folder" and len(sys.argv) >= 3:
        # Check for batch size
        batch_size = None
        folder_path = sys.argv[2]
        if len(sys.argv) >= 5 and sys.argv[3] == "--batch-size":
            try:
                batch_size = int(sys.argv[4])
                print(f"Using batch size: {batch_size}")
            except ValueError:
                print(f"Invalid batch size: {sys.argv[4]}. Using no batching.")
        
        test_with_folder(folder_path, batch_size)
    elif sys.argv[1] == "--screenshots":
        # Use the default Screenshots folder
        if os.path.isdir(default_screenshots_folder):
            print(f"Using Screenshots folder: {default_screenshots_folder}")
            # Check for batch size
            batch_size = None
            if len(sys.argv) >= 4 and sys.argv[2] == "--batch-size":
                try:
                    batch_size = int(sys.argv[3])
                    print(f"Using batch size: {batch_size}")
                except ValueError:
                    print(f"Invalid batch size: {sys.argv[3]}. Using no batching.")
            
            test_with_folder(default_screenshots_folder, batch_size)
        else:
            print(f"Error: Screenshots folder not found at: {default_screenshots_folder}")
            sys.exit(1)
    else:
        test_with_file(sys.argv[1])