"""Backward-compatible entry point for interactive admin creation.

Run with: python seed.py
The script prompts for an administrator name, email, and password.
No default credentials are stored in source code.
"""

from create_admin import create_admin


if __name__ == "__main__":
    create_admin()
