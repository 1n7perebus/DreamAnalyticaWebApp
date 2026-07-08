import urllib.request

def follow(url):
    r = urllib.request.urlopen(url, timeout=15)
    print(url)
    print('  status:', r.status)
    print('  final:', r.geturl())

token = 'testtoken123'
for base in ['https://dreamanalytica.com', 'https://www.dreamanalytica.com']:
    follow(f'{base}/verify-email/?t={token}')
