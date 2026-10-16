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
# ║  Version     : 1.0.0                                         ║
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

    def GitRequest(self):
        url = f"{self.api}{self.username}"
        self.log(f"Requesting {url}")

        try:
            r = requests.get(url, timeout=10)
        except requests.RequestException as e:
            print(f"Network error: {e}")
            return None

        self.log(f"Status code: {r.status_code}")
        self.log(f"Rate limit remaining: {r.headers.get('X-RateLimit-Remaining', 'unknown')}")

        if r.status_code == 404:
            print(f"User '{self.username}' not found.")
            return None
        if r.status_code != 200:
            print(f"Request failed with status {r.status_code}.")
            return None

        return r.json()

    def BuildReport(self, data):
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

        lines = self.BuildReport(data)

        print("=" * 40)
        print("\n".join(lines))
        print("=" * 40)

        if self.output:
            return self.SaveOutput(data, lines)

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
