import streamlit as st

def get_projected_grade(attendance_pct: float) -> tuple[str, str, str]:
    """Returns (grade_letter, badge_color, advice) based on attendance percentage."""
    if attendance_pct >= 95:
        return ("A+", "#10b981", "Exceptional consistency! You are in the top tier.")
    elif attendance_pct >= 85:
        return ("A", "#14b8a6", "Strong standing! Keep up this attendance habit.")
    elif attendance_pct >= 75:
        return ("B+", "#3b82f6", "Good standing. Meets the mandatory 75% university criteria.")
    elif attendance_pct >= 65:
        return ("C", "#f59e0b", "⚠️ Attendance Warning! Risk of being debarred if you miss more classes.")
    else:
        return ("D/F", "#ef4444", "🚨 Critical Deficit! You are currently below the required threshold.")

def render_gpa_forecaster(subjects_stats: list[dict]):
    """
    Renders the Attendance-to-GPA Impact Forecaster on the Student Dashboard.
    subjects_stats: list of dicts with keys: name, code, total, attended
    """
    if not subjects_stats:
        return

    st.markdown("""
        <style>
            .attendance-forecast-hero {
                margin: .2rem 0 1rem;
                padding: 20px 22px;
                border: 1px solid #d5e1d9;
                border-left: 5px solid #315b54;
                border-radius: 17px;
                background: linear-gradient(120deg,#203a43,#315b54 72%,#3c6658);
                box-shadow: 0 10px 25px rgba(32,58,67,.13);
            }
            .attendance-forecast-hero span {
                color: #d8ef9b;
                font-size: .68rem;
                font-weight: 700;
                letter-spacing: .14em;
                text-transform: uppercase;
            }
            .attendance-forecast-hero h2 {
                margin: 5px 0;
                color: #fffefa;
                font-size: clamp(1.25rem,2.4vw,1.65rem);
                line-height: 1.25;
            }
            .attendance-forecast-hero p {
                margin: 0;
                color: #e1ebe3;
                line-height: 1.5;
            }
            .attendance-forecast-outlook {
                min-height: 112px;
                box-sizing: border-box;
                padding: 16px;
                border: 1px solid #dce1d6;
                border-radius: 16px;
                background: #fffefa;
                box-shadow: 0 6px 18px rgba(32,58,67,.05);
            }
            .attendance-forecast-outlook small {
                display: block;
                color: #65746a;
                font-weight: 600;
            }
            .attendance-forecast-outlook strong {
                display: block;
                margin-top: 7px;
                font-size: 1.65rem;
                line-height: 1.15;
            }
            .attendance-forecast-outlook .detail {
                display: block;
                margin-top: 5px;
                color: #748176;
                font-size: .8rem;
            }
            .attendance-forecast-advice {
                margin: .85rem 0 1.15rem;
                padding: 12px 16px;
                border-left: 4px solid #829a79;
                border-radius: 0 12px 12px 0;
                background: #eef3eb;
                color: #385844;
                line-height: 1.5;
            }
            .attendance-forecast-scenario {
                margin-top: .75rem;
                padding: 17px 19px;
                border: 1px solid #cddbd1;
                border-left: 5px solid #315b54;
                border-radius: 15px;
                background: linear-gradient(120deg,#eaf1eb,#fffefa);
                color: #385844;
                line-height: 1.6;
            }
            .attendance-forecast-scenario .scenario-label {
                display: block;
                margin-bottom: 5px;
                color: #315b54;
                font-size: .68rem;
                font-weight: 700;
                letter-spacing: .12em;
                text-transform: uppercase;
            }
        </style>
        <section class="attendance-forecast-hero">
          <span>Plan your next steps</span>
          <h2>Attendance-to-Grade Impact Forecaster</h2>
          <p>See how attending future classes can change your attendance standing. This is not an exam or final-grade prediction.</p>
        </section>
    """, unsafe_allow_html=True)

    subject_names = [f"{subject['name']} ({subject['code']})" for subject in subjects_stats]
    selected_index = st.selectbox(
        "Select subject to forecast",
        range(len(subject_names)),
        format_func=lambda index: subject_names[index],
    )
    current = subjects_stats[selected_index]
    total = current["total"]
    attended = current["attended"]
    if total <= 0:
        st.info("No attendance has been recorded for this subject yet.")
        return

    current_pct = round((attended / total) * 100, 1)
    grade, color, advice = get_projected_grade(current_pct)

    requirement_met = attended / total >= 0.75
    needed_for_75 = max(0, 3 * total - 4 * attended)
    status_color = "#315b54" if requirement_met else "#bd7654"
    status_label = "Met" if requirement_met else f"{needed_for_75} more classes needed"
    col_stat1, col_stat2, col_stat3 = st.columns(3, gap="small")
    with col_stat1:
        st.markdown(
            f"<div class='attendance-forecast-outlook'>"
            f"<small>Current Attendance</small>"
            f"<strong style='color:#26382e'>{current_pct}%</strong>"
            f"<span class='detail'>{attended} of {total} classes</span></div>",
            unsafe_allow_html=True,
        )
    with col_stat2:
        st.markdown(
            f"<div class='attendance-forecast-outlook'>"
            f"<small>Attendance outlook</small>"
            f"<strong style='color:{color}'>{grade}</strong>"
            f"<span class='detail'>Based on attendance so far</span></div>",
            unsafe_allow_html=True,
        )
    with col_stat3:
        st.markdown(
            f"<div class='attendance-forecast-outlook'>"
            f"<small>75% Requirement</small>"
            f"<strong style='color:{status_color};font-size:1.25rem'>{status_label}</strong>"
            f"<span class='detail'>{'On track' if requirement_met else 'Attendance target'}</span></div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        f"<div class='attendance-forecast-advice'>{advice}</div>",
        unsafe_allow_html=True,
    )
    st.markdown("#### What if you attend future classes?")
    future_classes = st.slider(
        "Consecutive classes attended",
        min_value=1,
        max_value=20,
        value=4,
        key=f"attendance_forecast_{current.get('subject_id', selected_index)}",
    )

    simulated_total = total + future_classes
    simulated_attended = attended + future_classes
    simulated_pct = round((simulated_attended / simulated_total) * 100, 1)
    simulated_grade, _, _ = get_projected_grade(simulated_pct)
    delta_pct = round(simulated_pct - current_pct, 1)
    st.markdown(
        f"<div class='attendance-forecast-scenario'>"
        f"<span class='scenario-label'>Projected scenario</span>"
        f"If you attend the next <strong>{future_classes} classes</strong>, your "
        f"attendance would move from <strong>{current_pct}%</strong> to "
        f"<strong>{simulated_pct}%</strong> ({delta_pct:+.1f} percentage points). "
        f"Your attendance outlook would be <strong>{simulated_grade}</strong>."
        f"</div>",
        unsafe_allow_html=True,
    )
