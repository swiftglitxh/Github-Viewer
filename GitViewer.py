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
# ║  Version     : 1.2.0                                         ║
# ║  Description : A simple tool to view GitHub profiles and     ║
# ║                repositories from the command line.           ║
# ╠══════════════════════════════════════════════════════════════╣
# ║  Usage       : python gitviewer.py -u <username>             ║
# ║  Flags       : -u, --username  GitHub user to look up        ║
# ║                -v, --verbose   show extra details            ║
# ║                -o, --output    save to FILE (.json or text)  ║
# ║                --no-color      disable colours               ║
# ║                --no-icons      disable emoji icons           ║
# ╠══════════════════════════════════════════════════════════════╣
# ║  Imports     : argparse, json, os, sys                       ║
# ║                requests (third-party)                        ║
# ╚══════════════════════════════════════════════════════════════╝

import argparse
import json
import os
import sys

import requests

os.system("")  # enables ANSI colours on Windows terminals

GREEN = "\033[92m"
DARK = "\033[32m"
CYAN = "\033[96m"
RED = "\033[91m"
RESET = "\033[0m"

RULE = "=" * 40
LABEL_W = 14           # label column on rows that have an icon
TOP_W = LABEL_W + 3    # same column for rows without one (icon + space = 3 cells)

# Every icon is a double-width emoji, so the colons stay lined up.
ICONS = {
    "location": "📍", "company": "🏢", "repos": "📦", "followers": "👥",
    "following": "👤", "created": "📅", "url": "🔗", "email": "📧",
    "blog": "🌐", "twitter": "🐦", "hireable": "💼", "gists": "📝",
    "updated": "🔄", "avatar": "📷", "repos_url": "📂",
    "upload": "📤", "activity": "🕒",
}


def disable_color():
    global GREEN, DARK, CYAN, RED, RESET
    GREEN = DARK = CYAN = RED = RESET = ""


class GitViewer:
    def __init__(self, username, verbose=False, output=None, icons=True,
                 api="https://api.github.com/users/"):
        self.username = username
        self.verbose = verbose
        self.output = output
        self.icons = icons
        self.api = api

    # ─── Logging ───────────────────────────────────────────────

    def log(self, message):
        if self.verbose:
            print(f"{DARK}[+] {message}{RESET}")

    @staticmethod
    def err(message):
        print(f"{RED}[!] {message}{RESET}", file=sys.stderr)

    # ─── API ───────────────────────────────────────────────────

    def Get(self, url, params=None):
        """GET a URL and return parsed JSON, or None on any error."""
        self.log(f"Requesting {url}")

        try:
            r = requests.get(url, params=params, timeout=10)
        except requests.RequestException as e:
            self.err(f"Network error: {e}")
            return None

        self.log(f"Status code: {r.status_code}")
        self.log(f"Rate limit remaining: {r.headers.get('X-RateLimit-Remaining', 'unknown')}")

        if r.status_code == 404:
            self.err(f"Not found: {url}")
            return None
        if r.status_code == 403:
            self.err("Request blocked (likely rate limited). Try again later.")
            return None
        if r.status_code != 200:
            self.err(f"Request failed with status {r.status_code}.")
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

    # ─── Report ────────────────────────────────────────────────
    #
    # The report is built as a list of "rows" first, then rendered twice:
    # once with colours and icons for the terminal, once as plain text for -o.
    #
    #   ("sep",)                                    a ==== rule
    #   ("top", label, value)                       row without an icon
    #   ("cont", text)                              extra bio line (cyan)
    #   ("item", icon_key, label, value, stamp)     row with an icon
    #   ("sub", label, value)                       indented verbose detail
    #   ("stamp", text)                             green timestamp on its own line

    def BuildRows(self, data, last_repo, last_event):
        bio = [b.strip() for b in (data["bio"] or "").replace("\r", "").split("\n")]
        bio = [b for b in bio if b]

        rows = [
            ("sep",),
            ("top", "Username", data["login"]),
            ("top", "Name", data["name"] or "N/A"),
            ("top", "Bio", bio[0] if bio else "N/A"),
        ]
        rows += [("cont", line) for line in bio[1:]]
        rows += [
            ("item", "location", "Location", data["location"] or "N/A", None),
            ("item", "company", "Company", data["company"] or "N/A", None),
            ("item", "repos", "Public repos", data["public_repos"], None),
            ("item", "followers", "Followers", data["followers"], None),
            ("item", "following", "Following", data["following"], None),
            ("item", "created", "Created", data["created_at"][:10], None),
            ("item", "url", "Profile URL", data["html_url"], None),
        ]

        if self.verbose:
            hireable = data["hireable"] if data["hireable"] is not None else "N/A"
            rows += [
                ("item", "email", "Email", data["email"] or "N/A", None),
                ("item", "blog", "Blog", data["blog"] or "N/A", None),
                ("item", "twitter", "Twitter", data["twitter_username"] or "N/A", None),
                ("item", "hireable", "Hireable", hireable, None),
                ("item", "gists", "Public gists", data["public_gists"], None),
                ("item", "updated", "Updated", data["updated_at"][:10], None),
                ("item", "avatar", "Avatar URL", data["avatar_url"], None),
                ("item", "repos_url", "Repos URL", data["repos_url"], None),
            ]

        rows.append(("sep",))

        # Last upload (most recently pushed repo)
        if last_repo:
            pushed = last_repo.get("pushed_at") or ""
            stamp = f"({pushed[:10]} {pushed[11:16]} UTC)" if pushed else None
            rows.append(("item", "upload", "Last upload", last_repo["name"], stamp))
            if self.verbose:
                rows += [
                    ("sub", "Description", last_repo["description"] or "N/A"),
                    ("sub", "Language", last_repo["language"] or "N/A"),
                    ("sub", "Stars", last_repo["stargazers_count"]),
                    ("sub", "Forked", "Yes" if last_repo["fork"] else "No"),
                    ("sub", "URL", last_repo["html_url"]),
                ]
        else:
            rows.append(("item", "upload", "Last upload", "N/A (no public repos)", None))

        # Last activity (most recent public event)
        if last_event:
            when = last_event["created_at"]
            text = f"{self.DescribeEvent(last_event)} in {last_event['repo']['name']}"
            rows.append(("item", "activity", "Last activity", text, None))
            rows.append(("stamp", f"({when[:10]} {when[11:16]} UTC)"))
            if self.verbose:
                commits = last_event.get("payload", {}).get("commits") or []
                if commits:
                    msg = commits[-1]["message"].splitlines()[0]
                    rows.append(("sub", "Commit msg", msg))
                rows.append(("sub", "Event type", last_event["type"]))
        else:
            rows.append(("item", "activity", "Last activity",
                         "N/A (no recent public activity)", None))

        return rows

    def Render(self, rows, fancy=True):
        """Turn rows into text lines. fancy=True adds colours and icons."""
        use_icons = fancy and self.icons
        lines = []

        for row in rows:
            kind = row[0]

            if kind == "sep":
                lines.append(f"{GREEN}{RULE}{RESET}" if fancy else RULE)

            elif kind == "top":
                _, label, value = row
                lines.append(f"{label:<{TOP_W}}: {value}")

            elif kind == "cont":
                lines.append(f"{CYAN}{row[1]}{RESET}" if fancy else row[1])

            elif kind == "item":
                _, key, label, value, stamp = row
                if use_icons:
                    head = f"{ICONS[key]} {label:<{LABEL_W}}"
                else:
                    head = f"{label:<{TOP_W}}"
                line = f"{head}: {value}"
                if stamp:
                    line += f" {GREEN}{stamp}{RESET}" if fancy else f" {stamp}"
                lines.append(line)

            elif kind == "sub":
                _, label, value = row
                lines.append(f"  {label:<{TOP_W - 2}}: {value}")

            elif kind == "stamp":
                pad = " " * (TOP_W + 2)
                lines.append(f"{pad}{GREEN}{row[1]}{RESET}" if fancy else f"{pad}{row[1]}")

        return lines

    # ─── Saving and main flow ──────────────────────────────────

    def SaveOutput(self, data, lines):
        try:
            with open(self.output, "w", encoding="utf-8") as f:
                if self.output.lower().endswith(".json"):
                    json.dump(data, f, indent=4)
                else:
                    f.write("\n".join(lines) + "\n")
        except OSError as e:
            self.err(f"Could not write to '{self.output}': {e}")
            return False

        self.log(f"Saved output to {self.output}")
        return True

    def ShowProfile(self):
        data = self.GitRequest()
        if data is None:
            return False

        last_repo = self.LastUpload()
        last_event = self.LastActivity()

        rows = self.BuildRows(data, last_repo, last_event)

        print("\n".join(self.Render(rows, fancy=True)))

        if self.output:
            combined = {
                "profile": data,
                "last_upload": last_repo,
                "last_activity": last_event,
            }
            return self.SaveOutput(combined, self.Render(rows, fancy=False))

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
    parser.add_argument("--no-color", action="store_true",
                        help="disable coloured output")
    parser.add_argument("--no-icons", action="store_true",
                        help="disable emoji icons (for terminals that can't show them)")
    return parser.parse_args()


if __name__ == "__main__":
    # Emoji in bios and icons would crash a legacy Windows console without this.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    args = parse_args()

    if args.no_color or os.environ.get("NO_COLOR") or not sys.stdout.isatty():
        disable_color()

    GT = GitViewer(args.username, verbose=args.verbose, output=args.output,
                   icons=not args.no_icons)
    sys.exit(0 if GT.ShowProfile() else 1)
