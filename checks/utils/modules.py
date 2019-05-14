#!/usr/bin/env python
# vim: ft=python ts=4 sw=4 et

import os
import requests

REPO = os.environ['DRONE_REPO_NAME']
PR = os.environ['DRONE_PULL_REQUEST']
TOKEN = os.environ['GITHUB_TOKEN']

URL_TPL = 'https://api.github.com/repos/coopengo/{repo}/pulls/{pr}/files'
URL = URL_TPL.format(repo=REPO, pr=PR)
AUTH = 'Bearer {}'.format(TOKEN)


def main():
    r = requests.get(URL, headers={'Authorization': AUTH})
    if r.status_code < 200 or r.status_code > 300:
        raise Exception(r.text)
    files = [f['filename'] for f in r.json()]
    modules = []
    for f in files:
        s = f.split('/')
        if s[0] == 'modules':
            modules.append(s[1])
    modules = set(modules)
    for m in modules:
        print(m)



if __name__ == '__main__':
    main()
