from __future__ import print_function
import time
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from pprint import pprint
import streamlit as st
# Configure API key authorization: api-key
configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = st.secrets["BREVO_API_KEY"]


# create an instance of the API class
api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
def send_email(email,student_name,status):
    subject_content = ""
    body_content = f"<html><body><h1>Hello {student_name} !</h1>"
    if status=="approve":
        subject_content = "STARS Tutor Approval"
        #TODO append STARS website when it exists
        body_content += "<p>Your information has been approved and you can now access the STARS website</p>"
    elif status=="reject":
        subject_content = "STARS Tutor Rejection"
        body_content += "<p>Your information has been rejected. Please contact the administrator at arehman@fiu.edu for more information</p>"
    elif status =="remove":
        subject_content = "STARS Tutor Access Revoked"
        body_content += "<p>Your access to STARS tutor website has been revoked. Contact administrator at arehman@fiu.edu for more information</p>"
    elif status=="revise":
        subject_content = "STARS Tutor Revision Request"
        #TODO append STARS website when it exists
        body_content += "<p>Please reupload your course information at STARS website</p>"
    #end string
    body_content+="</body></html>"
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": email,"name":student_name.capitalize()}],
        sender={"email": "alvarezleandro720@gmail.com", "name": "Leandro"},
        subject=subject_content,
        html_content=body_content
    )
    try:
        # Send a transactional email
        api_response = api_instance.send_transac_email(send_smtp_email)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)

# send_email("miguelgarcia2002117@gmail.com","Miguel","approve")