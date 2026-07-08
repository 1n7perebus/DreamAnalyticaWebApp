from django.test import RequestFactory, SimpleTestCase, override_settings

from main.views import _pending_verification_verify_url, _public_absolute_uri


class PublicAbsoluteUriTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get('/', HTTP_HOST='dreamanalytica.com', secure=True)

    @override_settings(PUBLIC_SITE_URL='https://www.dreamanalytica.com')
    def test_uses_canonical_site_url(self):
        url = _public_absolute_uri(self.request, '/verify-email/?t=abc')
        self.assertEqual(url, 'https://www.dreamanalytica.com/verify-email/?t=abc')

    @override_settings(PUBLIC_SITE_URL='')
    def test_falls_back_to_request_host(self):
        url = _public_absolute_uri(self.request, '/verify-email/?t=abc')
        self.assertEqual(url, 'https://dreamanalytica.com/verify-email/?t=abc')

    @override_settings(PUBLIC_SITE_URL='https://www.dreamanalytica.com')
    def test_pending_verification_url_uses_www(self):
        url = _pending_verification_verify_url(self.request, 'signed-token')
        self.assertTrue(url.startswith('https://www.dreamanalytica.com/verify-email/?t='))
        self.assertIn('signed-token', url)
