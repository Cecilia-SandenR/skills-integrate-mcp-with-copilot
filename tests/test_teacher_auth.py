import json
import tempfile
import unittest
from http.cookies import SimpleCookie
from pathlib import Path
from unittest.mock import patch

from starlette.requests import Request
from starlette.responses import Response
from fastapi import HTTPException

from src import app as activities_app
from src import auth


def make_request(session_id=None):
    headers = []
    if session_id:
        headers.append(
            (b"cookie", f"{activities_app.SESSION_COOKIE_NAME}={session_id}".encode())
        )
    return Request(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "headers": headers,
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
        }
    )


class TeacherAuthenticationTests(unittest.TestCase):
    def test_catalog_remains_public(self):
        self.assertIn("Chess Club", activities_app.get_activities())

    def test_anonymous_signup_is_rejected(self):
        with self.assertRaises(HTTPException) as error:
            activities_app.signup_for_activity(
                "Chess Club", make_request(), "new-student@mergington.edu"
            )
        self.assertEqual(error.exception.status_code, 401)

    def test_anonymous_unregister_is_rejected(self):
        with self.assertRaises(HTTPException) as error:
            activities_app.unregister_from_activity(
                "Chess Club", make_request(), "michael@mergington.edu"
            )
        self.assertEqual(error.exception.status_code, 401)

    def test_teacher_can_manage_registrations(self):
        session_id = "valid-test-session"
        email = "new-student@mergington.edu"
        original_participants = activities_app.activities["Chess Club"]["participants"]
        participants_before = original_participants.copy()
        activities_app.teacher_sessions[session_id] = {
            "username": "teacher",
            "expires_at": 9_999_999_999,
        }
        try:
            request = make_request(session_id)
            activities_app.signup_for_activity("Chess Club", request, email)
            self.assertIn(email, activities_app.activities["Chess Club"]["participants"])

            activities_app.unregister_from_activity("Chess Club", request, email)
            self.assertEqual(
                activities_app.activities["Chess Club"]["participants"],
                participants_before,
            )
        finally:
            activities_app.activities["Chess Club"]["participants"] = participants_before
            activities_app.teacher_sessions.pop(session_id, None)

    def test_login_session_and_logout(self):
        response = Response()
        credentials = activities_app.TeacherLogin(
            username="teacher1", password="correct-password"
        )
        with patch.object(activities_app, "verify_teacher_credentials", return_value=True):
            result = activities_app.teacher_login(credentials, response)

        self.assertEqual(result, {"username": "teacher1"})
        cookies = SimpleCookie()
        cookies.load(response.headers["set-cookie"])
        session_cookie = cookies[activities_app.SESSION_COOKIE_NAME]
        self.assertTrue(session_cookie["httponly"])

        request = make_request(session_cookie.value)
        self.assertEqual(
            activities_app.get_auth_session(request), {"username": "teacher1"}
        )

        logout_response = Response()
        activities_app.teacher_logout(request, logout_response)
        with self.assertRaises(HTTPException) as error:
            activities_app.get_auth_session(request)
        self.assertEqual(error.exception.status_code, 401)

    def test_password_records_are_verified(self):
        password = "a-strong-teacher-password"
        record = auth.create_password_record(password)
        with tempfile.TemporaryDirectory() as temp_dir:
            credentials_path = Path(temp_dir) / "teachers.json"
            credentials_path.write_text(
                json.dumps({"teachers": {"teacher1": record}}), encoding="utf-8"
            )
            with patch.object(auth, "TEACHER_CREDENTIALS_FILE", credentials_path):
                self.assertTrue(auth.verify_teacher_credentials("Teacher1", password))
                self.assertFalse(auth.verify_teacher_credentials("Teacher1", "wrong"))


if __name__ == "__main__":
    unittest.main()