from http import HTTPStatus

from django.test import SimpleTestCase


class FaviconFileTests(SimpleTestCase):
    def test_get(self):
        names = [
            "apple-touch-icon.png",
            "favicon.ico",
            "favicon-96x96.png",
            "favicon.svg",
            "web-app-manifest-192x192.png",
            "web-app-manifest-512x512.png",
            "site.webmanifest",
        ]
        for name in names:
            with self.subTest(name):
                response = self.client.get(f"/{name}")
                assert response.status_code == HTTPStatus.OK
                assert response["Cache-Control"] == "max-age=86400, immutable, public"
                assert len(response.getvalue()) > 0
