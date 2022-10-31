# Global constants
TITLE = "Daily Dose of Malware"
DESC = "Malware is art. Don't let it become a filthy criminal's tool."

PATH = "malware"

# Websites
WEBSITES = {
    "Main":         "https://malwat.ch",
    "GitHub":       "https://github.com/Endermanch/MalwareDatabase",
    "MGenerator":   "https://mgen.fast-dl.cc",
    "VirusTotal":   "https://www.virustotal.com/gui/home/search",
    "ANY.RUN":      "https://any.run"
}

# Tree view
TREE_HEADER = {
    '': 85,
    'File Name': 230,
    'Type': 60,
    'Size': 60,
    'Signature': 80,
    'SHA-256': 400,
    'First Seen': 110,
    'DL': 20,
    'UP': 20,
    'Tags': 100
}

# Connect queries to satisfy request syntax
API_QUERIES = {
    'signature': 'get_siginfo',
    'tag': 'get_taginfo',
    'file_type': 'get_file_type',
    'hash': 'get_info'
}

# Approved filters
API_FILTERS = {
    'sig': 'signature',
    'sign': 'signature',
    'signature': 'signature',
    'tag': 'tag',
    'type': 'file_type',
    'ft': 'file_type',
    'filetype': 'file_type',
    'file_type': 'file_type',
    'sha256': 'hash',
    'sha-256': 'hash',
    'sha': 'hash',
    'hash': 'hash',
    'limit': 'limit'
}

# About
ABOUT_TITLE = "Malware Downloader"
ABOUT_DESC  = "The goal of this project is to create a simple, easy to use, and free download manager for malware samples. " \
              "It is not meant to be used for malicious purposes. " \
              "The creator does not take any responsibility for the misuse of this software. \n\n"

ABOUT_FACTS = [ "This project was created for a university assignment. ",
                "This project is open source and can be found on GitHub. ",
                "This project uses PyQt5 for the GUI. ",
                "Daily Dose of Malware used to be a CLI tool. ",
                "Daily Dose of Malware has become outdated in 2019, when most of the sources shut down. ",
                "This project's development started on October 11th, 2022. " ]


# Manual pages
MANUAL_PAGES = {
    "Getting started": "You can drag the help window around as you learn how to use the application. \n"
                  "It consists of multiline strings. \n"
                  "Work in progress.",

    "Using the downloader": "This is the second page of the help manual. \n"
                   "It consists of multiline strings. \n",

    "Searching for samples": "This is the third page of the help manual. \n"
                  "It consists of multiline strings. \n"
}


# API request messages (dictionary of dictionaries)
REQUEST_STRINGS = {
    # Own error API
    'illegal_query': {
        'severity': "warning",
        'title': "Wrong search query",
        'message': "The search query syntax is incorrect. Please try again."
    },

    # MalwareBazaar API
    'illegal_tag': {
        'severity': "warning",
        'title': "Warning",
        'message': "API Request Warning: Illegal tag name or tag not found.\nTags can't be empty and must be alphanumeric. Please correct your search query."
    },
    'tag_not_found': {
        'severity': "information",
        'title': "Tag not found",
        'message': "The specified tag does not exist in the database.\nPlease input a different tag.",
    },
    'no_results': {
        'severity': "information",
        'title': "No results",
        'message': "The search query did not match any malware samples.\nPlease try again with different keywords."
    },

    'illegal_signature': {
        'severity': "warning",
        'title': "Warning",
        'message': "API Request Warning: Illegal signature or signature not found.\nSignatures can't be empty and must be alphanumeric. Please correct your search query."
    },

    'illegal_hash': {
        'severity': "warning",
        'title': "Warning",
        'message': "API Request Warning: Illegal hash or hash not found.\nHashes can't be empty and must be alphanumeric. Please correct your search query."
    },
}