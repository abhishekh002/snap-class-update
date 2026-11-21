import base64
import streamlit as st


def _get_logo_url(is_dark: bool = True) -> str:
    # Both home and dashboard use a light, warm surface now.
    text_color = "#26382E"
    accent_color = "#B97453"

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 270 40" width="270" height="40" fill="none">
      <defs>
        <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="{accent_color}"/>
          <stop offset="100%" stop-color="{text_color}"/>
        </linearGradient>
      </defs>
      <g transform="translate(20, 20) scale(0.24)">
        <polygon points="0,-76 65,-38 65,38 0,76 -65,38 -65,-38" stroke="url(#g)" stroke-width="6"/>
        <path d="M 0,-55 L -40,28 L -20,28 L -10,6 L 10,6 L 0,-20 Z" fill="url(#g)"/>
        <path d="M -38,-55 L 38,-55 L 38,-42 L -38,-42 Z" fill="{text_color}"/>
        <path d="M -4,-2 L 28,-38 L 46,-38 L 8,3 L 42,42 L 24,42 L -4,7 Z" fill="url(#g)"/>
      </g>
      <text x="44" y="26" font-family="system-ui, -apple-system, sans-serif" font-size="16" font-weight="800" letter-spacing="1.5" fill="{text_color}">
        ABHISHEK <tspan fill="{accent_color}">TIWARI</tspan>
      </text>
    </svg>"""

    encoded = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"


def _render_creator_footer():
    st.divider()
    st.markdown(
        "<div style='width:100%;padding:14px 0 8px;background:transparent;"
        "text-align:center;color:#315b54;font-size:.78rem;font-weight:800;"
        "letter-spacing:.18em;text-transform:uppercase;'>SmartClass AI</div>",
        unsafe_allow_html=True,
    )


def footer_home():
    _render_creator_footer()


def footer_dashboard():
    _render_creator_footer()
