import asyncio
import importlib
import json
import os
from pathlib import Path
import secrets
import tempfile
import unittest
from unittest.mock import patch


class VolunteersApiTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        with patch.dict(os.environ, {
            "ACTIVITY_DB_PATH": str(Path(self.directory.name) / "activities.db")
        }):
            self.module = importlib.import_module("src.app")
        database = patch.object(
            self.module, "DATABASE_PATH", Path(self.directory.name) / "activities.db"
        )
        database.start()
        self.addCleanup(database.stop)
        self.token = secrets.token_urlsafe(32)
        environment = patch.dict(os.environ, {"STAFF_API_TOKEN": self.token})
        environment.start()
        self.addCleanup(environment.stop)
        self.module.initialize_database()

    def request(self, method, path, body=None, token=None):
        async def call():
            messages = []
            headers = [(b"content-type", b"application/json")]
            if token is not None:
                headers.append((b"authorization", ("Bearer " + token).encode()))
            scope = {
                "type": "http", "http_version": "1.1", "method": method,
                "scheme": "http", "path": path, "query_string": b"",
                "headers": headers, "server": ("test", 80), "client": ("test", 123),
            }

            async def receive():
                return {
                    "type": "http.request",
                    "body": json.dumps(body).encode() if body is not None else b"",
                    "more_body": False,
                }

            async def send(message):
                messages.append(message)

            await self.module.app(scope, receive, send)
            status = next(
                message["status"] for message in messages
                if message["type"] == "http.response.start"
            )
            data = b"".join(
                message.get("body", b"") for message in messages
                if message["type"] == "http.response.body"
            )
            return status, json.loads(data)

        return asyncio.run(call())

    def create_profile(self):
        profile = {
            "name": "Alex Volunteer", "email": "alex@example.org",
            "phone": "555-0100", "availability": "Fridays after 3 PM",
            "age_group": "Adult", "program_cycle": "Fall 2026",
            "interests": "Chess", "talents": "Coaching",
            "notes": "Contact by email", "photo_consent": True,
            "newsletter_consent": False,
        }
        status, volunteer = self.request(
            "POST", "/volunteers", profile, token=self.token
        )
        self.assertEqual(status, 201)
        self.assertEqual({key: volunteer[key] for key in profile}, profile)
        return volunteer

    def test_profiles_can_be_created_updated_and_persisted(self):
        volunteer = self.create_profile()
        volunteer_id = volunteer.pop("id")
        volunteer.update(availability="Tuesdays", photo_consent=False,
                         newsletter_consent=True)
        status, updated = self.request(
            "PUT", f"/volunteers/{volunteer_id}", volunteer, token=self.token
        )
        self.assertEqual(status, 200)
        self.assertEqual(updated["availability"], "Tuesdays")
        self.assertFalse(updated["photo_consent"])
        self.assertTrue(updated["newsletter_consent"])
        self.module.initialize_database()
        status, volunteers = self.request("GET", "/volunteers", token=self.token)
        self.assertEqual(status, 200)
        self.assertEqual(volunteers, [updated])

    def test_all_staff_routes_require_authorization(self):
        routes = [
            ("GET", "/volunteers", None),
            ("POST", "/volunteers", {"name": "Alex"}),
            ("PUT", "/volunteers/1", {"name": "Alex"}),
            ("PUT", "/activities/Chess Club/volunteers/1", None),
            ("DELETE", "/activities/Chess Club/volunteers/1", None),
        ]
        for method, path, body in routes:
            for token in (None, "invalid"):
                with self.subTest(method=method, path=path, token=token):
                    self.assertEqual(self.request(method, path, body, token)[0], 401)
        with patch.dict(os.environ, {"STAFF_API_TOKEN": ""}):
            self.assertEqual(
                self.request("GET", "/volunteers", token=self.token)[0], 503
            )
        self.assertEqual(self.request("GET", "/activities")[0], 200)

    def test_assignments_are_separate_private_and_do_not_use_student_spots(self):
        volunteer = self.create_profile()
        before = self.module.get_activities()["Chess Club"]
        with self.module.get_connection() as connection:
            connection.execute(
                "UPDATE activities SET max_participants = ? WHERE name = ?",
                (len(before["participants"]), "Chess Club"),
            )
        path = f"/activities/Chess Club/volunteers/{volunteer['id']}"
        for _ in range(2):
            self.assertEqual(self.request("PUT", path, token=self.token)[0], 200)
        self.module.initialize_database()
        status, activities = self.request("GET", "/activities")
        self.assertEqual(status, 200)
        roster = activities["Chess Club"]
        self.assertEqual(roster["participants"], before["participants"])
        self.assertEqual(roster["volunteers"], [
            {"id": volunteer["id"], "name": volunteer["name"]}
        ])
        self.assertEqual(self.request("DELETE", path, token=self.token)[0], 200)
        self.assertEqual(self.module.get_activities()["Chess Club"]["volunteers"], [])
        self.assertEqual(self.request("DELETE", path, token=self.token)[0], 404)

    def test_missing_records_and_invalid_profiles_are_rejected(self):
        for body in ({}, {"name": "   "}, {"name": "Alex", "unknown": "value"}):
            self.assertEqual(
                self.request("POST", "/volunteers", body, token=self.token)[0], 422
            )
        self.assertEqual(self.request(
            "PUT", "/volunteers/999", {"name": "Alex"}, token=self.token
        )[0], 404)
        self.assertEqual(self.request(
            "PUT", "/activities/Chess Club/volunteers/999", token=self.token
        )[0], 404)
        volunteer = self.create_profile()
        self.assertEqual(self.request(
            "PUT", f"/activities/Unknown/volunteers/{volunteer['id']}",
            token=self.token
        )[0], 404)


if __name__ == "__main__":
    unittest.main()
