from urllib.parse import urlparse


SUPPORTED_PUBLISHERS = {

    "ft.com": {
        "name": "Financial Times",
        "website": "https://www.ft.com",
    },

    "bloomberg.com": {
        "name": "Bloomberg",
        "website": "https://www.bloomberg.com",
    },

    "nytimes.com": {
        "name": "The New York Times",
        "website": "https://www.nytimes.com",
    },

    "medium.com": {
        "name": "Medium",
        "website": "https://medium.com",
    },
    
    "reuters.com": {
        "name": "reuters",
        "website": "https://reuters.com",
    },

    "washingtonpost.com": {
        "name": "Washington Post",
        "website": "https://washingtonpost.com",
    },

    "economist.com": {
        "name": "The Economist",
        "website": "https://economist.com",
    },
}


def get_publisher(url: str):

    hostname = urlparse(url).hostname

    if hostname is None:
        return None

    hostname = hostname.lower()

    if hostname.startswith("www."):
        hostname = hostname[4:]

    for domain, publisher in SUPPORTED_PUBLISHERS.items():

        if hostname == domain:

            return publisher

        if hostname.endswith("." + domain):

            return publisher

    return None
