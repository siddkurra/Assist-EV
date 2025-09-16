import json
import urllib.request
import time

def major_getter(s_id):
    majors = []
    with urllib.request.urlopen(f'https://assist.org/api/agreements?receivingInstitutionId={s_id}&sendingInstitutionId=2&academicYearId=74&categoryCode=major') as url:
        temp = json.loads(url.read().decode())
        reports = temp['reports']
        for report in reports:
            majors.append(report['label'])
    return majors


class JSONprocesser:
    def __init__(self, school_id, major):
        self.school_id = school_id
        self.major = major

    def key_getter(self):
        with urllib.request.urlopen(f'https://assist.org/api/agreements?receivingInstitutionId={self.school_id}&sendingInstitutionId=2&academicYearId=74&categoryCode=major') as url:
            temp = json.loads(url.read().decode())
        reports = temp['reports']
        for report in reports:
            if self.major == report['label']:
                return report['key']


    def data_getter(self):
        key = self.key_getter()
        try:
            with urllib.request.urlopen(f'https://assist.org/api/articulation/Agreements?Key={key}') as url:
                temp = json.loads(url.read().decode())
                articulations_str = temp["result"].get("articulations")
                articulations = json.loads(articulations_str)
                courses = []
                s_courses = []
                for articulation in articulations:
                    t = articulation['articulation']
                    course_info = []
                    if 'course' in t:
                        r = t['course']
                        #course_info = r.get("prefix") + "-" + r.get("courseNumber") + ": " + r.get("courseTitle") + "\n"
                        course_info.append([(r.get("prefix"), r.get("courseNumber"), r.get("courseTitle"), '')])
                    elif 'series' in t:
                        r = t['series']
                        conj = r['conjunction']
                        temp = []
                        for c in r['courses']:
                            #course_info += c.get("prefix") + "-" + c.get("courseNumber") + ": " + c.get("courseTitle") + f" ({conj}) \n"
                            temp.append((c.get("prefix"), c.get("courseNumber"), c.get("courseTitle"), conj))
                        course_info.append(temp)
                    elif 'requirement' in t:
                        #course_info += t['requirement']['name']
                        course_info.append(('','',t['requirement']['name'],''))
                    courses.append(course_info)

                    sending_info = []
                    if len(t['sendingArticulation']['courseGroupConjunctions']) != 0:
                        temp = t['sendingArticulation']['courseGroupConjunctions'][0]
                    else:
                        temp = {'na': 'temp'}

                    if len(t['sendingArticulation']['items']) == 0:
                        #sending_info = t['sendingArticulation']['noArticulationReason']
                        sending_info.append(('','',t['sendingArticulation']['noArticulationReason'],''))
                    elif 'groupConjunction' in temp:
                        conjun = t['sendingArticulation']['courseGroupConjunctions'][0]['groupConjunction']
                        for item in t['sendingArticulation']['items']:
                            if len(item['items']) == 1:
                                s = item['items'][0]
                                #sending_info += s.get("prefix") + "-" + s.get("courseNumber") + ": " + s.get("courseTitle")
                                sending_info.append((s.get("prefix"), s.get("courseNumber"), s.get("courseTitle"), conjun))
                            elif len(item['items']) > 1:
                                for i in item['items']:
                                    conj = i['courseConjunction']
                                    #sending_info += i.get("prefix") + "-" + i.get("courseNumber") + ": " + i.get("courseTitle") + f" ({conj})"
                                    sending_info.append((i.get("prefix"), i.get("courseNumber"), i.get("courseTitle"), conj + conjun))
                            #sending_info += f'\t{conjun} \n'
                    elif len(t['sendingArticulation']['items']) > 1:
                        conj = t['sendingArticulation']['items'][0]['courseConjunction']
                        for i in t['sendingArticulation']['items']:
                            item = i['items'][0]
                            #sending_info += item.get("prefix") + "-" + item.get("courseNumber") + ": " + item.get("courseTitle") + f" ({conj}) \n"
                            sending_info.append((item.get("prefix"), item.get("courseNumber"), item.get("courseTitle"), conj))
                    elif len(t['sendingArticulation']['items'][0]['items']) == 1:
                        s = t['sendingArticulation']['items'][0]['items'][0]
                        #sending_info = s.get("prefix") + "-" + s.get("courseNumber") + ": " + s.get("courseTitle") + "\n"
                        sending_info.append((s.get("prefix"), s.get("courseNumber"), s.get("courseTitle"), ''))
                    elif len(t['sendingArticulation']['items'][0]['items']) > 1:
                        conj = t['sendingArticulation']['items'][0]['courseConjunction']
                        for item in t['sendingArticulation']['items'][0]['items']:
                            #sending_info += item.get("prefix") + "-" + item.get("courseNumber") + ": " + item.get("courseTitle") + f" ({conj}) \n"
                            sending_info.append((item.get("prefix"), item.get("courseNumber"), item.get("courseTitle"), conj))
                    s_courses.append(sending_info)

                    #template =
            #pprint.pprint(courses)
            #pprint.pprint(s_courses)
            return courses, s_courses
        except Exception as e:
            print(e)
            #pprint.pprint(t)

class JSONbase:
    def __init__(self, data):
        self.data = data

    def json_dict_maker(self):
        course_dict = {}
        for d in self.data:
            time.sleep(0.2)
            sid, major, name = d
            datar = JSONprocesser(sid, major)
            articulations = datar.data_getter()
            course_dict[name] = articulations
        return course_dict

