from flask import Flask, render_template, request, jsonify
from backend import major_getter, JSONbase  # import your existing logic

application = Flask(__name__)

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

@application.route("/")
def home():
    return render_template("index.html", schools=school_map)

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

if __name__ == "__main__":
    application.run(debug=True)
