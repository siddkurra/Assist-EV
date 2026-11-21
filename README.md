# Assist-EV

Transfer planning for students at Evergreen Valley College (EVC). You pick the UC/CSU/private schools and majors you're considering, Assist-EV pulls the official articulation agreements from ASSIST.org, and then lets you lay the EVC courses out term by term.

## Status: shut down

The hosted version (formerly at assist-ev.us-west-2.elasticbeanstalk.com) has been taken offline.

ASSIST.org changed how its API accepts requests. The site's own frontend now gets an anti-forgery token (`X-XSRF-TOKEN`) and sends it back with every call, and requests without it are refused with `400 Bad Request`. Every endpoint this project depends on (`AcademicYears`, `agreements`, `articulation/Agreements`) is affected. Assist-EV was built on plain unauthenticated requests to those endpoints, so school and major lookups, and the planner that depends on them, stopped working.

We could have copied the token from ASSIST's own frontend. We decided not to: ASSIST never offered this API to third parties, and the token reads as a deliberate choice to keep it that way. Without sanctioned access, the service shouldn't run in public.

The code stays here as a record of the approach. The schedule parser, the articulation normalization, and the planner are independent of how the data is fetched, so if ASSIST ever offers sanctioned access, only `assist.py` needs to change.

## Motivation

ASSIST.org is the authoritative source for which community college courses transfer, but it answers one question at a time: one sending college, one receiving school, one major. A student who is applying to, say, five campuses ends up with five tabs and a spreadsheet trying to find the overlap. The overlap is the actual decision, since a course that satisfies requirements at four of those schools is worth more than one that satisfies one.

Assist-EV collapses that into a single view. Search several school/major pairs at once, see every requirement side by side, and the EVC courses that satisfy them get collected into one list you can schedule.

## How it works

There are three pieces.

**1. ASSIST's API (`assist.py`).** ASSIST doesn't publish a developer API. The site itself runs on a JSON API, and this client was written against it. Getting an agreement takes two calls:

- `GET /api/agreements?receivingInstitutionId=…&sendingInstitutionId=2&academicYearId=…&categoryCode=major` returns the majors a school has on file with EVC (institution `2`), each with a `key`.
- `GET /api/articulation/Agreements?Key=…` returns the agreement. The `articulations` field is itself a JSON string, so it gets decoded twice.

Academic year IDs are years since 1950 (2025–26 is `76`). An earlier version hardcoded `74`, which quietly served 2023–24 agreements. The client now reads `/api/AcademicYears` and walks back from the newest year until it finds one the school has actually published, since UCs and CSUs post new agreements at different times. Each year is tried independently, so a year that errors out is logged and skipped rather than failing the whole lookup.

Each articulation row has a receiving side (a single course, a series that must be taken together, or a general requirement) and a sending side (EVC courses joined by `And`/`Or`, possibly in multiple groups, or a reason there's no match). Both get normalized into `(prefix, number, title, conjunction)` tuples so the frontend only deals with one shape. Responses are cached in memory for six hours and multi-school searches run in parallel, which matters because ASSIST is slow and the old version slept between requests.

**2. The EVC schedule (`catalog.py`).** `data/courses.csv` is a scrape of the Fall 2025 schedule, one row per meeting line. The raw lines are fixed-width-ish text (`126755 202 38 7 Lec W 12:15 PM—02:05 PM 08/25/25— 12/11/25 LE209 Barta, Melody`), with a few irregularities: missing CRNs on continuation lines, no space between the time and the date on some rows, live-online `Slec`/`Slab` sections, and tutoring/work-experience rows with no meeting time. A single regex handles all 1,164 rows. This powers the subject/number dropdowns and the hover popups (formats, instructors, meeting times).

**3. The planner (`static/js/app.js`).** Plain JavaScript, no framework. After a search, every articulated EVC course goes into your plan. Courses are draggable into Fall, Spring, and Summer columns, across as many academic years as you add. A scheduled course leaves the list and comes back when you drag it back or hit ×. Clicking a green course in the results toggles it in and out of the plan.

## Project layout

```
application.py       Flask routes
assist.py            ASSIST API client, normalization, caching
catalog.py           EVC schedule parsing
data/courses.csv     Fall 2025 EVC schedule
templates/index.html
static/js/app.js     search, planner, drag and drop
static/css/app.css
.ebextensions/       Elastic Beanstalk instance config
```

## API

| Route | Returns |
|---|---|
| `GET /majors/<school_id>` | majors with an EVC agreement |
| `POST /search` | articulations for up to six `{id, major}` pairs |
| `GET /numbers/<subject>` | course numbers offered under a subject |
| `GET /course/<subject>/<number>` | sections, formats, instructors |
| `GET /health` | `ok` |

## Running locally

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python application.py
```

Then open http://127.0.0.1:5000. Lookups will fail with ASSIST's current API (see [Status](#status-shut-down)); the page itself loads.

## Deployment

This describes how it ran before the shutdown. Elastic Beanstalk, Python 3.13 on Amazon Linux 2023, single instance (no load balancer) on a `t4g.small`. The app is mostly I/O-bound waiting on ASSIST, so gunicorn runs 2 workers × 4 threads, and nginx serves `/static` directly. Pandas was dropped in favor of the standard `csv` module to keep memory low on the small instance.

```bash
eb create assist-ev-env --single -i t4g.small --cname assist-ev
eb deploy
```

## Limitations

- ASSIST's API is undocumented and was never meant for outside clients. That made the project fragile from the start, and it is what ended it.
- The schedule is a Fall 2025 snapshot. Moving it to S3 so it can be refreshed without redeploying is next.
- The plan lives in the page. Refreshing clears it.
- Sending college is fixed to EVC.

None of this replaces a counselor. Always confirm against ASSIST.org and your target school before you enroll.

## Prior work

These were useful for understanding how ASSIST structures its data:

- [ebowwa/ccc_transfers](https://github.com/ebowwa/ccc_transfers): documents the `agreements` endpoint, institution IDs, and the year-ID convention.
- [oshaw/assist-flowchart](https://github.com/oshaw/assist-flowchart): parses agreements into course flowcharts, including series handling.

## Team

Built by Siddharth Kurra, Saumya Goswami, and the Assist-EV team. An independent project, not affiliated with Evergreen Valley College or ASSIST.org.
