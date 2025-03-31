import streamlit as st
from pymongo import MongoClient
import pandas as pd

mongo_uri = "mongodb://localhost:27017/"
client = MongoClient(mongo_uri)
coursedb = client['courses']
course_collection = coursedb['course_list']

db = client["user_data"]
users_collection = db["users"]


@st.dialog("Remove a course")
def removeClassModal():
    st.write('Remove a course')
    with st.form(key='class_form'):
        course_id = st.text_input("Insert class id:")
        submit = st.form_submit_button('Submit')

        if submit:
            course_collection.delete_one({"course_id": course_id,})
            st.success(f"Class {course_id} removed successfully!")
            st.rerun()

def get_courses():
    courses = list(course_collection.find({}))
    return courses
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

@st.dialog("Approve Student")
def approveStudent(email):
    st.subheader(f"Are you sure you want to approve {email}?")
    approve, cancel = st.columns(2)
    with approve:
        if st.button("Approve",key='confirm_approval'):
            users_collection.update_one(
                {"email": email},
                {"$set": {"status": "approved"}}
            )
            st.success(f"Student {email} Approved!")
            st.rerun()
    with cancel:
        if st.button("Cancel",key='cancel_approval'):
            st.rerun()

@st.dialog("Reject Student")
def rejectStudent(student):
    st.subheader(f"Are you sure you want to reject {student}?")
    reject, cancel = st.columns(2)
    with reject:
        if st.button("Reject",key='confirm_rejection'):
            users_collection.update_one(
                {"email": student},
                {"$set": {"status": "rejected"}}
            )
            st.warning(f"Student {student} Rejected!") 
            st.rerun()
    with cancel:
        if st.button("Cancel",key='cancel_rejection'):
            st.rerun()

@st.dialog('Revise Student')
def reviseStudent(student):
    st.subheader('Are you sure you want student to reupload their course information?')
    revise, cancel = st.columns(2)
    with revise:
        if st.button("Revise",key='confirm_revision'):
            users_collection.update_one(
                {"email": student},
                {"$set": {"status": "pending_courses"}}
            )
            st.warning(f"Student {student} will not have to upload course information!") 
            st.rerun()
    with cancel:
        if st.button("Cancel",key='cancel_revision'):
            st.rerun()



@st.dialog("Add new classes")
def addclassModal():
    st.write('Add new classes')
    with st.form(key='class_form'):
        course_name = st.text_input("Insert class name")
        course_id = st.text_input('insert class id')
        submit = st.form_submit_button('Submit')

        if submit:
            course_collection.insert_one({"course_name": course_name,  "course_id": course_id})
            st.success(f"Class {course_name} added successfully!")
            st.rerun()

def students_page():
    st.title("Pending Students")
    data = get_pending_students()

    df_pending = pd.DataFrame(data)

    df_pending = df_pending.drop(columns=['_id','status','user_type','password'])
    
    st.write("Approve or Reject pending students")

    # Display table
    st.dataframe(df_pending)
    student_names = df_pending['email'].to_list()
    selected_student = st.selectbox("Select a student to approve/reject", student_names)

    # Display buttons for approve/reject
    col1,col2 = st.columns(2)
    with col1:
        approve_button = st.button("Approve",on_click=approveStudent,args=[selected_student])
    with col2:
        reject_button = st.button("Reject",on_click=rejectStudent,args=[selected_student])
    
    st.title('Enrolled Students')
    enrolled_students = get_enrolled_students()
    df_enrolled = pd.DataFrame(enrolled_students)
    df_enrolled = df_enrolled.drop(columns=['_id','status','user_type','password'])
    st.write('Reject or Revise current students')
    st.dataframe(df_enrolled)

    student_names = df_enrolled['email'].to_list()
    selected_student = st.selectbox("Select a student to Reject/ Revise", student_names)

    # Display buttons for approve/reject
    col1,col2 = st.columns(2)
    with col1:
        approve_button = st.button("Reject",key='reject_enrolled',on_click=rejectStudent,args=[selected_student])
    with col2:
        reject_button = st.button("Revise",on_click=reviseStudent,args=[selected_student])

def course_page():
    st.title("Welcome to the admin dashboard")
    st.write("Admin dashboard to add or remove courses")
    courses = get_courses()
    if not courses:
        st.write("no courses found")
    else:
        st.write("Current Courses:")
        df = pd.DataFrame(courses, columns=['course_name', 'course_id'])
        st.dataframe(df)
        col1,col2 = st.columns(2,gap='large')
        with col1:
            if st.button("Add new course"):
                addclassModal()
        with col2:
            if st.button("Remove course"):
                removeClassModal()
def admin_panel():
    if "admin_page" not in st.session_state:
        st.session_state.admin_page = "courses"
       
    with st.sidebar:
        st.title("Admin Panel")
        if st.sidebar.button("Course Settings"):
            st.session_state.admin_page ="courses"
            st.rerun()
        if st.sidebar.button("Students"):
            st.session_state.admin_page ="students"
            st.rerun()
    #The "pages"
    if st.session_state.admin_page =="courses":
       course_page()
            
    elif st.session_state.admin_page =="students":
        students_page()

          
            