#!/usr/bin/env python2
# vim: ft=python ts=4 sw=4 et

import os
import re
import sys
import requests

REPO = os.environ['DRONE_REPO_NAME']
PR = os.environ['DRONE_PULL_REQUEST']
GH_TOKEN = os.environ['GITHUB_TOKEN']
RM_TOKEN = os.environ['REDMINE_TOKEN']

GH_URL_PULL = 'https://api.github.com/repos/coopengo/{repo}/pulls/{pr}'
GH_URL_ISSUE = 'https://api.github.com/repos/coopengo/{repo}/issues/{pr}'
GH_HEADERS = {'Authorization': 'Bearer {}'.format(GH_TOKEN)}

RM_URL = 'https://support.coopengo.com/issues/{issue}.json'
RM_HEADERS = {'X-Redmine-API-Key': RM_TOKEN}

title_regexp = re.compile('\w+: .+')
body_regexp = re.compile('.*(fix|ref) #(\d+)', re.M | re.I | re.S)
changelog_regexp = re.compile('\* (BUG|FEA|OTH)#(\d+)')

rm_trackers = {1: 'bug', 2: 'fea'}
issues_projects = [1, 31]

gh_pull = None
gh_issue = None
gh_labels = None
rm_issue = None
rm_issue_type = None


def set_gh_pull():
    url = GH_URL_PULL.format(repo=REPO, pr=PR)
    r = requests.get(url, headers=GH_HEADERS)
    if r.status_code < 200 or r.status_code > 300:
        print('error:gh:{}:{}:{}'.format(url, r.status_code, r.text))
        sys.exit(1)
    global gh_pull
    gh_pull = r.json()


def set_gh_issue():
    url = GH_URL_ISSUE.format(repo=REPO, pr=PR)
    r = requests.get(url, headers=GH_HEADERS)
    if r.status_code < 200 or r.status_code > 300:
        print('error:gh:{}:{}:{}'.format(url, r.status_code, r.text))
        sys.exit(1)
    global gh_issue
    gh_issue = r.json()


def set_gh_labels():
    global gh_labels
    gh_labels = [l['name'] for l in gh_issue['labels']]


def get_gh_files():
    url = (GH_URL_PULL + '/files').format(repo=REPO, pr=PR)
    r = requests.get(url, headers=GH_HEADERS)
    if r.status_code < 200 or r.status_code > 300:
        print('error:gh:{}:{}:{}'.format(url, r.status_code, r.text))
        sys.exit(1)
    return r.json()


def check_labels():
    global rm_issue_type
    if 'enhancement' in gh_labels:
        rm_issue_type = 'fea'
    elif 'bug' in gh_labels:
        rm_issue_type = 'bug'
    print('labels:ok')
    return True


def check_title():
    ok = True
    if 'bypass title check' in gh_labels:
        print('title:bypass')
    else:
        if title_regexp.match(gh_pull['title']):
            print('title:ok')
        else:
            ok = False
            print('title:ko')
    return ok


def check_body():
    ok = True
    m = body_regexp.match(gh_pull['body'])
    if m:
        issue = int(m.group(2))
        global rm_issue
        if rm_issue and issue != rm_issue:
            ok = False
            print('body:ko:issue:{}-{}'.format(issue, rm_issue))
        else:
            print('body:ok:issue:{}'.format(issue))
            rm_issue = issue
    else:
        ok = False
        print('body:ko')
    return ok


def _check_content_changelog_line(label, line):
    ok = True
    m = changelog_regexp.match(line)
    if m:
        issue_type = m.group(1).lower()
        if issue_type != 'oth':
            global rm_issue_type
            if rm_issue_type and rm_issue_type != issue_type:
                ok = False
                print('content:ko:changelog:{}:issue_type:{}{}'.format(
                    label, rm_issue_type, issue_type))
            else:
                rm_issue_type = issue_type
                print('content:ok:changelog:{}:issue_type:{}'.format(
                    label, issue_type))
            issue = int(m.group(2))
            global rm_issue
            if rm_issue and rm_issue != issue:
                ok = False
                print('content:ko:changelog:{}:issue:{}-{}'.format(
                    label, issue, rm_issue))
            else:
                rm_issue = issue
                print('content:ok:changelog:{}:issue:{}'.format(label, issue))
        else:
            print('content:ko:changelog:{}:issue_type:{}'.format(
                    label, issue_type))
    else:
        ok = False
        print('content:ko:changelog:{}:{}'.format(label, line))
    return ok


def check_content():
    ok = True
    if 'bypass content check' in gh_labels:
        print('content:bypass')
    else:
        changelogs = []
        for f in get_gh_files():
            if 'CHANGELOG' in f['filename']:
                changelogs.append(f)
        if changelogs:
            for changelog in changelogs:
                label = changelog['filename'].split('/')[-2]
                patch = changelog['patch']
                lines = [
                    line[1:].strip()
                    for line in patch.splitlines()
                    if line.startswith('+')]
                if lines:
                    if not _check_content_changelog_line(label, lines[0]):
                        ok = False
                else:
                    ok = False
                    print('content:ko:changelog:{}'.format(
                        changelog['filename']))
        else:
            ok = False
            print('content:ko:changelog')
    return ok


def check_redmine():
    ok = True
    global rm_issue, rm_issue_type
    if rm_issue:
        url = RM_URL.format(issue=rm_issue)
        r = requests.get(url, headers=RM_HEADERS)
        if r.status_code < 200 or r.status_code > 300:
            print('error:rm:{}:{}:{}'.format(url, r.status_code, r.text))
            sys.exit(1)
        issue = r.json()['issue']
        print('redmine:ok:issue:{}'.format(issue['id']))
        if rm_issue_type:
            issue_type = rm_trackers[issue['tracker']['id']]
            if issue_type == rm_issue_type:
                print('redmine:ok:issue_type:{}'.format(issue_type))
            else:
                ok = False
                print('redmine:ko:issue_type:{}-{}'.format(
                    issue_type, rm_issue_type))
            issue_project = issue['project']['id']
            if issue_project in issues_projects:
                print('redmine:ok:issue_project:{}'.format(
                    issue['project']['name']))
            else:
                ok = False
                print('redmine:ko:issue_project:{}'.format(
                    issue['project']['name']))
        else:
            ok = False
            print('redmine:ko:issue_type:empty')
    else:
        ok = False
        print('redmine:ko:issue:empty')
    return ok


def main():
    set_gh_pull()
    set_gh_issue()
    set_gh_labels()
    if len(sys.argv) >= 2 and sys.argv[1] == 'tests':
        if 'bypass tests check' in gh_labels:
            print('tests:bypass')
            sys.exit(0)
        else:
            sys.exit(1)
    ok = True
    ok = check_labels() and ok
    ok = check_title() and ok
    ok = check_body() and ok
    ok = check_content() and ok
    ok = check_redmine() and ok
    if not ok:
        if 'bypass meta check' in gh_labels:
            print('meta:bypass')
        else:
            sys.exit(1)


if __name__ == '__main__':
    main()
