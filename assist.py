import json
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import requests

API_ROOT = "https://assist.org/api"
EVC_ID = 2
CACHE_TTL = 6 * 60 * 60
FALLBACK_YEARS = [76, 75, 74]

log = logging.getLogger(__name__)
_session = requests.Session()
_cache = {}
_cache_lock = threading.Lock()


def _get(path, **params):
    resp = _session.get(f"{API_ROOT}/{path}", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _cached(key, loader):
    now = time.time()
    with _cache_lock:
        hit = _cache.get(key)
        if hit and now - hit[0] < CACHE_TTL:
            return hit[1]
    value = loader()
    with _cache_lock:
        _cache[key] = (now, value)
    return value


def academic_years():
    def load():
        try:
            years = _get("AcademicYears")
            ids = sorted((y.get("Id") or y.get("id") for y in years), reverse=True)
            return [i for i in ids if i][:3] or FALLBACK_YEARS
        except (requests.RequestException, ValueError, AttributeError) as exc:
            log.warning("academic years lookup failed: %s", exc)
            return FALLBACK_YEARS

    return _cached("years", load)


def agreements(school_id):
    def load():
        error = None
        for year in academic_years():
            try:
                data = _get(
                    "agreements",
                    receivingInstitutionId=school_id,
                    sendingInstitutionId=EVC_ID,
                    academicYearId=year,
                    categoryCode="major",
                )
            except requests.RequestException as exc:
                log.warning("agreements school=%s year=%s failed: %s", school_id, year, exc)
                error = exc
                continue
            reports = data.get("reports") or []
            if reports:
                return {r["label"]: r["key"] for r in reports}
        if error:
            raise error
        return {}

    return _cached(("agreements", school_id), load)


def majors(school_id):
    return list(agreements(school_id))


def _course(c, conj=""):
    return (c.get("prefix") or "", c.get("courseNumber") or "", c.get("courseTitle") or "", conj or "")


def _receiving(art):
    if "course" in art:
        return [[_course(art["course"])]]
    if "series" in art:
        series = art["series"]
        return [[_course(c, series.get("conjunction")) for c in series.get("courses", [])]]
    if "requirement" in art:
        return [[("", "", art["requirement"].get("name", ""), "")]]
    return []


def _sending(art):
    block = art.get("sendingArticulation") or {}
    groups = block.get("items") or []
    if not groups:
        reason = block.get("noArticulationReason") or "No course articulated"
        return [("", "", reason, "")]

    group_conjs = block.get("courseGroupConjunctions") or []
    group_conj = group_conjs[0].get("groupConjunction", "") if group_conjs else ""

    if group_conj:
        out = []
        for group in groups:
            items = group.get("items") or []
            if len(items) == 1:
                out.append(_course(items[0], group_conj))
            else:
                conj = group.get("courseConjunction") or ""
                out.extend(_course(i, conj + group_conj) for i in items)
        return out

    if len(groups) > 1:
        conj = groups[0].get("courseConjunction", "")
        return [_course(g["items"][0], conj) for g in groups if g.get("items")]

    items = groups[0].get("items") or []
    conj = groups[0].get("courseConjunction", "") if len(items) > 1 else ""
    return [_course(i, conj) for i in items]


def articulation(school_id, major):
    key = agreements(school_id).get(major)
    if not key:
        return [], []

    def load():
        result = _get("articulation/Agreements", Key=key).get("result") or {}
        raw = result.get("articulations") or "[]"
        rows = json.loads(raw) if isinstance(raw, str) else raw
        receiving, sending = [], []
        for row in rows:
            art = row.get("articulation") or {}
            receiving.append(_receiving(art))
            sending.append(_sending(art))
        return receiving, sending

    return _cached(("articulation", key), load)


def articulations(requests_):
    def run(item):
        label, school_id, major = item
        try:
            return label, articulation(school_id, major)
        except (requests.RequestException, ValueError, KeyError) as exc:
            log.warning("articulation %s failed: %s", label, exc)
            return label, {"error": str(exc)}

    with ThreadPoolExecutor(max_workers=4) as pool:
        return dict(pool.map(run, requests_))
