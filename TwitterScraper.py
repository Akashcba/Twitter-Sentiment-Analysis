print ('==========================================================')
print ('')
print ('T W I T T E R  S C R A P E R')
print ('')
print ('==========================================================')
print ('')

# Import libraries
import urllib.request
import json
import datetime

from abc import ABCMeta
from urllib.request import urlopen
from abc import abstractmethod
from urllib.parse import urlencode
from urllib.parse import urlunparse
from bs4 import BeautifulSoup
from time import sleep
import codecs
import sys



# Let user define search to scrape
search_for = input("Enter search term: ")
print ('')
start_date = input("Start date [yyyy-mm-dd]: ")
end_date = input("End date [yyyy-mm-dd]: ")



# Do the actual search, retrieval, and writing
class TwitterSearch:

    __metaclass__ = ABCMeta

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

        write_f = codecs.open('tweets.csv', 'w+')
        urls_f = codecs.open('urls.txt', 'wb+')
        
       
       
        write_f.write('serial number, user id, name, user name, date, retweets, favorites, text, location, id, permalink, language')

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
                if "min_position" in response.keys():
                    max_position = response['min_position']
                else:
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
            req = urllib.request.Request(url, headers=headers)
            print ("Response received")
            response = urllib.request.urlopen(req)
            data = json.loads(response.read())
            print ("Data loaded")
            return data

        # If we get a ValueError exception due to a request timing out, we sleep for our error delay, then make
        # another attempt
        except ValueError as e:
            print (e.message)
            self.handle_error(url)

        #Handle other errors similarly
        except urllib.request.HTTPError as e:
            print ('HTTPError: ' + str(e.code))
            self.handle_error(url)

        except urllib.request.URLError as e:
            print ('URLError: ' + str(e.reason))
            self.handle_error(url)

        except Exception:
            import traceback
            print ('Generic Exception: ' + traceback.format_exc())
            self.handle_error(url)   

    def handle_error(self, url):
        print ("Sleeping for %i seconds" % self.error_delay)
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
                'user_id': None,
                'user_screen_name': "",
                'user_name': "",
                'created_at': None,
                'retweets': 0,
                'favorites': 0,
                'location': None,
                'language': None,
                'permalink': None
            }

            # Tweet Text
            text_p = li.find("p", class_="tweet-text")
            if text_p is not None:
                tweet['text'] = text_p.get_text().encode('utf-8')

            # Tweet User ID, User Screen Name, User Name, Permalink
            user_details_div = li.find("div", class_="tweet")
            if user_details_div is not None:
                tweet['user_id'] = user_details_div['data-user-id']
                tweet['user_screen_name'] = user_details_div['data-screen-name']
                tweet['user_name'] = user_details_div['data-name']
                tweet['permalink'] = 'https://twitter.com' + user_details_div['data-permalink-path']

            # Tweet date
            date_span = li.find("span", class_="_timestamp")
            if date_span is not None:
                tweet['created_at'] = float(date_span['data-time-ms'])

            # Tweet Retweets
            retweet_span = li.select("span.ProfileTweet-action--retweet > span.ProfileTweet-actionCount")
            if retweet_span is not None and len(retweet_span) > 0:
                tweet['retweets'] = int(retweet_span[0]['data-tweet-stat-count'])

            # Tweet Favourites
            favorite_span = li.select("span.ProfileTweet-action--favorite > span.ProfileTweet-actionCount")
            if favorite_span is not None and len(retweet_span) > 0:
                tweet['favorites'] = int(favorite_span[0]['data-tweet-stat-count'])

            #Location
            location_span = li.find("span", class_='Tweet-geo')
            if location_span is not None:
                tweet['location'] = location_span['title']

            #Language
            lang_p = li.find("p", class_='tweet-text')
            if lang_p is not None:
                tweet['language'] = lang_p['lang']

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
        self.max_tweets = max_tweets
        self.counter = 0
        self.cnt=0

    def save_tweets(self, tweets, write_f):
        """
        Save tweets to CSV file
        :return:
        """

        print ("Writing to 'tweets.csv'... [wait until done, or ctrl+C to interrupt]")

        for tweet in tweets:
            # Lets add a counter so we only collect a max number of tweets
            self.counter += 1

            if tweet['created_at'] is not None:
                self.cnt+=1
                t = datetime.datetime.fromtimestamp((tweet['created_at']/1000))
                fmt = "%Y-%m-%d %H:%M:%S"
                if tweet['location'] is not None:
                    loc = tweet['location'].replace('"', '""')
                else:
                    loc = ""
            
                write_f.write('\n"%d","%s","%s","%s","%s","%d","%d","%s","%s","%s","%s","%s"' % (self.cnt,tweet['user_id'], tweet['user_name'].replace('"', '""'), tweet['user_screen_name'].replace('"', '""'), t.strftime(fmt), tweet['retweets'], tweet['favorites'], tweet['text'].decode('utf-8').replace('"', '""').replace('\n',' '), loc, tweet['tweet_id'], tweet['permalink'], tweet['language']))
    

            
            # KILL THE MAX TWEETS SECTION TO GET AS MUCH AS POSSIBLE!
            # When we've reached our max limit, return False so collection stops
            #if self.counter >= self.max_tweets:
            #    return False

        return True

    def save_max_position(self, max_position, write_f):
        """
        Save URLs with max_position to CSV file
        :return:
        """
        my_str = max_position
        my_str_as_bytes = str.encode(my_str)
        write_f.write(my_str_as_bytes)
        my_str = '\n'
        my_str_as_bytes = str.encode(my_str)
        write_f.write(my_str_as_bytes)
        return True


if __name__ == '__main__':
    
    
    import importlib
        
    importlib.reload(sys)

    twit = TwitterSearchImpl(0, 5, 20)
    #twit.search("brexit since:2015-02-17 until:2016-06-18", "TWEET-743956284588826628-743529795045232641")
    twit.search(str(search_for) + " since:" + str(start_date) + " until:" + str(end_date), "TWEET-743956284588826628-743529795045232641")

