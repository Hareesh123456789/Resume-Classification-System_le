"""
---------------------------------------------------------
Personal Information Extractor
---------------------------------------------------------
Purpose:
Extract personal details from resume text.

Extracts:
- Name
- Email
- Phone Number
- LinkedIn
- GitHub
- Portfolio Website
---------------------------------------------------------
"""

import re


def extract_email(text):
    """Extract email address."""
    pattern = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
    match = re.search(pattern, text)

    if match:
        return match.group()

    return None


def extract_phone(text):
    """Extract phone number."""
    pattern = r'(\+91[\s-]?\d{10}|\d{10})'
    match = re.search(pattern, text)

    if match:
        return match.group()

    return None


def extract_linkedin(text):
    """Extract LinkedIn URL."""
    pattern = r'https?://(?:www\.)?linkedin\.com/[^\s]+'
    match = re.search(pattern, text)

    if match:
        return match.group()

    return None


def extract_github(text):
    """Extract GitHub URL."""
    pattern = r'https?://(?:www\.)?github\.com/[^\s]+'
    match = re.search(pattern, text)

    if match:
        return match.group()

    return None


def extract_portfolio(text):
    """Extract portfolio website."""
    urls = re.findall(r'https?://[^\s]+', text)

    for url in urls:
        if "linkedin" not in url.lower() and "github" not in url.lower():
            return url

    return None


def extract_name(text):
    """
    Extract candidate name.

    Current Strategy:
    The first ALL-CAPS line having at least two words
    is considered as the candidate name.
    """

    lines = text.split("\n")

    for line in lines:

        line = line.strip()

        if len(line.split()) >= 2:

            if line.isupper():

                return line.title()

    return None


def extract_personal_info(text):
    """
    Main Function
    """

    info = {

        "name": extract_name(text),

        "email": extract_email(text),

        "phone": extract_phone(text),

        "linkedin": extract_linkedin(text),

        "github": extract_github(text),

        "portfolio": extract_portfolio(text)

    }

    return info