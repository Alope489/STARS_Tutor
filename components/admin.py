import streamlit as st
import pandas as pd
from components.db_functions import course_collection,users_collection,tokens,get_pending_students,get_enrolled_students,get_courses,find_token,remove_token,get_pending_tutors,get_enrolled_tutors,set_archive_date, archive_chats,get_current_semester,get_user_chat_history,check_system_down_time
from uuid import uuid4
from components.send_email import send_email
from datetime import datetime,timedelta,timezone
import time
import json




if 'generated_code' not in st.session_state:
    st.session_state.generated_code = ''

@st.dialog("Remove a course")
def removeClassModal():
    st.write('Remove a course')
    with st.form(key='class_form'):
        course_id = st.text_input("Insert course_id:")
        submit = st.form_submit_button('Submit')

        if submit:
            course_collection.delete_one({"course_id": course_id,})
            st.success(f"Class {course_id} removed successfully!")
            st.rerun()



@st.dialog("Approve Student")
def approveStudent(student_email,student_name,student_status):
    st.subheader(f"Are you sure you want to approve {student_email}?")
    check_system_down_time()
    approve, cancel = st.columns(2)
    with approve:
        send_email(student_email,student_name,student_status)
        if st.button("Approve",key='confirm_approval'):
            users_collection.update_one(
                {"email": student_email},
                {"$set": {"status": "approved"}}
            )
            st.success(f"Student {student_email} Approved!")
            time.sleep(2)
            st.rerun()
    with cancel:
        if st.button("Cancel",key='cancel_approval'):
            st.rerun()

@st.dialog("Reject Student")
def rejectStudent(student_email,student_name,student_status):
    st.subheader(f"Are you sure you want to reject {student_email}?")
    check_system_down_time()
    reject, cancel = st.columns(2)
    with reject:
        send_email(student_email,student_name,student_status)
        if st.button("Reject",key='confirm_rejection'):
            users_collection.update_one(
                {"email": student_email},
                {"$set": {"status": "rejected"}}
            )
            st.warning(f"Student {student_email} Rejected!") 
            time.sleep(2)
            st.rerun()
    with cancel:
        if st.button("Cancel",key='cancel_rejection'):
            st.rerun()

@st.dialog('Revise Student')
def reviseStudent(student_email,student_name,student_status):
    st.subheader('Are you sure you want student to reupload their course information?')
    check_system_down_time()
    revise, cancel = st.columns(2)
    with revise:
        send_email(student_email,student_name,student_status)
        if st.button("Revise",key='confirm_revision'):
            users_collection.update_one(
                {"email": student_email},
                {"$set": {"status": "pending_courses", "courses":[]}}
            )
            st.warning(f"Student {student_email} will now have to upload course information!") 
            time.sleep(2)
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

@st.dialog('Download User Chat')
def download_chat(panther_id):
    user_chat_history = get_user_chat_history(panther_id)
    json_data = json.dumps(user_chat_history,indent=2)
    st.download_button(
        label="Download JSON",
        data=json_data,
        file_name=f"{panther_id}_data.json",
        mime="application/json",
        icon=":material/download:",
    )
@st.dialog('Confirm Archival Date')
def archival_date_confirmation(set_date):
    #if scheduler is to be used
    st.write('After an archive students will have to reupload their courses and you will have to approve them again')
    # st.write(f'{year} {month} {day}')
    confirm = st.button('confirm',key='confirm_archive_date')
    if confirm:
        set_archive_date(set_date)
        st.success('Date has been set!')
        time.sleep(1)
        st.rerun()

@st.dialog('Confirm Archive')
def confirm_archive():
    st.write('Are you sure you want to archive all chats? After an archive students and tutors will have to reupload their courses and you will have to approve them again. This is only meant for end of semester.')
    confirm = st.button('confirm',key='confirm_archive')
    if confirm:
        archive_chats()
        st.success('Chats archived!')
        time.sleep(2)
        st.rerun()

def students_page():
    st.title('Students Page')
    st.subheader("Pending Students")
    data = get_pending_students()
    if data:
        df_pending = pd.DataFrame(data)
        columns_to_drop = ['_id','status','user_type','password','salt']
        #also drop any columns containg 'chat' which would include current chat ids and chat histories
        chat_columns = df_pending.filter(regex='.*chat.*', axis=1).columns.tolist()
        columns_to_drop = columns_to_drop + chat_columns
        df_pending = df_pending.drop(columns=columns_to_drop)
        
        st.write("Approve or Reject pending students")

        # Display table
        st.dataframe(df_pending)
        student_names = df_pending['email'].to_list()
        selected_student_email = st.selectbox("Select a student to approve/reject", student_names)
        selected_student_name = df_pending[df_pending["email"]==selected_student_email]["fname"].values[0]
        # Display buttons for approve/reject
        col1,col2 = st.columns(2)
        with col1:
            approve_button = st.button("Approve",key='approve_pending_students',on_click=approveStudent,args=[selected_student_email,selected_student_name,"approve"])
        with col2:
            reject_button = st.button("Reject",key='reject_pending_students',on_click=rejectStudent,args=[selected_student_email,selected_student_name,"reject"])
       

    else:
        st.write('No pending students')
    
    st.subheader('Enrolled Students')
    enrolled_students = get_enrolled_students()
    if enrolled_students:
        df_enrolled = pd.DataFrame(enrolled_students)
        columns_to_drop = ['_id','status','user_type','password','salt']
        #also drop any columns containg 'chat' which would include current chat ids and chat histories
        chat_columns = df_enrolled.filter(regex='.*chat.*', axis=1).columns.tolist()
        columns_to_drop = columns_to_drop + chat_columns
        df_enrolled = df_enrolled.drop(columns=columns_to_drop)
        st.write('Reject or Revise current students')
        st.dataframe(df_enrolled)

        student_names = df_enrolled['email'].to_list()
        selected_student_email = st.selectbox("Select a student to Reject/ Revise", student_names)
        selected_student_name = df_enrolled[df_enrolled["email"]==selected_student_email]["fname"].values[0]
        # Display buttons for approve/reject
        col1,col2,col3= st.columns(3)
        with col1:
            remove_button = st.button("Remove",key='reject_enrolled_students',on_click=rejectStudent,args=[selected_student_email,selected_student_name,"remove"])
        with col2:
            revise_button = st.button("Revise",key='revise_enrolled_students',on_click=reviseStudent,args=[selected_student_email,selected_student_name,"revise"])
        with col3:
            download_chat_button = st.button('Download Chat',key='download_chat_enrolled_students',on_click=download_chat,args=[df_enrolled[df_enrolled["email"]==selected_student_email]["panther_id"].values[0]])
    else:
        st.write('No enrolled students')



def course_page():
    st.title("Welcome to the Admin Dashboard")
    st.subheader(st.session_state.current_semester)
    st.write("Admin dashboard to add or remove courses")
    courses = get_courses()
    if not courses:
        st.write("no courses found")
    else:
        st.subheader("Current Courses:")
        df = pd.DataFrame(courses, columns=['course_name', 'course_id'])
        st.dataframe(df)
        col1,col2 = st.columns(2,gap='large')
        with col1:
            if st.button("Add new course"):
                addclassModal()
        with col2:
            if st.button("Remove course"):
                removeClassModal()
    
    st.subheader('Archive Chats at end of semester')
    st.button('Archive',on_click=confirm_archive)
    

def tutors_page():
    #auth code for tutor sign up
    #admins have option of generating code and then setting it, or simply setting it with their own option
    st.title('Tutor Page')
    st.subheader('Set Auth Code for tutor sign up')
    token = find_token()
    if token:
        expiration_date = token['expiresAt']
        expiration_date = datetime.fromisoformat(str(expiration_date))
        delta = expiration_date-datetime.now()
        delta_string = f'{delta.days} days {delta.seconds // 3600} hours'
        curr_token = st.text_input(f'Current Token, set to expire in {delta_string}',token['token'])
    col1,col2 = st.columns(2)
    with col1:
        code = ''
        text_to_copy = st.text_input('Copy Code: ',st.session_state.generated_code)
        if st.button('Click to generate code'):
            st.session_state.generated_code=uuid4()
            st.rerun()
    with col2:
        set_token = st.text_input('Set Token: ')
        if st.button('Set Auth Token'):
            if set_token:
                #send to db, must remove previous contained in db.
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

    #display pending and enrolled tutors similar to students page
    st.subheader('Approve Tutors')
    data = get_pending_tutors()
    if data:
        df_pending = pd.DataFrame(data)
        columns_to_drop = ['_id','status','user_type','password','salt']
        chat_columns = df_pending.filter(regex='.*chat.*', axis=1).columns.tolist()
        columns_to_drop = columns_to_drop + chat_columns
        df_pending = df_pending.drop(columns=columns_to_drop)
        
        st.write("Approve or Reject pending tutors")

        # Display table
        st.dataframe(df_pending)
        student_names = df_pending['email'].to_list()
        selected_tutor_email = st.selectbox("Select a tutor to approve/reject", student_names)
        selected_tutor_name = df_pending[df_pending['email']==selected_tutor_email]["fname"].values[0]
        # Display buttons for approve/reject
        col1,col2 = st.columns(2)
        with col1:
            #same approve/reject functions can be used
            approve_button = st.button("Approve",key='approve_pending_tutor',on_click=approveStudent,args=[selected_tutor_email,selected_tutor_name,"approve"])
        with col2:
            reject_button = st.button("Reject",key='reject_pending_tutor',on_click=rejectStudent,args=[selected_tutor_email,selected_tutor_name,"reject"])
       
    else:
        st.write('No pending tutors')

    st.subheader('Enrolled Tutors')
    enrolled_tutors = get_enrolled_tutors()
    if enrolled_tutors:
        df_enrolled = pd.DataFrame(enrolled_tutors)
        columns_to_drop = ['_id','status','user_type','password','salt']
        #also drop any columns containg 'chat' which would include current chat ids and chat histories
        chat_columns = df_enrolled.filter(regex='.*chat.*', axis=1).columns.tolist()
        columns_to_drop = columns_to_drop + chat_columns
        df_enrolled = df_enrolled.drop(columns=columns_to_drop)
        st.write('Reject or Revise current tutors')
        st.dataframe(df_enrolled)

        tutor_names = df_enrolled['email'].to_list()
        selected_tutor_email = st.selectbox("Select a student to Reject/ Revise", tutor_names)
        selected_tutor_name = df_enrolled[df_enrolled["email"]==selected_tutor_email]["fname"].values[0]
        # Display buttons for approve/reject
        col1,col2,col3 = st.columns(3)
        with col1:
            reject_button = st.button("Remove",key='reject_enrolled_tutor',on_click=rejectStudent,args=[selected_tutor_email,selected_tutor_name,"remove"])
        with col2:
            revise_button = st.button("Revise",key='revise_enrolled_tutor',on_click=reviseStudent,args=[selected_tutor_email,selected_tutor_name,"revise"])
        with col3:
             download_chat_button = st.button('Download Chat',key='download_chat_enrolled_students',on_click=download_chat,args=[df_enrolled[df_enrolled["email"]==selected_tutor_email]["panther_id"].values[0]])
    else:
        st.write('No enrolled tutors')


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
        if st.sidebar.button("Menu"):
            st.session_state.admin_page ="courses"
            st.rerun()
        if st.sidebar.button("Students"):
            st.session_state.admin_page ="students"
            st.rerun()
        if st.sidebar.button("Tutors"):
            st.session_state.admin_page ="tutors"
            st.rerun()
        if st.button("Logout"):
                    st.session_state.logged_in = False
                    st.session_state.username = ""
                    st.session_state.messages = []
                    st.session_state.user_type =""
                    st.rerun()  
            
    #The "pages"
    if st.session_state.admin_page =="courses":
       course_page()
            
    elif st.session_state.admin_page =="students":
        students_page()
    elif st.session_state.admin_page=='tutors':
        tutors_page()

