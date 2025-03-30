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

def get_pending_students():
    students = list(users_collection.find({"student_status": "pending"}))
    return students

@st.dialog("Approve Student")
def approveStudent(student):
    st.title(f"Are you sure you want to approve {student}?")
    if st.button("Approve"):
        users_collection.update_one(
            {"username": student},
            {"$set": {"student_status": "approved"}}
        )
        st.rerun()
    elif st.button("Cancel"):
        st.rerun()

@st.dialog("Reject Student")
def rejectStudent(student):
    st.title(f"Are you sure you want to reject {student}?")
    if st.button("Reject"):
        users_collection.update_one(
            {"username": student},
            {"$set": {"student_status": "rejected"}}
        )
        st.rerun()
    elif st.button("Cancel"):
        st.rerun()



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
    if "admin_page" not in st.session_state:
        st.session_state.admin_page = "courses"
       
    with st.sidebar:
        st.title("Admin Panel")
        if st.sidebar.button("Course Settings"):
            st.session_state.admin_page ="courses"
            st.rerun()
        if st.sidebar.button("Student Approval"):
            st.session_state.admin_page ="student_approval"
            st.rerun()
    #The "pages"
    if st.session_state.admin_page =="courses":
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

    elif st.session_state.admin_page =="student_approval":
        st.title("Student Approval")

        data = get_pending_students()

        df = pd.DataFrame(data)

        st.write("Students Pending Approval")

            # Create table headers
        cols = st.columns([3, 3, 2, 2, 1])  # Adjust column widths
        cols[0].write("username")
        cols[1].write("email")

            # Loop through rows
        for index, row in df.iterrows():
            cols = st.columns([3, 3, 2, 2, 2])  
            cols[0].write(row["username"])
            cols[1].write(row["email"])
                
                
                # Add a button for each row
            if cols[3].button(f"Remove", key=f"remove_{row['username']}"):
                st.warning(f"Student {row['email']} removed!") 
                rejectStudent(row['username'])
                    # st.rerun()
            if cols[4].button(f"Approve", key=f"approve_{row['username']}"):
                st.success(f"Student {row['username']} Approved!")
                approveStudent(row['username'])
                    # st.rerun()