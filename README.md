# Simple Twitter Profile Analyzer

The goal of this simple python script is to analyze a Twitter profile through its tweets by detecting:
  - Average tweet activity, by hour and by day of the week
  - Timezone and language set for the Twitter interface
  - Sources used (mobile application, web browser, ...)
  - Geolocations
  - Most used hashtags, most retweeted users and most mentioned users
  - Friends analysis based on most frequent timezones/languages

There are plenty of things that could be added to the script, feel free to contribute! 👍

### Installation

⚠ First, update your API keys in the *secrets.py* file. To get API keys go to https://apps.twitter.com/

Python v2.7 or newer is required

You will need the following python packages installed: tweepy, ascii_graph, tqdm, numpy

```sh
pip install -r requirements.txt
```


### Usage

```
usage: tweets_analyzer.py -n <screen_name> [options]

Simple Twitter Profile Analyzer

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
  --friends             will perform quick friends analysis based on lang and
                        timezone (rate limit = 15 requests)
  -e path/to/file, --export path/to/file
                        exports results to file
  -j, --json            outputs json
  -s, --save            saves tweets to tweets/{twitter_handle}/{yyyy-mm-
                        dd_HH-MM-SS}.json
  --no-color            disables colored output
  --no-retweets         does not evaluate retweets
```

### Example output

![Twitter account activity](https://cdn-images-1.medium.com/max/800/1*KuhfDr_2bOJ7CPOzVXnwLA.png)

License
----
GNU GPLv3


If this tool has been useful for you, feel free to thank me by buying me a coffee

[![Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoff.ee/x0rz)
