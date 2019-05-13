#!/usr/bin/env python3
# vim: ft=python ts=4 sw=4 et
# -*- encoding: utf-8 -*-

import os
import re
import sys
import requests
import base64

# Retrieve from the environment variables usefull infos
# after Drone as cloned the project

REPO = os.environ['DRONE_REPO_NAME']
PR = os.environ['DRONE_PULL_REQUEST']
GH_TOKEN = os.environ['GITHUB_TOKEN']
GH_HEADERS = {'Authorization': 'Bearer {}'.format(GH_TOKEN)}

GH_URL_PULL = 'https://api.github.com/repos/coopengo/{repo}/pulls/{pr}'
GH_URL_ISSUE = 'https://api.github.com/repos/coopengo/{repo}/issues/{pr}'

# Initialize information for Redmine
RM_URL = 'https://support.coopengo.com/issues/{issue}.json'
RM_TOKEN = os.environ['REDMINE_TOKEN']
RM_HEADERS = {'X-Redmine-API-Key': RM_TOKEN}

# compile regular expression for title, body, changelog
title_regexp = re.compile(r'\w+: .+')
body_regexp = re.compile(r'.*(fix|ref) #(\d+)', re.M | re.I | re.S)
changelog_regexp = re.compile(r'\* (BUG|FEA|OTH)#(\d+)')

# pattern if bug
# grp1 = title_en, grp3 = title_fr,
# grp5 = Scenario de reproduction,
# grp7 = correction,
# grp9 = parametrages_fr,
# grp11 = scripts_fr,
# grp13 = business modules,
# grp15 = original description

bugStr = (r"## \[title_en\]((.|\n)*)"
          r"## \[title_fr\]((.|\n)*)"
          r"### \[repro_fr\]((.|\n)*)"
          r"### \[correction_fr\]((.|\n)*)"
          r"\[parametrage_fr\]((.|\n)*)"
          r"### \[scripts_fr\]((.|\n)*)"
          r"## \[business_modules\]((.|\n)*)"
          r"## \[original_description\]((.|\n)*$)")

# pattern if feature
# grp1 = title_en, grp3 = title_fr, grp5 = parametrages_fr,
# grp7 = scripts_fr, grp9 = business modules, grp11 = original description
featureStr = (r"## \[title_en\]((.|\n)*)"
              r"## \[title_fr\]((.|\n)*)"
              r"### \[parametrage_fr\]((.|\n)*)"
              r"### \[scripts_fr\]((.|\n)*)"
              r"## \[business_modules\]((.|\n)*)"
              r"## \[original_description\]((.|\n)*$)")

bug_regexp = re.compile(bugStr)
feature_regexp = re.compile(featureStr)

minimum_regexp = re.compile(r'[\s\S]{15,}')

# dict containing tracker name values
rm_trackers = {1: 'bug', 2: 'fea'}
issues_projects = [1, 31, 37]

# initialize variables
gh_pull = None
#
gh_issue = None
# list of labels for the specific pull request
gh_labels = None
# list of modified files in the repository
ghIssueFiles = None
# equals to the identifier defined in the body of the pull request
rm_issue = None

# feature or bug => defined depending on the label on the gh pull request
rm_issue_type = None


# function to retrieve request and parse to JSON
# in one time
def requestInJson(url, headers):
    r = requests.get(url, headers=headers)

    if r.status_code < 200 or r.status_code > 300:
        print(('error   :gh:{}:{}:{}'.format(url, r.status_code, r.text)))
        sys.exit(1)

    return r.json()

# set the GitHub pull JSON object


def set_gh_pull():
    global gh_pull
    url = GH_URL_PULL.format(repo=REPO, pr=PR)
    gh_pull = requestInJson(url, headers=GH_HEADERS)

# get issue from github repo


def set_gh_issue():
    global gh_issue
    url = GH_URL_ISSUE.format(repo=REPO, pr=PR)
    gh_issue = requestInJson(url, headers=GH_HEADERS)

# name of issues stored in an array


def set_gh_labels():
    global gh_labels
    gh_labels = [l['name'] for l in gh_issue['labels']]

# informations about files changed in the pull request
# create a dict of modified files
# key    : filename
# Value  : URL to the content of the file
# Moreover, this function return the object from github


def get_gh_files():

    global ghIssueFiles
    ghIssueFiles = dict()
    url = (GH_URL_PULL + '/files').format(repo=REPO, pr=PR)
    isHere = False

    gh_files = requestInJson(url, headers=GH_HEADERS)
    for f in gh_files:
        if str(rm_issue) + ".md" in f['filename']:
            print(f['filename'] + " added to the queue...")
            ghIssueFiles[f['filename']] = f['contents_url']
            isHere = True

    if isHere:
        return gh_files

    else:
        print("content :ko:{}.md".format(rm_issue))
        sys.exit(1)


def check_labels():

    global rm_issue_type
    if 'enhancement' in gh_labels:
        rm_issue_type = 'fea'
    elif 'bug' in gh_labels:
        rm_issue_type = 'bug'
    print('labels  :ok')
    return True


def check_title():
    ok = True
    if 'bypass title check' in gh_labels:
        print('title   :bypass')
    else:
        if title_regexp.match(gh_pull['title']):
            print('title   :ok')
        else:
            ok = False
            print('title   :ko')
    return ok


def check_body():
    ok = True
    m = body_regexp.match(gh_pull['body'])

    # it maatch
    if m:
        # retrieve ticket number (issue number)
        issue = int(m.group(2))
        # what i don't understand is here, rm_issue is ==None everytime ?
        global rm_issue
        # if both are defined but doesn't match
        if issue and rm_issue and issue != rm_issue:
            ok = False
            print(('body    :ko:issue:{}-{}'.format(issue, rm_issue)))
        else:
            # set rm_issue
            print(('body    :ok:issue:{}'.format(issue)))
            rm_issue = issue

    # if it doesn't match
    else:
        ok = False
        print('body    :ko')
    return ok


def check_content_mdfiles():
    ok = True
    get_gh_files()

    for name, content in ghIssueFiles.items():
        if str(rm_issue) in name:
            r = requestInJson(content, headers=GH_HEADERS)
            fileContent = base64.b64decode(r['content'])

    if real_issue_type == 'fea':
        m = feature_regexp.match(fileContent.decode('utf8'))

        # if the file match the pattern, tags are respected
        if m:

            print('content :ok:fea')
            title_en = m.group(1).replace("(required)", "")
            title_fr = m.group(3).replace("(required)", "")
            # parametrage_fr = m.group(5).replace(
            #     "<Paramétrage (éventuel) à faire>", "")
            # scripts_fr = m.group(7).replace("<Scripts à passer>", "")
            business_modules = m.group(9)
            original_description = m.group(11).replace(
                "(required / automatic)", "")

            if not minimum_regexp.match(title_en):
                ok = False
                print('content :ko:title not specified')
            else:
                print('content :ok:title_en')

            if not minimum_regexp.match(title_fr):
                ok = False
                print('content :ko:title not specified')
            else:
                print('content :ok:title_fr')
            if not minimum_regexp.match(business_modules):
                ok = False
                print('content :ko:business_modules not specified')
            else:
                print('content :ok:business_modules')
            if not minimum_regexp.match(original_description):
                ok = False
                print('content :ko:original_description')
            else:
                print('content :ok:original_description')

        else:
            print('content :ko:tags not respected')
            ok = False

    elif real_issue_type == 'bug':
        m = bug_regexp.match(fileContent.decode('utf8'))

        # if the file match the pattern, tags are respected
        if m:
            print('content :ok:bug')
            title_en = m.group(1).replace("(required)", "")
            title_fr = m.group(3).replace("(required)", "")
            # parametrage_fr = m.group(9).replace(
            #     "<Paramétrage (éventuel) à faire>", "")
            # scripts_fr = m.group(11).replace("<Scripts à passer>", "")
            business_modules = m.group(13)
            original_description = m.group(15).replace(
                "(required / automatic)", "")

            if not minimum_regexp.match(title_en):
                ok = False
                print('content :ko:title not specified')
            else:
                print('content :ok:title_en')

            if not minimum_regexp.match(title_fr):
                ok = False
                print('content :ko:title not specified')
            else:
                print('content :ok:title_fr')
            if not minimum_regexp.match(business_modules):
                ok = False
                print('content :ko:business_modules not specified')
            else:
                print('content :ok:business_modules')
            if not minimum_regexp.match(original_description):
                ok = False
                print('content :ko:original_description')
            else:
                print('content :ok:original_description')

        else:
            print('content :ko:tags not respected')
            ok = False

    if ok:
        print('content :ok')
    else:
        print('content :ko')
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
                print(('content:ko:changelog:{}:issue_type:{}{}'.format(
                    label, rm_issue_type, issue_type)))
            else:
                rm_issue_type = issue_type
                print(('content:ok:changelog:{}:issue_type:{}'.format(
                    label, issue_type)))
            issue = int(m.group(2))
            global rm_issue
            if rm_issue and rm_issue != issue:
                ok = False
                print(('content:ko:changelog:{}:issue:{}-{}'.format(
                    label, issue, rm_issue)))
            else:
                rm_issue = issue
                print(('content:ok:changelog:{}:issue:{}'.format(
                    label, issue)))
        else:
            print(('content:ok:changelog:{}:issue_type:{}'.format(
                label, issue_type)))
    else:
        ok = False
        print(('content:ko:changelog:{}:{}'.format(label, line)))
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
                    print(('content:ko:changelog:{}'.format(
                        changelog['filename'])))
        else:
            ok = False
            print('content:ko:changelog')
    return ok


def check_redmine():
    ok = True
    global rm_issue, rm_issue_type, real_issue_type

    # if rm issue is defined
    if rm_issue:
        # connect to redmine
        url = RM_URL.format(issue=rm_issue)
        issue = requestInJson(url, headers=RM_HEADERS)['issue']

        print(('redmine:ko:issue:{}'.format(issue['id'])))

        # if issue type is defined (issue type == feature or bug)
        if rm_issue_type:
            # ensure the issue type is the same on redmine
            issue_type = rm_trackers[issue['tracker']['id']]
            real_issue_type = issue_type

            #
            if issue_type == rm_issue_type:
                print(('redmine :ok:issue_type:{}'.format(issue_type)))
            else:
                ok = False
                print(('redmine :ko:issue_type:{}-{}'.format(
                    issue_type, rm_issue_type)))

            issue_project = issue['project']['id']
            if issue_project in issues_projects:
                print(('redmine :ok:issue_project:{}'.format(
                    issue['project']['name'])))
            else:
                ok = False
                print(('redmine :ko:issue_project:{}'.format(
                    issue['project']['name'])))

        # if issue type is not defined
        else:
            ok = False
            print('redmine :ko:issue_type:empty')

    # if redmine issue is not defined
    elif rm_issue is None:
        # No problem if issue is #0000
        ok = False
        print('redmine :ko:issue:empty')

    return ok


def main():

    # set usefull data
    set_gh_pull()
    set_gh_issue()
    set_gh_labels()

    # checking args send by user
    # if user send more than 2 values,
    if len(sys.argv) >= 2 and sys.argv[1] == 'tests':
        # if tests checks needs to be bypassed
        if 'bypass tests check' in gh_labels:
            # no need to check exit without error
            print('tests:bypass')
            sys.exit(0)
        else:
            # exit with error
            sys.exit(1)

    # Special manner to check if every check is complete
    ok = True
    ok = check_labels() and ok
    ok = check_title() and ok
    ok = check_body() and ok
    ok = check_redmine() and ok
    ok = check_content_mdfiles() and ok
    ok = check_content() and ok

    if not ok:
        if 'bypass meta check' in gh_labels:
            print('meta:bypass')
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
