#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 @x0rz
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# Usage:
# python tweets_analyzer.py -n screen_name
#
# Install:
# pip install tweepy ascii_graph tqdm numpy

from __future__ import unicode_literals

from ascii_graph import Pyasciigraph
from ascii_graph.colors import Gre, Yel, Red
from ascii_graph.colordata import hcolor
from tqdm import tqdm
import tweepy
import numpy
import argparse
import collections
import contextlib
import datetime
import re
import json
import sys
import os

__version__ = '0.2-dev'

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from secrets import consumer_key, consumer_secret, access_token, access_token_secret

# Here are sglobals used to store data - I know it's dirty, whatever
start_date = 0
end_date = 0
export = ""
jsono = {}
save_folder = "tweets"
color_supported = True
ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

parser = argparse.ArgumentParser(
    description=f"Simple Twitter Profile Analyzer (https://github.com/x0rz/tweets_analyzer) version {__version__}",
    usage='%(prog)s -n <screen_name> [options]',
)
parser.add_argument('-l', '--limit', metavar='N', type=int, default=1000,
                    help='limit the number of tweets to retreive (default=1000)')
parser.add_argument('-n', '--name', required=True, metavar="screen_name",
                    help='target screen_name')

parser.add_argument('-f', '--filter', help='filter by source (ex. -f android will get android tweets only)')

parser.add_argument('--no-timezone', action='store_true',
                    help='removes the timezone auto-adjustment (default is UTC)')

parser.add_argument('--utc-offset', type=int,
                    help='manually apply a timezone offset (in seconds)')

parser.add_argument('--friends', action='store_true',
                    help='will perform quick friends analysis based on lang and timezone (rate limit = 15 requests)')

parser.add_argument('-e', '--export', metavar='path/to/file', type=str,
                    help='exports results to file')

parser.add_argument('-j', '--json', action='store_true',
                    help='outputs json')

parser.add_argument('-s', '--save', action='store_true',
                    help='saves tweets to %s/{twitter_handle}/{yyyy-mm-dd_HH-MM-SS}.json' % save_folder)

parser.add_argument('--no-color', action='store_true',
                    help='disables colored output')

parser.add_argument('--no-retweets', action='store_true',
                    help='does not evaluate retweets')

args = parser.parse_args()

activity_hourly = {
    ("%2i:00" % i).replace(" ", "0"): 0 for i in range(24)
}

activity_weekly = {
    "%i" % i: 0 for i in range(7)
}

detected_langs = collections.Counter()
detected_sources = collections.Counter()
detected_places = collections.Counter()
geo_enabled_tweets = 0
detected_hashtags = collections.Counter()
detected_domains = collections.Counter()
detected_timezones = collections.Counter()
retweets = 0
retweeted_users = collections.Counter()
mentioned_users = collections.Counter()
id_screen_names = {}
friends_timezone = collections.Counter()
friends_lang = collections.Counter()


def process_tweet(tweet):
    """ Processing a single Tweet and updating our datasets """
    global start_date
    global end_date
    global geo_enabled_tweets
    global retweets

    if args.no_retweets:
        if hasattr(tweet, 'retweeted_status'):
            return
        if hasattr(tweet, 'is_quote_status') and tweet.is_quote_status:
            return

    # Check for filters before processing any further
    if (
            args.filter
            and tweet.source
            and args.filter.lower() not in tweet.source.lower()
    ):
        return

    tw_date = tweet.created_at

    # Updating most recent tweet
    end_date = end_date or tw_date
    start_date = tw_date

    # Handling retweets
    with contextlib.suppress(Exception):
        # We use id to get unique accounts (screen_name can be changed)
        rt_id_user = tweet.retweeted_status.user.id_str
        retweeted_users[rt_id_user] += 1

        if tweet.retweeted_status.user.screen_name not in id_screen_names:
            id_screen_names[rt_id_user] = f"@{tweet.retweeted_status.user.screen_name}"

        retweets += 1
    # Adding timezone from profile offset to set to local hours
    if tweet.user.utc_offset and not args.no_timezone:
        tw_date = (tweet.created_at + datetime.timedelta(seconds=tweet.user.utc_offset))

    if args.utc_offset:
        tw_date = (tweet.created_at + datetime.timedelta(seconds=args.utc_offset))

    # Updating our activity datasets (distribution maps)
    activity_hourly[f"{str(tw_date.hour).zfill(2)}:00"] += 1
    activity_weekly[str(tw_date.weekday())] += 1

    # Updating langs
    detected_langs[tweet.lang] += 1

    # Updating sources
    detected_sources[tweet.source] += 1

    # Detecting geolocation
    if tweet.place:
        geo_enabled_tweets += 1
        tweet.place.name = tweet.place.name
        detected_places[tweet.place.name] += 1

    # Updating hashtags list
    if tweet.entities['hashtags']:
        for ht in tweet.entities['hashtags']:
            ht['text'] = f"#{ht['text']}"
            detected_hashtags[ht['text']] += 1

    # Updating domains list
    if tweet.entities['urls']:
        for url in tweet.entities['urls']:
            domain = urlparse(url['expanded_url']).netloc
            if domain != "twitter.com":  # removing twitter.com from domains (not very relevant)
                detected_domains[domain] += 1

    # Updating mentioned users list
    if tweet.entities['user_mentions']:
        for ht in tweet.entities['user_mentions']:
            mentioned_users[ht['id_str']] += 1
            if ht['screen_name'] not in id_screen_names:
                id_screen_names[ht['id_str']] = f"@{ht['screen_name']}"


def process_friend(friend):
    """ Process a single friend """
    friends_lang[friend.lang] += 1  # Getting friend language & timezone
    if friend.time_zone:
        friends_timezone[friend.time_zone] += 1


def get_friends(api, username, limit):
    """ Download friends and process them """
    for friend in tqdm(tweepy.Cursor(api.friends, screen_name=username).items(limit), unit="friends", total=limit):
        process_friend(friend)


def get_tweets(api, username, fh, limit):
    """ Download Tweets from username account """
    if args.json is False:
        for status in tqdm(tweepy.Cursor(api.user_timeline, screen_name=username).items(limit), unit="tw", total=limit):
            process_tweet(status)
            if args.save:
                fh.write(f"{json.dumps(status._json)},")
    else:
        for status in (tweepy.Cursor(api.user_timeline, screen_name=username).items(limit)):
            process_tweet(status)
            if args.save:
                fh.write(f"{json.dumps(status._json)},")


def int_to_weekday(day):
    weekdays = "Monday Tuesday Wednesday Thursday Friday Saturday Sunday".split()
    return weekdays[int(day) % len(weekdays)]


def supports_color():
    if args.no_color:
        return False
    # copied from https://github.com/django/django/blob/master/django/core/management/color.py
    plat = sys.platform
    supported_platform = plat != 'Pocket PC' and (plat != 'win32' or 'ANSICON' in os.environ)
    # isatty is not always implemented, #6223.
    is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    return bool(supported_platform and is_a_tty)


def cprint(strng):
    if not color_supported:
        strng = ansi_escape.sub('', strng)
    if args.json is False:
        print(strng)
        export_string(strng)


def export_string(strng):
    global export
    if args.export is not None:
        export += strng + "\n"


def export_write():
    global export
    if args.export is not None:
        with open(args.export, "w") as text_file:
            if args.json is False:
                # remove ANSI color codes for export
                export = ansi_escape.sub('', export)
                # remove non ascii characters
                export = "".join(i for i in export if ord(i) < 128)
            else:
                export = json.dumps(jsono)
            text_file.write(export)


def print_stats(dataset, top=5):
    """ Displays top values by order """
    if sum := numpy.sum(list(dataset.values())):
        sorted_keys = sorted(dataset, key=dataset.get, reverse=True)
        max_len_key = max([len(x) for x in sorted_keys][:top])  # use to adjust column width
        i = 0
        for k in sorted_keys:
            try:
                cprint(("- \033[1m{:<%d}\033[0m {:>6} {:<4}" % max_len_key)
                       .format(k, dataset[k], "(%d%%)" % ((float(dataset[k]) / sum) * 100)))
            except Exception:
                import ipdb
                ipdb.set_trace()
            i += 1
            if i >= top:
                break
    else:
        cprint("No data")
    cprint("")


def print_charts(dataset, title, weekday=False):
    """ Prints nice charts based on a dict {(key, value), ...} """
    chart = []
    keys = sorted(dataset.keys())
    mean = numpy.mean(list(dataset.values()))
    median = numpy.median(list(dataset.values()))
    if args.json is False:
        export_string(title)

    for key in keys:
        if (dataset[key] >= median * 1.33):
            displayed_key = "%s (\033[92m+\033[0m)" % (int_to_weekday(key) if weekday else key)
        elif (dataset[key] <= median * 0.66):
            displayed_key = "%s (\033[91m-\033[0m)" % (int_to_weekday(key) if weekday else key)
        else:
            displayed_key = (int_to_weekday(key) if weekday else key)
        if args.json is False:
            export_string(f"{dataset[key]} - {int_to_weekday(key) if weekday else key}")
        chart.append((displayed_key, dataset[key]))

    thresholds = {
        int(mean): Gre, int(mean * 2): Yel, int(mean * 3): Red,
    }

    data = hcolor(chart, thresholds)

    graph = Pyasciigraph(
        separator_length=4,
        multivalue=False,
        human_readable='si',
    )

    if args.json is False:
        for line in graph.graph(title, data):
            if not color_supported:
                ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
                line = ansi_escape.sub('', line)
            print(line)
    cprint("")


def main():
    global color_supported
    color_supported = supports_color()

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    twitter_api = tweepy.API(auth)

    now = datetime.datetime.now()
    save_path = f"{save_folder}/{args.name}"
    save_file = False
    if args.save:
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        save_file = open(
            f"{save_path}/" + now.strftime("%Y-%m-%d_%H-%M-%S") + ".json", "w"
        )
        save_file.write("[")

    # Getting general account's metadata
    cprint(f"[+] Getting @{args.name} account data...")
    jsono['user_name'] = args.name

    user_info = twitter_api.get_user(screen_name=args.name)

    cprint("[+] lang           : \033[1m%s\033[0m" % user_info.lang)
    cprint("[+] geo_enabled    : \033[1m%s\033[0m" % user_info.geo_enabled)
    cprint("[+] time_zone      : \033[1m%s\033[0m" % user_info.time_zone)
    cprint("[+] utc_offset     : \033[1m%s\033[0m" % user_info.utc_offset)
    jsono['user_lang'] = user_info.lang
    jsono['user_geo_enabled'] = user_info.geo_enabled
    jsono['user_time_zone'] = user_info.time_zone
    jsono['user_utc_offset'] = user_info.utc_offset

    if user_info.utc_offset is None:
        cprint("[\033[91m!\033[0m] Can't get specific timezone for this user")
        jsono['user_utc_offset_note'] = "Can't get specific timezone for this user"

    if args.utc_offset:
        cprint("[\033[91m!\033[0m] Applying timezone offset %d (--utc-offset)" % args.utc_offset)
        jsono['user_utc_offset_set'] = "Applying timezone offset %d (--utc-offset)" % args.utc_offset

    cprint("[+] statuses_count : \033[1m%s\033[0m" % user_info.statuses_count)
    jsono['status_count'] = user_info.statuses_count

    # Will retreive all Tweets from account (or max limit)
    num_tweets = numpy.amin([args.limit, user_info.statuses_count])
    cprint("[+] Retrieving last %d tweets..." % num_tweets)
    jsono['status_retrieving'] = num_tweets

    # Download tweets
    get_tweets(twitter_api, args.name, save_file, limit=num_tweets)
    cprint("[+] Downloaded %d tweets from %s to %s (%d days)" % (
        num_tweets, start_date, end_date, (end_date - start_date).days))
    jsono['status_start_date'] = f"{start_date}"
    jsono['status_end_date'] = f"{end_date}"
    jsono['status_days'] = f"{(end_date - start_date).days}"

    # Checking if we have enough data (considering it's good to have at least 30 days of data)
    if (end_date - start_date).days < 30 and (num_tweets < user_info.statuses_count):
        cprint(
            "[\033[91m!\033[0m] Looks like we do not have enough tweets from user, you should consider retrying (--limit)")
        jsono[
            'status_note'] = "Looks like we do not have enough tweets from user, you should consider retrying (--limit)"

    if (end_date - start_date).days != 0:
        cprint("[+] Average number of tweets per day: \033[1m%.1f\033[0m" % (
                num_tweets / float((end_date - start_date).days)))
        jsono['status_average_tweets_per_day'] = (num_tweets / float((end_date - start_date).days))

    # Print activity distrubution charts
    if args.json is False:
        export_string("")
    print_charts(activity_hourly, "Daily activity distribution (per hour)")
    print_charts(activity_weekly, "Weekly activity distribution (per day)", weekday=True)
    jsono["activity_hourly"] = activity_hourly
    jsono["activity_weekly"] = activity_weekly

    cprint("[+] Detected languages (top 5)")
    print_stats(detected_langs)
    jsono["top_languages"] = detected_langs

    _extracted_from_main_(
        "[+] Detected sources (top 10)", detected_sources, 10, "top_sources"
    )
    cprint("[+] There are \033[1m%d\033[0m geo enabled tweet(s)" % geo_enabled_tweets)
    jsono['geo_enabled_tweet_count'] = geo_enabled_tweets

    if len(detected_places) != 0:
        _extracted_from_main_(
            "[+] Detected places (top 10)", detected_places, 10, "top_places"
        )
    _extracted_from_main_(
        "[+] Top 10 hashtags", detected_hashtags, 10, "top_hashtags"
    )
    if not args.no_retweets:
        cprint("[+] @%s did \033[1m%d\033[0m RTs out of %d tweets (%.1f%%)" % (
            args.name, retweets, num_tweets, (float(retweets) * 100 / num_tweets)))
        jsono['rt_count'] = retweets
        retweeted_users_names = {
            id_screen_names[k]: retweeted_users[k]
            for k in retweeted_users.keys()
        }
        _extracted_from_main_(
            "[+] Top 5 most retweeted users",
            retweeted_users_names,
            5,
            "top_retweeted_users",
        )
    mentioned_users_names = {
        id_screen_names[k]: mentioned_users[k] for k in mentioned_users.keys()
    }
    _extracted_from_main_(
        "[+] Top 5 most mentioned users",
        mentioned_users_names,
        5,
        "top_mentioned_users",
    )
    _extracted_from_main_(
        "[+] Most referenced domains (from URLs)",
        detected_domains,
        6,
        "top_referenced_domains",
    )
    if args.friends:
        max_friends = numpy.amin([user_info.friends_count, 300])
        cprint("[+] Getting %d @%s's friends data..." % (max_friends, args.name))
        try:
            get_friends(twitter_api, args.name, limit=max_friends)
        except tweepy.error.TweepError as e:
            if e[0][0]['code'] == 88:
                cprint("[\033[91m!\033[0m] Rate limit exceeded to get friends data, you should retry in 15 minutes")
                jsono['friend_rate_note'] = "Rate limit exceeded to get friends data, you should retry in 15 minutes"
            raise

        _extracted_from_main_(
            "[+] Friends languages", friends_lang, 6, "top_friends_languages"
        )
        _extracted_from_main_(
            "[+] Friends timezones",
            friends_timezone,
            8,
            "top_friend_timezones",
        )
    if args.json is not False:
        print(json.dumps(jsono))
    export_write()

    if args.save:
        save_file.seek(-1, os.SEEK_END)  # drop last ,
        save_file.truncate()
        save_file.write("]")
        save_file.close()


# TODO Rename this here and in `main`
def _extracted_from_main_(arg0, arg1, top, arg3):
    cprint(arg0)
    print_stats(arg1, top=top)
    jsono[arg3] = arg1


if __name__ == '__main__':
    try:
        main()
    except tweepy.error.TweepError as e:
        cprint("[\033[91m!\033[0m] Twitter error: %s" % e)
    except Exception as e:
        cprint("[\033[91m!\033[0m] Error: %s" % e)
