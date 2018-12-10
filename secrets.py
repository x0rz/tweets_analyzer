import os
# Go to https://apps.twitter.com/ and create an app.
# The consumer key and secret will be generated for you after
consumer_key=os.getenv('TWITTER_CONSUMER_KEY')
consumer_secret=os.getenv('TWITTER_CONSUMER_SECRET')

# After the step above, you will be redirected to your app's page.
# Create an access token under the the "Create New App" section
access_token=os.getenv('TWITTER_ACCESS_TOKEN')
access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

