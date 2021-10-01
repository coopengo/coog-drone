#!/usr/bin/env python
# vim: ft=python ts=4 sw=4 et

import argparse
import os
import requests
import sys

REPO = os.environ['DRONE_REPO_NAME']
PR = os.environ['DRONE_PULL_REQUEST']
TOKEN = os.environ['GITHUB_TOKEN']

URL_TPL = 'https://api.github.com/repos/coopengo/{repo}/pulls/{pr}/files?per_page=100'
URL = URL_TPL.format(repo=REPO, pr=PR)
AUTH = 'Bearer {}'.format(TOKEN)


def main(args):
    files = []
    page = 1

    def read():
        r = requests.get(URL + '&page=%i' % page, headers={'Authorization': AUTH})
        if r.status_code < 200 or r.status_code > 300:
            raise Exception(r.text)
        return [f['filename'] for f in r.json()]

    while True:
        new_files = read()
        files += new_files

        # If we got exactly the max number, we have to keep going
        if len(new_files) == 100:
            page += 1
        else:
            break

    modules = []
    for f in files:
        s = f.split('/')
        if s[0] == 'modules':
            if args.skip_if_only_doc and s[2] == 'doc':
                continue
            modules.append(s[1])
    modules = set(modules)
    for m in modules:
        print(m)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip-if-only-doc', action='store_true',
            help="Skip modules where only docs were changed")
    args = parser.parse_args()
    main(args)
