import pytest
import os
import json
from unittest.mock import patch, MagicMock, call
from score_extractor.season_processor import (
    extract_date_from_filename,
    save_season_results,
    find_screenshots_dir,
    extract_scores_from_multiple_images,
    process_season_folder,
    process_all_seasons
)

# === Tests for extract_date_from_filename ===

@pytest.mark.parametrize("filename, expected_date", [
    # Standard YYYY.MM.DD format
    ("Screenshot_2023.10.25_15.30.00.png", "2023-10-25 15:30:00"),
    ("MyMatch-2024-01-15.jpg", "2024-01-15 12:00:00"), # No time, defaults to noon
    # Standard DD.MM.YYYY format
    ("Game_Capture_15.11.2023_SomeText.png", "2023-11-15 12:00:00"), # No time
    ("Match-01-02-2024-Stats.jpeg", "2024-02-01 12:00:00"), # No time
    # SW Squadrons format
    ("Star Wars Squadrons Screenshot 2022.09.24 - 00.17.55.76.png", "2022-09-24 00:17:55"),
    ("star wars squadrons screenshot 2023.05.01 - 14.05.10.123.jpg", "2023-05-01 14:05:10"), # Case insensitive
    # Mixed formats with time
    ("2023-12-25_20.05.30_match.png", "2023-12-25 20:05:30"),
    ("Screenshot 10.03.2024 18.45.15.png", "2024-03-10 18:45:15"),
    # No date
    ("random_image.png", None),
    ("MyGameStats.jpg", None),
    ("20231025_image.png", None), # Needs separators
])
def test_extract_date_from_filename(filename, expected_date):
    """Test extracting dates from various filename patterns"""
    assert extract_date_from_filename(filename) == expected_date

# === Fixture for dummy files ===

@pytest.fixture
def dummy_image_files(tmp_path):
    """Create dummy image files in a temporary directory"""
    img_dir = tmp_path / "images"
    img_dir.mkdir()
    files = {
        "match_2024-01-01_100000.png": img_dir / "match_2024-01-01_100000.png",
        "match_no_date.jpg": img_dir / "match_no_date.jpg",
        "error_image.png": img_dir / "error_image.png"
    }
    for file_path in files.values():
        file_path.touch() # Create empty files
    return files


# === Tests for extract_scores_from_multiple_images ===

# Define mock return values for extract_scores_from_image
MOCK_RESULTS = {
    "match_2024-01-01_100000.png": {"match_result": "IMPERIAL Victory", "teams": {"imperial": {"players": ["Player A"]}}},
    "match_no_date.jpg": {"match_result": "REBEL Victory", "teams": {"rebel": {"players": ["Player B"]}}},
}

# Define a side effect function for the mock
def mock_extract_side_effect(image_path):
    filename = os.path.basename(image_path)
    if filename == "error_image.png":
        raise ValueError("Simulated processing error")
    return MOCK_RESULTS.get(filename, {"error": "Unknown image"})

@patch('score_extractor.season_processor.extract_scores_from_image', side_effect=mock_extract_side_effect)
def test_extract_scores_from_multiple_images(mock_extract, dummy_image_files):
    """Test processing multiple images, mocking the AI call"""
    
    image_paths = list(dummy_image_files.values())
    results = extract_scores_from_multiple_images(image_paths)
    
    # Check that the mock was called for each image
    assert mock_extract.call_count == len(image_paths)
    mock_extract.assert_has_calls([
        call(dummy_image_files["match_2024-01-01_100000.png"]), # Compare Path objects directly
        call(dummy_image_files["match_no_date.jpg"]),          # Compare Path objects directly
        call(dummy_image_files["error_image.png"])             # Compare Path objects directly
    ], any_order=True) # Order might vary depending on listdir
    
    # Check the structure of the results dictionary
    assert len(results) == len(image_paths)
    assert "match_2024-01-01_100000.png" in results
    assert "match_no_date.jpg" in results
    assert "error_image.png" in results
    
    # Check successful extraction with date
    res1 = results["match_2024-01-01_100000.png"]
    assert res1["match_result"] == "IMPERIAL Victory"
    assert res1["match_date"] == "2024-01-01 12:00:00" # Default time added
    
    # Check successful extraction without date
    res2 = results["match_no_date.jpg"]
    assert res2["match_result"] == "REBEL Victory"
    assert "match_date" not in res2 # No date in filename
    
    # Check error handling
    res3 = results["error_image.png"]
    assert "error" in res3
    assert res3["error"] == "Simulated processing error"


# === Fixture for dummy season folder structure ===
@pytest.fixture
def dummy_season_folder(tmp_path):
    season_dir = tmp_path / "TestSeasonX"
    season_dir.mkdir()
    img1 = season_dir / "img1.png"
    img2 = season_dir / "img2.jpg"
    non_img = season_dir / "notes.txt"
    img1.touch()
    img2.touch()
    non_img.touch()
    return season_dir

# === Tests for process_season_folder ===

# Mock results for extract_scores_from_multiple_images used in season processing
MOCK_SEASON_IMG_RESULTS = {
    "img1.png": {"match_result": "Result 1"},
    "img2.jpg": {"match_result": "Result 2"},
}

@patch('score_extractor.season_processor.extract_scores_from_multiple_images', return_value=MOCK_SEASON_IMG_RESULTS)
@patch('score_extractor.season_processor.save_season_results')
def test_process_season_folder(mock_save, mock_extract, dummy_season_folder):
    """Test processing a single season folder"""
    output_dir = dummy_season_folder.parent / "Output" # Place output dir next to season dir
    
    season_results = process_season_folder(str(dummy_season_folder), output_dir=str(output_dir))
    
    season_name = "TestSeasonX"
    
    # Check that extract_scores_from_multiple_images was called correctly
    mock_extract.assert_called_once()
    call_args, _ = mock_extract.call_args
    # Check the list of image paths passed to the mock
    expected_paths = sorted([str(dummy_season_folder / "img1.png"), str(dummy_season_folder / "img2.jpg")])
    actual_paths = sorted(call_args[0])
    assert actual_paths == expected_paths
    
    # Check that save_season_results was called correctly
    mock_save.assert_called_once_with(
        str(dummy_season_folder),
        season_name,
        MOCK_SEASON_IMG_RESULTS,
        str(output_dir)
    )
    
    # Check the returned results
    assert season_name in season_results
    assert season_results[season_name] == MOCK_SEASON_IMG_RESULTS

# Test with batching
@patch('score_extractor.season_processor.extract_scores_from_multiple_images') # Mocked with side effect below
@patch('score_extractor.season_processor.save_season_results')
@patch('score_extractor.season_processor.time.sleep', return_value=None) # Mock sleep
def test_process_season_folder_batching(mock_sleep, mock_save, mock_extract, dummy_season_folder):
    """Test processing a single season folder with batching"""
    output_dir = dummy_season_folder.parent / "Output"
    batch_size = 1 # Process one image per batch
    
    # Modify mock to return results based on input filename for batching test
    def batch_mock_side_effect(image_paths):
        results = {}
        for path in image_paths:
            filename = os.path.basename(path)
            if filename == "img1.png":
                results[filename] = {"match_result": "Result 1"}
            elif filename == "img2.jpg":
                 results[filename] = {"match_result": "Result 2"}
        return results
        
    mock_extract.side_effect = batch_mock_side_effect

    season_results = process_season_folder(str(dummy_season_folder), batch_size=batch_size, output_dir=str(output_dir))
    
    season_name = "TestSeasonX"
    
    # Check that extract_scores_from_multiple_images was called twice (once per batch)
    assert mock_extract.call_count == 2
    
    # Check that save_season_results was called twice (once after each batch)
    assert mock_save.call_count == 2
    
    # Check the final returned results (should be combined from batches)
    assert season_name in season_results
    assert len(season_results[season_name]) == 2
    assert "img1.png" in season_results[season_name]
    assert "img2.jpg" in season_results[season_name]
    assert season_results[season_name]["img1.png"] == {"match_result": "Result 1"}
    assert season_results[season_name]["img2.jpg"] == {"match_result": "Result 2"}
    
    # Check sleep was called between batches
    assert mock_sleep.call_count == 1


# === Fixture for dummy base directory structure ===
@pytest.fixture
def dummy_base_dir(tmp_path):
    base = tmp_path / "SeasonsBase"
    base.mkdir()
    season1 = base / "S1"
    season2 = base / "S2"
    not_a_season = base / "config.txt"
    season1.mkdir()
    season2.mkdir()
    (season1 / "img1.png").touch()
    (season2 / "imgA.jpg").touch()
    (season2 / "imgB.png").touch()
    not_a_season.touch()
    return base

# === Tests for process_all_seasons ===

# Mock return value for process_season_folder used in all seasons test
MOCK_PROCESS_SEASON_RETURN = {
    "S1": {"img1.png": {"result": "S1R1"}}, # Note: structure is {season_name: results_dict}
    "S2": {"imgA.jpg": {"result": "S2RA"}, "imgB.png": {"result": "S2RB"}},
}

@patch('score_extractor.season_processor.process_season_folder',
       side_effect=lambda folder, batch, out_dir: {os.path.basename(folder): MOCK_PROCESS_SEASON_RETURN.get(os.path.basename(folder), {})})
def test_process_all_seasons(mock_process_season, dummy_base_dir):
    """Test processing multiple season folders"""
    output_dir = dummy_base_dir.parent / "AllOutput"
    output_file = "combined_results.json"
    
    all_results = process_all_seasons(str(dummy_base_dir), output_file=output_file, output_dir=str(output_dir))
    
    # Check that process_season_folder was called for each season directory
    assert mock_process_season.call_count == 2
    # Check calls were made with correct paths (order might vary)
    mock_process_season.assert_has_calls([
        call(str(dummy_base_dir / "S1"), None, str(output_dir)), # Default batch size is None
        call(str(dummy_base_dir / "S2"), None, str(output_dir))
    ], any_order=True)
    
    # Check the combined results dictionary structure {season_name: results_dict}
    assert "S1" in all_results
    assert "S2" in all_results
    assert all_results["S1"] == MOCK_PROCESS_SEASON_RETURN["S1"]
    assert all_results["S2"] == MOCK_PROCESS_SEASON_RETURN["S2"]
    
    # Check that the combined output file was created
    expected_output_path = output_dir / output_file
    assert expected_output_path.exists()
    
    # Check the content of the combined file
    with open(expected_output_path, 'r') as f:
        saved_data = json.load(f)
    assert saved_data == all_results