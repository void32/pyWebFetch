#! /usr/local/bin/python3
import argparse
from bs4 import BeautifulSoup
import requests
import re
import wget

#Set up the command line parser
parser = argparse.ArgumentParser(description='Follow links and download files.')
parser.add_argument("-d","--dry-run", dest="dryrun", action="store_true", help="Show what would be done, without download the files.")

# Start url: string: -u http://www... --url
parser.add_argument("-u", "--start-url", dest="startURL", help="Start url", metavar="FILE")

# login url: string: -u http://www... --url
parser.add_argument("-i", "--login-url", dest="loginURL", help="Login url", metavar="FILE")

# Links to follow
parser.add_argument("-l", "--links", dest="classForLinksToFollow", help="Class for links to follow", metavar="FILE")

# Types to fetch
parser.add_argument("-t", "--file-types", dest="fileExtensionForLinksToDownload", help="Files types to download", metavar="FILE")

# max depth: int: -n 3
parser.add_argument("-n",dest="maxDepth", default=100, type=int, help="max traversal depth")

# Payload
parser.add_argument("-p", "--payload", dest="payloadFile", help="File with loads for login ", metavar="FILE")

args=parser.parse_args()

print(args.startURL)
print(args.loginURL)

print(args.classForLinksToFollow)
print(args.fileExtensionForLinksToDownload)
print(args.maxDepth)
print(args.payloadFile)

# A user do not need to put http prefix - remove if they have
args.startURL = str(args.startURL).lstrip("http://")
args.loginURL = str(args.loginURL).lstrip("http://")


# load payload if present
payload = {}
if args.payloadFile is not None:
    print(args.payloadFile)
    payloadFile=open(args.payloadFile)
    for line in payloadFile:
        key,value=[x.strip() for x in line.split(':')]
        payload[key]=value
print(payload)

def download_file(url):
    global session
    local_filename = url.split('/')[-1]
    # NOTE the stream=True parameter
    r = session.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()
    return local_filename

def validate_url(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return regex.match(url)

def fetch(url, links, filetypes, count):
    global session
    print(url)

    if count < args.maxDepth:
        # Fetch web page
        data = session.get(url).text
        soup = BeautifulSoup(data)

        # All links on site
        all_links = [link for link in soup.find_all('a') if
                        validate_url(link.get('href')) or
                        str(link.get('href')).startswith("/") or True]

        # Files to download
        download_links = list(set([link.get('href') for link in all_links if
                                   link.get('href').endswith(args.fileExtensionForLinksToDownload)]))

        for link in download_links:
            print("Downloads "+str(link))

            # Make relative paths into absolute Paths
            if str(link).startswith("/"):
                import urllib.parse
                link = urllib.parse.urljoin(url, link)
                print("link:", link)

            # Download
            if not args.dryrun:
                download_file(str(link))
                #session.get(str(link))
                #wget.download(str(link))
                print

        # Links to follow
        follow_links = list(set([link.get('href') for link in soup.find_all('a', class_=args.classForLinksToFollow)]))
        for link in follow_links:
            fetch(link, links, filetypes, count+1)

# Use 'with' to ensure the session context is closed after use.
with requests.Session() as session:
    session.post("http://"+args.loginURL, data=payload)
    fetch("http://"+args.startURL, args.classForLinksToFollow, args.fileExtensionForLinksToDownload, 0)