from html import escape
from textwrap import dedent

import streamlit as st


def Subject_card(name, code, section, stats=None, footer_callback=None):
    html = dedent(f"""
        <div style="box-sizing:border-box; width:100%; background:#fffefa;
                    border:1px solid #dce1d6; border-left:6px solid #829a79;
                    padding:24px; border-radius:16px; margin-bottom:20px;
                    box-shadow:0 8px 22px rgba(48,66,51,.08);">
            <h3 style="margin:0; color:#26382e; font-size:1.45rem;">{escape(str(name))}</h3>
            <p style="color:#65746a; margin:10px 0;">
                Code: <span style="background:#e2eadc; color:#385844; padding:2px 8px;
                                    border-radius:999px;">{escape(str(code))}</span>
                | Section: {escape(str(section))}
            </p>
        """)
    if stats:
        html += dedent("""
            <div style="display:flex; gap:8px; flex-wrap:wrap; width:fit-content; max-width:100%;">
        """)
        for icon, label, value in stats:
            html += (
                f'<div style="background:#edd8cf; color:#744b40; padding:5px 12px; '
                f'border-radius:12px; font-size:0.9rem;">'
                f'{escape(str(icon))} <b>{escape(str(value))}</b> '
                f'{escape(str(label))}</div>'
            )
        html += "</div>"

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)
    if footer_callback:
        footer_callback()
