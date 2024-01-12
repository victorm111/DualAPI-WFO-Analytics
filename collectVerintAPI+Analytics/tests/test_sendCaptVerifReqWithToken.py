import csv
import glob
import re
import http.client
import json
import logging
import os
import shutil
import sys
import time as time
from datetime import date, timedelta
from os import listdir

import pandas as pd
import pytest_check as check  # soft asserts
import requests
import requests.adapters
import urllib3
#from urllib3.util.retry import Retry

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


class test_CaptureVerification:
  def __init__(self, test_read_config_file: object) -> None:
    """init the class"""

    LOGGER.debug('CaptureVerification:: init start')
    self.yesterdaydate = (date.today() - timedelta(1)).isoformat() # yesterday's date for daily report
    self.todaydate = date.today().isoformat()

    self.collect_yesterday = test_read_config_file['latest_24hrs']['enable']

    self.Payload_start_time = "2023-12-18T00:00:00-00:00"   # "start_time": "2023-12-08T00:00:00-00:00",
    self.Payload_end_time = self.todaydate + 'T00:00:00-00:00'
    self.preppedReq = ''
    self.CaptVerif_send_url = ''

    if self.collect_yesterday:
      self.Payload_start_time = self.yesterdaydate + 'T00:00:00-00:00' # if 24hr yesterday data collection

    self.issue_filter = {}
    self.page_size = 2000
    self.org_id = 708000501

    self.title = 'CaptureVerification'
    self.author = 'VW'
    self.URL = test_read_config_file['urls']['url_wfo']
    self.URL_api = test_read_config_file['urls']['url_wfo_captVerifapi']

    self.s = 'null'  # session request

    self.CaptVerifDaily_df = pd.DataFrame()  # hold return data, zero it initially
    self.CaptVerifDaily_noCDRnotFound = pd.DataFrame() # Capt Verif results df but with no 'Record in error, no CDR found' errors filter out, CCaaS CDR not supported
    self.response_dict = 'null'
    self.token = 'null'
    self.payload = {}
    self.headers = {}
    self.session = 'null'
    self.retry = 'null'
    self.adapter = 'null'
    self.csv_file = list()    # tracks csv file status
    self.folderPath = './output/CaptVerif/'   # location where csv saved
    self.zipPath = '.\output\CaptVerif' + '\CaptVerifCSV_session' + '.zip'
    self.s = 'null'   # session tracker
    self.session = 'null'
    self.adapter = 'null'   # session adapter
    self.zipExtractFolder = '.\output\CaptVerif'
    self.csv_path = r'.\output\CaptVerif\*.csv'
    self.csv_headers = 'null'
    self.test_result = False    # tracks if capt verif call rec issues returned, overall test result


    LOGGER.debug('CaptureVerification:: init finished')
    return


  def test_getCaptVerifCSV_buildReq(self, test_read_config_file, getVerintToken):
    """retrieves daily capt verif csv, packs to df"""

    for fileName in listdir(self.folderPath):
      # Check file extension
      if fileName.endswith('.zip') or fileName.endswith('.csv'):
        # Remove File
        os.remove(self.folderPath + fileName)

    # create an Empty DataFrame object, holds capt verif results
    ##df = pd.DataFrame()

    LOGGER.info('test_getCaptVerifCSV_buildreq():: started')

    self.token = getVerintToken
    assert self.token, 'test_getCaptVerifCSV_buildreq():: token not retrieved'

    LOGGER.debug('test_getCaptVerifCSV_buildreq:: token retrieved')
    self.payload = json.dumps({
      "org_id": self.org_id,
      "start_time": self.Payload_start_time,
      "end_time": self.Payload_end_time,
      #"start_time": self.yesterdaydate + 'T00:00:00-00:00',
      #"end_time": self.todaydate + 'T00:00:00-00:00',    # "end_time": "2023-12-06T05:00:00-04:00"
      "page_size": self.page_size,
      "issue_filter": self.issue_filter
    })
    self.headers = {
      'Verint-Session-ID': '42334',
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Impact360AuthToken': self.token
    }

    # create a sessions object
    self.session = requests.Session()
    assert self.session,'test_getCaptVerifCSV_buildreq:: error session not created'
    # Set the Content-Type header to application/json for all requests in the session
    # session.headers.update({'Content-Type': 'application/json'})
    retry = urllib3.Retry(connect=25, backoff_factor=0.5)

    self.adapter = requests.adapters.HTTPAdapter(max_retries=retry)
    self.session.mount('https://', self.adapter)
    self.session.mount('http://', self.adapter)
    # Set the Content-Type header to application/json for all requests in the session
    self.session.headers.update(self.headers)

    self.CaptVerif_send_url = 'https://' + self.URL+self.URL_api
    req = requests.Request('POST', url=self.CaptVerif_send_url, headers=self.session.headers, data=self.payload)
    self.preppedReq = req.prepare()
    #self.preppedReq.body = self.payload

    LOGGER.debug('test_getCaptVerifCSV_buildreq():: finished')
    return self.session, self.preppedReq

  def test_getCaptVerifCSV_sendReq(self, session, preppedReq) -> object:
    """ send the request and create df from response """

    LOGGER.info(f'test_getCaptVerifCSV_sendReq:: request start')
    self.session = session          # session built previously
    self.preppedReq = preppedReq    # prepped request

    try:
      self.s = self.session.send(preppedReq, timeout=25, verify=False)  # send request
      # self.s=self.session.post('https://'+self.URL+self.URL_api, data=self.payload, timeout=25, verify=False)

    except requests.exceptions.HTTPError as errh:
      print("Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
      print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
      print("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
      print("OOps: Something Else", err)

    else:
      assert self.s.status_code==200, 'test_getCaptVerifCSV_sendReq():: session request response not 200 OK'
    # access session cookies
    #print(f'session cookies: {s.cookies}')
      LOGGER.info(f'test_getCaptVerifCSV_sendReq:: request start {self.Payload_start_time}')
      LOGGER.info(f'test_getCaptVerifCSV_sendReq:: request start {self.Payload_end_time}')

      LOGGER.info(f'test_getCaptVerifCSV_sendReq:: AWE Capt Verif csv request response received {self.s.status_code}, now attempt write Capt Verif zip archive to {self.zipPath}')

      try:
        with open(self.zipPath, 'wb') as zipFile:
            zipFile.write(self.s.content)
            LOGGER.debug('test_getCaptVerifCSV_sendReq:: capt verif req response zip file write file OK')
      except:
        LOGGER.exception('test_getCaptVerifCSV_sendReq:: AWE Capt Verif zip archive cannot be opened')
      else:
        LOGGER.info('test_getCaptVerifCSV_sendReq:: AWE Capt Verif zip retrieved OK')

      # need to unzip Capt Verif csv and import to DF
      # extract the file
      try:
        shutil.unpack_archive(self.zipPath, self.zipExtractFolder)
      except:
        LOGGER.exception('test_getCaptVerifCSV_sendReq:: AWE Capt Verif unzip exception')
      else:
        LOGGER.debug('test_getCaptVerifCSV_sendReq:: AWE capt verif zip archive unzip success')
      # determine the zip file name
      #path = r'.\output\CaptVerif\*.csv'

      self.csv_file = glob.glob(self.csv_path)
      LOGGER.debug(f'test_getCaptVerifCSV_sendReq:: AWE Capt Verif confirm csv available after unzip')

      check.not_equal(self.csv_file, [], 'test_getCaptVerifCSV:: error csv file not found after unzip')

      # read the csv into a df
      LOGGER.info(f'test_getCaptVerifCSV_sendReq:: AWE Capt Verif unzipped csv now available at {self.csv_file[0]}, now try to open csv and read into df')
      # read csv headers
      try:
        f = open(self.csv_file[0], 'r')
      except:
        LOGGER.exception('test_getCaptVerifCSV_sendReq:: unzip capt verif zip file failed')
      else:
        reader = csv.reader(f)
        LOGGER.debug('test_getCaptVerifCSV_sendReq:: AWE Capt Verif results csv read OK')
        self.csv_headers = next(reader, None)
        self.CaptVerifDaily_df = pd.read_csv(self.csv_file[0], header=0, names=self.csv_headers)
        # delete rows if error 'Recorded in error, CDR not found' reported in row as TRUE, AWE does not support CCaaS CDR
        self.CaptVerifDaily_noCDRnotFound = self.CaptVerifDaily_df[self.CaptVerifDaily_df['Recorded in error, CDR not found'] != True]

        LOGGER.info(f'test_getCaptVerifCSV_sendReq:: AWE Capt Verif capt verif csv, calls found with issues: {len(self.CaptVerifDaily_noCDRnotFound)} ')

        # dump csv with 'no CDR found' errors removed
        # determine filename of current csv

        regex = (r'CaptureVerificationIssues-(.*)csv')
        match = re.findall(regex, f.name)
        new_file_path_noCDR = self.zipExtractFolder + str(match) + 'csv'
        try:
          self.CaptVerifDaily_noCDRnotFound.to_csv(new_file_path_noCDR, index=False, header=self.csv_headers)
        except:
          LOGGER.exception('test_getSearchAndReplay::  AWE S&R csv creation error')
        else:
          LOGGER.info('test_getSearchAndReplay::  AWE S&R csv written ok')


        if len(self.CaptVerifDaily_noCDRnotFound) == 0:
          self.test_result = True

        # check non zero df

        check.equal(len(self.CaptVerifDaily_noCDRnotFound), 0, ' !!!!! test_getCaptVerifCSV:: AEE Capt Verif df non zero size after csv read, call rec issues indicated !!!!!')
        # check if data

        LOGGER.info(f'***** test_getCaptVerifCSV_sendReq():: AWE Capt Verif API test routines finished')

      return self.CaptVerifDaily_noCDRnotFound, self.test_result, self.session

