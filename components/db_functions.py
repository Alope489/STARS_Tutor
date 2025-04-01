import streamlit as st
from pymongo import MongoClient

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
    courses = list(course_collection.find({},{"course_name":1,"course_id":1,"_id":0}))
    return courses
def get_user_courses(user_id):
        user_doc = users_collection.find_one({'panther_id':user_id})
        user_courses = user_doc.get("courses", [])
        return user_courses

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

def parse_courses(courses):
    #this is to be used in course upload, receving a course array, need to filter out those inside the course collection
    tutored_courses = course_collection.find({
        'course_id' : {"$in":courses}
    })
    return list(tutored_courses)

def get_pending_students():
    students = list(users_collection.find({"user_type":"student","status": "pending_approval"}))
    return students

def get_enrolled_students():
    students = list(users_collection.find({"user_type":"student","status":"approved"}))
    return students
def get_pending_tutors():
    pending_tutors = list(users_collection.find({"user_type":"tutor","status":"pending_approval"}))
    return pending_tutors

def get_enrolled_tutors():
    enrolled_tutors = list(users_collection.find({"user_type":"tutor","status":"approved"}))
    return enrolled_tutors
def find_token():
    token = list(tokens.find())
    return token[0]

def remove_token():
    tokens.delete_many({})
