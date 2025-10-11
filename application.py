from flask import Flask, render_template, request, jsonify
from backend import major_getter, JSONbase
import pandas as pd
import os

application = Flask(__name__)

# --- Load and Process Courses CSV ---
csv_path = os.path.join(os.path.dirname(__file__), "data", "courses.csv")
course_df = pd.read_csv(csv_path)
course_list = sorted(course_df["Course Title"].dropna().unique())

abbrv_number_map = {}
for item in course_list:
    parts = str(item).split(" ", 1)
    if len(parts) == 2:
        abbrv, number = parts
        abbrv_number_map.setdefault(abbrv.upper(), []).append(number)

# Sort numbers for each abbreviation
for abbrv in abbrv_number_map:
    abbrv_number_map[abbrv] = sorted(abbrv_number_map[abbrv])

abbrv_list = sorted(list(abbrv_number_map.keys()))

# --- School map ---
school_map = {
    1: "California State University, Maritime Academya",
    7: "University of California, San Diego",
    11: "California Polytechnic University, San Luis Obispo",
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
    75: "California Polytechnic University, Pomona",
    76: "California State University, Los Angeles",
    79: "University of California, Berkeley",
    81: "California State University, Long Beach",
    85: "California State University, San Bernardino",
    88: "Sonoma State University",
    89: "University of California, Davis",
    98: "California State University, Bakersfield",
    115: "California Polytechnic University, Humboldt",
    116: "San Francisco State University",
    117: "University of California, Los Angeles",
    120: "University of California, Irvine",
    128: "University of California, Santa Barbara",
    129: "California State University, Fullerton",
    132: "University of California, Santa Cruz",
    141: "California State University, Chico",
    143: "California State University, Channel Islands",
    144: "University of California, Merced",
    211: "Dominican University of California",
    217: "University of the Pacific",
    222: "Palo Alto University",
    227: "Santa Clara University",
    228: "Simpson University",
    209: "Loyola Marymount University",
    214: "Pepperdine University"
}

# --- Routes ---
@application.route("/")
def home():
    # pass the list of abbreviations to the template (numbers requested dynamically)
    return render_template("index.html", schools=school_map, abbrvs=abbrv_list)

@application.route("/majors/<int:school_id>")
def majors(school_id):
    try:
        majors = major_getter(school_id)
        return jsonify({"majors": majors})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@application.route("/search", methods=["POST"])
def search():
    data = request.json  # [{"id": school_id, "major": "..."}, ...]
    processed_data = [(d["id"], d["major"], f"{school_map[d['id']]} — {d['major']}") for d in data]
    jb = JSONbase(processed_data)
    course_dict = jb.json_dict_maker()
    return jsonify(course_dict)

@application.route("/get_numbers/<abbrv>")
def get_numbers(abbrv):
    numbers = abbrv_number_map.get(abbrv.upper(), [])
    return jsonify({"numbers": numbers})

if __name__ == "__main__":
    application.run(debug=True)
