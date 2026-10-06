"""Extract education records from an education section or a full resume.

Uses local text rules, not an AI model. Missing details remain None.
"""

import re


DEGREES = (
    ("Ph.D", r"ph\.?\s*d\.?|doctor\s+of\s+philosophy"),
    ("M.Tech", r"m\.?\s*tech\.?|master\s+of\s+technology"),
    ("B.Tech", r"b\.?\s*tech\.?|bachelor\s+of\s+technology"),
    ("M.E", r"m\.\s*e\.?|(?-i:ME)|master\s+of\s+engineering"),
    ("B.E", r"b\.\s*e\.?|(?-i:BE)|bachelor\s+of\s+engineering"),
    ("M.Sc", r"m\.?\s*sc\.?|master\s+of\s+science"),
    ("B.Sc", r"b\.?\s*sc\.?|bachelor\s+of\s+science"),
    ("M.Com", r"m\.?\s*com\.?|master\s+of\s+commerce"),
    ("B.Com", r"b\.?\s*com\.?|bachelor\s+of\s+commerce"),
    ("MBA", r"m\.?\s*b\.?\s*a\.?|master\s+of\s+business\s+administration"),
    ("BBA", r"b\.?\s*b\.?\s*a\.?|bachelor\s+of\s+business\s+administration"),
    ("MCA", r"m\.?\s*c\.?\s*a\.?|master\s+of\s+computer\s+applications?"),
    ("BCA", r"b\.?\s*c\.?\s*a\.?|bachelor\s+of\s+computer\s+applications?"),
    ("M.A", r"m\.\s*a\.?|(?-i:MA)|master\s+of\s+arts"),
    ("B.A", r"b\.\s*a\.?|(?-i:BA)|bachelor\s+of\s+arts"),
    ("Diploma", r"d[ \t]*i[ \t]*p[ \t]*l[ \t]*o[ \t]*m[ \t]*a"),
    ("Class 12", r"class\s*(?:12(?:th)?|xii)|12th|hsc|intermediate|higher\s+secondary"),
    ("Class 10", r"class\s*(?:10(?:th)?|x)|10th|ssc|matriculation|secondary\s+school\s+certificate"),
)
DEGREE_PATTERNS = [
    (name, re.compile(r"(?<!\w)(?:" + pattern + r")(?!\w)", re.I))
    for name, pattern in DEGREES
]
EDUCATION_HEADING = re.compile(
    r"^\s*(?:education(?:al)?(?:\s+(?:qualifications?|details|background))?"
    r"|academic\s+(?:profile|details|qualifications?|background)"
    r"|qualifications?)\s*:?[ \t]*$", re.I | re.M
)
OTHER_HEADING = re.compile(
    r"^\s*(?:technical\s+skills|skills|(?:work|professional)\s+experience"
    r"|experience|(?:academic\s+)?projects?(?:\s+experience)?"
    r"|certifications?|achievements?|internships?|career\s+objective"
    r"|summary|personal\s+details|declaration|languages|interests)\s*:?[ \t]*$",
    re.I | re.M,
)
YEAR = r"(?:19|20)\d{2}"
RANGE = re.compile(r"\b(" + YEAR + r")\s*(?:-|\u2013|\u2014|to)\s*(" + YEAR + r"|present|current|ongoing)\b", re.I)
FIELDS = ("degree", "specialization", "institution", "university", "year", "score")


def _education_text(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")
    heading = EDUCATION_HEADING.search(text)
    if heading:
        text = text[heading.end():]
        end = OTHER_HEADING.search(text)
        if end:
            text = text[:end.start()]
    return text.strip()


def _year(block):
    labeled = re.search(
        r"(?:passing\s+year|year\s+of\s+(?:passing|graduation)|graduated|graduation|expected)"
        r"\s*[:\-]?\s*(?:in\s+)?(" + YEAR + r")\b", block, re.I
    )
    if labeled:
        return labeled.group(1)
    span = RANGE.search(block)
    if span:
        return span.group(2) if span.group(2).isdigit() else None
    if re.search(r"\b(?:pursuing|ongoing|present|currently)\b", block, re.I):
        return None
    years = set(re.findall(r"\b(" + YEAR + r")\b", block))
    # Unlabeled, conflicting years cannot be resolved by selecting the last one.
    return next(iter(years)) if len(years) == 1 else None


def _score(block):
    number = r"\d{1,2}(?:\.\d+)?"
    value = number + r"(?:\s*/\s*(?:10|4)(?:\.0)?)?"
    prefix = re.search(r"\b(CGPA|GPA)\s*[:=\-]?\s*(" + value + r")(?![\d.])", block, re.I)
    suffix = re.search(r"(?<![\d.])(" + value + r")\s*\(?\s*(CGPA|GPA)\b", block, re.I)
    if prefix or suffix:
        match = prefix or suffix
        label, result = (match.group(1), match.group(2)) if prefix else (match.group(2), match.group(1))
        result = re.sub(r"\s+", "", result)
        parts = result.split("/")
        maximum = float(parts[1]) if len(parts) == 2 else 10
        if 0 <= float(parts[0]) <= maximum:
            return result + " (" + label.upper() + ")"
        return None
    percent = re.search(r"(?<![\d.])(\d{1,3}(?:\.\d+)?)\s*(?:%|percent\b)", block, re.I)
    if percent and 0 <= float(percent.group(1)) <= 100:
        return percent.group(1) + "%"
    cells = _cells(block)
    # A table may contain an unlabeled score after the passing year. Retain the
    # value, but do not infer a CGPA denominator or percentage from its size.
    seen_year = False
    raw_scores = []
    for cell in cells:
        if re.search(r"\b" + YEAR + r"\b", cell):
            seen_year = True
        elif seen_year and re.fullmatch(r"\d{1,3}(?:\.\d+)?", cell):
            if 0 <= float(cell) <= 100:
                raw_scores.append(cell)
    return raw_scores[0] if len(raw_scores) == 1 else None


def _cells(block):
    return [p.strip(" ;:-") for p in re.split(r"\n|\||\t|\s{2,}", block) if p.strip(" ;:-")]


def _organization(cell):
    cell = re.sub(r"^(?:institution|college|school|university|board)\s*:\s*", "", cell, flags=re.I)
    cell = re.sub(r"^affiliated\s+to\s+", "", cell, flags=re.I)
    cell = re.split(r"\b" + YEAR + r"\b|\b(?:CGPA|GPA)\b|\b\d+(?:\.\d+)?\s*%", cell, maxsplit=1, flags=re.I)[0]
    return cell.strip(" ;:-()") or None


BOARD = re.compile(r"\b(?:board|CBSE|ICSE|SBTET(?:-\w+)?|BIE|BSE)\b", re.I)
UNIVERSITY = re.compile(r"\b(?:university|JNTU\w*)\b", re.I)
INSTITUTION = re.compile(r"\b(?:college|institute|institution|polytechnic|school|university)\b", re.I)


def _is_field(cell):
    if re.search(r"\b" + YEAR + r"\b", cell):
        return True
    if re.fullmatch(r"\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)?\s*%?", cell):
        return True
    return bool(re.search(
        r"\b(?:CGPA|GPA|percentage|score|marks|specialization|specialisation|branch|major|duration|year)\b",
        cell, re.I
    ))


def _organizations(block):
    institution = None
    university = None
    cells = _cells(block)
    consumed = set()
    for index, cell in enumerate(cells):
        if index in consumed:
            continue
        # Degree + institution on one row: ignore the degree prefix.
        matches = [p.search(cell) for _, p in DEGREE_PATTERNS]
        matches = [m for m in matches if m]
        if matches:
            first = min(matches, key=lambda m: m.start())
            tail = cell[first.end():].lstrip(" ,;:-")
            if re.match(r"in\s", tail, re.I) and "," in tail:
                tail = tail.split(",", 1)[1]
            cell = tail.strip()
        if not cell:
            continue
        name = _organization(cell)
        if not name:
            continue
        is_board = BOARD.search(name)
        is_university = UNIVERSITY.search(name)
        is_institution = INSTITUTION.search(name)
        if not (is_board or is_university or is_institution):
            continue
        # Preserve a common institution prefix split onto the preceding line.
        if index and re.fullmatch(r"(?:government|govt\.?|private|public|national|state)", cells[index - 1], re.I):
            name = cells[index - 1] + " " + name
        for next_index in range(index + 1, min(index + 6, len(cells))):
            candidate = cells[next_index]
            if _is_field(candidate) or OTHER_HEADING.fullmatch(candidate):
                break
            if any(p.search(candidate) for _, p in DEGREE_PATTERNS):
                break
            if BOARD.search(candidate) or UNIVERSITY.search(candidate) or INSTITUTION.search(candidate):
                break
            part = _organization(candidate)
            if not part:
                break
            name += " " + part
            consumed.add(next_index)
        name = re.sub(r"\s+,", ",", re.sub(r"\s+", " ", name)).strip(" ,;:-()")
        if (is_board or is_university) and not university:
            university = name
        if is_institution and not is_board and not institution:
            institution = name
    return institution, university


def _specialization(block, degree_match):
    labeled = re.search(r"\b(?:specialization|specialisation|branch|major)\s*:\s*([^\n|;]+)", block, re.I)
    if labeled:
        value = labeled.group(1)
    else:
        tail = block[degree_match.end():].split("\n", 1)[0].lstrip(" ,;:|\t-")
        tail = re.split(r"\||;|,|\b" + YEAR + r"\b|\b(?:CGPA|GPA)\b", tail, maxsplit=1, flags=re.I)[0]
        value = re.sub(r"^\s*(?:in\s+|[-:]\s*)", "", tail, flags=re.I).strip()
        if re.search(r"\b(?:college|institute|university|school|board|pursuing)\b", value, re.I):
            return None
    value = value.strip(" ,;:.-()")
    # Normalize split technical acronyms; never remove spaces from arbitrary
    # institution names, where the correct spelling cannot be established.
    for acronym in ("CSE", "ECE", "EEE", "AIML", "AI", "ML", "IT"):
        pattern = r"(?<!\w)" + r"[ \t]*".join(acronym) + r"(?!\w)"
        value = re.sub(pattern, acronym, value, flags=re.I)
    return value or None


def extract_education(text):
    """Return a list of dicts compatible with schemas.resume_schema.Education.

    Pass the education section when available. Full resumes need a recognizable
    education heading to isolate education from unrelated degree mentions.
    """
    if not isinstance(text, str):
        raise TypeError("Education input must be text.")
    section = _education_text(text)
    if not section:
        return []
    entries = []
    offset = 0
    for line in section.splitlines(keepends=True):
        found = [(name, pattern.search(line)) for name, pattern in DEGREE_PATTERNS]
        found = [(name, match) for name, match in found if match]
        if found:
            name, match = min(found, key=lambda item: (item[1].start(), -len(item[1].group())))
            entries.append((offset, name))
        offset += len(line)
    records = []
    for i, (start, degree) in enumerate(entries):
        end = entries[i + 1][0] if i + 1 < len(entries) else len(section)
        block = section[start:end]
        institution, university = _organizations(block)
        # Specialization matching needs positions relative to this block.
        pattern = next(p for name, p in DEGREE_PATTERNS if name == degree)
        degree_match = pattern.search(block)
        record = dict(zip(FIELDS, (degree, _specialization(block, degree_match),
                                  institution, university, _year(block), _score(block))))
        if record not in records:
            records.append(record)
    return records
