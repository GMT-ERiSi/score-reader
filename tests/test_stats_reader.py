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


# Fixture to provide a populated database connection
@pytest.fixture(scope="function")
def populated_db_conn(db_conn):
    """Fixture to set up a test database and populate it with sample data"""
    cursor = db_conn.cursor()

    # Insert sample data
    # Seasons
    cursor.execute("INSERT INTO seasons (name) VALUES (?)", ("TestSeason1",))
    season_id = cursor.lastrowid

    # Teams
    cursor.execute("INSERT INTO teams (name) VALUES (?)", ("Alpha Team",))
    alpha_id = cursor.lastrowid
    cursor.execute("INSERT INTO teams (name) VALUES (?)", ("Bravo Team",))
    bravo_id = cursor.lastrowid
    cursor.execute("INSERT INTO teams (name) VALUES (?)", ("Charlie Team",))
    charlie_id = cursor.lastrowid

    # Players (using generate_player_hash for consistency)
    players = {
        "Player A1": {"id": None, "hash": generate_player_hash("Player A1")},
        "Player A2": {"id": None, "hash": generate_player_hash("Player A2")},
        "Player A3": {"id": None, "hash": generate_player_hash("Player A3")},
        "Player B1": {"id": None, "hash": generate_player_hash("Player B1")},
        "Player B2": {"id": None, "hash": generate_player_hash("Player B2")},
        "Player C1": {"id": None, "hash": generate_player_hash("Player C1")},
        "Player C2": {"id": None, "hash": generate_player_hash("Player C2")},
    }
    for name, data in players.items():
        cursor.execute("INSERT INTO players (name, player_hash) VALUES (?, ?)", (name, data["hash"]))
        data["id"] = cursor.lastrowid

    # Match 1: Alpha vs Bravo (Alpha wins)
    cursor.execute("""
        INSERT INTO matches (season_id, imperial_team_id, rebel_team_id, winner, filename, match_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (season_id, alpha_id, bravo_id, "IMPERIAL", "dummy_match1.png", "2025-08-04 10:00:00"))
    match1_id = cursor.lastrowid
    # Player Stats Match 1
    cursor.execute("""INSERT INTO player_stats (match_id, player_id, player_name, player_hash, team_id, faction, score, kills, deaths, assists, cap_ship_damage) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                   (match1_id, players["Player A1"]["id"], "Player A1", players["Player A1"]["hash"], alpha_id, "IMPERIAL", 5000, 10, 2, 5, 15000))
    cursor.execute("""INSERT INTO player_stats (match_id, player_id, player_name, player_hash, team_id, faction, score, kills, deaths, assists, cap_ship_damage) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                   (match1_id, players["Player A2"]["id"], "Player A2", players["Player A2"]["hash"], alpha_id, "IMPERIAL", 4500, 8, 3, 6, 12000))
    cursor.execute("""INSERT INTO player_stats (match_id, player_id, player_name, player_hash, team_id, faction, score, kills, deaths, assists, cap_ship_damage) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                   (match1_id, players["Player B1"]["id"], "Player B1", players["Player B1"]["hash"], bravo_id, "REBEL", 3000, 5, 4, 3, 8000))
    cursor.execute("""INSERT INTO player_stats (match_id, player_id, player_name, player_hash, team_id, faction, score, kills, deaths, assists, cap_ship_damage) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                   (match1_id, players["Player B2"]["id"], "Player B2", players["Player B2"]["hash"], bravo_id, "REBEL", 2500, 4, 5, 2, 5000))
    # Update team wins/losses for Match 1
    cursor.execute("UPDATE teams SET wins = wins + 1 WHERE id = ?", (alpha_id,))
    cursor.execute("UPDATE teams SET losses = losses + 1 WHERE id = ?", (bravo_id,))


    # Match 2: Alpha vs Charlie (Charlie wins)
    cursor.execute("""
        INSERT INTO matches (season_id, imperial_team_id, rebel_team_id, winner, filename, match_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (season_id, alpha_id, charlie_id, "REBEL", "dummy_match2.png", "2025-08-04 11:00:00"))
    match2_id = cursor.lastrowid
    # Player Stats Match 2
    cursor.execute("""INSERT INTO player_stats (match_id, player_id, player_name, player_hash, team_id, faction, score, kills, deaths, assists, cap_ship_damage) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                   (match2_id, players["Player A1"]["id"], "Player A1", players["Player A1"]["hash"], alpha_id, "IMPERIAL", 3500, 6, 5, 4, 10000))
    cursor.execute("""INSERT INTO player_stats (match_id, player_id, player_name, player_hash, team_id, faction, score, kills, deaths, assists, cap_ship_damage) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                   (match2_id, players["Player A3"]["id"], "Player A3", players["Player A3"]["hash"], alpha_id, "IMPERIAL", 3000, 5, 6, 3, 9000)) # New player A3
    cursor.execute("""INSERT INTO player_stats (match_id, player_id, player_name, player_hash, team_id, faction, score, kills, deaths, assists, cap_ship_damage) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                   (match2_id, players["Player C1"]["id"], "Player C1", players["Player C1"]["hash"], charlie_id, "REBEL", 6000, 12, 3, 7, 20000))
    cursor.execute("""INSERT INTO player_stats (match_id, player_id, player_name, player_hash, team_id, faction, score, kills, deaths, assists, cap_ship_damage) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                   (match2_id, players["Player C2"]["id"], "Player C2", players["Player C2"]["hash"], charlie_id, "REBEL", 5500, 10, 4, 8, 18000))
    # Update team wins/losses for Match 2
    cursor.execute("UPDATE teams SET losses = losses + 1 WHERE id = ?", (alpha_id,))
    cursor.execute("UPDATE teams SET wins = wins + 1 WHERE id = ?", (charlie_id,))

    db_conn.commit()
    yield db_conn # Provide the populated connection


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


def test_generate_stats_reports(populated_db_conn):
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
    standings_path = os.path.join(TEST_REPORTS_DIR, "team_standings.json")
    with open(standings_path, 'r') as f:
        standings = json.load(f)
    
    assert len(standings) == 3 # Alpha, Bravo, Charlie
    # Charlie: 1 W, 0 L -> 1.0 win rate
    # Alpha: 1 W, 1 L -> 0.5 win rate
    # Bravo: 0 W, 1 L -> 0.0 win rate
    assert standings[0]['name'] == 'Charlie Team' and standings[0]['win_rate'] == 1.0
    assert standings[1]['name'] == 'Alpha Team' and standings[1]['win_rate'] == 0.5
    assert standings[2]['name'] == 'Bravo Team' and standings[2]['win_rate'] == 0.0

    # Specific check for player performance (Player A1 played 2 games)
    perf_path = os.path.join(TEST_REPORTS_DIR, "player_performance.json")
    with open(perf_path, 'r') as f:
        performance = json.load(f)
    
    player_a1_perf = next((p for p in performance if p['name'] == 'Player A1'), None)
    assert player_a1_perf is not None
    assert player_a1_perf['games_played'] == 2
    assert player_a1_perf['total_score'] == 5000 + 3500
    assert player_a1_perf['total_kills'] == 10 + 6
    assert player_a1_perf['total_deaths'] == 2 + 5


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

def test_generate_elo_ladder(populated_db_conn):
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
    assert len(history) == 2 # Two matches were processed

    # Match 1: Alpha (Imp) vs Bravo (Reb), Alpha wins
    match1_hist = history[0]
    assert match1_hist['imperial']['team_name'] == 'Alpha Team'
    assert match1_hist['rebel']['team_name'] == 'Bravo Team'
    assert match1_hist['winner'] == 'IMPERIAL'
    assert match1_hist['imperial']['old_rating'] == starting_elo
    assert match1_hist['rebel']['old_rating'] == starting_elo
    # Expected outcome for equal teams is 0.5
    expected_alpha_m1 = 0.5
    expected_bravo_m1 = 0.5
    # New ratings
    new_alpha_m1 = calculate_new_rating(starting_elo, expected_alpha_m1, 1.0, k_factor) # Win
    new_bravo_m1 = calculate_new_rating(starting_elo, expected_bravo_m1, 0.0, k_factor) # Loss
    assert match1_hist['imperial']['new_rating'] == pytest.approx(new_alpha_m1)
    assert match1_hist['rebel']['new_rating'] == pytest.approx(new_bravo_m1)
    assert new_alpha_m1 == 1016
    assert new_bravo_m1 == 984

    # Match 2: Alpha (Imp) vs Charlie (Reb), Charlie wins
    match2_hist = history[1]
    assert match2_hist['imperial']['team_name'] == 'Alpha Team'
    assert match2_hist['rebel']['team_name'] == 'Charlie Team'
    assert match2_hist['winner'] == 'REBEL'
    # Old ratings are the results from Match 1 for Alpha, starting for Charlie
    assert match2_hist['imperial']['old_rating'] == pytest.approx(new_alpha_m1)
    assert match2_hist['rebel']['old_rating'] == starting_elo # Charlie's first match
    # Expected outcomes
    expected_alpha_m2 = calculate_expected_outcome(new_alpha_m1, starting_elo)
    expected_charlie_m2 = 1.0 - expected_alpha_m2
    # New ratings
    new_alpha_m2 = calculate_new_rating(new_alpha_m1, expected_alpha_m2, 0.0, k_factor) # Loss
    new_charlie_m2 = calculate_new_rating(starting_elo, expected_charlie_m2, 1.0, k_factor) # Win
    assert match2_hist['imperial']['new_rating'] == pytest.approx(new_alpha_m2)
    assert match2_hist['rebel']['new_rating'] == pytest.approx(new_charlie_m2)
    # Expected values: E_alpha = 1/(1+10^((1000-1016)/400)) = 1/(1+10^-0.04) ~= 0.523
    # E_charlie = 1 - 0.523 = 0.477
    # R'_alpha = 1016 + 32*(0 - 0.523) ~= 1016 - 16.736 = 999.264
    # R'_charlie = 1000 + 32*(1 - 0.477) ~= 1000 + 16.736 = 1016.736
    assert new_alpha_m2 == pytest.approx(999.264, abs=1e-3)
    assert new_charlie_m2 == pytest.approx(1016.736, abs=1e-3)


    # --- Validate Ladder ---
    assert isinstance(ladder, list)
    assert len(ladder) == 3 # Alpha, Bravo, Charlie

    # Find teams in ladder
    alpha_ladder = next((t for t in ladder if t['team_name'] == 'Alpha Team'), None)
    bravo_ladder = next((t for t in ladder if t['team_name'] == 'Bravo Team'), None)
    charlie_ladder = next((t for t in ladder if t['team_name'] == 'Charlie Team'), None)

    assert alpha_ladder is not None
    assert bravo_ladder is not None
    assert charlie_ladder is not None

    # Check final ELO ratings (should match the last entry in history for each team)
    assert alpha_ladder['elo_rating'] == round(new_alpha_m2) # approx 999
    assert bravo_ladder['elo_rating'] == round(new_bravo_m1) # approx 984
    assert charlie_ladder['elo_rating'] == round(new_charlie_m2) # approx 1017

    # Check stats
    assert alpha_ladder['matches_played'] == 2
    assert alpha_ladder['matches_won'] == 1
    assert alpha_ladder['matches_lost'] == 1
    assert alpha_ladder['win_rate'] == 50.0

    assert bravo_ladder['matches_played'] == 1
    assert bravo_ladder['matches_won'] == 0
    assert bravo_ladder['matches_lost'] == 1
    assert bravo_ladder['win_rate'] == 0.0

    assert charlie_ladder['matches_played'] == 1
    assert charlie_ladder['matches_won'] == 1
    assert charlie_ladder['matches_lost'] == 0
    assert charlie_ladder['win_rate'] == 100.0

    # Check ranking (Charlie > Alpha > Bravo)
    assert charlie_ladder['rank'] == 1
    assert alpha_ladder['rank'] == 2
    assert bravo_ladder['rank'] == 3

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