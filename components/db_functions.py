import streamlit as st
from pymongo import MongoClient
from datetime import datetime,date


mongo_uri = "mongodb://localhost:27017/"
client = MongoClient(mongo_uri)
coursedb = client['courses']
course_collection = coursedb['course_list']

db = client["user_data"]
users_collection = db["users"]
tokens = db['tokens']
archival_date = db['archival_date']

if 'courses_valid' not in st.session_state: 
    st.session_state.courses_valid = False

def set_archive_date(set_date):
    #set_date is a date object but we need to make it datetime. Just add a time field with the minimum time 0:0:0 at midnight
    if isinstance(set_date,date):
        set_date = datetime.combine(set_date,datetime.min.time())
    archival_date.update_one({},{"$set":{"archival_date":set_date}})
def get_archive_date():
    archive_date = list(archival_date.find({}))
    return archive_date
def get_courses():
    courses = list(course_collection.find({},{"course_name":1,"course_id":1,"_id":0}))
    return courses
def get_all_chat_fields():
    users = users_collection.find()
    chat_fields = set()
    for user in users:
        for field in user:
            if 'chat' in field.lower():
                chat_fields.add(field)
    return list(chat_fields)
def archive_chats():
    #status back to pending_courses, courses array empty, all chat histories and chat_ids removed
    chat_fields = get_all_chat_fields()
    chat_fields_unset = {field: "" for field in chat_fields}
    users_collection.update_many({},{"$set":{"status":"pending_courses","courses":[]},"$unset":chat_fields_unset})
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
    return token

def remove_token():
    tokens.delete_many({})

# chat_fields = get_all_chat_fields()
# chat_fields_unset = {field: "" for field in chat_fields}
# print(chat_fields_unset)
archive_chats()