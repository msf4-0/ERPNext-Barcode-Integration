import requests


url = 'https://www.facebook.com'
r = requests.get(url, allow_redirects=True)

open(url+'.html', 'wb').write(r.content)