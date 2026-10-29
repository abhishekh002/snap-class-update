import streamlit as st
from src.database.db import enroll_student_to_subject, get_subject_by_code

@st.dialog('Enroll in Subject')
def enroll_dialog():
    st.write('Enter the subject code provided by your teacher to enroll')
    join_code = st.text_input('Subject Code',placeholder='Eg. CS101')

    if st.button('Enroll now', type='primary', width='stretch'):
        if not join_code.strip():
            st.warning('Please enter a subject code')
            return

        subject = get_subject_by_code(join_code.strip())
        if subject is None:
            st.warning('No subject found with that code.')
            return

        student_id = st.session_state.student_data['student_id']
        enrollment = enroll_student_to_subject(student_id, subject['subject_id'])
        if enrollment is None:
            st.warning('You are already enrolled in this subject.')
        elif enrollment:
            st.success(f"Successfully enrolled in {subject['name']}!")
            st.rerun()
        else:
            st.error('Could not enroll in the subject. Please try again.')
    