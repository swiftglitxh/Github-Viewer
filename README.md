# GitHub Profile Viewer
<img width="1672" height="941" alt="43d39089-1c26-4ad6-ae51-7185b087db8b" src="https://github.com/user-attachments/assets/a82cc1d3-35bb-48a4-b7a9-5b1b062172e7" />

A lightweight Python command-line tool for retrieving and displaying GitHub user profiles using the **GitHub REST API**.

GitHub Profile Viewer provides a simple way to inspect public GitHub account information directly from your terminal, with support for verbose reporting and exporting results to JSON or plain text.

## Features

- **Profile Lookup** — Retrieve public GitHub user information.
- **Detailed Reports** — Display usernames, bios, locations, followers, and repository counts.
- **Verbose Mode** — Show additional profile fields, HTTP status codes, and API rate-limit information.
- **Export Results** — Save profile information as JSON or plain text.
- **Error Handling** — Handle network failures, invalid usernames, and unsuccessful API requests.
- **Lightweight** — Requires only Python and the `requests` library.

## Requirements

- Python 3.8 or newer
- `requests` library
- Internet connection

## Installation

**1. Clone the repository**

```bash
git clone https://github.com/SwiftGlitxh/github-profile-viewer.git
cd github-profile-viewer
```

**2. Install dependencies**

```bash
python -m pip install requests
```

**3. Run the tool**

```bash
python github_viewer.py -u SwiftGlitxh
```

> Replace `github_viewer.py` with your actual Python script filename if different.

## Usage
<img width="548" height="434" alt="image" src="https://github.com/user-attachments/assets/8a4a0ce1-0482-489a-a0f6-3446e67c6742" />

### Basic
