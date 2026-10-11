import importlib
import os
import tempfile
import unittest


class ActivitiesApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.database.close()
        os.environ["ACTIVITY_DB_PATH"] = cls.database.name
        cls.app = importlib.import_module("src.app")

    @classmethod
    def tearDownClass(cls):
        os.unlink(cls.database.name)
        os.environ.pop("ACTIVITY_DB_PATH", None)

    def test_database_is_seeded_with_activities_and_participants(self):
        activities = self.app.get_activities()

        self.assertIn("Chess Club", activities)
        self.assertIn("michael@mergington.edu", activities["Chess Club"]["participants"])

    def test_signup_persists_and_duplicate_signup_is_rejected(self):
        email = "persistence-test@mergington.edu"

        self.app.signup_for_activity("Chess Club", email)
        activities = importlib.reload(self.app).get_activities()

        self.assertIn(email, activities["Chess Club"]["participants"])
        with self.assertRaises(self.app.HTTPException) as error:
            self.app.signup_for_activity("Chess Club", email)
        self.assertEqual(error.exception.status_code, 400)

        self.app.unregister_from_activity("Chess Club", email)

    def test_unregistering_an_unknown_registration_is_rejected(self):
        with self.assertRaises(self.app.HTTPException) as error:
            self.app.unregister_from_activity(
                "Chess Club", "not-registered@mergington.edu"
            )

        self.assertEqual(error.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()