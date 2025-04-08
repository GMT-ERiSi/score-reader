import unittest
import os
import sqlite3
import json
import tempfile
import shutil
from stats_reader.elo_ladder import generate_elo_ladder, calculate_expected_outcome, calculate_new_rating


class TestEloLadder(unittest.TestCase):
    """Tests for the ELO ladder generator"""

    def setUp(self):
        """Set up a test database with sample match data"""
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_squadrons_stats.db")
        self.output_dir = os.path.join(self.test_dir, "test_stats_reports")
        
        # Create the output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create and populate the test database
        self.create_test_database()
    
    def tearDown(self):
        """Clean up temporary files"""
        shutil.rmtree(self.test_dir)
    
    def create_test_database(self):
        """Create a test database with sample data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create schema
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS seasons (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            reference_id INTEGER,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY,
            season_id INTEGER,
            match_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            imperial_team_id INTEGER,
            rebel_team_id INTEGER,
            winner TEXT,
            filename TEXT,
            FOREIGN KEY (season_id) REFERENCES seasons(id),
            FOREIGN KEY (imperial_team_id) REFERENCES teams(id),
            FOREIGN KEY (rebel_team_id) REFERENCES teams(id)
        )
        ''')
        
        # Insert test data
        # Seasons
        cursor.execute("INSERT INTO seasons (id, name) VALUES (1, 'TEST_SEASON')")
        
        # Teams
        teams = [
            (1, "Alpha Squad", None, 0, 0),
            (2, "Beta Squad", None, 0, 0),
            (3, "Gamma Squad", None, 0, 0),
            (4, "Delta Squad", None, 0, 0),
        ]
        cursor.executemany("INSERT INTO teams (id, name, reference_id, wins, losses) VALUES (?, ?, ?, ?, ?)", teams)
        
        # Matches - using the correct format for winners ("IMPERIAL" or "REBEL")
        matches = [
            (1, 1, "2023-01-01 12:00:00", 1, 2, "IMPERIAL", "match1.png"),  # Alpha (IMP) beats Beta (REB)
            (2, 1, "2023-01-02 12:00:00", 2, 3, "REBEL", "match2.png"),     # Beta (IMP) loses to Gamma (REB)
            (3, 1, "2023-01-03 12:00:00", 3, 4, "IMPERIAL", "match3.png"),  # Gamma (IMP) beats Delta (REB)
            (4, 1, "2023-01-04 12:00:00", 4, 1, "REBEL", "match4.png"),     # Delta (IMP) loses to Alpha (REB)
            (5, 1, "2023-01-05 12:00:00", 1, 3, "IMPERIAL", "match5.png"),  # Alpha (IMP) beats Gamma (REB)
        ]
        cursor.executemany(
            "INSERT INTO matches (id, season_id, match_date, imperial_team_id, rebel_team_id, winner, filename) VALUES (?, ?, ?, ?, ?, ?, ?)",
            matches
        )
        
        # Update team wins/losses based on matches
        cursor.execute("UPDATE teams SET wins = 3, losses = 0 WHERE id = 1")  # Alpha won all matches
        cursor.execute("UPDATE teams SET wins = 1, losses = 1 WHERE id = 2")  # Beta won 1, lost 1
        cursor.execute("UPDATE teams SET wins = 1, losses = 1 WHERE id = 3")  # Gamma won 1, lost 1
        cursor.execute("UPDATE teams SET wins = 0, losses = 2 WHERE id = 4")  # Delta lost all matches
        
        conn.commit()
        conn.close()
    
    def test_calculate_expected_outcome(self):
        """Test the expected outcome calculation"""
        # Equal ratings should give 0.5 expected outcome
        self.assertAlmostEqual(calculate_expected_outcome(1000, 1000), 0.5)
        
        # Higher rating should give >0.5 expected outcome
        self.assertGreater(calculate_expected_outcome(1100, 1000), 0.5)
        
        # Lower rating should give <0.5 expected outcome
        self.assertLess(calculate_expected_outcome(1000, 1100), 0.5)
        
        # Specific value test
        self.assertAlmostEqual(calculate_expected_outcome(1200, 1000), 0.75975, places=5) # Adjusted expected value slightly
    
    def test_calculate_new_rating(self):
        """Test the new rating calculation"""
        # Win against equal opponent
        old_rating = 1000
        expected = 0.5
        actual = 1.0  # win
        k_factor = 32
        
        new_rating = calculate_new_rating(old_rating, expected, actual, k_factor)
        self.assertEqual(new_rating, 1016)  # 1000 + 32 * (1 - 0.5) = 1016
        
        # Loss against equal opponent
        actual = 0.0  # loss
        new_rating = calculate_new_rating(old_rating, expected, actual, k_factor)
        self.assertEqual(new_rating, 984)  # 1000 + 32 * (0 - 0.5) = 984
    
    def test_generate_elo_ladder(self):
        """Test that the ELO ladder is generated correctly"""
        ladder, history = generate_elo_ladder(self.db_path, self.output_dir)
        
        # Check that the ladder is sorted by ELO rating
        self.assertEqual(len(ladder), 4)  # All 4 teams should be in the ladder
        self.assertGreaterEqual(ladder[0]['elo_rating'], ladder[1]['elo_rating'])
        
        # Alpha Squad should have the highest rating (won all matches)
        alpha_entry = next((team for team in ladder if team['team_name'] == 'Alpha Squad'), None)
        self.assertIsNotNone(alpha_entry)
        self.assertEqual(alpha_entry['matches_won'], 3)
        self.assertEqual(alpha_entry['matches_lost'], 0)
        self.assertEqual(alpha_entry['win_rate'], 100.0)
        
        # Verify Delta has lowest rating (lost all matches)
        delta_entry = next((team for team in ladder if team['team_name'] == 'Delta Squad'), None)
        self.assertIsNotNone(delta_entry)
        self.assertEqual(delta_entry['matches_won'], 0)
        self.assertEqual(delta_entry['matches_lost'], 2)
        self.assertEqual(delta_entry['win_rate'], 0.0)
        
        # Check that history has entries for all matches
        self.assertEqual(len(history), 5)  # 5 matches in our test data
        
        # Verify JSON files were created
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "elo_ladder.json")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "elo_history.json")))
        
        # Verify content of JSON files
        with open(os.path.join(self.output_dir, "elo_ladder.json"), 'r') as f:
            ladder_json = json.load(f)
            self.assertEqual(len(ladder_json), 4)
        
        with open(os.path.join(self.output_dir, "elo_history.json"), 'r') as f:
            history_json = json.load(f)
            self.assertEqual(len(history_json), 5)

    def test_sample_match_data(self):
        """Test with a sample from the actual data format"""
        # Create a new test database with the sample data
        sample_db_path = os.path.join(self.test_dir, "sample_db.db")
        conn = sqlite3.connect(sample_db_path)
        cursor = conn.cursor()
        
        # Create schema
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS seasons (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            reference_id INTEGER,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY,
            season_id INTEGER,
            match_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            imperial_team_id INTEGER,
            rebel_team_id INTEGER,
            winner TEXT,
            filename TEXT,
            FOREIGN KEY (season_id) REFERENCES seasons(id),
            FOREIGN KEY (imperial_team_id) REFERENCES teams(id),
            FOREIGN KEY (rebel_team_id) REFERENCES teams(id)
        )
        ''')
        
        # Insert sample data matching your real format
        # Seasons
        cursor.execute("INSERT INTO seasons (id, name) VALUES (1, 'SCL14')")
        cursor.execute("INSERT INTO seasons (id, name) VALUES (2, 'SCL15')")
        
        # Teams
        teams = [
            (1, "NRD", None, 3, 0),
            (2, "HP", None, 0, 1),
            (3, "IMP1", None, 0, 2)
        ]
        cursor.executemany("INSERT INTO teams (id, name, reference_id, wins, losses) VALUES (?, ?, ?, ?, ?)", teams)
        
        # Matches - using the correct "IMPERIAL" or "REBEL" winner format
        matches = [
            (1, 1, "2022-09-28 12:00:00", 2, 1, "REBEL", "Star Wars Squadrons Screenshot 2022.09.28 - 23.29.59.35.png"),
            (2, 1, "2022-09-29 12:00:00", 3, 1, "REBEL", "Star Wars Squadrons Screenshot 2022.09.29 - 16.39.56.68.png"),
            (3, 2, "2022-12-07 12:00:00", 3, 1, "REBEL", "Star Wars Squadrons Screenshot 2022.12.07 - 21.01.50.89.png")
        ]
        cursor.executemany(
            "INSERT INTO matches (id, season_id, match_date, imperial_team_id, rebel_team_id, winner, filename) VALUES (?, ?, ?, ?, ?, ?, ?)",
            matches
        )
        
        conn.commit()
        conn.close()
        
        # Generate ELO ladder with this sample data
        sample_output_dir = os.path.join(self.test_dir, "sample_output")
        os.makedirs(sample_output_dir, exist_ok=True)
        
        ladder, history = generate_elo_ladder(sample_db_path, sample_output_dir)
        
        # Verify NRD has highest rating (won all matches)
        nrd_entry = next((team for team in ladder if team['team_name'] == 'NRD'), None)
        self.assertIsNotNone(nrd_entry)
        self.assertEqual(nrd_entry['matches_won'], 3)
        self.assertEqual(nrd_entry['matches_lost'], 0)
        self.assertEqual(nrd_entry['win_rate'], 100.0)
        self.assertEqual(nrd_entry['rank'], 1)  # Should be ranked #1
        
        # Verify IMP1 has lowest rating (lost all matches)
        imp1_entry = next((team for team in ladder if team['team_name'] == 'IMP1'), None)
        self.assertIsNotNone(imp1_entry)
        self.assertEqual(imp1_entry['matches_won'], 0)
        self.assertEqual(imp1_entry['matches_lost'], 2)
        self.assertEqual(imp1_entry['win_rate'], 0.0)


if __name__ == '__main__':
    unittest.main()
