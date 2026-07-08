import urllib.error
import urllib.request
from urllib.parse import urljoin


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def trace(url):
    print('Tracing:', url)
    current = url
    opener = urllib.request.build_opener(NoRedirect)
    for _ in range(8):
        try:
            resp = opener.open(current, timeout=15)
            print('  FINAL', resp.status, current)
            return
        except urllib.error.HTTPError as e:
            loc = e.headers.get('Location', '')
            print(f'  {e.code} {current}')
            print(f'     -> {loc}')
            if not loc or e.code not in (301, 302, 303, 307, 308):
                return
            current = urljoin(current, loc)


token = 'abc123'
trace('https://dreamanalytica.com/verify-email/?t=' + token)
print()
trace('https://www.dreamanalytica.com/verify-email/?t=' + token)
