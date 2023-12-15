# Standard Libraries
import os

# Brokerage website for pulling agent data
# source = [
#     'bhhs',
#     'coldwell',
#     'compass',
#     'kw',
#     'realtor'
# ]
# source = [
#     'bhhs'
# ]

source = 'realtor'

chrome_options = {
    'user_data_path': os.getenv("__CHROME_USER_DATA"),
    'profile_path': 'Profile 2'
}

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
    'realtor': [
        'Santa Clara, CA'
    ]
}

timeouts = {
    'default': 5
}