import streamlit as st
from pypdf import PdfReader
from pymongo import MongoClient
import re 
import json

mongo_uri = "mongodb://localhost:27017/"
client = MongoClient(mongo_uri)
coursedb = client['courses']
course_collection = coursedb['course_list']

db = client["user_data"]
users_collection = db["users"]
tokens = db['tokens']

if 'courses_valid' not in st.session_state: 
    st.session_state.courses_valid = False
def get_courses():
    courses = list(course_collection.find({}))
    return courses
def get_course_names(course_ids):
    courses = list(course_collection.find({"course_id":{"$in":course_ids}},{"course_name":1,"_id":0}))
    course_names = [course['course_name']for course in courses]
    return course_names
def add_courses_to_student(panther_id,course_ids):
    print('adding courses to student')
    users_collection.update_one({"panther_id":panther_id}, #query
                                {"$push":{"courses":{"$each":course_ids}},
                                 "$set":{"status":"pending_approval"}
                                 }, #update
                                )
    st.success('Course information successfully uploaded')
    st.session_state.status='pending_approval'
def get_enrolled_students():
    students = list(users_collection.find({"status":"approved"}))
    return students
def parse_courses(courses):
    #this is to be used in course upload, receving a course array, need to filter out those inside the course collection
    tutored_courses = course_collection.find({
        'course_id' : {"$in":courses}
    })
    return list(tutored_courses)

def get_pending_students():
    students = list(users_collection.find({"status": "pending_approval"}))
    return students

def course_upload():
    st.write('Provide PDF of your current courses. This will be found under MyFIU, Manage Classes, View Class Schedule. Then, Click where it says Print Schedule and Download the File.')
    st.image('components\images\FIU Schedule.png')
    #first check, is to ensure its a pdf
    try:
        file = st.file_uploader("Choose a file")
        if file:
            reader = PdfReader(file)
            last_page  = reader.pages[-1]
            text = last_page.extract_text()
            # seconc check text should contain : 'Schedule of Classes', else provide an error message
            if 'Schedule of Classes' in text:
                pattern = r'[A-Z]{3}-\d{4}'
                courses = re.findall(pattern,text)
                # third check student should be taking at least 1 course, else provide error message
                if courses:
                   #fourth check student courses need to be inside courses database.
                   tutored_courses = parse_courses(courses)
                   #use this to test
                   tutored_courses =  ['CAP-2752','ABC-123','DEF-456']
                   if tutored_courses:
                       
                       st.session_state.courses_valid = True
                       st.info(f'These are the courses we are currently tutoring:  \n\n {" | ".join(tutored_courses)}')
                       return tutored_courses
                   else:
                       st.error('We are not offering tutoring for these courses and do not have bots available')
                       
                    
                else:
                    st.error('You must be enrolled in at least 1 course to access our service.')
                
            else:
                st.error('Please Provide PDF of your class schedule. Go to MyFIU, Manage Classes, View Class schedule. Then, you will click on print schedule and download the file.')
    except Exception as e:
        st.error('Please Provide PDF of your class schedule. Go to MyFIU, Manage Classes, View Class schedule. Then, you will click on print schedule and download the file. ')
