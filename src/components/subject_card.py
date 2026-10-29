from html import escape
from textwrap import dedent

import streamlit as st


def Subject_card(name, code, section, stats=None, footer_callback=None):
    html = dedent(f"""
        <div style="box-sizing:border-box; width:100%; background:white;
                    border-left:8px solid #EB459E; padding:25px;
                    border-radius:20px; border:1px solid black; margin-bottom:20px;">
            <h3 style="margin:0; color:#1e293b; font-size:1.5rem;">{escape(str(name))}</h3>
            <p style="color:#64748b; margin:10px 0;">
                Code: <span style="background:#E0E3FF; color:#5865F2; padding:2px 8px;
                                    border-radius:5px;">{escape(str(code))}</span>
                | Section: {escape(str(section))}
            </p>
        """)
    if stats:
        html += dedent("""
            <div style="display:flex; gap:8px; flex-wrap:wrap; width:fit-content; max-width:100%;">
        """)
        for icon, label, value in stats:
            html += (
                f'<div style="background:#EB459E10; padding:5px 12px; '
                f'border-radius:12px; font-size:0.9rem;">'
                f'{escape(str(icon))} <b>{escape(str(value))}</b> '
                f'{escape(str(label))}</div>'
            )
        html += "</div>"

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)
    if footer_callback:
        footer_callback()
