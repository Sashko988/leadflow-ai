import unittest

import web


class WebRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        web.app.config.update(TESTING=True, SECRET_KEY="test-secret")
        cls.client = web.app.test_client()

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})

    def test_public_landing_has_primary_cta(self):
        response = self.client.get("/")
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Your business", body)
        self.assertIn("Book a free demo", body)
        self.assertIn("AI systems that create momentum", body)

    def test_demo_page_has_form(self):
        response = self.client.get("/demo")
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('name="email"', body)
        self.assertIn("Send demo request", body)

    def test_login_offers_social_sign_in(self):
        response = self.client.get("/login")
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Continue with Google", body)
        self.assertIn("Continue with Microsoft", body)

    def test_unconfigured_social_provider_returns_to_login(self):
        response = self.client.get("/auth/google")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_demo_rejects_invalid_submission_without_smtp(self):
        response = self.client.post("/demo", data={"name": "", "email": "not-an-email"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Please enter your name and a valid work email", response.get_data(as_text=True))

    def test_dashboard_requires_login(self):
        with self.client.session_transaction() as session:
            session.clear()
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_new_lead_requires_login(self):
        with self.client.session_transaction() as session:
            session.clear()
        response = self.client.get("/leads/new")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])


if __name__ == "__main__":
    unittest.main()
