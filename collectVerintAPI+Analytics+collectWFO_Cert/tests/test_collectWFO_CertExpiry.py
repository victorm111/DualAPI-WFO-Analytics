
from cryptography import x509
import socket
import ssl
import sys
import datetime
import logging
from pprint import pprint
import pytest_check as check
import pandas as pd

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

def test_collectCertExpiry(test_read_config_file) -> any:


    hostname = test_read_config_file['urls']['host_certCheck']
    new_row = {}



    #test_results.number_of_tests += 1  # increment number of tests


    # create default context
    context = ssl.create_default_context()

    # override context so that it can get expired cert
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    ip1 = socket.getaddrinfo(hostname, 80, proto=socket.IPPROTO_TCP)
    ip2 = socket.getaddrinfo(hostname, 443, proto=socket.IPPROTO_TCP)

    LOGGER.info('test_collectCertExpiry::  start')
    LOGGER.info(f'test_collectCertExpiry::  hostname: {hostname}')
    LOGGER.info(f'test_collectCertExpiry::  IP addresses: {ip1} {ip2}')

# SSL Socket = ssock, start connection with socket.create_connection()

    with socket.create_connection((hostname, 443)) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            #LOGGER.debug("test_collectCertExpiry :: SSL/TLS version:", ssock.version())
            # print()

            cert = ssock.getpeercert(True)

            # convert cert to PEM format
            pem_data = ssl.DER_cert_to_PEM_cert(cert)
            #print("PEM cert:", pem_data)

            # pem_data in string. convert to bytes using str.encode()
            # extract cert info from PEM format
            cert_data = x509.load_pem_x509_certificate(str.encode(pem_data))

            # show cert expiry date
            today = datetime.date.today()           # get today date
            margin = datetime.timedelta(days=14)     # determine margin
            #LOGGER.info(f"test_collectCertExpiry:: WFO Cert Expiry date: {cert_data.not_valid_after} today date: {today}")
            # check today+margin > current cert expiry
            todayAndMargin = today+margin
            cert_date = datetime.date(cert_data.not_valid_after.year, cert_data.not_valid_after.month, cert_data.not_valid_after.day)
            try:

                assert cert_date > todayAndMargin

            except AssertionError:
                LOGGER.error(
                        f' !!!!!! test_collectCertExpiry: WFO cert within 14 days expiry, expiry date: {cert_data.not_valid_after}')

            else:
                LOGGER.info(
                        f' test_collectCertExpiry: WFO cert outside 14 days expiry, expiry date: {cert_data.not_valid_after}')


            LOGGER.info('test_collectCertExpiry::  finished')

            return




