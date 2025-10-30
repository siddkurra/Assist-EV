import csv
import re
from collections import defaultdict
from pathlib import Path

SECTION_RE = re.compile(
    r"^(?:(?P<crn>\d{6})\s+)?"
    r"(?P<section>\d{3})\s+\d+\s+\d+\s+"
    r"(?:(?P<kind>Slec|Slab|Lec|Lab|IO|IH|WE|Tutoring)\s+)?"
    r"(?:(?P<days>[MTWHFSU]+)\s+(?P<start>\d\d:\d\d [AP]M)\s*—\s*(?P<end>\d\d:\d\d [AP]M)\s*)?"
    r"(?P<first>\d\d/\d\d/\d\d)\s*—\s*(?P<last>\d\d/\d\d/\d\d)"
    r"(?P<rest>.*)$"
)
INSTRUCTOR_RE = re.compile(r"(?:^|\s)([A-Z][\w'.-]*,\s*[\w'.-]*)\s*$")

KINDS = {
    "Lec": "Lecture",
    "Lab": "Lab",
    "Slec": "Live online lecture",
    "Slab": "Live online lab",
    "IO": "Online",
    "IH": "Hybrid",
    "WE": "Work experience",
    "Tutoring": "Tutoring",
}
ASYNC_KINDS = {"IO", "IH"}


def parse_section(raw):
    m = SECTION_RE.match(raw.strip())
    if not m:
        return None

    rest = m["rest"].strip()
    instructor = ""
    found = INSTRUCTOR_RE.search(rest)
    if found:
        instructor = found.group(1).rstrip(", ").strip()
        rest = rest[: found.start()].strip()

    if m["days"]:
        meets = f"{m['days']} {m['start']}–{m['end']}"
    else:
        meets = "Asynchronous" if m["kind"] in ASYNC_KINDS else "By arrangement"
    return {
        "crn": m["crn"] or "",
        "section": m["section"],
        "format": KINDS.get(m["kind"], "Other"),
        "meets": meets,
        "dates": f"{m['first']} – {m['last']}",
        "room": rest or "TBA",
        "instructor": instructor or "Staff",
    }


class Catalog:
    def __init__(self, path):
        self.sections = defaultdict(list)
        self.numbers = defaultdict(set)

        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                code = (row.get("Course Title") or "").strip()
                subject, _, number = code.partition(" ")
                if not number:
                    continue
                code = f"{subject.upper()} {number}"
                self.numbers[subject.upper()].add(number)
                section = parse_section(row.get("Raw Line") or "")
                if section:
                    self.sections[code].append(section)

    @property
    def subjects(self):
        return sorted(self.numbers)

    def numbers_for(self, subject):
        return sorted(self.numbers.get(subject.upper(), ()))

    def details(self, code):
        sections = self.sections.get(code.upper(), [])
        return {
            "course": code.upper(),
            "offered": bool(sections),
            "sections": sections,
            "formats": sorted({s["format"] for s in sections}),
            "instructors": sorted({s["instructor"] for s in sections if s["instructor"] != "Staff"}),
        }


def load_catalog():
    return Catalog(Path(__file__).parent / "data" / "courses.csv")
