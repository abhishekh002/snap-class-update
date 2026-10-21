import streamlit as st
from src.components.footer import footer_dashboard
from src.ui.base_layout import style_background_dashboard, style_base_layout

from src.components.header import header_dashboard

from src.database.db import check_teacher_exists, create_teacher, teacher_login


def register_teacher(teacher_username, teacher_name, teacher_pass, teacher_pass_confirm):
    if not all((teacher_username, teacher_name, teacher_pass, teacher_pass_confirm)):
        return False, "All fields are required!"
    if check_teacher_exists(teacher_username):
        return False, "Username already taken"
    if teacher_pass != teacher_pass_confirm:
        return False, "Passwords don't match"

    create_teacher(teacher_username, teacher_pass, teacher_name)
    return True, "Successfully created! Login now."


def teacher_screen():
    style_background_dashboard()
    style_base_layout()
    if "teacher_data" in st.session_state:
        teacher_dashboard()
    elif "teacher_login_type" not in st.session_state or st.session_state.teacher_login_type == "login":
        teacher_screen_login()
    elif st.session_state.teacher_login_type == "register":
        teacher_screen_register()

def teacher_dashboard():    
    teacher = st.session_state.teacher_data
    header_dashboard()
    st.subheader(f"Welcome, {teacher['name']}")
    if st.button("Logout", type="secondary", key="teacher_logout"):
        del st.session_state["teacher_data"]
        st.session_state["teacher_login_type"] = "login"
        st.rerun()
    footer_dashboard()


def teacher_screen_login():
    style_background_dashboard()
    style_base_layout()
    if "teacher_registration_message" in st.session_state:
        st.success(st.session_state.pop("teacher_registration_message"))

    c1, c2 = st.columns(2, vertical_alignment="center", gap="large")
    with c1:
        header_dashboard()
    with c2:
        if st.button("GO BACK TO HOME", type="secondary", key="loginbackbtn", shortcut="Ctrl+Backspace"):
            st.session_state['login_type'] = None
            st.rerun()

    st.space()
    st.markdown(
        """
        <h2 style="text-align:center; white-space:nowrap;
                    font-size:clamp(0.85rem, 2vw, 1.5rem);">
            Teacher Login with Password 
        </h2>
        """,
        unsafe_allow_html=True,
    )
    st.space()
    st.space()
    teacher_username = st.text_input("Enter username", placeholder="@abhishekh", key="teacher_login_username")
    teacher_pass = st.text_input("Enter password", type="password", placeholder="Enter password", key="teacher_login_password")
    st.divider()
    btnc1 , btnc2 = st.columns(2)

    with btnc1:
        if st.button("Login", icon=":material/passkey:", shortcut="Ctrl+Enter", width="stretch"):
            teacher = teacher_login(teacher_username, teacher_pass)
            if teacher:
                st.session_state.teacher_data = teacher
                st.rerun()
            st.error("Invalid username or password.")
    with btnc2:
        if st.button('Register Instead', type='primary' ,icon=':material/passkey:',width='stretch'):
            st.session_state.teacher_login_type = 'register'
    footer_dashboard()

def teacher_screen_register():
    c1, c2 = st.columns(2, vertical_alignment="center", gap="large")
    with c1:
        header_dashboard()
    with c2:
        if st.button("GO BACK TO HOME", type="secondary", key="login back_btn", shortcut="Ctrl+Backspace"):
            st.session_state['login_type'] = None
            st.rerun()
            
    st.header("Teacher Registration")

    st.space()
    st.space()

    teacher_username = st.text_input("Enter username", placeholder="@abhishekh", key="teacher_register_username")

    teacher_name = st.text_input("Enter name", placeholder="Abhishekh kumar Tiwari", key="teacher_register_name")
    
    teacher_pass = st.text_input("Enter password", type="password", placeholder="Enter password", key="teacher_register_password")

    teacher_pass_confirm = st.text_input("Confirm your password", type="password", placeholder="Confirm password", key="teacher_register_password_confirm")


    st.divider()

    btnc1 , btnc2 = st.columns(2)

    with btnc1:
        if st.button("Register Now", icon=":material/passkey:", shortcut="Ctrl+Enter", width="stretch"):
            success, message = register_teacher(
                teacher_username,
                teacher_name,
                teacher_pass,
                teacher_pass_confirm,
            )
            if success:
                st.session_state.teacher_registration_message = message
                st.session_state.teacher_login_type = "login"
                st.rerun()
            else:
                st.error(message)
    with btnc2:
        if st.button('Login Instead', type='primary' ,icon=':material/passkey:',width='stretch'):
            st.session_state.teacher_login_type = 'login'
    footer_dashboard()

  


    
