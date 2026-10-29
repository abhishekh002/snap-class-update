import streamlit as st
import streamlit.components.v1 as components


def style_background_home():
    st.markdown("""
        <style>
            .stApp,
            [data-testid="stAppViewContainer"],
            [data-testid="stHeader"] {
                background: transparent !important;
            }

            .stApp div[data-testid="stColumn"] {
                background-color: #FFFFFF !important;
                padding: 2.5rem !important;
                border-radius: 5rem !important;
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
        'position:fixed;inset:0;z-index:-1;background:#22DAFF;pointer-events:none;';
      document.body.appendChild(canvas);

      const ctx = canvas.getContext('2d');
      const resize = () => { canvas.width = innerWidth; canvas.height = innerHeight; };
      resize(); addEventListener('resize', resize);

      const dots = Array.from({ length: 80 }, () => ({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.6,
        vy: (Math.random() - 0.5) * 0.6,
      }));

      function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        for (let i = 0; i < dots.length; i++) {
          const d = dots[i];
          d.x += d.vx; d.y += d.vy;
          if (d.x < 0 || d.x > canvas.width) d.vx *= -1;
          if (d.y < 0 || d.y > canvas.height) d.vy *= -1;

          ctx.beginPath();
          ctx.arc(d.x, d.y, 2.5, 0, Math.PI * 2);
          ctx.fillStyle = 'rgba(255,255,255,0.9)';
          ctx.fill();

          for (let j = i + 1; j < dots.length; j++) {
            const e = dots[j];
            const dist = Math.hypot(d.x - e.x, d.y - e.y);
            if (dist < 110) {
              ctx.strokeStyle = 'rgba(255,255,255,' + (1 - dist / 110) * 0.5 + ')';
              ctx.beginPath();
              ctx.moveTo(d.x, d.y);
              ctx.lineTo(e.x, e.y);
              ctx.stroke();
            }
          }
        }
        requestAnimationFrame(draw);
      }
      draw();
    }

    const parentDoc = window.parent.document;
    if (!parentDoc.getElementById('bg-script')) {
      const s = parentDoc.createElement('script');
      s.id = 'bg-script';
      s.textContent = '(' + init.toString() + ')()';
      parentDoc.body.appendChild(s);
    }
    </script>
    """, height=0)
    

def style_background_dashboard():

    st.markdown("""
        <style>

                .stApp {
                    background-color: #B8B8FF !important;
                    background-image:
                        radial-gradient(circle at 30% 70%, rgba(255,255,255,.5) 0 12px, transparent 13px),
                        radial-gradient(circle at 70% 40%, rgba(255,255,255,.35) 0 20px, transparent 21px),
                        radial-gradient(circle at 50% 20%, rgba(255,255,255,.45) 0 8px, transparent 9px) !important;
                    background-size: 200px 200px, 300px 300px, 150px 150px !important;
                    animation: rise 10s linear infinite !important;
                }

                [data-testid="stHeader"] {
                    background: transparent !important;
                }

                @keyframes rise {
                    from { background-position: 0 0, 0 0, 0 0; }
                    to   { background-position: 0 -200px, 0 -300px, 0 -150px; }
                }

        </style>

                """
            ,unsafe_allow_html=True)
    

    

def style_base_layout():
# asdasd
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Climate+Crisis:YEAR@1979&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@100..900&display=swap');

                
         /* Hide Top Bar of streamlit */
            #MainMenu, footer, header {
                visibility: hidden;
            }
                
            .block-container {
                padding-top:1.5rem !important;    
            }

            h1 {
                font-family: 'Climate Crisis', sans-serif !important;
                font-size: 3.5rem !important;
                line-height:1.1 1important;
                margin-bottom:0rem !important;
            }
                

            h2 {
                font-family: 'Climate Crisis', sans-serif !important;
                font-size: 2rem !important;
                line-height:0.9 !important;
                margin-bottom:0rem !important;
            }
                
            h3, h4, p {
                font-family: 'Outfit', sans-serif;    
            }
                

            button{
                border-radius: 1.5rem !important;
                background-color: #5865F2 !important;
                color: white !important;
                padding: 10px 20px !important;
                border: none !important;
                transition: transform 0.25s ease-in-out !important;
                }

            button[kind="secondary"]{
                border-radius: 1.5rem !important;
                background-color: #EB459E !important;
                color: white !important;
                padding: 10px 20px !important;
                border: none !important;
                transition: transform 0.25s ease-in-out !important;
                }

            button[kind="tertiary"]{
                border-radius: 1.5rem !important;
                background-color: black !important;
                color: white !important;
                padding: 10px 20px !important;
                border: none !important;
                transition: transform 0.25s ease-in-out !important;
                }

            button:hover{
                transform :scale(1.05)}
        </style>  

                """
            ,unsafe_allow_html=True)