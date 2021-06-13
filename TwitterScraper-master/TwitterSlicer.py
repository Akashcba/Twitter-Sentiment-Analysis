print '================================'
print '=        TwitterSlicer         ='
print '================================'
print ''
print 'You will query the advanced search at twitter.com'
print 'and get a dataset consisting of slices (a set number'
print 'of tweets per day in your search interval).'
print ''

# Import libraries
import urllib2
import json
import datetime
from abc import ABCMeta
from urllib import urlencode
from abc import abstractmethod
from urlparse import urlunparse
from bs4 import BeautifulSoup
from time import sleep
import codecs
import sys
from datetime import datetime
from datetime import timedelta

#==========================================================
# DEFINE CALASSES

# Do the actual search, retrieval, and writing of the slice data
# This code is an edited version of https://github.com/hv8/Twitter-Search-API-Python
class TwitterSearch:
    __metaclass__ = ABCMeta

    # Empty the output file and write a header line to it
    write_f = open('tweets.csv', 'w')
    write_f.write('date, user, name, retweets, favorites, text')
    write_f.close


    # Open the file ready for appending stuff to it
    write_f = open('tweets.csv', 'a')

    def __init__(self, rate_delay, error_delay=5):
        """
        :param rate_delay: How long to pause between calls to Twitter
        :param error_delay: How long to pause when an error occurs
        """
        self.rate_delay = rate_delay
        self.error_delay = error_delay

    def search(self, query, max_position=None):
        """
        Scrape items from twitter
        :param query:   Query to search Twitter with. Takes form of queries constructed with using Twitters
                        advanced search: https://twitter.com/search-advanced
        """
        url = self.construct_url(query, max_position)
        continue_search = True
        min_tweet = None
        response = self.execute_search(url)

        write_f = open('tweets.csv', 'a')  # open the file with a for appending
        urls_f = open('urls.txt', 'wb+')

        while response is not None and continue_search and response['items_html'] is not None:
            tweets = self.parse_tweets(response['items_html'])

            # If we have no tweets, then we can break the loop early
            if len(tweets) == 0:
                break

            # If we haven't set our min tweet yet, set it now
            if min_tweet is None:
                min_tweet = tweets[0]

            continue_search = self.save_tweets(tweets, write_f)

            # Our max tweet is the last tweet in the list
            max_tweet = tweets[-1]
            if min_tweet['tweet_id'] is not max_tweet['tweet_id']:
                max_position = "TWEET-%s-%s" % (max_tweet['tweet_id'], min_tweet['tweet_id'])
                url = self.construct_url(query, max_position=max_position)
                self.save_max_position(url, urls_f)
                # Sleep for our rate_delay
                sleep(self.rate_delay)
                response = self.execute_search(url)

        write_f.close()
        urls_f.close()

    def execute_search(self, url):
        """
        Executes a search to Twitter for the given URL
        :param url: URL to search twitter with
        :return: A JSON object with data from Twitter
        """
        try:
            # Specify a user agent to prevent Twitter from returning a profile card
            headers = {
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36'
            }
            req = urllib2.Request(url, headers=headers)
            # print "connecting ; ",
            response = urllib2.urlopen(req)
            data = json.loads(response.read())
            # print "reading ; ",
            return data
            # If we get a ValueError exception due to a request timing out, we sleep for our error delay, then make
            # another attempt
        except ValueError as e:
            print
            e.message
            self.handle_error(url)

        # Handle other errors similarly
        except urllib2.HTTPError, e:
            print
            'HTTPError: ' + str(e.code)
            self.handle_error(url)

        except urllib2.URLError, e:
            print
            'URLError: ' + str(e.reason)
            self.handle_error(url)

        except Exception:
            import traceback
            print 'Generic Exception: ' + traceback.format_exc()
            self.handle_error(url)

    def handle_error(self, url):
        print 'Sleeping for %i seconds' % self.error_delay
        sleep(self.error_delay)
        return self.execute_search(url)

    @staticmethod
    def parse_tweets(items_html):
        """
        Parses Tweets from the given HTML
        :param items_html: The HTML block with tweets
        :return: A JSON list of tweets
        """
        soup = BeautifulSoup(items_html, "lxml")
        tweets = []
        for li in soup.find_all("li", class_='js-stream-item'):

            # If our li doesn't have a tweet-id, we skip it as it's not going to be a tweet.
            if 'data-item-id' not in li.attrs:
                continue

            tweet = {
                'tweet_id': li['data-item-id'],
                'text': "",
                'user_screen_name': "",
                'user_name': "",
                'retweets': 0,
                'favorites': 0,
            }

            # Tweet Text
            text_p = li.find("p", class_="tweet-text")
            if text_p is not None:
                tweet['text'] = text_p.get_text().encode('utf-8')

            # Tweet User ID, User Screen Name, User Name, Permalink
            user_details_div = li.find("div", class_="tweet")
            if user_details_div is not None:
                tweet['user_screen_name'] = user_details_div['data-screen-name']
                tweet['user_name'] = user_details_div['data-name']

            # Tweet Retweets
            retweet_span = li.select("span.ProfileTweet-action--retweet > span.ProfileTweet-actionCount")
            if retweet_span is not None and len(retweet_span) > 0:
                tweet['retweets'] = int(retweet_span[0]['data-tweet-stat-count'])

            # Tweet Favourites
            favorite_span = li.select("span.ProfileTweet-action--favorite > span.ProfileTweet-actionCount")
            if favorite_span is not None and len(retweet_span) > 0:
                tweet['favorites'] = int(favorite_span[0]['data-tweet-stat-count'])

            tweets.append(tweet)
        return tweets

    @staticmethod
    def construct_url(query, max_position=None):
        """
        For a given query, will construct a URL to search Twitter with
        :param query: The query term used to search twitter
        :param max_position: The max_position value to select the next pagination of tweets
        :return: A string URL
        """

        params = {
            # Type Param
            'f': 'tweets',
            # Query Param
            'q': query
        }

        # If our max_position param is not None, we add it to the parameters
        if max_position is not None:
            params['max_position'] = max_position

        url_tupple = ('https', 'twitter.com', '/i/search/timeline', '', urlencode(params), '')
        return urlunparse(url_tupple)

    @abstractmethod
    def save_tweets(self, tweets, write_f):
        """
        An abstract method that's called with a list of tweets.
        When implementing this class, you can do whatever you want with these tweets.
        """

    @abstractmethod
    def save_max_position(self, max_position, write_f):
        """
        An abstract method to log search URLs with max_position, in order to resume search.
        """


class TwitterSearchImpl(TwitterSearch):
    def __init__(self, rate_delay, error_delay, max_tweets):
        """
        :param rate_delay: How long to pause between calls to Twitter
        :param error_delay: How long to pause when an error occurs
        :param max_tweets: Maximum number of tweets to collect for this example
        """
        super(TwitterSearchImpl, self).__init__(rate_delay, error_delay)

        # THIS SETS THE MAXIMUM NUMBER OF TWEETS TO COLLECT (PER ROUND)
        self.max_tweets = maximum
        self.counter = 0

    def save_tweets(self, tweets, write_f):
        """
        Save tweets to CSV file
        :return:
        """

        # print 'writing'
        for tweet in tweets:
            # Lets add a counter so we only collect a max number of tweets
            self.counter += 1
            write_f.write(('\n%s;%s;%s;%s;%s,;%s' % (
                str(datetime.date(dt_obj_start)), tweet['user_screen_name'], tweet['user_name'].replace('"', '""'),
                tweet['retweets'], tweet['favorites'],
                tweet['text'].replace('"', '""').replace('\n', ' ').replace('\r', ' ').replace('  ', ' ')
            )))

            # When we've reached our max limit, return False so collection stops
            if self.counter >= self.max_tweets:
                return False

        return True

    def save_max_position(self, max_position, write_f):
        """
        Save URLs with max_position to CSV file
        :return:
        """
        write_f.write(max_position)
        write_f.write('\n')
        return True

# ==========================================================
# RUN THE PROGRAM



# Let user define search term
search_for = raw_input("Search term: ")

# Have the user input start and stop dates and convert them to datetime format
start_date = raw_input("Start date [yyyy-mm-dd]: ")
stop_date = raw_input("End date [yyyy-mm-dd]: ")
dt_str_start = start_date
dt_str_stop = stop_date
dt_obj_start = datetime.strptime(dt_str_start, '%Y-%m-%d')
dt_obj_stop = datetime.strptime(dt_str_stop, '%Y-%m-%d')

# Let the user set the slice size
maximum = int(raw_input("Slice size (number of tweets): "))

# Make sure that the search loop is running (one date slice at a time)
# for as long as the (increasing) dtr_obj_start is before the (fixed) dtr_obj_stop
while dt_obj_start <= dt_obj_stop: # As long as the stop date has not been reached
    dt_obj_slice = dt_obj_start + timedelta(days=1) # Add 1 day to the start date to get the end of the 1-day slice
    print 'Getting slice from ' + str(datetime.date(dt_obj_start))
    #print 'This technically means a search from ' + str(datetime.date(dt_obj_start)) + ' to ' + str(datetime.date(dt_obj_slice))

    if __name__ == '__main__':
        reload(sys)
        sys.setdefaultencoding('utf8')
        twit = TwitterSearchImpl(0, 5, 20)
        twit.search(str(search_for) + " since:" + str(datetime.date(dt_obj_start)) + " until:" + str(datetime.date(dt_obj_slice)),
                    "TWEET-743956284588826628-743529795045232641")

    # After getting the slice, increase start date by 1 to move on
    dt_obj_start = dt_obj_start + timedelta(days=1)

print 'Slicing complete, now go analyse your data!'

