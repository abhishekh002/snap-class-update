import streamlit as st
import streamlit.components.v1 as components


def style_background_home():
    st.markdown("""
        <style>
            .stApp,
            [data-testid="stAppViewContainer"],
            [data-testid="stApp"] {
                --sc-paper: #f5f3ec;
                background: transparent !important;
                z-index: 1 !important;
            }

            [data-testid="stHeader"] { background: transparent !important; }

            .stApp div[data-testid="stColumn"] {
                box-sizing: border-box;
                background-color: #fffefa !important;
                padding: 2rem !important;
                border: 1px solid #dce1d6;
                border-radius: 1.5rem !important;
                box-shadow: 0 14px 36px rgba(48, 66, 51, .08);
            }

            iframe[height="0"] { display: none; }
        </style>
    """, unsafe_allow_html=True)

    components.html("""
    <script>
    function init() {
      if (document.getElementById('bg-canvas')) return;

      const canvas = document.createElement('canvas');
      canvas.id = 'bg-canvas';
      canvas.style.cssText =
        'position:fixed;inset:0;z-index:0;background:linear-gradient(125deg,#e6ecdf,#dbe6d5 62%,#e8eadc);pointer-events:none;';
      document.body.appendChild(canvas);

      const ctx = canvas.getContext('2d');
      const resize = () => { canvas.width = innerWidth; canvas.height = innerHeight; };
      resize(); addEventListener('resize', resize);

      let elapsed = 0;

      function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        elapsed += 1;
        const scanY = (elapsed * 0.55) % (canvas.height + 80) - 40;
        const scanGlow = ctx.createLinearGradient(0, scanY - 22, 0, scanY + 22);
        scanGlow.addColorStop(0, 'rgba(130,154,121,0)');
        scanGlow.addColorStop(0.5, 'rgba(130,154,121,0.12)');
        scanGlow.addColorStop(1, 'rgba(130,154,121,0)');
        ctx.fillStyle = scanGlow;
        ctx.fillRect(0, scanY - 22, canvas.width, 44);

        const marks = [
          { x: canvas.width * 0.10, y: canvas.height * 0.28, phase: 0.0, checked: true },
          { x: canvas.width * 0.90, y: canvas.height * 0.32, phase: 1.4, checked: false },
          { x: canvas.width * 0.12, y: canvas.height * 0.76, phase: 2.7, checked: false },
          { x: canvas.width * 0.88, y: canvas.height * 0.78, phase: 4.1, checked: true },
        ];
        for (const mark of marks) {
          const pulse = 0.22 + (Math.sin(elapsed * 0.025 + mark.phase) + 1) * 0.06;
          const size = 25 + Math.sin(elapsed * 0.02 + mark.phase) * 2;
          ctx.save();
          ctx.globalAlpha = pulse;
          ctx.translate(mark.x, mark.y);
          ctx.strokeStyle = '#385844';
          ctx.lineWidth = 2;
          ctx.lineCap = 'round';
          const half = size / 2;
          const corner = 8;
          ctx.beginPath();
          ctx.moveTo(-half, -half + corner); ctx.lineTo(-half, -half); ctx.lineTo(-half + corner, -half);
          ctx.moveTo(half - corner, -half); ctx.lineTo(half, -half); ctx.lineTo(half, -half + corner);
          ctx.moveTo(half, half - corner); ctx.lineTo(half, half); ctx.lineTo(half - corner, half);
          ctx.moveTo(-half + corner, half); ctx.lineTo(-half, half); ctx.lineTo(-half, half - corner);
          ctx.stroke();

          ctx.beginPath();
          ctx.arc(0, -3, 4, 0, Math.PI * 2);
          ctx.moveTo(-7, 8);
          ctx.quadraticCurveTo(-7, 2, 0, 2);
          ctx.quadraticCurveTo(7, 2, 7, 8);
          ctx.strokeStyle = '#829a79';
          ctx.lineWidth = 1.7;
          ctx.stroke();

          if (mark.checked) {
            ctx.globalAlpha = pulse + 0.16;
            ctx.beginPath();
            ctx.arc(half - 1, half - 1, 5, 0, Math.PI * 2);
            ctx.fillStyle = '#b97453';
            ctx.fill();
            ctx.beginPath();
            ctx.moveTo(half - 3.5, half - 1);
            ctx.lineTo(half - 1.5, half + 1);
            ctx.lineTo(half + 2, half - 3);
            ctx.strokeStyle = '#fffefa';
            ctx.lineWidth = 1.3;
            ctx.stroke();
          }
          ctx.restore();
        }
        canvas._animationFrame = requestAnimationFrame(draw);
      }
      draw();
    }

    const parentDoc = window.parent.document;
    const oldCanvas = parentDoc.getElementById('bg-canvas');
    if (oldCanvas?._animationFrame) {
      window.parent.cancelAnimationFrame(oldCanvas._animationFrame);
    }
    oldCanvas?.remove();
    parentDoc.getElementById('bg-script')?.remove();
    const s = parentDoc.createElement('script');
    s.id = 'bg-script';
    s.textContent = '(' + init.toString() + ')()';
    parentDoc.body.appendChild(s);
    </script>
    """, height=0)


def style_background_dashboard():
    st.markdown("""
        <style>
            .stApp {
                --sc-paper: #f5f3ec;
                background-color: #f5f3ec !important;
                background-image: radial-gradient(ellipse at 12% 8%, rgba(211,224,202,.48), transparent 34rem) !important;
            }

            [data-testid="stHeader"] { background: transparent !important; }
        </style>
    """, unsafe_allow_html=True)

    # The animated canvas belongs only to Home. Remove it when a portal opens
    # so it cannot cover the sign-in or dashboard interface.
    components.html("""
        <script>
        const parentDoc = window.parent.document;
        const canvas = parentDoc.getElementById('bg-canvas');
        if (canvas?._animationFrame) {
          window.parent.cancelAnimationFrame(canvas._animationFrame);
        }
        canvas?.remove();
        parentDoc.getElementById('bg-script')?.remove();
        </script>
    """, height=0)


def style_base_layout():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Lora:wght@500;600;700&display=swap');

            :root {
                --sc-forest: #385844;
                --sc-sage: #829a79;
                --sc-terracotta: #b97453;
                --sc-coral: #c87869;
                --sc-cobalt: #dbe6d5;
                --sc-paper: #f5f3ec;
                --sc-card: #fffefa;
                --sc-ink: #26382e;
                --sc-muted: #65746a;
                --sc-line: #dce1d6;
            }

            #MainMenu, footer, header { visibility: hidden; }

            .stApp, [data-testid="stAppViewContainer"] {
                color: var(--sc-ink);
                background-color: var(--sc-paper);
            }

            .block-container { padding-top: 1.5rem !important; }

            h1, h2, h3, h4 {
                color: var(--sc-forest) !important;
                font-family: 'Lora', Georgia, serif !important;
                letter-spacing: -.025em;
            }

            h1 { font-size: clamp(2.1rem, 4vw, 3.25rem) !important; line-height: 1.12 !important; }
            h2 { font-size: clamp(1.65rem, 3vw, 2.15rem) !important; line-height: 1.2 !important; }

            body, input, textarea, select, [data-testid="stMarkdownContainer"],
            [data-testid="stWidgetLabel"] {
                font-family: 'DM Sans', 'Segoe UI', sans-serif;
            }

            [data-testid="stMarkdownContainer"] p { color: var(--sc-ink); }
            [data-testid="stWidgetLabel"],
            [data-testid="stCaptionContainer"],
            [data-testid="stMarkdownContainer"] small { color: var(--sc-muted) !important; }
            a { color: var(--sc-forest) !important; text-decoration-thickness: 1px; }

            .stButton > button,
            .stFormSubmitButton > button,
            .stDownloadButton > button {
                min-height: 2.65rem;
                padding: .55rem 1.15rem !important;
                border: 1.5px solid var(--sc-sage) !important;
                border-radius: 999px !important;
                background: #ffffff !important;
                color: var(--sc-forest) !important;
                font-weight: 600 !important;
                box-shadow: 0 3px 9px rgba(48,66,51,.09);
                transition: background-color .18s ease, color .18s ease, border-color .18s ease, transform .18s ease, box-shadow .18s ease;
            }

            .stButton > button p,
            .stFormSubmitButton > button p,
            .stDownloadButton > button p,
            .stButton > button span,
            .stFormSubmitButton > button span,
            .stDownloadButton > button span {
                color: inherit !important;
            }

            .stButton > button[kind="primary"],
            .stFormSubmitButton > button[kind="primary"],
            .stButton button[data-testid="stBaseButton-primary"],
            .stFormSubmitButton button[data-testid="stBaseButton-primary"] {
                border-color: var(--sc-forest) !important;
                background: var(--sc-forest) !important;
                color: #fffefa !important;
            }

            .stButton > button[kind="secondary"],
            .stFormSubmitButton > button[kind="secondary"],
            .stButton button[data-testid="stBaseButton-secondary"] {
                border-color: var(--sc-terracotta) !important;
                background: var(--sc-terracotta) !important;
                color: #ffffff !important;
            }

            .stButton > button[kind="tertiary"] {
                border-color: var(--sc-sage) !important;
                background: #e6ece1 !important;
                color: var(--sc-forest) !important;
                box-shadow: none;
            }

            .stButton > button:hover,
            .stFormSubmitButton > button:hover,
            .stDownloadButton > button:hover {
                border-color: var(--sc-sage) !important;
                background: #e6ece1 !important;
                color: var(--sc-forest) !important;
                transform: translateY(-1px);
                box-shadow: 0 5px 12px rgba(38,56,46,.1);
            }

            .stButton > button[kind="primary"]:hover,
            .stFormSubmitButton > button[kind="primary"]:hover,
            .stButton button[data-testid="stBaseButton-primary"]:hover {
                border-color: #294a36 !important;
                background: #294a36 !important;
                color: white !important;
            }

            .stButton > button[kind="secondary"]:hover,
            .stButton button[data-testid="stBaseButton-secondary"]:hover {
                border-color: #965b41 !important;
                background: #965b41 !important;
                color: #ffffff !important;
            }

            .stButton > button:focus-visible,
            .stFormSubmitButton > button:focus-visible,
            .stDownloadButton > button:focus-visible {
                outline: 3px solid rgba(185,116,83,.55) !important;
                outline-offset: 2px;
            }

            input, textarea, [data-baseweb="select"] > div {
                border-color: #b9c8b4 !important;
                border-radius: .75rem !important;
                background-color: #ffffff !important;
            }
        </style>
    """, unsafe_allow_html=True)
