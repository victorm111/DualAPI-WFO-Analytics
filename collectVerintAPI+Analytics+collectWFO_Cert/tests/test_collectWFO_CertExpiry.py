
from cryptography import x509
import socket
import ssl
import sys
import datetime
import logging
import pytest_check as check
import pandas as pd

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

def test_collectCertExpiry(test_read_config_file, test_results) -> any:


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

    with socket.create_connection((hostname, 443)) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            LOGGER.debug("test_collectCertExpiry :: SSL/TLS version:", ssock.version())
            # print()

            # get cert in DER format
            data = ssock.getpeercert(True)
            #print("Data:", data)
            #print()

            # convert cert to PEM format
            pem_data = ssl.DER_cert_to_PEM_cert(data)
            #print("PEM cert:", pem_data)

            # pem_data in string. convert to bytes using str.encode()
            # extract cert info from PEM format
            cert_data = x509.load_pem_x509_certificate(str.encode(pem_data))

            # show cert expiry date
            today = datetime.date.today()           # get today date
            margin = datetime.timedelta(days=14)     # determine margin
            LOGGER.info(f"test_collectCertExpiry:: WFO Cert Expiry date: {cert_data.not_valid_after} 'today date: {today}")

            result = check.greater((today + margin), datetime.date(cert_data.not_valid_after.year, cert_data.not_valid_after.month, cert_data.not_valid_after.day), 'WFO cert expiry in less than 14 days')

            # create a results row
            new_row = {'TestName': 'checkWFOCertExpiry', 'Description': "Flags error if WFO Cert expiry within 14 days"}

            if result:
                new_row = {'TestName': 'checkWFOCertExpiry',
                           'Description': "Flags error if WFO Cert expiry within 14 days", 'Result': 'FAILED',
                           'Interval_ref': 'current cert: ' + str(datetime.date(cert_data.not_valid_after.year, cert_data.not_valid_after.month,
                                      cert_data.not_valid_after.day)), 'Interval_compare': '14 day margin from today: ' + str(today + margin)}

            else:


                new_row = {'TestName': 'checkWFOCertExpiry',
                           'Description': "Flags error if WFO Cert expiry within 14 days", 'Result': 'PASSED',
                           'Interval_ref': 'current cert: ' + str(datetime.date(cert_data.not_valid_after.year, cert_data.not_valid_after.month,
                                      cert_data.not_valid_after.day)), 'Interval_compare': '14 day margin from today' + str(today + margin)}

            # assert today + margin <= datetime.date(cert_data.not_valid_after.year, cert_data.not_valid_after.month, cert_data.not_valid_after.day), 'WFO cert within 14 day expiry'
            df2 = pd.DataFrame(new_row, index=[0])
            LOGGER.info('test_collectCertExpiry::  finished')

            return test_results._append(df2)



