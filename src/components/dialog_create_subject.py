import streamlit as st
from src.database.db import create_subject

@st.dialog('Create New Subject')
def create_subject_dialog(teacher_id):
    st.markdown("""
        <style>
            .create-subject-intro {
                margin: .25rem 0 1rem;
                padding: 1rem 1.1rem;
                border: 1px solid #dce1d6;
                border-left: 4px solid #829a79;
                border-radius: 14px;
                background: linear-gradient(125deg, #e6ecdf, #fffefa);
                color: #526457;
                line-height: 1.55;
            }
            .create-subject-intro strong { color: #385844; }
        </style>
        <div class="create-subject-intro">
          <strong>Set up a class</strong><br>
          Add a subject name, code, and section so students can join the right class.
        </div>
    """, unsafe_allow_html=True)
    sub_id = st.text_input('Subject Code',placeholder='#702EA')
    sub_name = st.text_input('Subject Name',placeholder='DATA SCIENCE & ARTIFICIAL INTELLIGENCE')
    sub_section = st.text_input('Section',placeholder='B')


    if st.button("Create Subject Now" , type='primary',width='stretch'):
        if sub_id and sub_name and sub_section:
            try:
                create_subject(sub_id,sub_name,sub_section,teacher_id)
                st.toast('Subject created successfully!')
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning('Please fill in all fields.')
