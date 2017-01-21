#!/usr/bin/env python3
#
# Clone all of a user's public & private GitHub repositories.
#

import sys
import argparse
import requests
import json
import subprocess
import os
import time

PROTOCOL = "https://"
GH_API_ROOT = PROTOCOL + "api.github.com"

FILENAME = sys.argv[0]

"""Argparse override to print usage to stderr on argument error."""
class ArgumentParserUsage(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write("error: %s\n" % message)
        self.print_help(sys.stderr)
        sys.exit(2)

"""Print usage and exit depending on given exit code."""
def usage(exit_code):
    if exit_code == 0:
        pipe = sys.stdout
    else:
        # if argument was non-zero, print to STDERR instead
        pipe = sys.stderr

    parser.print_help(pipe)
    sys.exit(exit_code)

"""Log a message to a specific pipe (defaulting to stdout)."""
def log_message(message, pipe=sys.stdout):
    print("[{}] {}: {}".format(
        time.strftime("%F %T"), FILENAME, message), file=pipe)

"""If verbose, log an event."""
def log(message):
    if not args.verbose:
        return
    log_message(message)

"""Log an error. If given a 2nd argument, exit using that error code."""
def error(message, exit_code=None):
    log_message("error: " + message, sys.stderr)
    if exit_code:
        sys.exit(exit_code)

"""Try to update (pull/clone) a repo."""
def update_repo(repo_name, dl_url, outdir):
    repo_dir = os.path.join(outdir, repo_name)
    if os.path.isdir(repo_dir):
        # folder exists: assume it's already been cloned & we just have to pull
        log("repo: update/fetch: {}".format(repo_name))
        subprocess.call(["git", "pull"], cwd=repo_dir)
    else:
        # no repo, do a git clone
        log("repo: new/clone: {}".format(repo_name))
        subprocess.call(["git", "clone", dl_url, repo_dir])

parser = ArgumentParserUsage(description="Description of the program's function (identical if you'd like).")

# add arguments
parser.add_argument("-u", "--user",
        help="get specified user's repos instead of the OAuth user's ones")
parser.add_argument("-v", "--verbose", help="be verbose",
        action="store_true")
parser.add_argument("-o", "--output-directory",
        help="directory to store repos in")
parser.add_argument("token", help="OAuth token for user")

# parse arguments
args = parser.parse_args()

if args.output_directory:
    outdir = args.output_directory
else:
    outdir = "."



auth_header = { "Authorization": "token {}".format(args.token) }

if args.user:
    # TODO: unneat
    next_repos_user_selection = "{}/{}/{}".format("users", args.user, "repos")
else:
    next_repos_user_selection = "{}/{}".format("user", "repos")

# retrieve names/URLs of all repos
repos = []
more_pages = True
next_repos_url = "{}/{}".format(GH_API_ROOT, next_repos_user_selection)
page_num = 1
while more_pages:
    log("downloading page number {}...".format(page_num))
    req = requests.get(next_repos_url, headers=auth_header)

    # make sure we were able to get the page fine
    if not req.ok:
        error("GitHub API request failed", 1)

    log("continuing...")
    req_json = json.loads(req.text)
    repos.extend(req_json)
    log("continuing #2...")
    if "next" in req.links:
        next_repos_url = req.links["next"]["url"]
        page_num += 1
    else:
        more_pages = False

for repo in repos:
    update_repo(repo["full_name"], repo["clone_url"].replace(
            PROTOCOL, PROTOCOL + args.token + "@"), outdir)
