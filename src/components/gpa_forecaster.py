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

    st.subheader("Attendance-to-Grade Impact Forecaster")
    st.caption(
        "Explore how future attendance changes your attendance standing. "
        "This is not a prediction of exam marks or final course grades."
    )

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

    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1:
        st.metric("Current Attendance", f"{current_pct}%", f"{attended}/{total} classes")
    with col_stat2:
        st.markdown(
            f"<div style='background:{color}22; border: 1px solid {color}; border-radius: 8px; padding: 10px; text-align: center;'>"
            f"<span style='color:{color}; font-size: 1.25rem; font-weight: 700;'>Attendance outlook: {grade}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with col_stat3:
        needed_for_75 = max(0, 3 * total - 4 * attended)
        if attended / total >= 0.75:
            st.metric("75% Requirement", "Met", delta="On track")
        else:
            st.metric("Classes to reach 75%", needed_for_75)

    st.write(f"*{advice}*")
    st.divider()
    st.markdown("**What if you attend future classes?**")
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
    st.info(
        f"If you attend the next **{future_classes} classes**, your attendance "
        f"would change from **{current_pct}%** to **{simulated_pct}%** "
        f"({delta_pct:+.1f} percentage points). Your attendance outlook would be "
        f"**{simulated_grade}**."
    )
