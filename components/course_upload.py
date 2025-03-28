import streamlit as st
from pypdf import PdfReader
import re 
import json

def course_upload():
    st.write('Provide PDF of your current courses. This will be found under MyFIU, Manage Classes, View Class Schedule. Then, Click where it says Print Schedule and Download the File.')
    st.image('components\images\FIU Schedule.png')
    try:
        file = st.file_uploader("Choose a file")
        if file:
            reader = PdfReader(file)
            last_page  = reader.pages[-1]
            text = last_page.extract_text()
            #text should contain : 'Schedule of Classes', else provide an error message
            if 'Schedule of Classes' in text:
                course_data = text.split('Units')
                courses = [course_str.split('\n')[-1] for course_str in course_data][:-1]
                #student should be taking at least 1 course, else provide error message
                if courses:
                    # st.write(courses)
                    pass
                else:
                    st.error('You must be enrolled in at least 1 course to access our service.')
                
            else:
                st.error('Please Provide PDF of your class schedule. Go to MyFIU, Manage Classes, View Class schedule. Then, you will click on print schedule and download the file.')
    except Exception as e:
        st.error('Please Provide PDF of your class schedule. Go to MyFIU, Manage Classes, View Class schedule. Then, you will click on print schedule and download the file. ')
