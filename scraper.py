import urllib.request
import urllib
from urllib.parse import quote
import datetime
from datetime import timezone
import json
import logging
logging.basicConfig(level=logging.INFO)
import time
import sys
import os

# for dealing witht eh authentication
import yaml

# load up the auth globally
with open("auth.yaml") as f:
    auth = yaml.load(f)
    ACCESS_TOKEN = auth["app_id"] + "|" + auth["app_secret"]
query = "?fields=feed{comments{created_time,like_count,message,from{name}},link,shares,message,name,likes,created_time,from{name},picture}"#,posts{message,likes,shares,name}"
#query = "326170274196469/feed/?"
endpoint_base = "https://graph.facebook.com/v2.5/"
page_id = "326170274196469"
time_format = "%Y-%m-%d"

CSV_HEADERS = ["date","page", "posted by", "message","link", "shares", "likes", "number of comments", "pic", "url", "type"]

# test what bits of the urllib code we have to alter
def test_facebook_page_data(page_id, access_token=ACCESS_TOKEN):
    # make a url
    base = "https://graph.facebook.com/v2.5"
    node = "/" + page_id
    parameters = "?access_token={}".format(access_token)
    url = base + node + parameters
    logging.info(url)
    # make the request
    req = urllib.request.Request(url)
    opener = urllib.request.build_opener(urllib.request.HTTPHandler)
    resp = opener.open(req)
    data = json.loads(resp.read().decode('utf-8'))
    #print(json.dumps(data, indent=4, sort_keys=True))
    return data

def request_until_success(url, max_attempts=5, wait=5):
    """Makes a request a few times in case of a 500 error.
    Should use exponential backoff?
    """
    req = urllib.request.Request(url)
    success = False
    num_tries = 0
    while not success:
        try:
            num_tries += 1
            response = urllib.request.urlopen(req)
            success = response.getcode() == 200
        except urllib.request.HTTPError as e:
            logging.error(e)
            logging.error("Error on url {}".format(url))
            if e.code == 500 and num_tries < max_attempts:
                logging.error("trying again soon")
                time.sleep(wait)
            else:
                logging.error(e.reason)
                raise e

    return json.loads(response.read().decode('UTF-8'))

def make_facebook_query(page_id, query_string, access_token,
                        since=datetime.datetime.now(timezone.utc)-datetime.timedelta(32),
                        until=datetime.datetime.now(timezone.utc)):
    """Makes the query specified by the url.
    Does paging if necessary and returns a list of results"""
    query_string += "&access_token={}".format(access_token)
    #query_string += "&until={}".format(until.strftime(time_format))
    #query_string += "&since={}".format(since.strftime(time_format))
    # query_string = quote(query_string, safe='/?=&{}()')
    url = endpoint_base + page_id + query_string
    more_pages = True
    results = []
    logging.info("Querying {}".format(url))
    logging.info("since: {} until: {}".format(since, until))
    while more_pages:
        data = request_until_success(url)
        #data = json.loads(data)
        #print(json.dumps(data, indent=2))
        if 'feed' in data:
            data = data['feed']
        last_date = datetime.datetime.now(timezone.utc)#data['data'][-1]['created_time']
        last_i = len(data)
        # find the furthest back date in this page
        dates = []
        for i,item in enumerate(data['data']):
            item_date = datetime.datetime.strptime(item['created_time'], "%Y-%m-%dT%H:%M:%S%z")
            dates.append(item_date)
            if 'likes' in item and len(item['likes']['data']) == 25:
                logging.info('Checking for extra likes:')
                item['likes'] = get_all_items(item['likes'])
            if 'comments' in item:
                # better make sure we have them all (facebook only sends 25 at a time)
                if len(item['comments']['data']) == 25:
                    logging.info('Checking for extra comments:')
                    item['comments'] = get_all_items(item['comments'])

                # set the date of the post to its youngest comment
                youngest_date = item_date
                for c in item['comments']['data']:
                    c_date = datetime.datetime.strptime(c['created_time'], "%Y-%m-%dT%H:%M:%S%z")
                    if c_date > youngest_date:
                        youngest_date = c_date
                item_date = youngest_date # extra variable probably unnecessary

            if item_date < last_date and last_date >= since:
                last_date = item_date
                last_i = i+1

        filtered = [item for i,item in enumerate(data['data'][:last_i]) if dates[i] <= until]

        logging.info("last date: {}, got {} to add".format(last_date, len(filtered)))
        results.append(filtered)
        if 'next' in data['paging']:

            #last_date = datetime.datetime.strptime(last_date, "%Y-%m-%dT%H:%M:%S%z")
            if last_date >= since:
                logging.info("...querying another page ({})".format(len(results)))
                more_pages = True
                url = data['paging']['next']
            elif last_date <= since:
                logging.info("...done")
                more_pages = False
            else:
                more_pages = False
        else:
            more_pages = False

    return results

def get_all_items(base):
    """Tries to get everything and stick all of their datas together.
    Returns the original item (some kind of dict presumably) with all
    expanded 'data' field. Assumes cursors in base['paging']"""
    current = base
    i = 0
    while 'next' in current['paging']: # just go and go until there is no where to go
        i += 1
        print('...{}'.format(i*25))
        current = request_until_success(current['paging']['next'])
        #print(json.dumps(current, indent=2))
        base['data'].extend(current['data'])
    return base

def process_responses(data, page=''):
    """Handles responses to a very specific query"""
    structured_data = [] # going to be a list of lists?
    i = 0
    for result in data:
        for post in result:#['data']:
            i += 1

            result = get_post_tuple(post, page)

            structured_data.append(result)
            # if there is a list of comments we need to process those
            if 'comments' in post:
                for comment in post['comments']['data']:
                    result = get_post_tuple(comment, page, source="comment", parent=post['id'])
                    structured_data.append(result)

    return structured_data

def get_post_tuple(post, page, source="post", parent=None):
    """Gets fields out of a post or comment"""
    num_comments = (len(post['comments']['data'])) if 'comments' in post else '0'
    date = datetime.datetime.strptime(post['created_time'], "%Y-%m-%dT%H:%M:%S%z")
    date = date.strftime("%d/%m/%Y %I:%M:%S %p")
    likes = (len(post['likes']['data'])) if 'likes' in post else '0'
    msg = post.get('message', '')
    shares = post['shares']['count'] if 'shares' in post else '0'
    name = post['from']['name']
    pic = post.get('picture', '')
    link = post.get('link', '')
    if not parent:
        pid = post['id'] if 'id' in post else ''
    else:
        pid = parent
    if pid:
        if '_' in pid:
            split = pid.split('_')
            url = 'http://www.facebook.com/{}/posts/{}'.format(*tuple(split))
        else:
            url = 'http://www.facebook.com/'+pid
    else:
        url = ''


    return (date, page,
            name, msg, link,
            shares, likes,
            num_comments,
            pic, url, source)

def write_data(data, headers, fpath):
    num_cols = len(headers)
    if not isinstance(headers, tuple):
        headers = tuple(headers)
    with open(fpath, 'w', encoding='utf-16') as f:
        # write the headers
        f.write(("{}\t"*num_cols).format(*headers)+"\n")
        for i,row in enumerate(data):
            # double check it is safe
            # qutes make excel happy
            clean_row = ['"{0}"'.format(str(value).replace('"',"'")).expandtabs() for value in row]

            f.write(("{}\t"*num_cols).format(*tuple(clean_row))+"\n")
            if (i+1) % 20 == 0:
                logging.info("Processed {} rows".format(i+1))

def setup_args():
    """organise the command line arguments"""
    parser = argparse.ArgumentParser(
        description="Scrape some facebook data from one or more pages")
    parser.add_argument("page-file",
                        help="Name or ID of the facebook page or a path to a file containing a list of names/IDs")

    parser.add_argument("-o", "--outfile",
                        help="Path to file for output.\nIf unspecified, the default is the page/file with '.csv' appended")
    parser.add_argument("-s", "--since",
                        default=(datetime.datetime.now(timezone.utc)-datetime.timedelta(32)).strftime(time_format),
                        help="The furthest back to go.\nNo results older than this date should be output.\nIf unsepcified, defaults to the current time minus 32 days")
    parser.add_argument("-u", "--until",
                        default=datetime.datetime.now(timezone.utc).strftime(time_format),
                        help="The starting date, no results younger than this date will be returned.\nDefaults to the current time.\nThe expected format is: YYYY-MM-DD")
    return parser

if __name__ == '__main__':
    """do stuff
    """
    # let's do this properly
    import argparse
    parser = setup_args()
    args = vars(parser.parse_args())
    if os.path.exists(args['page-file']):
        with open(args['page-file'], 'r') as f:
            page_id = [page.strip() for page in f]
    else:
        page_id = [args['page-file']]
    if 'outfile' in args and args['outfile']:
        output_path = args['outfile']
    else:
        output_path = args['page-file']+'.csv'

    data = []
    for page in page_id:
        logging.info("~~~~~~~~~~~~~~~{}~~~~~~~~~~~~~~~".format(page))
        raw_data = make_facebook_query(page, query, ACCESS_TOKEN,
                                       since=datetime.datetime.strptime(
                                           args['since'],time_format).replace(tzinfo=timezone.utc),
                                       until=datetime.datetime.strptime(
                                           args['until'],time_format).replace(tzinfo=timezone.utc))
        data += process_responses(raw_data, page=page)
        logging.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    write_data(data, CSV_HEADERS, output_path)
