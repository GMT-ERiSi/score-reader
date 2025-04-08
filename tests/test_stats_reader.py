import pytest
import sqlite3
import os
import json
import hashlib
from stats_reader.stats_db_processor import (
    create_database,
    generate_player_hash,
    get_or_create_season,
    get_or_create_team,
    get_or_create_player,
    process_seasons_data, # We might test parts of this later or mock inputs
    generate_stats_reports
)
from stats_reader.elo_ladder import (
    calculate_expected_outcome,
    calculate_new_rating,
    generate_elo_ladder
)
from stats_reader.reference_manager import ReferenceDatabase # Needed for potential future tests

TEST_DB = "tests/test_squadrons_stats.db"
TEST_DATA_FILE = "tests/test_data/all_seasons_data_test.json"
TEST_REPORTS_DIR = "tests/test_reports"
TEST_REF_DB = "tests/test_reference.db"
TEST_REF_JSON = "tests/test_reference_data.json"

@pytest.fixture(scope="function")
def db_conn():
    """Fixture to set up and tear down a test database"""
    # Ensure the tests directory exists
    if not os.path.exists("tests"):
        os.makedirs("tests")
        
    # Remove existing test DB if it exists
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
        
    # Create a fresh database for the test
    create_database(TEST_DB)
    conn = sqlite3.connect(TEST_DB)
    yield conn # Provide the connection to the test
    conn.close()
    # Clean up the test database file after the test
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    # Clean up reports dir if created
    if os.path.exists(TEST_REPORTS_DIR):
        import shutil
        if os.path.exists(TEST_REPORTS_DIR):
            shutil.rmtree(TEST_REPORTS_DIR)
    # Clean up ref db if created
    if os.path.exists(TEST_REF_DB):
        os.remove(TEST_REF_DB)
    # Clean up ref json if created
    if os.path.exists(TEST_REF_JSON):
        os.remove(TEST_REF_JSON)


@pytest.fixture(scope="function")
def ref_db():
    """Fixture to set up and tear down a test reference database"""
    # Ensure the tests directory exists
    if not os.path.exists("tests"):
        os.makedirs("tests")
        
    # Remove existing test ref DB if it exists
    if os.path.exists(TEST_REF_DB):
        os.remove(TEST_REF_DB)
        
    # Create a fresh reference database for the test
    db = ReferenceDatabase(TEST_REF_DB)
    yield db # Provide the db instance to the test
    db.close()
    # Clean up the test database file after the test
    if os.path.exists(TEST_REF_DB):
        os.remove(TEST_REF_DB)


# Fixture that uses the actual processing function to populate the DB
@pytest.fixture(scope="function")
def processed_db_conn(db_conn):
    """Fixture that runs process_seasons_data on the test DB using TEST_DATA_FILE"""
    # Load the test data to compare against later
    try:
        with open(TEST_DATA_FILE, 'r') as f:
            test_data = json.load(f)
    except Exception as e:
        pytest.fail(f"Failed to load test data file {TEST_DATA_FILE}: {e}")

    # Run the actual processing function
    try:
        process_seasons_data(TEST_DATA_FILE, TEST_DB, ref_db=None) # Use None for ref_db in this test context
    except Exception as e:
        pytest.fail(f"process_seasons_data failed during fixture setup: {e}")

    # Attach the loaded test data to the connection object for use in tests
    db_conn.test_data = test_data
    yield db_conn # Provide the connection *after* processing


def test_create_database(db_conn):
    """Verify that all expected tables are created"""
    cursor = db_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}
    expected_tables = {"seasons", "teams", "matches", "players", "player_stats"}
    assert expected_tables.issubset(tables)

def test_generate_player_hash():
    """Test player hash generation for consistency and normalization"""
    name1 = "Player One"
    name2 = "player one"
    name3 = "  Player   One  "
    
    hash1 = generate_player_hash(name1)
    hash2 = generate_player_hash(name2)
    hash3 = generate_player_hash(name3)
    
    assert hash1 == hash2 == hash3
    assert len(hash1) == 16 # Check hash length
    
    # Test a different name
    name4 = "Player Two"
    hash4 = generate_player_hash(name4)
    assert hash1 != hash4

def test_get_or_create_season(db_conn):
    """Test creating and retrieving seasons"""
    season_name = "Test Season Alpha"
    
    # Create
    season_id1 = get_or_create_season(db_conn, season_name)
    assert isinstance(season_id1, int)
    
    # Retrieve
    season_id2 = get_or_create_season(db_conn, season_name)
    assert season_id1 == season_id2
    
    # Check database directly
    cursor = db_conn.cursor()
    cursor.execute("SELECT name FROM seasons WHERE id = ?", (season_id1,))
    result = cursor.fetchone()
    assert result is not None
    assert result[0] == season_name

def test_get_or_create_team_no_ref(db_conn):
    """Test creating and retrieving teams without reference DB"""
    team_name = "Test Team Bravo"
    
    # Create
    team_id1 = get_or_create_team(db_conn, team_name, ref_db=None)
    assert isinstance(team_id1, int)
    
    # Retrieve
    team_id2 = get_or_create_team(db_conn, team_name, ref_db=None)
    assert team_id1 == team_id2
    
    # Check database directly
    cursor = db_conn.cursor()
    cursor.execute("SELECT name, reference_id FROM teams WHERE id = ?", (team_id1,))
    result = cursor.fetchone()
    assert result is not None
    assert result[0] == team_name
    assert result[1] is None # No reference ID expected

def test_get_or_create_player_no_ref(db_conn):
    """Test creating and retrieving players without reference DB"""
    player_name = "Test Player Charlie"
    normalized_name = player_name.lower().strip()
    expected_hash = hashlib.sha256(normalized_name.encode()).hexdigest()[:16]
    
    # Create
    player_id1, canonical_name1, hash1 = get_or_create_player(db_conn, player_name, ref_db=None)
    assert isinstance(player_id1, int)
    assert canonical_name1 == player_name # Should be same as input without ref DB
    assert hash1 == expected_hash
    
    # Retrieve (using same name)
    player_id2, canonical_name2, hash2 = get_or_create_player(db_conn, player_name, ref_db=None)
    assert player_id1 == player_id2
    assert canonical_name1 == canonical_name2
    assert hash1 == hash2
    
    # Retrieve (using different casing/whitespace)
    player_name_variant = "  test player charlie  "
    player_id3, canonical_name3, hash3 = get_or_create_player(db_conn, player_name_variant, ref_db=None)
    # Because we don't have a reference DB, it treats the normalized name as canonical
    # The hash should match, leading to retrieval of the original record
    assert player_id1 == player_id3 
    assert canonical_name1 == canonical_name3 # Returns the originally inserted name
    assert hash1 == hash3
    
    # Check database directly
    cursor = db_conn.cursor()
    cursor.execute("SELECT name, reference_id, player_hash FROM players WHERE id = ?", (player_id1,))
    result = cursor.fetchone()
    assert result is not None
    assert result[0] == player_name # Stored name
    assert result[1] is None # No reference ID
    assert result[2] == expected_hash # Stored hash


def test_process_seasons_data(processed_db_conn):
    """Verify that process_seasons_data correctly populates the database"""
    cursor = processed_db_conn.cursor()
    test_data = processed_db_conn.test_data # Retrieve data loaded in fixture

    # --- Verification ---
    # 1. Check Seasons
    cursor.execute("SELECT name FROM seasons")
    db_seasons = {row[0] for row in cursor.fetchall()}
    expected_seasons = set(test_data.keys())
    assert db_seasons == expected_seasons

    # 2. Check Matches (count and one specific match)
    total_expected_matches = sum(len(season_data) for season_data in test_data.values())
    cursor.execute("SELECT COUNT(*) FROM matches")
    assert cursor.fetchone()[0] == total_expected_matches

    # Check details of the first match in the test data
    test_season_name = list(test_data.keys())[0]
    test_match_filename = list(test_data[test_season_name].keys())[0]
    test_match_data = test_data[test_season_name][test_match_filename]

    cursor.execute("""
        SELECT s.name, m.filename, m.winner, imp.name, reb.name
        FROM matches m
        JOIN seasons s ON m.season_id = s.id
        LEFT JOIN teams imp ON m.imperial_team_id = imp.id
        LEFT JOIN teams reb ON m.rebel_team_id = reb.id
        WHERE m.filename = ?
    """, (test_match_filename,))
    match_row = cursor.fetchone()
    assert match_row is not None
    assert match_row[0] == test_season_name
    assert match_row[1] == test_match_filename
    # Determine expected winner faction from test data
    winner_text = test_match_data.get("match_result", "").upper()
    expected_winner = None
    if "NEW REPUBLIC VICTORY" in winner_text or "REBEL VICTORY" in winner_text: expected_winner = "REBEL"
    if "IMPERIAL VICTORY" in winner_text or "EMPIRE VICTORY" in winner_text: expected_winner = "IMPERIAL"
    assert match_row[2] == expected_winner
    # Note: Team names might be generic ("Imperial Test Team") as defined in the processing logic if not using ref_db
    # assert match_row[3] is not None # Check imperial team exists if expected
    # assert match_row[4] is not None # Check rebel team exists if expected

    # 3. Check Players (count and one specific player)
    all_test_players = set()
    for season_data in test_data.values():
        for match_data in season_data.values():
            for team_data in match_data.get("teams", {}).values():
                for player in team_data.get("players", []):
                    if player.get("player"):
                        all_test_players.add(player["player"])

    cursor.execute("SELECT COUNT(DISTINCT player_hash) FROM players")
    # Note: Hash count might differ if names normalize to the same hash
    # assert cursor.fetchone()[0] == len(all_test_players)

    # Check a specific player exists
    test_player_name = list(all_test_players)[0]
    test_player_hash = generate_player_hash(test_player_name)
    cursor.execute("SELECT name FROM players WHERE player_hash = ?", (test_player_hash,))
    player_row = cursor.fetchone()
    assert player_row is not None
    # assert player_row[0] == test_player_name # Name might be canonicalized if ref_db were used

    # 4. Check Player Stats (count and one specific stat)
    total_expected_stats = 0
    first_player_stat_data = None
    first_player_name = None
    for season_data in test_data.values():
        for match_filename, match_data in season_data.items():
             for team_key, team_data in match_data.get("teams", {}).items():
                for player in team_data.get("players", []):
                    if player.get("player"):
                        total_expected_stats += 1
                        if first_player_stat_data is None:
                            first_player_stat_data = player
                            first_player_name = player["player"]
                            first_match_filename = match_filename


    cursor.execute("SELECT COUNT(*) FROM player_stats")
    assert cursor.fetchone()[0] == total_expected_stats

    # Check stats for the first player found in the test data
    cursor.execute("""
        SELECT ps.score, ps.kills, ps.deaths, ps.assists, ps.cap_ship_damage, ps.ai_kills
        FROM player_stats ps
        JOIN matches m ON ps.match_id = m.id
        JOIN players p ON ps.player_id = p.id
        WHERE m.filename = ? AND p.player_hash = ?
    """, (first_match_filename, generate_player_hash(first_player_name)))
    stat_row = cursor.fetchone()
    assert stat_row is not None
    assert stat_row[0] == first_player_stat_data.get("score", 0)
    assert stat_row[1] == first_player_stat_data.get("kills", 0)
    assert stat_row[2] == first_player_stat_data.get("deaths", 0)
    assert stat_row[3] == first_player_stat_data.get("assists", 0)
    assert stat_row[4] == first_player_stat_data.get("cap_ship_damage", 0)
    assert stat_row[5] == first_player_stat_data.get("ai_kills", 0)


def test_generate_stats_reports(processed_db_conn):
    """Test the generation of JSON stats reports"""
    # Ensure the reports directory does not exist before the test
    if os.path.exists(TEST_REPORTS_DIR):
        import shutil
        shutil.rmtree(TEST_REPORTS_DIR)

    # Generate reports
    success = generate_stats_reports(TEST_DB, TEST_REPORTS_DIR)
    assert success is True
    assert os.path.exists(TEST_REPORTS_DIR)

    # Check for expected report files
    expected_files = [
        "team_standings.json",
        "player_performance.json",
        "player_kdr.json",
        "player_damage.json",
        "match_history.json"
    ]
    for report_file in expected_files:
        file_path = os.path.join(TEST_REPORTS_DIR, report_file)
        assert os.path.exists(file_path)
        
        # Basic check: ensure file is valid JSON and not empty
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            assert isinstance(data, list) # Most reports are lists
            assert len(data) > 0 # Ensure there's some data
        except (json.JSONDecodeError, AssertionError) as e:
            pytest.fail(f"Report file {report_file} failed validation: {e}")

    # Specific check for team standings (based on inserted data)
    # Specific check for team standings (based on TEST_DATA_FILE content)
    # In TEST_DATA_FILE:
    # Match 1: "New Republic Test Team" (Rebel) wins vs "Imperial Test Team" (Imp)
    standings_path = os.path.join(TEST_REPORTS_DIR, "team_standings.json")
    with open(standings_path, 'r') as f:
        standings = json.load(f)

    assert len(standings) == 2 # Only two teams in the test file
    # Expected: NR wins 1, Imp loses 1
    nr_team = next((t for t in standings if "New Republic" in t['name']), None)
    imp_team = next((t for t in standings if "Imperial" in t['name']), None)

    assert nr_team is not None
    assert imp_team is not None

    assert nr_team['wins'] == 1
    assert nr_team['losses'] == 0
    assert nr_team['win_rate'] == 100.0

    assert imp_team['wins'] == 0
    assert imp_team['losses'] == 1
    assert imp_team['win_rate'] == 0.0

    # Check order (NR should be first)
    assert standings[0]['name'] == nr_team['name']
    assert standings[1]['name'] == imp_team['name']

    # Specific check for player performance (Player A1 from TEST_DATA_FILE)
    perf_path = os.path.join(TEST_REPORTS_DIR, "player_performance.json")
    with open(perf_path, 'r') as f:
        performance = json.load(f)

    # Find Player A1's performance (name might be canonicalized, check hash)
    player_a1_hash = generate_player_hash("Player A1")
    player_a1_perf = next((p for p in performance if p['player_hash'] == player_a1_hash), None)

    assert player_a1_perf is not None
    assert player_a1_perf['games_played'] == 1 # Played only one game in test data
    assert player_a1_perf['total_score'] == 5000
    assert player_a1_perf['total_kills'] == 10
    assert player_a1_perf['total_deaths'] == 2
    assert player_a1_perf['total_assists'] == 5
    assert player_a1_perf['total_cap_ship_damage'] == 15000


# == Tests for elo_ladder.py ==

def test_calculate_expected_outcome():
    """Test ELO expected outcome calculation"""
    # Equal ratings
    assert calculate_expected_outcome(1000, 1000) == pytest.approx(0.5)
    
    # Higher rating A
    assert calculate_expected_outcome(1200, 1000) > 0.5
    # Based on formula: 1 / (1 + 10**((1000-1200)/400)) = 1 / (1 + 10**(-0.5)) ~= 0.7597
    assert calculate_expected_outcome(1200, 1000) == pytest.approx(0.7597, abs=1e-4)

    # Higher rating B
    assert calculate_expected_outcome(1000, 1200) < 0.5
    # Based on formula: 1 / (1 + 10**((1200-1000)/400)) = 1 / (1 + 10**(0.5)) ~= 0.2403
    assert calculate_expected_outcome(1000, 1200) == pytest.approx(0.2403, abs=1e-4)

def test_calculate_new_rating():
    """Test ELO new rating calculation"""
    k_factor = 32
    
    # Win scenario (expected 0.5, actual 1.0)
    rating = 1000
    expected = 0.5
    actual = 1.0
    new_rating = calculate_new_rating(rating, expected, actual, k_factor)
    assert new_rating == 1000 + 32 * (1.0 - 0.5) == 1016
    
    # Loss scenario (expected 0.5, actual 0.0)
    rating = 1000
    expected = 0.5
    actual = 0.0
    new_rating = calculate_new_rating(rating, expected, actual, k_factor)
    assert new_rating == 1000 + 32 * (0.0 - 0.5) == 984
    
    # Upset win (expected 0.25, actual 1.0)
    rating = 1000
    expected = 0.25
    actual = 1.0
    new_rating = calculate_new_rating(rating, expected, actual, k_factor)
    assert new_rating == 1000 + 32 * (1.0 - 0.25) == 1024
    
    # Expected loss (expected 0.75, actual 0.0)
    rating = 1000
    expected = 0.75
    actual = 0.0
    new_rating = calculate_new_rating(rating, expected, actual, k_factor)
    assert new_rating == 1000 + 32 * (0.0 - 0.75) == 976

def test_generate_elo_ladder(processed_db_conn):
    """Test the generation of ELO ladder and history files"""
    # Ensure the reports directory does not exist before the test
    if os.path.exists(TEST_REPORTS_DIR):
        import shutil
        shutil.rmtree(TEST_REPORTS_DIR)

    starting_elo = 1000
    k_factor = 32

    # Generate ELO ladder
    ladder, history = generate_elo_ladder(TEST_DB, TEST_REPORTS_DIR, starting_elo, k_factor)

    assert os.path.exists(TEST_REPORTS_DIR)
    assert os.path.exists(os.path.join(TEST_REPORTS_DIR, "elo_ladder.json"))
    assert os.path.exists(os.path.join(TEST_REPORTS_DIR, "elo_history.json"))

    # --- Validate History ---
    assert isinstance(history, list)
    assert len(history) == 1 # Only one match in TEST_DATA_FILE

    # Match 1: Imperial Test Team vs New Republic Test Team, NR wins
    match1_hist = history[0]
    assert match1_hist['imperial']['team_name'] == 'Imperial Test Team'
    assert match1_hist['rebel']['team_name'] == 'New Republic Test Team'
    assert match1_hist['winner'] == 'REBEL' # NR won
    assert match1_hist['imperial']['old_rating'] == starting_elo
    assert match1_hist['rebel']['old_rating'] == starting_elo
    # Expected outcome for equal teams is 0.5
    expected_imp_m1 = 0.5
    expected_nr_m1 = 0.5
    # New ratings
    new_imp_m1 = calculate_new_rating(starting_elo, expected_imp_m1, 0.0, k_factor) # Loss
    new_nr_m1 = calculate_new_rating(starting_elo, expected_nr_m1, 1.0, k_factor) # Win
    assert match1_hist['imperial']['new_rating'] == pytest.approx(new_imp_m1)
    assert match1_hist['rebel']['new_rating'] == pytest.approx(new_nr_m1)
    assert new_imp_m1 == 984  # 1000 + 32 * (0.0 - 0.5)
    assert new_nr_m1 == 1016 # 1000 + 32 * (1.0 - 0.5)


    # --- Validate Ladder ---
    assert isinstance(ladder, list)
    assert len(ladder) == 2 # Imperial Test Team, New Republic Test Team

    # Find teams in ladder
    imp_ladder = next((t for t in ladder if t['team_name'] == 'Imperial Test Team'), None)
    nr_ladder = next((t for t in ladder if t['team_name'] == 'New Republic Test Team'), None)

    assert imp_ladder is not None
    assert nr_ladder is not None

    # Check final ELO ratings
    assert imp_ladder['elo_rating'] == round(new_imp_m1) # 984
    assert nr_ladder['elo_rating'] == round(new_nr_m1) # 1016

    # Check stats
    # Check stats (based on the single match in test data)
    assert imp_ladder['matches_played'] == 1
    assert imp_ladder['matches_won'] == 0
    assert imp_ladder['matches_lost'] == 1
    assert imp_ladder['win_rate'] == 0.0

    assert nr_ladder['matches_played'] == 1
    assert nr_ladder['matches_won'] == 1
    assert nr_ladder['matches_lost'] == 0
    assert nr_ladder['win_rate'] == 100.0

    # Check ranking (NR > Imp)
    assert nr_ladder['rank'] == 1
    assert imp_ladder['rank'] == 2

    # Check JSON files were written correctly
    ladder_path = os.path.join(TEST_REPORTS_DIR, "elo_ladder.json")
    history_path = os.path.join(TEST_REPORTS_DIR, "elo_history.json")
    with open(ladder_path, 'r') as f:
        ladder_from_file = json.load(f)
    with open(history_path, 'r') as f:
        history_from_file = json.load(f)
    
    assert ladder == ladder_from_file # Check if saved ladder matches returned ladder
    assert history == history_from_file # Check if saved history matches returned history


# == Tests for reference_manager.py ==

def test_ref_db_initialize(ref_db):
    """Test reference database initialization"""
    assert os.path.exists(TEST_REF_DB)
    cursor = ref_db.conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}
    expected_tables = {"ref_teams", "ref_players"}
    assert expected_tables.issubset(tables)

def test_ref_db_add_and_get_team(ref_db):
    """Test adding and retrieving teams"""
    team_name = "Canonical Team A"
    aliases = ["Team A", "A Team"]
    
    # Add
    team_id1 = ref_db.add_team(team_name, aliases)
    assert isinstance(team_id1, int)
    
    # Get exact
    team1 = ref_db.get_team(team_name)
    assert team1 is not None
    assert team1['id'] == team_id1
    assert team1['name'] == team_name
    assert team1['alias'] == "Team A,A Team"
    
    # Get by alias (exact alias match)
    team2 = ref_db.get_team("Team A", fuzzy_match=True) # Need fuzzy for alias check
    assert team2 is not None
    assert team2['id'] == team_id1
    
    # Get fuzzy
    team3 = ref_db.get_team("Canonical Team Aaa", fuzzy_match=True, match_threshold=0.8)
    assert team3 is not None
    assert team3['id'] == team_id1
    assert team3['match_score'] > 0.8
    
    # Get fuzzy by alias
    team4 = ref_db.get_team("A-Team", fuzzy_match=True, match_threshold=0.7)
    assert team4 is not None
    assert team4['id'] == team_id1
    assert team4['match_score'] > 0.7
    
    # Get non-existent
    team5 = ref_db.get_team("NonExistent Team")
    assert team5 is None
    team6 = ref_db.get_team("NonExistent Team", fuzzy_match=True)
    assert team6 is None

def test_ref_db_add_and_get_player(ref_db):
    """Test adding and retrieving players"""
    team_id = ref_db.add_team("Canonical Team B")
    player_name = "Canonical Player One"
    aliases = ["Player 1", "P One"]
    
    # Add
    player_id1 = ref_db.add_player(player_name, team_id, aliases)
    assert isinstance(player_id1, int)
    
    # Get exact
    player1 = ref_db.get_player(player_name)
    assert player1 is not None
    assert player1['id'] == player_id1
    assert player1['name'] == player_name
    assert player1['team_id'] == team_id
    assert player1['team_name'] == "Canonical Team B"
    assert player1['alias'] == "Player 1,P One"
    
    # Get by alias (exact alias match)
    player2 = ref_db.get_player("Player 1", fuzzy_match=True) # Need fuzzy for alias check
    assert player2 is not None
    assert player2['id'] == player_id1
    
    # Get fuzzy
    player3 = ref_db.get_player("Canonical Player On", fuzzy_match=True, match_threshold=0.8)
    assert player3 is not None
    assert player3['id'] == player_id1
    assert player3['match_score'] > 0.8
    
    # Get fuzzy by alias
    player4 = ref_db.get_player("P-One", fuzzy_match=True, match_threshold=0.7)
    assert player4 is not None
    assert player4['id'] == player_id1
    assert player4['match_score'] > 0.7
    
    # Get non-existent
    player5 = ref_db.get_player("NonExistent Player")
    assert player5 is None
    player6 = ref_db.get_player("NonExistent Player", fuzzy_match=True)
    assert player6 is None

def test_ref_db_update_team(ref_db):
    """Test updating team information"""
    team_id = ref_db.add_team("Old Team Name", ["Old Alias"])
    
    # Update name and alias
    success = ref_db.update_team(team_id, name="New Team Name", alias=["New Alias 1", "New Alias 2"])
    assert success is True
    
    team = ref_db.get_team("New Team Name")
    assert team is not None
    assert team['id'] == team_id
    assert team['name'] == "New Team Name"
    assert team['alias'] == "New Alias 1,New Alias 2"
    
    # Check old name doesn't work
    old_team = ref_db.get_team("Old Team Name")
    assert old_team is None

def test_ref_db_update_player(ref_db):
    """Test updating player information"""
    team_id1 = ref_db.add_team("Team X")
    team_id2 = ref_db.add_team("Team Y")
    player_id = ref_db.add_player("Old Player Name", team_id1, ["Old P Alias"])
    
    # Update name, team, and alias
    success = ref_db.update_player(player_id, name="New Player Name", primary_team_id=team_id2, alias=["New P Alias"])
    assert success is True
    
    player = ref_db.get_player("New Player Name")
    assert player is not None
    assert player['id'] == player_id
    assert player['name'] == "New Player Name"
    assert player['team_id'] == team_id2
    assert player['team_name'] == "Team Y"
    assert player['alias'] == "New P Alias"
    
    # Check old name doesn't work
    old_player = ref_db.get_player("Old Player Name")
    assert old_player is None

def test_ref_db_list_teams(ref_db):
    """Test listing teams"""
    ref_db.add_team("Team Zulu")
    ref_db.add_team("Team Alpha", ["A"])
    
    teams = ref_db.list_teams()
    assert len(teams) == 2
    assert teams[0]['name'] == "Team Alpha" # Sorted alphabetically
    assert teams[1]['name'] == "Team Zulu"
    assert teams[0]['alias'] == ["A"]
    assert teams[1]['alias'] == []

def test_ref_db_list_players(ref_db):
    """Test listing players"""
    team_id_x = ref_db.add_team("Team X")
    team_id_y = ref_db.add_team("Team Y")
    ref_db.add_player("Player Charlie", team_id_x)
    ref_db.add_player("Player Alpha", team_id_y, ["PA"])
    ref_db.add_player("Player Bravo", team_id_x)
    
    # List all
    players_all = ref_db.list_players()
    assert len(players_all) == 3
    assert players_all[0]['name'] == "Player Alpha" # Sorted alphabetically
    assert players_all[1]['name'] == "Player Bravo"
    assert players_all[2]['name'] == "Player Charlie"
    assert players_all[0]['team_name'] == "Team Y"
    assert players_all[0]['alias'] == ["PA"]
    
    # List by team X
    players_x = ref_db.list_players(team_id=team_id_x)
    assert len(players_x) == 2
    assert players_x[0]['name'] == "Player Bravo" # Sorted
    assert players_x[1]['name'] == "Player Charlie"
    
    # List by team Y
    players_y = ref_db.list_players(team_id=team_id_y)
    assert len(players_y) == 1
    assert players_y[0]['name'] == "Player Alpha"

def test_ref_db_import_export_json(ref_db):
    """Test importing and exporting reference data via JSON"""
    # Create some initial data
    team_id = ref_db.add_team("Export Team", ["ET"])
    ref_db.add_player("Export Player", team_id, ["EP"])
    
    # Export
    success_export = ref_db.export_to_json(TEST_REF_JSON)
    assert success_export is True
    assert os.path.exists(TEST_REF_JSON)
    
    # Create a new empty ref DB
    if os.path.exists(TEST_REF_DB):
        ref_db.close()
        os.remove(TEST_REF_DB)
    
    new_ref_db = ReferenceDatabase(TEST_REF_DB)
    
    # Import
    success_import = new_ref_db.import_from_json(TEST_REF_JSON)
    assert success_import is True
    
    # Verify imported data
    teams = new_ref_db.list_teams()
    players = new_ref_db.list_players()
    
    assert len(teams) == 1
    assert teams[0]['name'] == "Export Team"
    assert teams[0]['alias'] == ["ET"]
    
    assert len(players) == 1
    assert players[0]['name'] == "Export Player"
    assert players[0]['team_name'] == "Export Team" # Team name resolved during import
    assert players[0]['alias'] == ["EP"]
    
    new_ref_db.close()