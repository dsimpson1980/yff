import mechanize
import cookielib
import getpass
from BeautifulSoup import BeautifulSoup

from yahoo_tools import get_league_number

def get_proj_points(x):
    fn = x.find('td', attrs={'class': "Alt Ta-end Nowrap Bdrstart"})
    fn = fn.find('div').text
    return float(fn)

def get_points(br, url):
    br.open(url)
    page = br.response().read()
    soup = BeautifulSoup(page)
    points = []
    rows = []
    try:
        for n in xrange(3):
            table = soup.find('div', attrs={'id': 'statTable%s-wrap' % n})
            table = table.find('table')
            rows += table.findAll('tr')[2:]
        points.append(map(get_proj_points, rows))
        return points
    except:
        return []

def initialise_browser(url):
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
    username = raw_input('Yahoo Username: ')
    password = getpass.getpass()
    br.form['username'] = username
    br.form['passwd'] = password
    br.submit()
    return br

def main():
    league_num = get_league_number()
    url = 'http://football.fantasysports.yahoo.com/f1/{!s}'.format(league_num)
    url += '/%s?stat1=P&ssort=W'
    br = initialise_browser(url % 1)
    points = []
    for team_num in xrange(1, 13):
        points.append(get_points(br, url % team_num))
    for p in points:
        print p

if __name__ == '__main__':
    main()
