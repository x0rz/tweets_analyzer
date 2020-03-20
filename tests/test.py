# usage: tweets_analyzer.py -n <screen_name> [options]
#
# Simple Twitter Profile Analyzer
#
# optional arguments:
#   -h, --help            show this help message and exit
#   -l N, --limit N       limit the number of tweets to retreive (default=1000)
#   -n screen_name, --name screen_name
#                         target screen_name
#   -f FILTER, --filter FILTER
#                         filter by source (ex. -f android will get android
#                         tweets only)
#   --no-timezone         removes the timezone auto-adjustment (default is UTC)
#   --utc-offset UTC_OFFSET
#                         manually apply a timezone offset (in seconds)
#   --friends             will perform quick friends analysis based on lang and
#                         timezone (rate limit = 15 requests)
#   -e path/to/file, --export path/to/file
#                         exports results to file
#   -j, --json            outputs json
#   -s, --save            saves tweets to tweets/{twitter_handle}/{yyyy-mm-
#                         dd_HH-MM-SS}.json
#   --no-color            disables colored output
#   --no-retweets         does not evaluate retweets

import unittest
import tempfile
from subprocess import Popen, PIPE
import os, shutil
import json
import datetime

from parameterized import parameterized, param


class TestClass(unittest.TestCase):  # pylint: disable=too-many-public-methods
    params_mapping = {
        'screen_name': '-n',
        'tweets_limit': '-l',
        'tweets_filter': '-f',
        'tweets_save': '-s',
        'tweets_no_retweets': '--no-retweets',
        'friends': '--friends',
        'export': '-e',
        'outputs_json': '-j'
    }
    @classmethod
    def setUpClass(cls) -> None:
        cls.install_path = tempfile.mkdtemp()
        cls.output_dir = os.path.join(cls.install_path, '.tmp')
        source_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)))
        for file_name in os.listdir(source_dir):
            full_file_name = os.path.join(source_dir, file_name)
            if os.path.isfile(full_file_name):
                shutil.copy(full_file_name, cls.install_path)
            else:
                shutil.copytree(full_file_name, os.path.join(cls.install_path, file_name))
        os.mkdir(cls.output_dir)

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            shutil.rmtree(cls.install_path)
        except:
            pass

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()

    test_cases = [
        dict(screen_name=None),
        dict(screen_name='screen_0_tweets'),
        dict(screen_name='screen_0_tweets', tweets_limit=0),
        dict(screen_name='screen_0_tweets', tweets_limit=10),
        dict(screen_name='screen_10_tweets'),
        dict(screen_name='screen_10_tweets', tweets_limit=0),
        dict(screen_name='screen_10_tweets', tweets_limit=5),
        dict(screen_name='screen_10_tweets', tweets_limit=9),
        dict(screen_name='screen_10_tweets', tweets_limit=10),
        dict(screen_name='screen_10_tweets', tweets_limit=11),
        dict(screen_name='screen_10000_tweets'),
        dict(screen_name='screen_10000_tweets', tweets_limit=9999),
        dict(screen_name='screen_10000_tweets', tweets_limit=10000),
        dict(screen_name='screen_10000_tweets', tweets_limit=10001),
        dict(screen_name='screen_10000_tweets', tweets_filter='android'),
        dict(screen_name='screen_10000_tweets', tweets_filter='android', tweets_limit=0),
        dict(screen_name='screen_10000_tweets', tweets_filter='android', tweets_limit=10),
        dict(screen_name='screen_10000_tweets', tweets_filter='android', tweets_limit=500),
        dict(screen_name='screen_10000_tweets', tweets_filter='android', tweets_save=True),
        dict(screen_name='screen_10000_tweets', tweets_filter='android', tweets_limit=0, tweets_save=True),
        dict(screen_name='screen_10000_tweets', tweets_filter='android', tweets_limit=10, tweets_save=True),
        dict(screen_name='screen_10000_tweets', tweets_filter='android', tweets_limit=500, tweets_save=True),
        dict(screen_name='screen_10000_tweets', tweets_save=True),
        dict(screen_name='screen_10000_tweets', tweets_limit=0, tweets_save=True),
        dict(screen_name='screen_10000_tweets', tweets_limit=10, tweets_save=True),
        dict(screen_name='screen_10000_tweets', tweets_limit=500, tweets_save=True),

        dict(screen_name='screen_10000_tweets', tweets_no_retweets=True),
        dict(screen_name='screen_10000_tweets', tweets_no_retweets=True, tweets_filter='android'),
        dict(screen_name='screen_10000_tweets', tweets_no_retweets=True, tweets_filter='android', tweets_limit=0),
        dict(screen_name='screen_10000_tweets', tweets_no_retweets=True, tweets_filter='android', tweets_limit=10),
        dict(screen_name='screen_10000_tweets', tweets_no_retweets=True, tweets_filter='android', tweets_save=True),
        dict(screen_name='screen_10000_tweets', tweets_no_retweets=True, tweets_filter='android', tweets_limit=0, tweets_save=True),
        dict(screen_name='screen_10000_tweets', tweets_no_retweets=True, tweets_filter='android', tweets_limit=10, tweets_save=True),

        dict(screen_name='screen_10000_tweets', friends=True),
        dict(screen_name='screen_10000_tweets', friends=True, tweets_no_retweets=True),
        dict(screen_name='screen_10000_tweets', friends=True, tweets_no_retweets=True, tweets_filter='android'),
        dict(screen_name='screen_10000_tweets', friends=True, tweets_no_retweets=True, tweets_filter='android',
              tweets_save=True),
        dict(screen_name='screen_10000_tweets', friends=True, tweets_no_retweets=True, tweets_filter='android',
              tweets_limit=10,
              tweets_save=True),
        dict(screen_name='screen_10000_tweets', friends=True, tweets_no_retweets=True, tweets_filter='android',
              tweets_limit=10),
        dict(screen_name='screen_10000_tweets', friends=True, tweets_no_retweets=True, tweets_limit=10),
        dict(screen_name='screen_10000_tweets', friends=True, tweets_filter='android', tweets_limit=10),

        dict(screen_name='screen_10000_tweets', friends=True, tweets_no_retweets=True),
        dict(screen_name='screen_10000_tweets', friends=True, tweets_no_retweets=True, tweets_filter='android'),
        dict(screen_name='screen_10000_tweets', friends=True, tweets_no_retweets=True, tweets_filter='android',
              tweets_save=True),
        dict(screen_name='screen_10000_tweets', friends=True, tweets_no_retweets=True, tweets_filter='android',
              tweets_limit=10,
              tweets_save=True),
    ]

    def test_tweets_analyzer(self):
        for test_case in self.test_cases:
            with self.subTest(str(test_case)):
                self._test_tweets_analyzer(**test_case)

    def _test_tweets_analyzer(self, **kwargs):
        test_params = {}
        cmd_params = []
        for param_name, param_value in kwargs.items():
            cmd_key = self.params_mapping.get(param_name, None)
            if cmd_key is None:
                cmd_key = param_name
            if isinstance(param_value, bool) and param_value:
                cmd_params.append(f'{cmd_key} {param_value}')
            elif isinstance(param_value, str):
                cmd_params.append(f'{cmd_key} {param_value}')
            else:
                raise ValueError("Unexpected parameter type")
            test_params[param_name] = param_value
        cmd = ['pipenv', 'run', f'{self.install_path}/tweets_analyzer.py']
        cmd.extend(cmd_params)
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate()

        if self._check_cmd_output(
                got_code=proc.returncode,
                got_stderr=stderr,
                got_stdout=stdout,
                **test_params):
            self._check_tweets(**test_params)

    def _check_cmd_output(self, screen_name=None, friends: bool = False, outputs_json: bool = False,
                          got_code=None, got_stderr=None, got_stdout=None, **extra_args):
        expected_code = 0
        expected_stderr = b''
        expected_stdout = b''
        if screen_name is None:
            expected_code = 2
            expected_stderr = b'usage: tweets_analyzer.py -n <screen_name> [options]\ntweets_analyzer.py: error: the following arguments are required: -n/--name\n'
        self.assertEqual((expected_code, expected_stderr, expected_stdout), ( got_code, got_stderr, got_stdout))
        return expected_code == 0

    def _check_tweets(self, screen_name=None, tweets_limit: int = 1000, tweets_filter: str = None, tweets_save: bool = False,
                      tweets_no_retweets: bool = False, **extra_args):
        if self.is_valid_screen_name(screen_name):
            expected_tweets = self._get_expected_tweets_count_from_screen_name(screen_name)
        else:
            expected_tweets = []
        if tweets_filter:
            expected_tweets = self._filter_tweets_by_filter(expected_tweets)
        if tweets_no_retweets:
            self._remove_retweets(expected_tweets)
        expected_tweets = min(expected_tweets, tweets_limit)
        expected_tweets = expected_tweets[:expected_tweets]

        if not tweets_save:
            self._check_no_saved_tweets()
            return
        got_tweets = self._load_saved_tweets()
        # Do some logic on matching expected and got tweets
        self.assertEqual(expected_tweets, got_tweets)

    def _check_no_saved_tweets(self):
        self.assertFalse(os.path.exists(os.path.join(self.install_path, 'tweets')))

    def _load_saved_tweets(self):
        output = []
        base_path = os.path.join(self.install_path, 'tweets')
        for dir_name in os.listdir(base_path):
            full_dir_name = os.path.join(base_path, dir_name)
            if not os.path.isdir(full_dir_name):
                self.fail(f'Found unexpected file {full_dir_name} in tweets directory')
            for file_name in os.listdir(full_dir_name):
                full_file_name = os.path.join(full_dir_name, file_name)
                try:
                    self.assertTrue(datetime.datetime.strptime(file_name, '%Y-%m-%d_%H-%M-%S.json'))
                except ValueError:
                    self.fail('tweet file has wrong file name')
                try:
                    with open(full_file_name, 'r') as f:
                        file_tweets = json.load(f)
                except:
                    self.fail('tweet file has wrong file name')
                output.extend(file_tweets)
        return output

    def _filter_tweets_by_filter(self, filter, tweets):
        output = []
        for tweet in tweets:
            # Reduce tweets by filter
            if True is True:
                output.append(tweet)
        return output

    def _remove_retweets(self, tweets):
        for tweet in tweets:
            del tweet['retweets']

    def is_valid_screen_name(self, screen_name):
        return screen_name in ['screen_0_tweets', 'screen_10_tweets' , 'screen_10000_tweets']

    def _get_expected_tweets_count_from_screen_name(self, screen_name):
        with open(os.path.join(os.path.dirname(__file__), 'test_data/tweets.json'), 'r') as f:
            return json.load(f)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        del self.temp_dir