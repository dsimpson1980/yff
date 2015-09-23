import mechanize
import cookielib
from BeautifulSoup import BeautifulSoup

from data.config import get_league_number, get_yahoo_username


def get_proj_points(x):
    fn = x.find('td', attrs={'class': "Alt Ta-end Nowrap Bdrstart"})
    id = x.find('a', attrs={'data-ys-playernote-view': 'notes'})
    if fn is None:
        fn = x.find('td', attrs={'class': "Ta-end Nowrap Bdrstart"})
    fn = float(fn.find('div').text)
    try:
        id = id.attrMap['data-ys-playerid']
    except:
        print 'test'
    return id, fn

def get_points(br, url):
    br.open(url)
    page = br.response().read()
    soup = BeautifulSoup(page)
    rows = []
    for n in xrange(3):
        table = soup.find('div', attrs={'id': 'statTable%s-wrap' % n})
        table = table.find('table')
        rows += table.findAll('tr')[2:]
    points = map(get_proj_points, rows)
    return points

def initialise_browser(url):
    import keyring
    import getpass

    br = mechanize.Browser()
    cj = cookielib.LWPCookieJar()
    br.set_cookiejar(cj)
    br.set_handle_equiv(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)
    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

    br.addheaders = [('User-agent', 'Chrome')]
    br.open(url)
    br.select_form(nr=0)
    yahoo_username = get_yahoo_username()
    sys_username = getpass.getuser()
    service_name = 'yff'
    password = keyring.get_password(service_name, sys_username)
    if password is None:
        password = getpass.getpass(
            'Password for yahoo user: {s!}'.format(yahoo_username))
        keyring.set_password(service_name, sys_username, password)
    br.form['username'] = yahoo_username
    br.form['passwd'] = password
    br.submit()
    return br

def get_all_points():
    league_num = get_league_number()
    url = 'http://football.fantasysports.yahoo.com/f1/{!s}'.format(league_num)
    url += '/%s?stat1=P&ssort=W'
    br = initialise_browser(url % 1)
    all_points = {}
    for team_num in xrange(1, 13):
        points = get_points(br, url % team_num)
        for k, v in points:
            all_points[k] = v
    return all_points

if __name__ == '__main__':
    league_num = get_league_number()
    url = 'http://football.fantasysports.yahoo.com/f1/%s' % league_num
    br = initialise_browser(url)
    points = get_all_points()
    print points
