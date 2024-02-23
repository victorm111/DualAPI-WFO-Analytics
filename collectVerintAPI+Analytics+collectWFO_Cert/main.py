
import logging
import pytest
import os
from definitions import setup_env

import time as time

from datetime import date,  timedelta
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# collect code version

try:
    from version import __version__
except ModuleNotFoundError:
    exec(open("./version.py").read())

today = str(date.today())
t = time.localtime()
current_time = time.strftime("%H:%M:%S", t)

def main():
    """
    kicks off the code, populate pytest_args

    call pytest with pytest_args
    : param None
    :return None
    """

    # get the current working directory
    current_working_directory = os.getcwd()
    #args_string = "--cov=. --cov-report term --cov-report html:coverage_re"
    args_string=''
    # setup env variables
    setup_env()

# tests folder
    pytest_args = [args_string,"collectVerintAPI+Analytics+collectWFO_Cert\\tests"]
    #pytest_args = [args_string, current_working_directory + '\\tests']
    LOGGER.info(f'main() test start .... ')
    LOGGER.info(f"test code version: {__version__}")
    LOGGER.info(f'main() today date: {today}')
    LOGGER.info(f'main() current time: {current_time}')
    LOGGER.info('main.py:: starting, call pytest.main with tests folder as arg')


    # print output to the console
    print(f'current_working_directory: {current_working_directory}')
    LOGGER.info(f'main() call pytest, pytest_args: {pytest_args}')
    pytest.main(pytest_args)
    LOGGER.info(f'main() finished pytest.... ')
    return

if __name__ == "__main__":

    main()