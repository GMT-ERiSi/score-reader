import os
import sys
import json
import time
import argparse
from dotenv import load_dotenv

# Import the extract_scores_from_image function from your existing module
from score_extractor.test_extraction import extract_scores_from_image

# Load environment variables from .env file
load_dotenv()

def extract_scores_from_multiple_images(image_paths):
    """
    Process multiple game score screen images and extract structured data.
    
    Args:
        image_paths (list): List of paths to image files
        
    Returns:
        dict: Extracted scores for each image as JSON, keyed by filename
    """
    results = {}
    
    for image_path in image_paths:
        try:
            filename = os.path.basename(image_path)
            print(f"Processing image: {filename}")
            
            # Try to extract date from filename
            match_date = extract_date_from_filename(filename)
            if match_date:
                print(f"Extracted date from filename: {match_date}")
            
            result = extract_scores_from_image(image_path)
            
            # Add the date to the result if found
            if match_date:
                result['match_date'] = match_date
                
            results[filename] = result
            
            print(f"Successfully processed {filename}")
        except Exception as e:
            print(f"Error processing {image_path}: {str(e)}")
            results[os.path.basename(image_path)] = {"error": str(e)}
    
    return results

def extract_date_from_filename(filename):
    """
    Extract a date from a filename using various patterns
    
    Args:
        filename (str): The filename to parse
        
    Returns:
        str or None: Extracted date in YYYY-MM-DD HH:MM:SS format, or None if not found
    """
    import re
    from datetime import datetime
    
    # Try to find a date pattern in the filename
    
    # Pattern: YYYY.MM.DD or YYYY-MM-DD
    date_pattern = re.search(r'(20\d{2})[.-](\d{2})[.-](\d{2})', filename)
    if date_pattern:
        year, month, day = date_pattern.groups()
        # Try to find a time pattern too
        time_pattern = re.search(r'(\d{2})\.(\d{2})\.(\d{2})', filename)
        if time_pattern and len(time_pattern.groups()) == 3:
            hour, minute, second = time_pattern.groups()
            return f"{year}-{month}-{day} {hour}:{minute}:{second}"
        else:
            # Default to noon if no time found
            return f"{year}-{month}-{day} 12:00:00"
    
    # Pattern: DD.MM.YYYY or DD-MM-YYYY
    date_pattern = re.search(r'(\d{2})[.-](\d{2})[.-](20\d{2})', filename)
    if date_pattern:
        day, month, year = date_pattern.groups()
        # Try to find a time pattern too
        time_pattern = re.search(r'(\d{2})\.(\d{2})\.(\d{2})', filename)
        if time_pattern and len(time_pattern.groups()) == 3:
            hour, minute, second = time_pattern.groups()
            return f"{year}-{month}-{day} {hour}:{minute}:{second}"
        else:
            # Default to noon if no time found
            return f"{year}-{month}-{day} 12:00:00"
    
    # Try to extract timestamps from Star Wars Squadrons screenshot format
    # Example: Star Wars Squadrons Screenshot 2022.09.24 - 00.17.55.76.png
    sw_pattern = re.search(r'Star Wars\s+Squadrons\s+Screenshot\s+(\d{4})\.(\d{2})\.(\d{2})\s+-\s+(\d{2})\.(\d{2})\.(\d{2})', filename, re.IGNORECASE)
    if sw_pattern:
        year, month, day, hour, minute, second = sw_pattern.groups()
        return f"{year}-{month}-{day} {hour}:{minute}:{second}"
    
    return None

def process_season_folder(season_folder, batch_size=None, output_dir=None):
    """
    Process all images in a season folder
    
    Args:
        season_folder (str): Path to the season folder
        batch_size (int, optional): Number of images to process in one batch
        
    Returns:
        dict: Results for the season
    """
    season_name = os.path.basename(season_folder)
    print(f"\n{'='*50}")
    print(f"Processing season: {season_name}")
    print(f"{'='*50}")
    
    supported_extensions = ['.jpg', '.jpeg', '.png']
    image_paths = []
    
    # Find all image files in the folder
    for filename in os.listdir(season_folder):
        if any(filename.lower().endswith(ext) for ext in supported_extensions):
            file_path = os.path.join(season_folder, filename)
            image_paths.append(file_path)
    
    if not image_paths:
        print(f"No images found in {season_folder}")
        return {}
        
    print(f"Found {len(image_paths)} images to process")
    
    # Process images (with batching if specified)
    if batch_size and batch_size > 0:
        season_results = {}
        total_batches = (len(image_paths) + batch_size - 1) // batch_size  # Ceiling division
        
        for i in range(0, len(image_paths), batch_size):
            batch = image_paths[i:i+batch_size]
            batch_num = i // batch_size + 1
            print(f"\nProcessing batch {batch_num}/{total_batches} ({len(batch)} images)")
            
            batch_results = extract_scores_from_multiple_images(batch)
            season_results.update(batch_results)
            
            # Save intermediate results
            save_season_results(season_folder, season_name, season_results, output_dir)
            
            # Small delay between batches to avoid API rate limits
            if i + batch_size < len(image_paths):
                print("Waiting 2 seconds before next batch...")
                time.sleep(2)
    else:
        # Process all images at once
        season_results = extract_scores_from_multiple_images(image_paths)
        save_season_results(season_folder, season_name, season_results, output_dir)
    
    return {season_name: season_results}

def save_season_results(folder_path, season_name, results, output_dir=None):
    """Save the results for a season to a JSON file"""
    # Determine output path - either in output_dir or in the season folder
    if output_dir:
        # Make sure the output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Create a season subdirectory within the output directory
        season_output_dir = os.path.join(output_dir, season_name)
        if not os.path.exists(season_output_dir):
            os.makedirs(season_output_dir)
            
        output_path = os.path.join(season_output_dir, f"{season_name}_results.json")
    else:
        # Save in the original season folder
        output_path = os.path.join(folder_path, f"{season_name}_results.json")
    
    with open(output_path, "w") as f:
        json.dump({season_name: results}, f, indent=2)
    
    print(f"Season results saved to: {output_path}")

def process_all_seasons(base_dir, output_file="all_seasons_data.json", batch_size=None, output_dir=None):
    """
    Process all season folders within the base directory
    
    Args:
        base_dir (str): Base directory containing season folders
        output_file (str): Output file for all combined results
        batch_size (int, optional): Number of images to process in one batch
        
    Returns:
        dict: Combined results for all seasons
    """
    print(f"\nProcessing all seasons in: {base_dir}")
    
    # Find all directories in the base directory
    season_folders = []
    for entry in os.listdir(base_dir):
        full_path = os.path.join(base_dir, entry)
        if os.path.isdir(full_path):
            season_folders.append(full_path)
    
    if not season_folders:
        print(f"No season folders found in {base_dir}")
        return {}
    
    season_folders.sort()  # Sort folders alphabetically
    print(f"Found {len(season_folders)} season folders: {[os.path.basename(f) for f in season_folders]}")
    
    # Process each season folder
    all_results = {}
    for season_folder in season_folders:
        season_results = process_season_folder(season_folder, batch_size, output_dir)
        all_results.update(season_results)
    
    # Save combined results
    if output_dir:
        # Save in the specified output directory
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        output_path = os.path.join(output_dir, output_file)
    else:
        # Save in the base directory
        output_path = os.path.join(base_dir, output_file)
        
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\nAll season results saved to: {output_path}")
    return all_results

def find_screenshots_dir():
    """Find the Screenshots directory used by test_extraction"""
    # Default Screenshots folder at same level as project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parent_dir = os.path.dirname(project_root)
    default_screenshots_folder = os.path.join(parent_dir, "Screenshots")
    
    if os.path.isdir(default_screenshots_folder):
        return default_screenshots_folder
    
    # Try alternative locations
    alt_screenshots = os.path.join(script_dir, "Screenshots")
    if os.path.isdir(alt_screenshots):
        return alt_screenshots
    
    return None

if __name__ == "__main__":
    # Check if API key is set
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable is not set")
        print("Set it by running: export ANTHROPIC_API_KEY=your-api-key-here")
        print("Or make sure your .env file contains: ANTHROPIC_API_KEY=your-api-key-here")
        sys.exit(1)
    
    # Create argument parser
    parser = argparse.ArgumentParser(description="Process Star Wars Squadrons screenshots by season")
    
    # Find the Screenshots directory
    default_base_dir = find_screenshots_dir()
    if not default_base_dir:
        default_base_dir = "Seasons"
    
    # Add arguments
    parser.add_argument("--base-dir", type=str, default=default_base_dir,
                        help=f"Base directory containing season folders (default: '{default_base_dir}')")
    parser.add_argument("--season", type=str,
                        help="Process only a specific season folder")
    parser.add_argument("--output", type=str, default="all_seasons_data.json",
                        help="Output filename for all combined results (default: 'all_seasons_data.json')")
    parser.add_argument("--output-dir", type=str, default="Extracted Results",
                        help="Directory to save the results (default: 'Extracted Results')")
    parser.add_argument("--batch-size", type=int, default=5,
                        help="Number of images to process in one batch (default: 5)")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Determine base directory
    base_dir = args.base_dir
    if not os.path.isdir(base_dir):
        # Try to find it relative to the script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)
        potential_base_dir = os.path.join(parent_dir, args.base_dir)
        
        if os.path.isdir(potential_base_dir):
            base_dir = potential_base_dir
        else:
            print(f"Error: Base directory not found at {args.base_dir} or {potential_base_dir}")
            sys.exit(1)
    
    # Set up output directory - use the specified output dir or a default in the project root
    output_dir = args.output_dir
    if output_dir:
        # Make sure it's an absolute path
        if not os.path.isabs(output_dir):
            output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), output_dir)
        
        # Ensure the directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
    
    # Process seasons
    if args.season:
        # Process only the specified season
        season_path = os.path.join(base_dir, args.season)
        if not os.path.isdir(season_path):
            print(f"Error: Season directory not found at {season_path}")
            sys.exit(1)
        
        process_season_folder(season_path, args.batch_size, output_dir)
    else:
        # Process all seasons
        process_all_seasons(base_dir, args.output, args.batch_size, output_dir)