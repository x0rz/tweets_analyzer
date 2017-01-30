# Simple Twitter Profile Analyzer

The goal of this simple python script is to analyze a Twitter profile through its tweets by detecting:
  - Average tweet activity, by hour and by day of the week
  - Timezone and language set for the Twitter interface
  - Sources used (mobile application, web browser, ...)
  - Geolocations
  - Most used hashtags, most retweeted users and most mentioned users

There are plenty of things that could be added to the script, feel free to contribute! 👍

### Installation
Update your API keys in the *secrets.py* file.

```sh
$ pip install tweepy ascii_graph tqdm numpy
```

Sorry, I only tested the script with *python2*

### Usage

```
usage: tweets_analyzer.py [-h] [-l N] -n screen_name [-f FILTER]
                          [--no-timezone] [--utc-offset UTC_OFFSET]

Analyze a Twitter account activity

optional arguments:
  -h, --help            show this help message and exit
  -l N, --limit N       limit the number of tweets to retreive (default=1000)
  -n screen_name, --name screen_name
                        target screen_name
  -f FILTER, --filter FILTER
                        filter by source (ex. -f android will get android
                        tweets only)
  --no-timezone         removes the timezone auto-adjustment (default is UTC)
  --utc-offset UTC_OFFSET
                        manually apply a timezone offset (in seconds)
```

Example output:
![Twitter account activity](https://cdn-images-1.medium.com/max/800/1*KuhfDr_2bOJ7CPOzVXnwLA.png)

License
----
GNU GPLv3
