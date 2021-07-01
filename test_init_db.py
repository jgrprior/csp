import unittest
import sqlite3

from init_db import init_db as initialise_db
from init_db import generate_users
from init_db import insert_users
from init_db import generate_rooms
from init_db import insert_rooms
from init_db import generate_room_members
from init_db import insert_room_members
from init_db import generate_activities
from init_db import insert_activities
from init_db import generate_buddies
from init_db import insert_buddies

from init_db import ANIMALS
from init_db import COLOURS


class DatabaseTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db = sqlite3.connect(
            ":memory:",
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        )
        db.row_factory = sqlite3.Row

        initialise_db(db)

        users = generate_users(hash_iterations=10)
        insert_users(db, users)

        rooms = generate_rooms(db)
        insert_rooms(db, rooms)

        room_members = generate_room_members(db)
        insert_room_members(db, room_members)

        activities = generate_activities(db)
        insert_activities(db, activities)

        buddies = generate_buddies(db)
        insert_buddies(db, buddies)

        cls.db = db

    def test_generate_users(self):
        """Test that users have been generated."""
        user_count = self.db.execute("SELECT COUNT(*) FROM user").fetchone()[0]
        self.assertTrue(user_count, len(ANIMALS) * len(COLOURS))

    def test_negative_performance(self):
        """Test that we haven't generated any negative performances."""
        negative_performances = self.db.execute(
            "SELECT COUNT(*) FROM activity WHERE performance < 1"
        ).fetchone()[0]

        self.assertEqual(negative_performances, 0)


if __name__ == "__main__":
    unittest.main()
