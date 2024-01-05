# Standard Libraries
import os

# Brokerage website for pulling agent data
# source = [
#     'bhhs',
#     'coldwell',
#     'compass',
#     'kw',
#     'realtor.com'
# ]
# source = [
#     'bhhs'
# ]

source = 'realtor.com'

chrome_options = {
    'user_data_path': os.getenv("__CHROME_USER_DATA"),
    'profile_path': 'Default',
    "chrome_exe_path": os.getenv("__CHROME_V114"),
}

browsermob_proxy_path = os.getenv("__BROWSERMOB_PROXY_PATH")

locations = {
    'bhhs': [
        'Santa Clara, CA, USA'
    ],
    'coldwell': [
        'Santa Clara, CA',
    ],
    'compass': [
        'Santa Clara County, CA',
    ],
    'kw': [
        'Santa Clara, CA'
    ],
    'realtor.com': [
        'Sacramento, CA'
    ]
}

timeouts = {
    'default': 5
}