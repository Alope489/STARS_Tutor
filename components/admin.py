import streamlit as st
import pandas as pd
from components.courses import course_collection,users_collection,get_pending_students,get_enrolled_students,get_courses,tokens
from uuid import uuid4
import pyperclip
from datetime import datetime,timedelta,timezone
import time

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
def copy_to_clipboard(text):
    try:
        pyperclip.copy(text)
        st.success('Successfully copied code')
    except Exception as e:
        st.error(f'Try installing pyperclip.  Error: {e}')

def find_token():
    token = list(tokens.find())
    return token
def remove_token():
    tokens.delete_many({})
def tutors_page():
    #auth code for tutor sign up
    #admins have option of generating code and then setting it, or simply setting it with their own option
    st.title('Tutor Page')
    st.write('Set auth token for tutor sign up')
    col1,col2 = st.columns(2)
    with col1:
        code = uuid4()
        text_to_copy = st.text_area('Copy Code: ',code)
        if st.button('Click to copy code'):
            copy_to_clipboard(text_to_copy)
    with col2:
        set_token = st.text_area('Set Token: ')
        if st.button('Set Auth Token'):
            if set_token:
                #send to db, must remove previous contained in db.
                token = find_token()
                if token:
                    remove_token()
                #must set attribute for expiresAt, 1 week from now is 604800
                expiry = timedelta(seconds=604800)
                #mongodb operates in utc time
                expiresAt = datetime.now() + expiry
                tokens.insert_one({"token":set_token,"expiresAt":expiresAt})
                st.success(f'Your token will expire at : \n\n {expiresAt}')
                time.sleep(2)
                st.rerun()
            else:
                st.error('Set the auth code correctly.')


def admin_panel():
    st.markdown(
    """
    <style>
        .stButton > button {
            width: 200px;  /* Adjust width as needed */
        }
    </style>
    """,
    unsafe_allow_html=True
)
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
        if st.sidebar.button("Tutors"):
            st.session_state.admin_page ="tutors"
            st.rerun()
    #The "pages"
    if st.session_state.admin_page =="courses":
       course_page()
            
    elif st.session_state.admin_page =="students":
        students_page()
    elif st.session_state.admin_page=='tutors':
        tutors_page()

          
            