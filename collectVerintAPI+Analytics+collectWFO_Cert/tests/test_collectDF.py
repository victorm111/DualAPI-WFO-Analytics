
import logging
import pandas as pd
import re


import os
import sys
import time as time
from datetime import date
import pytest_check as check        # soft asserts
# import the classes

from . test_AnalyticsEngDetail import test_AnalyticsEngagementDetailReport
from . test_sendCaptVerifReqWithToken import test_CaptureVerification
from . test_sendSearchAndReplayReqWithToken import test_SearchReplay

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


class test_ClassCollectEngID:
    """this class collects all API responses from Verint Capt Verif, S&R and Analytics Eng Detailed report, then """
    """ compares eng call ids from Analytics Eng Detailed rpt (used as base reference) and Verint S&R """
    """ want to see that Verint S&R contains all engagement ids included in Analytics hist ED report"""
    """ same start, end times used in all API requests, Analytics need 00, 15, 30, 34 min boundary """
    """ in start and end times"""

    def __init__(self, test_read_config_file: object) -> None:

        # Init dataframes es that store retrieved datasets
        self.df_SR = pd.DataFrame()
        self.df_CaptVerificationDaily = pd.DataFrame()
        self.df_DetailEngDaily = pd.DataFrame()
        self.dfSR_EngIDS = list()

        self.dfSR_CallStarts = list()      # stores Capt Verif matched to mismatch calls
        self.dfAnalyticsED_EngIDS = list()
        #self.dfCaptVerif_EngIDS = list()
        self.df_DetailEngDaily_sorted_NotRecorded = pd.DataFrame()      # records  calls missing from AWE S&R but in Analytics ED
        self.df_sorted_Recorded_notIn_DetailEngDaily = pd.DataFrame()   # records calls missing from Analytics ED but in AWE S&R
        self.AnalyticsNumber_calls = 0           # returned from Analytics EngDetailed API
        self.SR_Number_calls = 0                 # returned from AWE S&R API
        self.df_SR_sorted = pd.DataFrame()       # sorted S&R calls
        self.df_DetailEngDaily_sorted = pd.DataFrame()
        self.df_CaptVerificationDaily = pd.DataFrame()

        self.ED_column_headers = list()     # Analytics ED column headers returned from API call
        self.SR_column_headers = list()  # Verint S&R column headers returned from API call

        self.csv_DailyMissing_output = test_read_config_file['dirs']['ED_column_headers']   # calls in ED but not in AWE S&R
        self.csv_DailyMissingED_output = test_read_config_file['dirs'][
            'SR_column_headers']  # calls in ED but not in AWE S&R
        self.captVerifResult = False        # Capt verif test result False if failed result, call rec indicates rec issues found
        self.tests_failed = 0     # number of tests failed
        self.number_of_tests = 0    # number of comparison tests incl capt verif test
        self.listTest = {"TestName":[],"Result":[], "Description":[], "Interval_ref":[], "Interval_compare":[], "ref_num_calls":[], "compared_num_calls":[], "sw_version":[]}   # table containing test results
        self.TestResults_df = pd.DataFrame()  # as per self.listTest but a pandas df
        self.ED_session = ''        # request session
        self.SR_session = ''        # store request session associated with request
        self.CaptVerif_session = ''        # store request session associated with request

        self.ED_prepped = ''        # prepped request
        self.ED_url = ''            # prepped URL

        self.CaptVerif_prepped = ''     # prepped request
        self.CaptVerif_url = ''         # prepped URL

        self.SR_prepped = ''  # prepped request
        self.SR_url = ''  # prepped URL

    def test_collect_df(self, test_read_config_file, getCCaaSToken, getVerintToken) -> any:
        """run Analytics detailed Eng , Verint Capt Verif + S&R API, collect df"""
        # create class instance
        LOGGER.debug('test_collect_df:: started')
        LOGGER.debug('test_collect_df:: init test_AnalyticsEngagementDetailReport class')
        test_DetailReport = test_AnalyticsEngagementDetailReport(test_read_config_file)
        LOGGER.debug('test_collect_df:: test_Analytics_ED_buildRequest()')
        self.ED_session, self.ED_prepped = test_DetailReport.test_Analytics_ED_buildRequest(getCCaaSToken)
        LOGGER.debug('test_collect_df:: test_Analytics_ED_sendRequest()')
        self.df_DetailEngDaily, self.AnalyticsNumber_calls, self.ED_column_headers = test_DetailReport.test_AnalyticdED_sendRequest(self.ED_session, self.ED_prepped)  # retrieves daily data

        LOGGER.debug(
            'test_collect_df:: init test_SearchReplay class')
        test_SRReport = test_SearchReplay(test_read_config_file)
        LOGGER.debug(
            'test_collect_df:: init test_SearchReplay class complete, build request')
        self.SR_session, self.SR_prepped = test_SRReport.test_getSearchAndReplay_buildReq(getVerintToken)
        LOGGER.debug(
            'test_collect_df:: init test_SearchReplay class complete, send request')
        self.df_SR = test_SRReport.test_getSearchAndReplay_sendReq(self.SR_session, self.SR_prepped)

        self.SR_Number_calls = len(self.df_SR)

        # retrieve Verint capt verif
        LOGGER.debug('test_collect_df:: init test_CaptureVerification class')
        test_CaptVerifReport = test_CaptureVerification(test_read_config_file)
        LOGGER.debug(
            'test_collect_df:: test_CaptureVerification:: test_getCaptVerifCSV_buildreq request capt verif zip/csv results')
        self.CaptVerif_session, self.CaptVerif_prepped = test_CaptVerifReport.test_getCaptVerifCSV_buildReq(test_read_config_file, getVerintToken)
        self.df_CaptVerificationDaily, self.captVerifResult, self.CaptVerif_session = test_CaptVerifReport.test_getCaptVerifCSV_sendReq(self.CaptVerif_session, self.CaptVerif_prepped)
        self.number_of_tests += 1  # increment number of tests
        check.equal(self.captVerifResult, True, 'test_getCaptVerifCSV(): AWE reported call recording issues')

        self.listTest["TestName"].append("checkAll-AWE-CaptVerif")
        self.listTest["Description"].append(
            "Checks for AWE reported call recording capture verification issues")

        self.listTest["Interval_ref"].append('starting:' + test_CaptVerifReport.Payload_start_time + ',' 'ending:' + test_CaptVerifReport.Payload_end_time)
        self.listTest["Interval_compare"].append('n/a')
        self.listTest["ref_num_calls"].append(len(test_CaptVerifReport.CaptVerifDaily_noCDRnotFound))
        self.listTest["compared_num_calls"].append('n/a')

        self.listTest["sw_version"].append('tbd')


        if not self.captVerifResult:
            self.tests_failed += 1
            # update test dictionary

            self.listTest["Result"].append("FAILED")

        else:
            # update test dictionary

            self.listTest["Result"].append("PASSED")


            LOGGER.info(
                f'test_collect_df:: test_getCaptVerifCSV() AWE Capt Verif reports issues with {len(self.df_CaptVerificationDaily)} calls')

        LOGGER.debug(
            'test_collect_df:: test_getCaptVerifCSV() capt verif zip/csv results finished')

        LOGGER.debug('test_collect_df:: finished collecting Analytics and Verint API data')

        return

    def test_compare_df(self) -> any:
        """compare engagement ids across df pulled from S+R, Analytics Daily Detailed reports, check in both directions"""

        if self.AnalyticsNumber_calls != 0:

          # sort by start times
          if len(self.df_SR):
            self.df_SR_sorted = self.df_SR.sort_values(by='local_audio_start_time', ascending=False)
          if len(self.df_DetailEngDaily):
            self.df_DetailEngDaily_sorted = self.df_DetailEngDaily.sort_values(by='dialog_start_time', ascending=False)
          if len(self.df_CaptVerificationDaily):
            self.df_CaptVerificationDaily_sorted = self.df_CaptVerificationDaily.sort_values(by='Start time', ascending=False)

          LOGGER.info(f'test_collectDF:: test_compare_df:: Analytics ED no. calls: {len(self.df_DetailEngDaily)}, Verint S&R no. calls: {len(self.df_SR)}, Verint Capture Verif no. calls {len(self.df_CaptVerificationDaily)} ')
          LOGGER.debug('test_collectDF:: test_compare_df:: start compare dataframes, collect Analytics Eng Detail engagement_ids')
          self.dfAnalyticsED_EngIDS = self.df_DetailEngDaily.engagement_id

          LOGGER.debug(f'test_collectDF:: test_compare_df:: Analytics ED eng ids are: \n {self.dfAnalyticsED_EngIDS}')
          if len(self.df_SR_sorted):
            self.dfSR_EngIDS = list(self.df_SR_sorted.cd8)
            self.dfSR_CallStarts = list(self.df_SR.local_audio_start_time)
            self.SR_column_headers = list(self.df_SR_sorted.columns)

          LOGGER.debug(f'test_collectDF:: test_compare_df:: Verint S&R returned engagement ids are: \n {self.dfSR_EngIDS}')
          LOGGER.info(f'test_collectDF:: test_compare_df:: check that all CCaaS Analytics ED Eng call IDs (as reference) match all listed call Eng IDs from AWE S&R ')
          #test = self.df_DetailEngDaily_sorted.engagement_id.array != self.df_SR_sorted.cd8.array # compare arrays
          self.df_DetailEngDaily_sorted_NotRecorded = self.df_DetailEngDaily_sorted[~self.df_DetailEngDaily_sorted['engagement_id'].isin(self.dfSR_EngIDS)]
          # pull Capt Verif calls with same call starts as mismatched calls
          # dump missed calls to csv

          try:
                self.listTest["TestName"].append("checkAllAnalyticsEngIDsInAWE-S&R")
                self.listTest["Description"].append("Checks all call eng IDs returned from CCaaS Analyticd ED detailed report are listed in AWE S&R")
                # extract interval from api request
                regex = (r'interval=(.*)&page')
                match = re.findall(regex,self.ED_prepped.path_url)

                self.listTest["Interval_ref"].append(match)
                self.listTest["Interval_compare"].append(self.SR_prepped.body)
                self.listTest["sw_version"].append('n/a')
                self.listTest["ref_num_calls"].append(len(self.df_DetailEngDaily_sorted))
                self.listTest["compared_num_calls"].append(self.SR_Number_calls)

                self.number_of_tests += 1  # increment number of tests
                assert not len(self.df_DetailEngDaily_sorted_NotRecorded), 0

                #if len(self.df_DetailEngDaily_sorted_NotRecorded) != 0:

          except AssertionError:

                self.tests_failed+=1
                # update test dictionary
                self.listTest["Result"].append("FAILED")
                LOGGER.error(
                        f'test_compare_df:: test_compare_df() !!!!!!!!  ERROR {len(self.df_DetailEngDaily_sorted_NotRecorded)} calls reported in Analytics (as reference) not in Verint S&R !!!!!!!')
                LOGGER.debug(
                        f'test_compare_df:: test_compare_df() ERROR !!!!!!!! listing call eng ids reported in Analytics not in Verint S&R : {self.df_DetailEngDaily_sorted_NotRecorded}')

                LOGGER.info(
                        f'test_compare_df:: test_compare_df() attempt dump ERROR calls not recorded but in Analytics ED to csv in dir: {self.csv_DailyMissing_output}')

                try:
                    self.df_DetailEngDaily_sorted_NotRecorded.to_csv(self.csv_DailyMissing_output, index=False,
                                                                             header=self.ED_column_headers)
                except:
                    LOGGER.exception(
                            'test_compare_df:: test_compare_df() daily csv creation error')
                else:
                    LOGGER.debug('test_compare_df::test_compare_df() call mismatch csv written ok')

          else:
                LOGGER.info('********** SUCCESS test_compare_df:: test_compare_df() NO call recording mismatch, all call eng IDs in Analytics ED rpt (as reference) are listed in AWE S&R **********')
                # update test dictionary
                self.listTest["Result"].append("PASSED")

        else:

            LOGGER.info(
                f'test_collectDF:: test_compare_df:: no calls returned from Analytics ED *********')
            LOGGER.info(
                f'test_collectDF:: test_compare_df:: ASSERTION check >> double check no calls returned from AWE S&R *********')
            # double check AWE S&R also equal to zero calls
            try:
                self.listTest["TestName"].append("checkZeroAnalyticsEngIDsAlsoInAWE-S&R")
                self.listTest["Description"].append("Checks zero call eng IDs returned from CCaaS Analyticd ED detailed report matched in AWE S&R")

                self.listTest["Interval_ref"].append(self.ED_prepped.url)
                self.listTest["Interval_compare"].append(self.SR_prepped.body)
                self.listTest["sw_version"].append('tbd')
                self.listTest["ref_num_calls"].append(len(self.df_DetailEngDaily))
                self.listTest["compared_num_calls"].append(self.SR_Number_calls)

                self.number_of_tests += 1  # increment number of tests
                assert self.SR_Number_calls == 0

            except AssertionError:
                LOGGER.error(f'test_compare_df::test_compare_df() Analytics number calls = 0 but {self.SR_Number_calls} calls returned from AWE S&R')
                LOGGER.debug(
                    f'test_compare_df::test_compare_df() dump calls not reported in Analytics (returned 0 calls) to {self.csv_DailyMissingED_output}')
                self.tests_failed += 1
                # update test dictionary
                self.listTest["Result"].append("FAILED")

                # dump the calls
                try:
                    self.df_SR_sorted.to_csv(self.csv_DailyMissingED_output, index=False,
                                                                         header=self.SR_column_headers)
                except:
                    LOGGER.exception(
                        f'test_compare_df:: test_compare_df() daily {self.csv_DailyMissingED_output} csv creation error')
                else:
                    LOGGER.error('test_compare_df::test_compare_df() call mismatch csv written ok')

            else:
                LOGGER.info(
                    f'***** SUCCESS test_compare_df::test_compare_df() Analytics number calls = 0 and calls returned from AWE S&R also = 0')
                # update test dictionary
                self.listTest["Result"].append("PASSED")

        if len(self.df_SR):
            # check if calls in AWE S&R but not in Analytics Detailed Report
            LOGGER.info('test_compare_df:: ASSERTION check if all call Eng IDs listed in AWE S&R are matched to engagement ids returned in Analytics Eng Detailed Report')

            self.df_sorted_Recorded_notIn_DetailEngDaily = self.df_SR[
                ~self.df_SR.cd8.isin(self.df_DetailEngDaily_sorted['engagement_id'])]

            try:
                # update test dictionary
                self.listTest["TestName"].append("checkAllAWE-S&RcallIDsAlsoInAnalyticsEDreport")
                self.listTest["Description"].append("Checks all call eng IDs returned from AWE S&R matched in CCaaS Analyticd ED detailed report")

                self.listTest["Interval_ref"].append(self.SR_prepped.body)
                self.listTest["Interval_compare"].append(self.ED_prepped.url)
                self.listTest["sw_version"].append('tbd')
                self.listTest["ref_num_calls"].append(self.SR_Number_calls)
                self.listTest["compared_num_calls"].append(len(self.df_DetailEngDaily_sorted))

                self.number_of_tests += 1  # increment number of tests
                assert not len(self.df_sorted_Recorded_notIn_DetailEngDaily), 0

            except AssertionError:

                self.tests_failed += 1
                # update test dictionary
                self.listTest["Result"].append("FAILED")

                LOGGER.error(
                    f'test_compare_df::  !!!! ERROR number of calls reported in Verint S&R but not in Analytics ED report: {len(self.df_sorted_Recorded_notIn_DetailEngDaily)}')
                LOGGER.debug(
                    f'test_compare_df::  !!!! list call eng ids reported in Verint S&R but not in Analytics ED report: {self.df_sorted_Recorded_notIn_DetailEngDaily}')

                LOGGER.debug(
                    f'test_compare_df:: test_compare_df() attempt dump ERROR calls in AWE S&R but not in Analytics ED report to csv in: {self.csv_DailyMissingED_output}')

                try:
                    self.df_sorted_Recorded_notIn_DetailEngDaily.to_csv(self.csv_DailyMissingED_output, index=False,
                                                             header=self.SR_column_headers)
                except:
                    LOGGER.exception(
                    f'test_compare_df:: test_compare_df() ERROR calls in AWE S&R but not in Analytics {self.csv_DailyMissingED_output} csv creation error')
                else:
                    LOGGER.debug('test_compare_df::test_compare_df() ERROR list of calls in AWE S&R but not in Analytics csv written ok')
            else:

                # update test dictionary
                self.listTest["Result"].append("PASSED")
                LOGGER.info('********** SUCCESS test_compare_df:: ALL call eng ids listed in AWE S&R (as reference) are matched to engagement ids listed in Analytics Eng Detailed Report ****** ')

        else:
            LOGGER.info(
                'test_compare_df::no calls returned from AWE S&R, need to confirm also no calls returned from Analytics')

            try:

                # update test dictionary
                self.listTest["TestName"].append("checkZeroAWECalls-MatchedInAnalyticsEDreport")
                self.listTest["Description"].append("Checks zero call eng IDs returned from AWE S&R matched in CCaaS Analyticd ED detailed report")

                self.listTest["Interval_ref"].append(self.SR_prepped.body)
                self.listTest["Interval_compare"].append(self.ED_prepped.url)
                self.listTest["sw_version"].append('tbd')
                self.listTest["ref_num_calls"].append(self.SR_Number_calls)
                self.listTest["compared_num_calls"].append(len(self.df_DetailEngDaily))

                self.number_of_tests += 1  # increment number of tests
                assert not len(self.df_DetailEngDaily), 0

            except AssertionError:

                self.tests_failed += 1
                # update test dictionary

                self.listTest["Result"].append("FAILED")

                LOGGER.error(
                    f'test_compare_df::  !!!!!!! ERROR 0 calls reported in Verint S&R but Analytics ED reported: {len(self.df_DetailEngDaily_sorted)}')

                LOGGER.debug(
                    f'test_compare_df:: test_compare_df() attempt dump calls in Analytics ED report but not in AWE S&R to csv in: {self.csv_DailyMissing_output}')

                try:

                    self.df_DetailEngDaily_sorted.to_csv(self.csv_DailyMissing_output, index=False,
                                                                        header=self.ED_column_headers)
                except:
                    LOGGER.exception(
                        f'test_compare_df:: test_compare_df() ERROR calls in AWE S&R but not in Analytics {self.csv_DailyMissing_output} csv creation error')
                else:
                    LOGGER.debug(
                        'test_compare_df::test_compare_df() ERROR list of calls in AWE S&R but not in Analytics csv written ok')
            else:
                # update test dictionary

                self.listTest["Result"].append("PASSED")

                LOGGER.info(
                    '********** SUCCESS test_compare_df:: call detail from AWE S&R (as reference) match Analytics Eng Detailed Report ****** ')

        LOGGER.info(f'test_collectDF:: test_compare_df:: all API call eng ID results comparison testing finished')
        LOGGER.info(f'test_collectDF:: test_compare_df:: Analytics reported calls: {self.AnalyticsNumber_calls}, AWE S&R calls: {self.SR_Number_calls}')
        LOGGER.info(
            f'test_collectDF:: test_compare_df:: AWE capt verif calls with issues: {len(self.df_CaptVerificationDaily)}')


        # LOGGER.info(f'******** test_collectDF:: test_compare_df:: tests status: {self.listTest} ')
        self.TestResults_df = pd.DataFrame.from_dict(self.listTest, orient='columns')
        return self.TestResults_df
