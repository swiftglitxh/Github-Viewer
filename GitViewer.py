#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ╔══════════════════════════════════════════════════════════════╗
# ║                                                              ║
# ║    ╔═╗╦╔╦╗╦ ╦╦ ╦╔╗   ╦  ╦╦╔═╗╦ ╦╔═╗╦═╗                       ║
# ║    ║ ╦║ ║ ╠═╣║ ║╠╩╗  ╚╗╔╝║║╣ ║║║║╣ ╠╦╝                       ║
# ║    ╚═╝╩ ╩ ╩ ╩╚═╝╚═╝   ╚╝ ╩╚═╝╚╩╝╚═╝╩╚═                       ║
# ║                                                              ║
# ╠══════════════════════════════════════════════════════════════╣
# ║  Project     : GitHub Viewer                                 ║
# ║  Author      : SwiftGlitxh                                   ║
# ║  Version     : 1.1.0                                         ║
# ║  Description : A simple tool to view GitHub profiles and     ║
# ║                repositories from the command line.           ║
# ╠══════════════════════════════════════════════════════════════╣
# ║  Imports     : argparse, json, sys                           ║
# ║                requests (third-party)                        ║
# ╚══════════════════════════════════════════════════════════════╝

import argparse
import json
import sys

import requests


class GitViewer:
    def __init__(self, username, verbose=False, output=None,
                 api="https://api.github.com/users/"):
        self.username = username
        self.verbose = verbose
        self.output = output
        self.api = api

    def log(self, message):
        if self.verbose:
            print(f"[+] {message}")

    def Get(self, url, params=None):
        """GET a URL and return parsed JSON, or None on any error."""
        self.log(f"Requesting {url}")

        try:
            r = requests.get(url, params=params, timeout=10)
        except requests.RequestException as e:
            print(f"Network error: {e}")
            return None

        self.log(f"Status code: {r.status_code}")
        self.log(f"Rate limit remaining: {r.headers.get('X-RateLimit-Remaining', 'unknown')}")

        if r.status_code == 404:
            print(f"Not found: {url}")
            return None
        if r.status_code == 403:
            print("Request blocked (likely rate limited). Try again later.")
            return None
        if r.status_code != 200:
            print(f"Request failed with status {r.status_code}.")
            return None

        return r.json()

    def GitRequest(self):
        return self.Get(f"{self.api}{self.username}")

    def LastUpload(self):
        """Most recently pushed repo."""
        repos = self.Get(f"{self.api}{self.username}/repos",
                         params={"sort": "pushed", "per_page": 1})
        return repos[0] if repos else None

    def LastActivity(self):
        """Most recent public event."""
        events = self.Get(f"{self.api}{self.username}/events/public",
                          params={"per_page": 1})
        return events[0] if events else None

    @staticmethod
    def DescribeEvent(event):
        """Turn a raw event into a short readable summary."""
        etype = event["type"]
        payload = event.get("payload", {})
        action = payload.get("action", "")

        if etype == "PushEvent":
            ref = payload.get("ref", "").replace("refs/heads/", "")
            return f"Pushed to {ref}" if ref else "Pushed commits"
        if etype == "CreateEvent":
            return f"Created {payload.get('ref_type', 'item')}"
        if etype == "DeleteEvent":
            return f"Deleted {payload.get('ref_type', 'item')}"
        if etype == "WatchEvent":
            return "Starred a repo"
        if etype == "ForkEvent":
            return "Forked a repo"
        if etype == "IssuesEvent":
            return f"{action.capitalize()} an issue"
        if etype == "IssueCommentEvent":
            return "Commented on an issue"
        if etype == "PullRequestEvent":
            return f"{action.capitalize()} a pull request"
        if etype == "PullRequestReviewEvent":
            return "Reviewed a pull request"
        if etype == "ReleaseEvent":
            return f"{action.capitalize()} a release"
        if etype == "PublicEvent":
            return "Made a repo public"
        return etype.replace("Event", "")

    def BuildReport(self, data, last_repo, last_event):
        lines = [
            f"Username     : {data['login']}",
            f"Name         : {data['name'] or 'N/A'}",
            f"Bio          : {data['bio'] or 'N/A'}",
            f"Location     : {data['location'] or 'N/A'}",
            f"Company      : {data['company'] or 'N/A'}",
            f"Public repos : {data['public_repos']}",
            f"Followers    : {data['followers']}",
            f"Following    : {data['following']}",
            f"Created      : {data['created_at'][:10]}",
            f"Profile URL  : {data['html_url']}",
        ]

        if self.verbose:
            lines += [
                f"Email        : {data['email'] or 'N/A'}",
                f"Blog         : {data['blog'] or 'N/A'}",
                f"Twitter      : {data['twitter_username'] or 'N/A'}",
                f"Hireable     : {data['hireable'] if data['hireable'] is not None else 'N/A'}",
                f"Public gists : {data['public_gists']}",
                f"Updated      : {data['updated_at'][:10]}",
                f"Avatar URL   : {data['avatar_url']}",
                f"Repos URL    : {data['repos_url']}",
            ]

        # Last upload (most recently pushed repo)
        lines.append("-" * 40)
        if last_repo:
            pushed = (last_repo.get("pushed_at") or "")
            lines.append(f"Last upload  : {last_repo['name']} ({pushed[:10]} {pushed[11:16]} UTC)")
            if self.verbose:
                lines += [
                    f"  Description: {last_repo['description'] or 'N/A'}",
                    f"  Language   : {last_repo['language'] or 'N/A'}",
                    f"  Stars      : {last_repo['stargazers_count']}",
                    f"  Forked     : {'Yes' if last_repo['fork'] else 'No'}",
                    f"  URL        : {last_repo['html_url']}",
                ]
        else:
            lines.append("Last upload  : N/A (no public repos)")

        # Last activity (most recent public event)
        if last_event:
            when = last_event["created_at"]
            lines.append(f"Last activity: {self.DescribeEvent(last_event)} "
                         f"in {last_event['repo']['name']} "
                         f"({when[:10]} {when[11:16]} UTC)")
            if self.verbose:
                payload = last_event.get("payload", {})
                commits = payload.get("commits") or []
                if commits:
                    msg = commits[-1]["message"].splitlines()[0]
                    lines.append(f"  Commit msg : {msg}")
                lines.append(f"  Event type : {last_event['type']}")
        else:
            lines.append("Last activity: N/A (no recent public activity)")

        return lines

    def SaveOutput(self, data, lines):
        try:
            with open(self.output, "w", encoding="utf-8") as f:
                if self.output.lower().endswith(".json"):
                    json.dump(data, f, indent=4)
                else:
                    f.write("\n".join(lines) + "\n")
        except OSError as e:
            print(f"Could not write to '{self.output}': {e}")
            return False

        self.log(f"Saved output to {self.output}")
        return True

    def ShowProfile(self):
        data = self.GitRequest()
        if data is None:
            return False

        last_repo = self.LastUpload()
        last_event = self.LastActivity()

        lines = self.BuildReport(data, last_repo, last_event)

        print("=" * 40)
        print("\n".join(lines))
        print("=" * 40)

        if self.output:
            combined = {
                "profile": data,
                "last_upload": last_repo,
                "last_activity": last_event,
            }
            return self.SaveOutput(combined, lines)

        return True


def parse_args():
    parser = argparse.ArgumentParser(
        description="View a GitHub user's profile from the command line."
    )
    parser.add_argument("-u", "--username", required=True,
                        help="GitHub username to look up")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="show extra details and request info")
    parser.add_argument("-o", "--output", metavar="FILE",
                        help="save the result to FILE (.json for JSON, otherwise plain text)")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    GT = GitViewer(args.username, verbose=args.verbose, output=args.output)
    sys.exit(0 if GT.ShowProfile() else 1)
