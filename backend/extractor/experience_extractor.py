"""Extract employment and internships into the existing Experience schema."""

import re


EXPERIENCE_HEADING = re.compile(
    r"^[ \t]*(?:(?:(?:work|professional|employment|internship|intership)[ \t]+)?"
    r"exper(?:ience|ince)|employment[ \t]+history|work[ \t]+history|internships?)"
    r"[ \t]*:?[ \t]*$", re.I | re.M,
)

OTHER_HEADING = re.compile(
    r"^[ \t]*(?:education(?:al)?(?:[ \t]+qualifications?)?|academic[ \t]+(?:profile|background)"
    r"|(?:technical[ \t]+)?skills|(?:academic[ \t]+)?projects?(?:[ \t]+experience)?"
    r"|certifications?|achievements?|key[ \t]+achievements|career[ \t]+objective"
    r"|summary|personal[ \t]+details|declaration|languages|interests)"
    r"[ \t]*:?[ \t]*$", re.I | re.M,
)

MONTH = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
YEAR = r"(?:19|20)\d{2}"
DATE = r"(?:" + MONTH + r"\.?[ \t]*" + YEAR + r"|" + YEAR + r"[-/](?:0?[1-9]|1[0-2])|(?:0?[1-9]|1[0-2])[-/]" + YEAR + r"|" + YEAR + r")"

DATE_RANGE = re.compile(
    r"(?<![\w/])(" + DATE + r")[ \t]*(?:-|\u2013|\u2014|to)[ \t]*("
    + DATE + r"|present|current|ongoing)(?!\w)", re.I,
)

ROLE = re.compile(
    r"\b(?:engineer|developer|intern|trainee|analyst|manager|consultant|designer"
    r"|scientist|tester|administrator|specialist|assistant|researcher|accountant"
    r"|executive|technician|coordinator|associate|lead)\b", re.I,
)

COMPANY = re.compile(
    r"\b(?:ltd|limited|inc|pvt|llc|corporation|technologies|solutions|systems|labs)\b",
    re.I,
)

ACTION = re.compile(
    r"^(?:developed|built|created|maintained|implemented|worked|managed|responsible"
    r"|led|designed|assisted|seeking|looking|learned|completed|improved)\b",
    re.I,
)

LABEL = re.compile(
    r"^(company|employer|organization|organisation|role|position|job[ \t]+title"
    r"|duration|dates|description)[ \t]*:[ \t]*(.*)$", re.I,
)

LABEL_FIELDS = {
    "company": "company",
    "employer": "company",
    "organization": "company",
    "organisation": "company",
    "role": "role",
    "position": "role",
    "job title": "role",
    "duration": "duration",
    "dates": "duration",
    "description": "description",
}


def _section(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")
    match = EXPERIENCE_HEADING.search(text)

    if match:
        text = text[match.end():]
        end = OTHER_HEADING.search(text)
        return text[:end.start()] if end else text

    return "" if OTHER_HEADING.search(text) else text


def _line(text):
    return re.sub(
        r"^[ \t]*(?:[\u2022*\-]+[ \t]*|\d+[.)][ \t]+)",
        "",
        text,
    ).strip()


def _looks_role(text):
    return (
        bool(ROLE.search(text))
        and len(text.split()) <= 12
        and not ACTION.match(text)
        and not COMPANY.search(text)
    )


def _header(text):
    parts = [
        part.strip(" ,;|-\u2013\u2014")
        for part in re.split(
            r"\||[ \t]+(?:-|\u2013|\u2014|at|@)[ \t]+",
            text,
            flags=re.I,
        )
    ]
    parts = [part for part in parts if part]

    if len(parts) >= 2:
        if _looks_role(parts[0]):
            return parts[0], " | ".join(parts[1:])
        if _looks_role(parts[1]):
            return parts[1], parts[0]

    if "," in text:
        left, right = text.split(",", 1)
        if _looks_role(left.strip()) and COMPANY.search(right):
            return left.strip(), right.strip()

    return (text, None) if _looks_role(text) else (None, None)


def _empty():
    return {
        "company": None,
        "role": None,
        "duration": None,
        "description": None,
    }


def extract_experience(text):
    """Return experience records with missing fields set to None."""
    if not isinstance(text, str):
        raise TypeError("Experience input must be text.")

    section = _section(text)
    records = []
    current = None
    description = []

    def finish():
        nonlocal current, description

        if current and (current["role"] or current["company"]):
            current["description"] = "\n".join(description).strip() or None

            if current not in records:
                records.append(current)

        current = None
        description = []

    for raw in section.splitlines():
        line = _line(raw)

        if not line or EXPERIENCE_HEADING.fullmatch(line):
            continue

        label = LABEL.match(line)

        if label:
            label_name = re.sub(r"[ \t]+", " ", label.group(1).lower())
            field = LABEL_FIELDS[label_name]
            value = label.group(2).strip() or None

            if field in ("company", "role") and current and current[field]:
                finish()

            if current is None:
                current = _empty()

            if field == "description":
                if value:
                    description.append(value)
            else:
                current[field] = value

            continue

        date = DATE_RANGE.search(line)
        duration = (
            date.group(1) + " - " + date.group(2)
            if date else None
        )

        content = (
            (line[:date.start()] + line[date.end():]).strip(" ,;|-\u2013\u2014")
            if date else line
        )

        is_bullet = bool(
            re.match(
                r"^[ \t]*(?:[\u2022*\-]+[ \t]+|\d+[.)][ \t]+)",
                raw,
            )
        )

        role, company = _header(content) if content else (None, None)

        if is_bullet and not company:
            role = None

        if role:
            if current and current["role"]:
                finish()

            if current is None:
                current = _empty()

            current["role"] = role

            if company:
                current["company"] = company
            if duration:
                current["duration"] = duration

            continue

        if (
            content
            and COMPANY.search(content)
            and not ACTION.match(content)
            and not is_bullet
            and len(content.split()) <= 12
        ):
            if current and current["company"]:
                finish()

            if current is None:
                current = _empty()

            current["company"] = content

            if duration:
                current["duration"] = duration

            continue

        if current:
            if duration:
                current["duration"] = duration
            if content:
                description.append(content)

    finish()
    return records
