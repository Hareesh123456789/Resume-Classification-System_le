"""Extract projects using text rules and explicit technology mentions."""

import re


PROJECT_HEADING = re.compile(
    r"^[ \t]*(?:(?:academic|personal|major|mini|key)[ \t]+)?"
    r"projects?(?:[ \t]+(?:experience|details|work))?[ \t]*:?[ \t]*$",
    re.I | re.M,
)

OTHER_HEADING = re.compile(
    r"^[ \t]*(?:education(?:al)?(?:[ \t]+qualifications?)?"
    r"|academic[ \t]+(?:profile|background)|(?:technical[ \t]+)?skills"
    r"|(?:(?:work|professional|employment|internship)[ \t]+)?experience"
    r"|employment[ \t]+history|work[ \t]+history|internships?"
    r"|certifications?|achievements?|key[ \t]+achievements"
    r"|career[ \t]+objective|summary|personal[ \t]+details"
    r"|declaration|languages|interests)[ \t]*:?[ \t]*$",
    re.I | re.M,
)

TITLE_LABEL = re.compile(
    r"^(?:project(?:[ \t]+(?:title|name|\d+))?|title)[ \t]*:[ \t]*(.*)$",
    re.I,
)

TECH_LABEL = re.compile(
    r"^(?:technolog(?:y|ies)(?:[ \t]+used)?|tech(?:nology)?[ \t]+stack"
    r"|tools(?:[ \t]+used)?|languages|frameworks)[ \t]*:[ \t]*(.*)$",
    re.I,
)

DESCRIPTION_LABEL = re.compile(
    r"^(?:description|summary)[ \t]*:[ \t]*(.*)$",
    re.I,
)

ACTION = re.compile(
    r"^(?:developed|built|created|designed|implemented|achieved|improved"
    r"|used|utilized|worked|integrated|trained|tested|deployed|provides"
    r"|supports|detects|predicts|automated|maintained|responsible)\b",
    re.I,
)

NO_PROJECTS = re.compile(
    r"^(?:none|nil|n/?a|no projects?(?: yet)?)[.!]?$",
    re.I,
)

NUMBERED = re.compile(r"^[ \t]*\d{1,2}[.)](?!\d)[ \t]*")
BULLET = re.compile(r"^[ \t]*[\u2022*\-][ \t]+")

TECH_ALIASES = {
    "Python": ("Python",),
    "JavaScript": ("JavaScript", "Java Script", "JS"),
    "TypeScript": ("TypeScript", "TS"),
    "Java": ("Java",),
    "C++": ("C++",),
    "C#": ("C#",),
    "PHP": ("PHP",),
    "Dart": ("Dart",),
    "Kotlin": ("Kotlin",),
    "Rust": ("Rust",),
    "HTML": ("HTML", "HTML5"),
    "CSS": ("CSS", "CSS3"),
    "SQL": ("SQL",),
    "Django": ("Django",),
    "Flask": ("Flask",),
    "FastAPI": ("FastAPI",),
    "React Native": ("React Native",),
    "React": ("React", "React.js", "ReactJS"),
    "Node.js": ("Node.js", "NodeJS", "Node JS"),
    "Express": ("Express", "Express.js", "ExpressJS"),
    "Angular": ("Angular",),
    "Vue.js": ("Vue.js", "VueJS"),
    "Flutter": ("Flutter",),
    "Spring Boot": ("Spring Boot",),
    "ASP.NET Core": ("ASP.NET Core",),
    "ASP.NET": ("ASP.NET",),
    ".NET": (".NET",),
    "Bootstrap": ("Bootstrap",),
    "Tailwind CSS": ("Tailwind CSS",),
    "MySQL": ("MySQL",),
    "PostgreSQL": ("PostgreSQL", "Postgres"),
    "SQLite": ("SQLite",),
    "MongoDB": ("MongoDB",),
    "Firebase": ("Firebase",),
    "Redis": ("Redis",),
    "Oracle": ("Oracle",),
    "TensorFlow": ("TensorFlow",),
    "PyTorch": ("PyTorch",),
    "Keras": ("Keras",),
    "scikit-learn": ("scikit-learn", "sklearn"),
    "OpenCV": ("OpenCV",),
    "NumPy": ("NumPy",),
    "Pandas": ("Pandas",),
    "Docker": ("Docker",),
    "Kubernetes": ("Kubernetes",),
    "AWS": ("AWS", "Amazon Web Services"),
    "Azure": ("Azure",),
    "Git": ("Git",),
}

TECH_PATTERNS = [
    (name, re.compile(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", re.I))
    for name, aliases in TECH_ALIASES.items()
    for alias in aliases
]


def _section(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")
    heading = PROJECT_HEADING.search(text)

    if heading:
        text = text[heading.end():]
        end = OTHER_HEADING.search(text)
        return text[:end.start()] if end else text

    return "" if OTHER_HEADING.search(text) else text


def _known_technologies(text):
    text = re.sub(r"https?://\S+", "", text, flags=re.I)

    matches = [
        (match.start(), match.end(), name)
        for name, pattern in TECH_PATTERNS
        for match in pattern.finditer(text)
    ]

    selected = []

    for start, end, name in sorted(
        matches,
        key=lambda item: (item[0] - item[1], item[0]),
    ):
        if not any(
            start < old_end and end > old_start
            for old_start, old_end, _ in selected
        ):
            selected.append((start, end, name))

    return [name for _, _, name in sorted(selected)]


def _listed_technologies(text):
    values = []

    for part in re.split(
        r"[,;|]|\s+(?:and|/|&)\s+",
        text,
        flags=re.I,
    ):
        part = part.strip().rstrip(".")

        if part:
            values.extend(_known_technologies(part) or [part])

    return values


def _looks_title(text):
    return (
        bool(re.search(r"[A-Za-z]", text))
        and len(text.split()) <= 18
        and not text.endswith((".", "!", "?", ";"))
        and not ACTION.match(text)
        and not re.match(
            r"(?:https?://|github\s*:|link\s*:|duration\s*:)",
            text,
            re.I,
        )
    )


def _title(text):
    left, separator, right = text.partition("|")
    label = TECH_LABEL.match(right.strip())

    if separator and (label or _known_technologies(right)):
        technologies = _listed_technologies(
            label.group(1) if label else right
        )
        return left.strip(" :"), technologies

    return text.strip(" :"), []


def extract_projects(text):
    """Return dictionaries with title, technologies, and description.

    Accept a project section or a full resume with a project heading.
    Unusual layouts may need explicit labels or layout-aware parsing.
    """
    if not isinstance(text, str):
        raise TypeError("Project input must be text.")

    records = []
    current = None
    descriptions = []
    gap = False

    def start():
        return {
            "title": None,
            "technologies": [],
            "description": None,
        }

    def add_technologies(values):
        seen = {
            value.casefold()
            for value in current["technologies"]
        }

        for value in values:
            if value.casefold() not in seen:
                current["technologies"].append(value)
                seen.add(value.casefold())

    def finish():
        nonlocal current, descriptions

        if current:
            current["description"] = (
                "\n".join(descriptions).strip() or None
            )

            if any(current.values()) and current not in records:
                records.append(current)

        current = None
        descriptions = []

    for raw in _section(text).splitlines():
        if not raw.strip():
            gap = True
            continue

        numbered = bool(NUMBERED.match(raw))
        bullet = bool(BULLET.match(raw))
        line = BULLET.sub("", NUMBERED.sub("", raw)).strip()

        if (
            not line
            or PROJECT_HEADING.fullmatch(line)
            or NO_PROJECTS.fullmatch(line)
        ):
            continue

        title_label = TITLE_LABEL.match(line)
        tech_label = TECH_LABEL.match(line)
        description_label = DESCRIPTION_LABEL.match(line)

        if title_label:
            finish()
            current = start()

            current["title"], technologies = _title(
                title_label.group(1)
            )
            current["title"] = current["title"] or None

            add_technologies(
                _known_technologies(current["title"] or "")
                + technologies
            )

        elif tech_label:
            if current is None:
                current = start()

            add_technologies(
                _listed_technologies(tech_label.group(1))
            )

        elif description_label:
            if current is None:
                current = start()

            value = description_label.group(1).strip()

            if value:
                descriptions.append(value)
                add_technologies(_known_technologies(value))

        else:
            title_like = _looks_title(line)

            if current is None:
                current = start()

            if title_like and not current["title"] and not descriptions:
                current["title"], technologies = _title(line)
                add_technologies(technologies)

            elif (
                title_like
                and current["title"]
                and not descriptions
                and not gap
                and re.match(
                    r"^(?:using|with|and|for|through)\b",
                    line,
                    re.I,
                )
            ):
                current["title"] += " " + line

            elif title_like and (
                numbered or (not bullet and (gap or descriptions))
            ):
                finish()
                current = start()
                current["title"], technologies = _title(line)
                add_technologies(technologies)

            else:
                descriptions.append(line)

            add_technologies(_known_technologies(line))

        gap = False

    finish()
    return records
