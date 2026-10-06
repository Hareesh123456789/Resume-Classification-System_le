"""Extract certificate names, explicit issuers, and completion years."""

import re


CERT_HEADING = re.compile(
    r"^[ \t]*(?:certifications?|certificates?|courses?(?:[ \t]+and[ \t]+certifications?)?"
    r"|training[ \t]+and[ \t]+certifications?)[ \t]*:?[ \t]*$",
    re.I | re.M,
)

OTHER_HEADING = re.compile(
    r"^[ \t]*(?:education(?:al)?(?:[ \t]+qualifications?)?"
    r"|academic[ \t]+(?:profile|background)|(?:technical[ \t]+)?skills"
    r"|(?:(?:work|professional|employment|internship)[ \t]+)?experience"
    r"|(?:academic[ \t]+)?projects?(?:[ \t]+experience)?"
    r"|achievements?|key[ \t]+achievements|career[ \t]+objective"
    r"|summary|personal[ \t]+details|declaration|languages|interests)"
    r"[ \t]*:?[ \t]*$", re.I | re.M,
)

LABEL = re.compile(
    r"^(name|certification(?:[ \t]+name)?|certificate(?:[ \t]+name)?"
    r"|course(?:[ \t]+name)?|title|organization|organisation|issuer|provider"
    r"|issued[ \t]+by|awarded[ \t]+by|year|issue[ \t]+date|issued(?:[ \t]+on)?"
    r"|completion[ \t]+date|completed)[ \t]*:[ \t]*(.*)$",
    re.I,
)

NAME_LABELS = {
    "name", "certification", "certification name", "certificate",
    "certificate name", "course", "course name", "title",
}

ORG_LABELS = {
    "organization", "organisation", "issuer", "provider",
    "issued by", "awarded by",
}

PROVIDER = re.compile(
    r"^(?:NPTEL|SWAYAM|Coursera|Udemy|edX|Microsoft|Google(?: Cloud)?"
    r"|IBM|Cisco|AWS|Amazon Web Services|Oracle|CompTIA|LinkedIn Learning"
    r"|Infosys(?: Springboard)?|freeCodeCamp|HackerRank)(?:[ \t]*[.!])?$",
    re.I,
)

ORG_WORD = re.compile(
    r"\b(?:institute|institution|university|college|school|academy|board|council)\b",
    re.I,
)

CERT_WORD = re.compile(
    r"\b(?:certified|certification|certificate|introduction|fundamentals"
    r"|essentials|specialization|specialisation|bootcamp|CCNA|CCNP|PMP"
    r"|CompTIA|IELTS|TOEFL)\b",
    re.I,
)

TOPIC = re.compile(
    r"\b(?:Python|Java|JavaScript|SQL|AWS|Azure|Linux|Excel|Scrum"
    r"|machine[ \t]+learning|artificial[ \t]+intelligence|data[ \t]+analytics)\b",
    re.I,
)

PROSE = re.compile(
    r"^(?:I|we|developed|built|achieved|seeking|responsible|worked|solved"
    r"|participated|completed[ \t]+(?:a|an|the)|no[ \t]+certifications?)\b",
    re.I,
)

YEAR = r"(?:19|20)\d{2}"

DURATION = re.compile(
    r"\([ \t]*\d+(?:\.\d+)?[ \t]*(?:weeks?|months?|hours?|days?)[ \t]*\)",
    re.I,
)

NUMBERED = re.compile(r"^[ \t]*\d{1,2}[.)](?!\d)[ \t]*")
BULLET = re.compile(r"^[ \t]*[\u2022*\-][ \t]+")

TABLE_HEADERS = {
    "name", "certificate name", "certification name", "course name",
    "organization", "organisation", "issuer", "provider", "year",
    "issue date", "completion date",
}


def _section(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")
    heading = CERT_HEADING.search(text)

    if heading:
        text = text[heading.end():]
        end = OTHER_HEADING.search(text)
        return text[:end.start()] if end else text

    return "" if OTHER_HEADING.search(text) else text


def _dates(text):
    explicit = re.findall(
        r"\b(?:issued(?:[ \t]+on)?|issue[ \t]+date|completed|completion[ \t]+date"
        r"|earned|year)[ \t]*[:=-]?[ \t]*[^;\n|]{0,40}?\b("
        + YEAR + r")\b",
        text,
        re.I,
    )

    remaining = re.sub(
        r"\b(?:expires?|expiry|expiration|valid[ \t]+(?:until|through))"
        r"[ \t]*[:=-]?[ \t]*[^;\n|]{0,40}?\b" + YEAR + r"\b",
        "",
        text,
        flags=re.I,
    )

    return set(re.findall(r"\b" + YEAR + r"\b", remaining)), set(explicit)


def _name_and_year(text):
    text = DURATION.sub("", text).strip()

    suffix = re.search(
        r"(?:\([ \t]*(" + YEAR + r")[ \t]*\)|[ \t]+("
        + YEAR + r"))[ \t]*$",
        text,
    )

    year = None

    if suffix:
        year = suffix.group(1) or suffix.group(2)
        text = text[:suffix.start()]

    name = re.sub(r"[ \t]+", " ", text).strip(" ,;-").rstrip(".")
    return name, year


def _entry(line):
    parts = [
        part.strip()
        for part in re.split(
            r"\||[ \t]+(?:-|\u2013|\u2014)[ \t]+",
            line,
        )
    ]

    first = parts[0]

    source = re.search(
        r"[ \t]+(issued by|awarded by|provided by|by|from)[ \t]+(.+)$",
        first,
        re.I,
    )

    if source:
        candidate, _ = _name_and_year(source.group(2))

        if (
            source.group(1).lower() not in ("by", "from")
            or PROVIDER.fullmatch(candidate)
            or ORG_WORD.search(candidate)
        ):
            parts.insert(1, source.group(2))
            first = first[:source.start()]

    name, year = _name_and_year(first)
    organization = None
    dates = [year] if year else []

    for part in parts[1:]:
        if re.fullmatch(r"\(?[ \t]*" + YEAR + r"[ \t]*\)?", part):
            dates.append(part)
            continue

        label = LABEL.match(part)

        if label:
            key = re.sub(r"[ \t]+", " ", label.group(1).lower())

            if key in ORG_LABELS:
                organization = label.group(2).strip() or None
            elif key not in NAME_LABELS:
                dates.append(label.group(1) + ": " + label.group(2))

            continue

        if re.match(
            r"^(?:expires?|expiry|expiration|valid[ \t]+(?:until|through))\b",
            part,
            re.I,
        ):
            continue

        org, part_year = _name_and_year(part)

        if part_year:
            dates.append(part_year)

        if not re.fullmatch(r"\(?[ \t]*" + YEAR + r"[ \t]*\)?", part):
            if _dates(part)[0] and re.match(
                r"^(?:issued|completed|earned|year)\b",
                part,
                re.I,
            ):
                dates.append(part)

            elif org and not organization:
                organization = re.sub(
                    r"[ \t]+(?:in|on)$",
                    "",
                    org,
                    flags=re.I,
                )

    return name or None, organization, dates


def _looks_name(line, listed):
    if (
        not re.search(r"[A-Za-z]", line)
        or len(line.split()) > 25
        or PROSE.match(line)
    ):
        return False

    if ORG_WORD.search(line) and not CERT_WORD.search(line):
        return False

    if CERT_WORD.search(line):
        return True

    return (
        not line.endswith((".", "!", "?"))
        and (listed or bool(TOPIC.search(line)))
    )


def extract_certifications(text):
    """Return name, organization, year dictionaries.

    Missing fields remain None. Full resumes need a certification heading.
    Clear labels and separators support arbitrary certificate and issuer names.
    """
    if not isinstance(text, str):
        raise TypeError("Certification input must be text.")

    records = []
    current = None
    years = set()
    explicit_years = set()
    last_field = None

    def start():
        return {
            "name": None,
            "organization": None,
            "year": None,
        }

    def add_dates(value):
        found, explicit = _dates(value)
        years.update(found)
        explicit_years.update(explicit)

    def finish():
        nonlocal current, years, explicit_years, last_field

        if current:
            choices = explicit_years or years
            current["year"] = (
                next(iter(choices)) if len(choices) == 1 else None
            )

            if any(current.values()) and current not in records:
                records.append(current)

        current = None
        years = set()
        explicit_years = set()
        last_field = None

    for raw in _section(text).splitlines():
        listed = bool(NUMBERED.match(raw) or BULLET.match(raw))
        line = BULLET.sub("", NUMBERED.sub("", raw)).strip()

        if not line or CERT_HEADING.fullmatch(line):
            continue

        cells = [part.strip().lower() for part in line.split("|")]

        if all(cell in TABLE_HEADERS for cell in cells):
            continue

        label = LABEL.match(line)

        if label:
            key = re.sub(r"[ \t]+", " ", label.group(1).lower())
            value = label.group(2).strip()

            if key in NAME_LABELS:
                if current and current["name"]:
                    finish()

                if current is None:
                    current = start()

                current["name"], org, dates = _entry(value)

                if org:
                    current["organization"] = org

                for date in dates:
                    add_dates(date)

                last_field = "name"

            elif key in ORG_LABELS:
                if current is None:
                    current = start()

                current["organization"] = value or None
                last_field = "organization"

            else:
                if current is None:
                    current = start()

                add_dates(key + ": " + value)
                last_field = "year"

            continue

        if re.match(
            r"^(?:expires?|expiry|expiration|valid[ \t]+(?:until|through)"
            r"|credential[ \t]+(?:id|url)|https?://)\b",
            line,
            re.I,
        ):
            continue

        if current and PROVIDER.fullmatch(line):
            current["organization"] = line.rstrip(".!")
            last_field = "organization"
            continue

        if current and _dates(line)[0] and not _looks_name(line, listed):
            add_dates(line)
            last_field = "year"
            continue

        if (
            current
            and last_field == "organization"
            and not listed
            and not _looks_name(line, False)
            and not line.endswith((".", "!", "?"))
        ):
            current["organization"] = (
                (current["organization"] or "") + " " + line
            ).strip()
            continue

        if ORG_WORD.search(line) and not CERT_WORD.search(line):
            last_field = None
            continue

        if (
            current
            and current["name"]
            and last_field == "name"
            and not listed
            and re.search(
                r"\b(?:to|of|in|and|for|with|artificial|machine"
                r"|data|computer|cloud)$",
                current["name"],
                re.I,
            )
        ):
            continuation, year = _name_and_year(line)
            current["name"] += " " + continuation

            if year:
                add_dates(year)

            continue

        if _looks_name(line, listed):
            finish()
            current = start()
            current["name"], current["organization"], dates = _entry(line)

            for date in dates:
                add_dates(date)

            last_field = "name"

    finish()
    return records
