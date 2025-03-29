import streamlit as st
from pymongo import MongoClient
import pandas as pd

mongo_uri = "mongodb://localhost:27017/"
client = MongoClient(mongo_uri)
coursedb = client['courses']
course_collection = coursedb['course_list']

db = client["user_data"]
users_collection = db["users"]

# def get_user_type():
#     user_id = st.session_state.username
#     user_doc = users_collection.find_one({"username":user_id})
#     user_type = user_doc.get('user_type')
#     return user_type

# def get_student_status():
#     user_id = st.session_state.username
#     user_doc = users_collection.find_one({"username":user_id})
#     #None if they are tutor/admin
#     student_status = user_doc.get('student_status',None)
#     return student_status
#Admin helper functions
@st.dialog("Remove a course")
def removeClassModal():
    st.write('Remove a course')
    with st.form(key='class_form'):
        course_code = st.text_input("Insert class code:")
        submit = st.form_submit_button('Submit')

        if submit:
            course_collection.delete_one({"course_code": course_code,})
            st.success(f"Class {course_code} removed successfully!")
            st.rerun()

def get_courses():
    courses = list(course_collection.find({}))
    return courses
def parse_courses(courses):
    #this is to be used in course upload, receving a course array, need to filter out those inside the course collection
    tutored_courses = course_collection.find({
        'course_id' : {"$in":courses}
    })
    return list(tutored_courses)

@st.dialog("Add new classes")
def addclassModal():
    st.write('Add new classes')
    with st.form(key='class_form'):
        course_code = st.text_input("Insert class code:")
        course_name = st.text_input("Insert class name")
        course_id = st.text_input('insert class id')
        submit = st.form_submit_button('Submit')

        if submit:
            course_collection.insert_one({"course_name": course_name, "course_code": course_code, "course_id": course_id})
            st.success(f"Class {course_name} added successfully!")
            st.rerun()

def admin_panel():
    st.title("Welcome to the admin dashboard")
    st.write("Admin dashboard to add or remove courses")
    courses = get_courses()
    if not courses:
        st.write("no courses found")
    else:
        st.write("some courses:")
        df = pd.DataFrame(courses, columns=['course_name', 'course_code', 'course_id'])


        st.table(df)
        
        if st.button("Add new course"):
            addclassModal()
        if st.button("Remove course"):
            removeClassModal()