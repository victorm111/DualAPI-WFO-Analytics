import http.client
import glob
import sys
import traceback

import json
import logging
import os
from os import listdir

from os import listdir
import pandas as pd
import shutil
import time as time
from datetime import date,  timedelta

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pytest_check as check        # soft asserts

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# getting the name of the directory
current = os.path.dirname(os.path.realpath(__file__))

# Getting the parent directory name
# where the current directory is present.
parent = os.path.dirname(current)
# adding the parent directory to
# the sys.path.
sys.path.append(parent)
# retrieve data and time for test run
today = str(date.today())
t = time.localtime()
current_time = time.strftime("%H_%M_%S", t)

# getting the name of the directory
current = os.path.dirname(os.path.realpath(__file__))

# Getting the parent directory name
# where the current directory is present.
parent = os.path.dirname(current)

class test_SearchReplay:
  def __init__(self, test_read_config_file: object) -> None:
    """init the class"""

    LOGGER.debug('test_SearchReplay:: init start')
    self.yesterdaydate = (date.today() - timedelta(1)).isoformat() # yesterday's date for daily report
    self.todaydate = date.today().isoformat()

    self.Payload_start_time = "2023-12-18T00:00:00.000Z"   #  "beginPeriod": "2023-12-18T00:00:00.000Z",
    self.collect_yesterday = test_read_config_file['latest_24hrs']['enable']

    if self.collect_yesterday:
      self.Payload_start_time = self.yesterdaydate + 'T00:00:00-00:00'  # update if 24hr test enabled

    self.title = 'SearchReplay'
    self.author = 'VW'
    self.URL = test_read_config_file['urls']['url_wfo']
    self.URL_api = test_read_config_file['urls']['url_wfo_SearchReplayapi']

    self.s = 'null'  # session request response
    self.SR_df = pd.DataFrame()  # hold returned data, create empty
    self.SR_df_sorted =pd.DataFrame()  # hold returned data, create empty

    self.response_dict = {}     # empty dictionary
    self.token = 'null'
    self.payload = {}
    self.headers = {}
    self.session = 'null'
    self.retry = 'null'
    self.adapter = 'null'
    self.Payload_end_time = self.todaydate + 'T00:00:00.000Z'
    self.requestType = 'Absolute'
    self.preppedReq = ''  # prepped req
    self.SR_send_url = ''   # session req url

    self.json_output = test_read_config_file['dirs']['SR_to_json_output']
    self.csv_output = test_read_config_file['dirs']['SR_to_csv_output']
    self.csv_headers = 'null'
    self.no_calls = 0  # number of calls retrieved

    # delete previous output csv files
    # Get All List of Files

    self.base_report_folder = test_read_config_file['dirs']['SR_report']

    # delete previous output files
    LOGGER.debug('test_SearchReplay:: init: delete previous output files')
    all_files = os.listdir(self.base_report_folder)

    for f in all_files:
      os.remove(self.base_report_folder + '/' + f)

    LOGGER.debug('test_SearchReplay:: init finished')
    return

  def test_getSearchAndReplay_buildReq(self, getVerintToken):
        """retrieves daily search and replay"""

        self.SR_df = pd.DataFrame()
        LOGGER.info('test_getSearchAndReplay_buildReq():: started')
        self.token = getVerintToken

        assert(self.token),'test_getSearchAndReplay_buildReq token not retrieved'
        LOGGER.debug('test_getSearchAndReplay_buildReq:: token retrieved, build request')

        self.payload = json.dumps({
          "period": {
            "beginPeriod": self.Payload_start_time,
            "endPeriod": self.Payload_end_time,
            "type": self.requestType
          }
        })
        self.headers = {
          'Verint-Session-ID': '42334',
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Impact360AuthToken': self.token
        }

        # create a sessions object
        self.session = requests.Session()
        assert self.session,'test_getSearchAndReplay_buildReq() session not created'
        # Set the Content-Type header to application/json for all requests in the session
        # session.headers.update({'Content-Type': 'application/json'})

        self.retry = Retry(connect=25, backoff_factor=0.5)

        self.adapter = HTTPAdapter(max_retries=self.retry)
        self.session.mount('https://', self.adapter)
        self.session.mount('http://', self.adapter)
        # Set the Content-Type header to application/json for all requests in the session
        self.session.headers.update(self.headers)

        LOGGER.info(f'test_getSearchAndReplay_buildReq:: request start: {self.Payload_start_time}')
        LOGGER.info(f'test_getSearchAndReplay_buildReq:: request start: {self.Payload_end_time}')
        self.SR_send_url = 'https://' + self.URL + self.URL_api
        req = requests.Request('POST', url=self.SR_send_url, headers=self.session.headers, data=self.payload)
        self.preppedReq = req.prepare()
        #self.preppedReq.body = self.payload

        LOGGER.debug('test_getSearchAndReplay_buildReq:: finished')
        return self.session, self.preppedReq

  def test_getSearchAndReplay_sendReq(self, session, preppedReq) -> object:

    self.session = session          # session built previously
    self.preppedReq = preppedReq    # prepped request

    LOGGER.debug('test_getSearchAndReplay_sendReq:: start')
    LOGGER.info(f'test_getSearchAndReplay_sendReq:: request interval: "starting:" + {self.Payload_start_time} "ending:" + {self.Payload_end_time}')

    try:
      self.s = self.session.send(preppedReq, timeout=25, verify=False)  # send request
      #self.s=self.session.post('https://'+self.URL+self.URL_api, data=self.payload, timeout=25, verify=False)

    except requests.exceptions.HTTPError as errh:
      print("Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
      print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
      print("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:

      traceback.print_exc(file=sys.stdout)
      print("OOps: Something Else", err)

    else:

      assert self.s.status_code==200, 'test_getSearchAndReplay() session request response not 200 OK'
      self.s.raise_for_status()

      print(f'test_getSearchAndReplay() session resp received code: {self.s.status_code}')
      LOGGER.info(f'test_getSearchAndReplay:: response received: {self.s.status_code}')

      try:
        self.response_dict = json.loads(self.s.text)
      except:
        LOGGER.exception('test_getSearchAndReplay:: json not received ok')
      else:
        LOGGER.debug('test_getSearchAndReplay:: test_getSearchAndReplay() json unpacked ok')
        check.not_equal(len(self.response_dict), 0, 'test_getSearchAndReplay() empty json returned')

        self.no_calls = len(self.response_dict.get('Sessions'))
        LOGGER.info(f'test_getSearchAndReplay:: test_getSearchAndReplay() number of calls returned: {self.no_calls}')

        if self.no_calls:

          LOGGER.info(f'test_getSearchAndReplay:: AWE test_getSearchAndReplay() calls retrieved, attempt write to csv at location: {self.csv_output}')
          # store call data headers from the json
          self.csv_headers = list(self.response_dict.get('Sessions')[0].keys())

          # create 2d list first, will store call data
          mylist = []
          for calls in range(self.no_calls):
            mylist.append(list(self.response_dict.get('Sessions')[calls].values()))

          # write calls list + headers to df
          for calls in range(self.no_calls):
            self.SR_df = pd.DataFrame(mylist, columns=self.csv_headers)

          check.not_equal(len(self.SR_df), 0, 'test_getSearchAndReplay() ERROR no calls df returned')
          self.SR_df_sorted = self.SR_df.sort_values(by='local_audio_start_time', ascending=False)

          try:
            self.SR_df_sorted.to_csv(self.csv_output, index=False, header=self.csv_headers)
          except:
            LOGGER.exception('test_getSearchAndReplay::  AWE S&R csv creation error')
          else:
            LOGGER.info('test_getSearchAndReplay::  AWE S&R csv written ok')

        else:
          LOGGER.info('test_getSearchAndReplay::  no calls retrieved therefore no output csv created, finish up')

      LOGGER.info('test_getSearchAndReplay::  API test routines finished')
      return self.SR_df



