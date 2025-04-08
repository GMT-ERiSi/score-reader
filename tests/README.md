# Testing the Squadrons Stats Reader Project

This directory contains the automated tests for the Squadrons Stats Reader project, covering both the `score_extractor` and `stats_reader` components. The tests utilize the `pytest` framework.

## Running the Tests

1.  **Ensure Dependencies are Installed:** Make sure you have installed the project's dependencies, including `pytest`. You can typically install them using the `requirements.txt` file:
    ```powershell
    # Ensure pip is available in your PATH
    pip install -r requirements.txt
    ```
2.  **Navigate to the Project Root:** Open your terminal (like PowerShell, cmd, bash, etc.) and navigate to the main project directory (`Screenshot Reader Project`).
3.  **Run Pytest:** Execute the following command (this works across different terminals like PowerShell, cmd, bash):
    ```powershell
    pytest
    ```
    Pytest will automatically discover and run all tests within the `tests` directory and its subdirectories (like `stats_reader/test_elo_ladder.py`).

## Test Structure

*   **`tests/test_score_extractor.py`**: Contains unit tests for the `score_extractor/season_processor.py` module. These tests focus on individual functions like filename parsing, date extraction, and the overall processing flow for seasons and multiple images. They heavily use mocking to isolate the tested functions from external dependencies (like AI image analysis).
*   **`tests/test_stats_reader.py`**: Contains integration tests for the `stats_reader/stats_db_processor.py` module and related components like `elo_ladder.py` and `reference_manager.py`.
    *   It uses a test data file (`tests/test_data/all_seasons_data_test.json`) which mimics the structure of the real extracted data.
    *   A fixture (`processed_db_conn`) runs the core `process_seasons_data` function to populate a temporary SQLite database (`tests/test_squadrons_stats.db`) using the test data file.
    *   Tests then verify the database population, report generation (`generate_stats_reports`), and ELO calculations (`generate_elo_ladder`) based on the data processed from the test file.
*   **`stats_reader/test_elo_ladder.py`**: Contains specific unit tests for the ELO calculation logic in `stats_reader/elo_ladder.py`. These tests create their own temporary database with specific match scenarios to verify the ELO formulas and ladder generation independent of the main data processing flow.
*   **`tests/test_data/all_seasons_data_test.json`**: A sample JSON file containing data structured similarly to the output of the `score_extractor`. This file is used by `tests/test_stats_reader.py` to populate the test database for integration testing.
*   **`tests/test_squadrons_stats.db`**: A temporary SQLite database created and destroyed during the execution of `tests/test_stats_reader.py`. It holds the processed data from `all_seasons_data_test.json`.
*   **`tests/test_reports/`**: A temporary directory created and destroyed during the execution of `tests/test_stats_reader.py`. It holds the generated JSON report files (standings, player stats, ELO ladder, etc.) for verification.

## Expected Results

When running `pytest`, all discovered tests should pass without errors. The output will indicate the number of tests passed, failed, or skipped. Temporary files and directories created during the tests (like the test database and reports directory) will be automatically cleaned up by the test fixtures upon completion.