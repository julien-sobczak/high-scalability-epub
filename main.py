#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
$ python main.py --start 2014-10-08 --end 2016-01-01
"""

import pypub
import re, unicodedata
import requests
from bs4 import BeautifulSoup
import time
import os
import argparse
import collections
import random

import sys
reload(sys)
sys.setdefaultencoding('utf8')

import socket
socket.setdefaulttimeout(5)  # Some image download are blocking

def sleep_for_a_while():
    # Required to avoid 429: Too Many Requests
    time.sleep(20 + random.randint(1, 15))


def generate_epub(name, category="", start=None, end=None):
    """
    Main method.
    """

    # Collect post to sort them after
    posts = {}

    for page in range(1, 4):

        sleep_for_a_while()
        r = requests.get('http://highscalability.com/blog/category/%s?currentPage=%s' % (category, page))
        html_doc = r.text

        soup = BeautifulSoup(html_doc, 'html.parser')
        for post in soup.select(".journal-entry"):
            #print(post)

            post_link = post.select(".journal-entry-text h2 a")[0]
            post_date = post.select(".journal-entry-float-date")[0]

            # Collect the HREF
            # Note: the link is useless because the list page contains the full post text.
            href = post_link.attrs['href']
            if not href.startswith("http://highscalability.com"):
                href = "http://highscalability.com%s" % href

            # Collect the title
            title = post_link.get_text()

            if not title:
                print("Fail to find the title: %s" % post)

            # Collect and parse the data
            date_text = post_date.get_text()  # Ex: December 16, 2016
            conv = time.strptime(date_text, "%b%d%Y")
            date_en = time.strftime("%Y-%m-%d", conv) # Ex: 2016-12-16
            print(date_en)

            # Filter according the dates
            if start and date_en < start:
                continue
            if end and date_en >= end:
                continue

            print("Processing post %s (%s)" % (title, date_en))

            # Collect the content
            # List pages contain only the beginning of the posts.
            # We need to retrieve each post page to get the full text
            sleep_for_a_while()
            r = requests.get(href)
            if r.status_code != 200:
                print("Error: Unable to retrieve blog post content: %s" % r.status_code)
                break

            post_doc = r.text
            post_soup = BeautifulSoup(post_doc, 'html.parser')
            content = post_soup.select(".journal-entry-text")[0]

            content_text = u"%s" % (str(content))

            # Post are traversed in reverse order
            posts[date_en] = {
                "date": date_text,
                "title": title,
                "content": content_text
            }


    # Sort the post starting from the oldest
    ordered_posts = collections.OrderedDict(sorted(posts.items()))

    # Generate the target file
    epub = pypub.Epub(name)
    print("Creating the epub...")
    for date_en, post in ordered_posts.iteritems():
        print("Adding post %s" % post["title"])
        c = pypub.create_chapter_from_string(post["content"], title=post["title"])
        epub.add_chapter(c)
        sleep_for_a_while()
    print("Ending epub generation")
    epub.create_epub(os.getcwd())


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Convert High Scalability Blog to Epub.')
    parser.add_argument('--start', dest='start', default=None,
                        help='filter posts published after the start date')
    parser.add_argument('--end', dest='end', default=None,
                        help='filter posts published before the end date')
    parser.add_argument('--category', dest='category', default="example",
                        help='Filter posts on a given category')
    parser.add_argument('--filename', dest='filename', default="HighScalability",
                        help='name of the output file without the extension')
    args = parser.parse_args()

    generate_epub(args.filename, category=args.category, start=args.start, end=args.end)
