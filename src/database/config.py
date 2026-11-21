import os

import streamlit as st
from supabase import create_client


supabase = create_client(
    st.secrets["supabase_url"],
    st.secrets["supabase_key"],
)


def get_supabase_admin_client():
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not service_key:
        service_key = st.secrets.get("supabase_service_role_key")
    if not service_key:
        raise RuntimeError(
            "Configure the server-only supabase_service_role_key in Streamlit secrets "
            "to manage notes and assessments. Add it to .streamlit/secrets.toml and "
            "restart Streamlit. Never expose this key in client-side code."
        )
    return create_client(st.secrets["supabase_url"], str(service_key))