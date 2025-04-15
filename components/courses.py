import streamlit as st
from pypdf import PdfReader
from pymongo import MongoClient
import re 
import json
from components.db_functions import parse_courses
import os 

def course_upload():
    st.write('Provide PDF of your current courses. This will be found under MyFIU, Manage Classes, View Class Schedule. Then, Click where it says Print Schedule and Download the File.')
    image_path = os.path.join("components", "images", "FIU Schedule.png")
    st.image(image_path)
    #first check, is to ensure its a pdf
    try:
        file = st.file_uploader("Choose a file", type=["pdf"])
        if file:
            reader = PdfReader(file)
            pages = reader.pages
            text = ""
            for page in pages:
                text+=page.extract_text()
            # seconc check text should contain : 'Schedule of Classes', else provide an error message
            if 'Schedule of Classes' in text:
                pattern = r'[A-Z]{3}-\d{4}'
                courses = re.findall(pattern,text)
                # third check student should be taking at least 1 course, else provide error message
                if courses:
                   #fourth check student courses need to be inside courses database.
                   tutored_courses = parse_courses(courses)
                   #use this to test
                #    tutored_courses =  ['CAP-2752','ABC-123','DEF-456']
                   if tutored_courses:
                       st.session_state.courses_valid = True
                       tutored_courses = [course.upper() for course in tutored_courses]
                       st.info(f'These are the courses we are currently tutoring:  \n\n {" | ".join(tutored_courses)}')
                       return tutored_courses
                   else:
                       st.error('We are not offering tutoring for these courses and do not have bots available')
                       
                    
                else:
                    st.error('You must be enrolled in at least 1 course to access our service.')
                
            else:
                st.error('Please Provide PDF of your class schedule. Go to MyFIU, Manage Classes, View Class schedule. Then, you will click on print schedule and download the file.')
    except Exception as e:
        st.error('Not a PDF. Please Provide PDF of your class schedule. Go to MyFIU, Manage Classes, View Class schedule. Then, you will click on print schedule and download the file. ')
