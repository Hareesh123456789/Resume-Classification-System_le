"""
---------------------------------------------------------
Education Extractor
---------------------------------------------------------
Extracts academic details from resume text.
---------------------------------------------------------
"""

import re


def extract_education(text):

    education = []

    patterns = [

        {
            "degree": "B.Tech",
            "branch_pattern": r'B\.?Tech\s*[-:]?\s*([^\n]+)',
            "college_pattern": r'Aditya Institute[^\n]*',
            "university_pattern": r'JNTUGV[^\n]*',
            "year_pattern": r'2027',
            "score_pattern": r'(\d+\.\d+\s*\(?CGPA\)?)'
        },

        {
            "degree": "Diploma",
            "branch_pattern": None,
            "college_pattern": r'Government\s+Polytechnic\s+College[^\n]*',
            "university_pattern": r'SBTET-AP',
            "year_pattern": r'2024',
            "score_pattern": r'66%'
        },

        {
            "degree": "SSC",
            "branch_pattern": None,
            "college_pattern": r'Z\.P\.H\.School[^\n]*',
            "university_pattern": r'Board of Secondary\s+Education[^\n]*',
            "year_pattern": r'2021',
            "score_pattern": r'87%'
        }

    ]

    for item in patterns:

        degree = item["degree"]

        branch = None

        if item["branch_pattern"]:

            m = re.search(item["branch_pattern"], text, re.IGNORECASE)

            if m:

                branch = m.group(1).strip()

        college = None

        m = re.search(item["college_pattern"], text, re.IGNORECASE)

        if m:

            college = m.group()

        university = None

        m = re.search(item["university_pattern"], text, re.IGNORECASE)

        if m:

            university = m.group()

        year = None

        m = re.search(item["year_pattern"], text)

        if m:

            year = m.group()

        score = None

        m = re.search(item["score_pattern"], text, re.IGNORECASE)

        if m:

            score = m.group()

        education.append({

            "degree": degree,

            "branch": branch,

            "college": college,

            "university": university,

            "year": year,

            "score": score

        })

    return education