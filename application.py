import requests
from flask import Flask, abort, jsonify, render_template, request

import assist
from catalog import load_catalog

application = Flask(__name__)
catalog = load_catalog()

SCHOOLS = {
    1: "California State University, Maritime Academy",
    7: "University of California, San Diego",
    11: "California Polytechnic State University, San Luis Obispo",
    12: "California State University, Monterey Bay",
    21: "California State University, East Bay",
    23: "California State University, San Marcos",
    24: "California State University, Stanislaus",
    26: "San Diego State University",
    29: "California State University, Fresno",
    39: "San Jose State University",
    42: "California State University, Northridge",
    46: "University of California, Riverside",
    50: "California State University, Dominguez Hills",
    60: "California State University, Sacramento",
    75: "California State Polytechnic University, Pomona",
    76: "California State University, Los Angeles",
    79: "University of California, Berkeley",
    81: "California State University, Long Beach",
    85: "California State University, San Bernardino",
    88: "Sonoma State University",
    89: "University of California, Davis",
    98: "California State University, Bakersfield",
    115: "California State Polytechnic University, Humboldt",
    116: "San Francisco State University",
    117: "University of California, Los Angeles",
    120: "University of California, Irvine",
    128: "University of California, Santa Barbara",
    129: "California State University, Fullerton",
    132: "University of California, Santa Cruz",
    141: "California State University, Chico",
    143: "California State University, Channel Islands",
    144: "University of California, Merced",
    209: "Loyola Marymount University",
    211: "Dominican University of California",
    214: "Pepperdine University",
    217: "University of the Pacific",
    222: "Palo Alto University",
    227: "Santa Clara University",
    228: "Simpson University",
}
MAX_PAIRS = 6


@application.route("/")
def home():
    schools = sorted(SCHOOLS.items(), key=lambda kv: kv[1])
    return render_template("index.html", schools=schools, subjects=catalog.subjects)


@application.route("/health")
def health():
    return "ok"


@application.route("/majors/<int:school_id>")
def majors(school_id):
    if school_id not in SCHOOLS:
        abort(404)
    try:
        return jsonify({"majors": assist.majors(school_id)})
    except requests.RequestException:
        return jsonify({"error": "ASSIST is not responding right now. Try again in a minute."}), 502


@application.route("/search", methods=["POST"])
def search():
    pairs = request.get_json(silent=True)
    if not isinstance(pairs, list) or not pairs:
        return jsonify({"error": "Pick at least one school and major."}), 400

    lookups = []
    for pair in pairs[:MAX_PAIRS]:
        school_id, major = pair.get("id"), pair.get("major")
        if school_id in SCHOOLS and major:
            lookups.append((f"{SCHOOLS[school_id]} — {major}", school_id, major))

    if not lookups:
        return jsonify({"error": "Pick at least one school and major."}), 400
    return jsonify(assist.articulations(lookups))


@application.route("/numbers/<subject>")
def numbers(subject):
    return jsonify({"numbers": catalog.numbers_for(subject)})


@application.route("/course/<subject>/<number>")
def course(subject, number):
    return jsonify(catalog.details(f"{subject} {number}"))


if __name__ == "__main__":
    application.run(debug=True)
