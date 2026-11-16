from datetime import date

import streamlit as st
from postgrest.exceptions import APIError
from storage3.exceptions import StorageApiError

from src.database.assessments_db import (
    ALLOWED_FILE_TYPES,
    MAX_SUBMISSION_SIZE,
    create_assessment,
    download_assessment_file,
    get_assessment_submissions,
    get_enrolled_students,
    get_student_assessments,
    get_student_submission,
    get_teacher_assessments,
    grade_assessment_submission,
    record_physical_submission,
    release_assessment_results,
    submit_online_assessment,
)


ASSESSMENT_FILE_TYPES = sorted(ALLOWED_FILE_TYPES)


def _teacher_assessment_tab(note: dict, teacher: dict) -> None:
    teacher_id = teacher.get("teacher_id") or teacher.get("id")
    if teacher_id is None:
        st.error("Your teacher account is missing an ID. Please log in again.")
        return
    if str(note.get("teacher_id")) != str(teacher_id):
        st.error("You can only publish assessments for your own notes.")
        return

    st.markdown("### Create an assessment for this note")
    st.caption("Students enrolled in this subject will see the assessment here.")
    with st.form(f"create_assessment_{note['id']}"):
        title = st.text_input("Assessment title *")
        instructions = st.text_area("Assessment questions and instructions *")
        assignment_file = st.file_uploader(
            "Optional assessment sheet",
            type=ASSESSMENT_FILE_TYPES,
            key=f"assessment_sheet_{note['id']}",
        )
        due_date = st.date_input(
            "Submission deadline (inclusive)",
            value=date.today(),
            min_value=date.today(),
            help="Submissions close after this date, using the app server's local date.",
        )
        submission_mode_label = st.radio(
            "How will students submit?",
            ["Upload a file in the app", "Hand in physically"],
            horizontal=True,
        )
        max_score = st.number_input(
            "Maximum score",
            min_value=1.0,
            max_value=10000.0,
            value=100.0,
            step=1.0,
        )
        create_clicked = st.form_submit_button(
            "Publish Assessment", type="primary", width="stretch"
        )

    if create_clicked:
        if not title.strip():
            st.error("Enter an assessment title.")
        elif not instructions.strip() and assignment_file is None:
            st.error("Add instructions or attach an assessment sheet.")
        else:
            try:
                create_assessment(
                    note_id=str(note["id"]),
                    subject_id=note["subject_id"],
                    teacher_id=teacher_id,
                    title=title,
                    instructions=instructions,
                    due_date=due_date,
                    submission_mode=(
                        "online"
                        if submission_mode_label == "Upload a file in the app"
                        else "physical"
                    ),
                    max_score=max_score,
                    assignment_file_name=(
                        assignment_file.name if assignment_file else None
                    ),
                    assignment_file_bytes=(
                        assignment_file.getvalue() if assignment_file else None
                    ),
                    assignment_file_type=(
                        assignment_file.type if assignment_file else ""
                    ),
                )
            except (
                APIError,
                RuntimeError,
                StorageApiError,
                ValueError,
                OSError,
            ) as error:
                st.error(f"Assessment could not be published: {error}")
            else:
                st.success("Assessment published for the enrolled students.")

    try:
        assessments = get_teacher_assessments(str(note["id"]), teacher_id)
    except (APIError, PermissionError, RuntimeError) as error:
        st.error(f"Could not load assessments: {error}")
        return

    for assessment in assessments:
        with st.container(border=True):
            st.markdown(f"### {assessment['title']}")
            st.write(assessment.get("instructions") or "No additional instructions.")
            st.caption(
                f"Due: {assessment['due_date']} · "
                f"Submission: {assessment['submission_mode']} · "
                f"Maximum score: {assessment['max_score']}"
            )
            if assessment.get("assignment_file_path"):
                try:
                    assignment_bytes = download_assessment_file(
                        assessment["assignment_file_path"]
                    )
                except (
                    APIError,
                    PermissionError,
                    RuntimeError,
                    StorageApiError,
                    ValueError,
                ) as error:
                    st.error(f"Could not load the assessment sheet: {error}")
                else:
                    st.download_button(
                        "Download assessment sheet",
                        data=assignment_bytes,
                        file_name=assessment["assignment_file_name"],
                        key=f"teacher_assessment_file_{assessment['id']}",
                    )

            try:
                submissions = get_assessment_submissions(assessment["id"])
            except (APIError, PermissionError, RuntimeError, ValueError) as error:
                st.error(f"Could not load student submissions: {error}")
                continue

            if assessment["submission_mode"] == "physical":
                try:
                    students = get_enrolled_students(assessment["subject_id"])
                except (APIError, PermissionError, RuntimeError) as error:
                    st.error(f"Could not load the enrolled students: {error}")
                    continue
                submitted_ids = {
                    str(submission["student_id"]) for submission in submissions
                }
                unsubmitted_students = [
                    student
                    for student in students
                    if str(student["student_id"]) not in submitted_ids
                ]
                if unsubmitted_students:
                    student_options = {
                        f"{student['name']} (ID {student['student_id']})": student
                        for student in unsubmitted_students
                    }
                    with st.form(f"physical_received_{assessment['id']}"):
                        selected_student_label = st.selectbox(
                            "Record physical submission",
                            list(student_options),
                        )
                        submitted_on = st.date_input(
                            "Date received",
                            value=min(date.today(), date.fromisoformat(assessment["due_date"])),
                            key=f"physical_date_{assessment['id']}",
                        )
                        record_clicked = st.form_submit_button("Mark as received")
                    if record_clicked:
                        try:
                            recorded_submission = record_physical_submission(
                                assessment["id"],
                                teacher_id,
                                student_options[selected_student_label]["student_id"],
                                submitted_on,
                            )
                        except (
                            APIError,
                            PermissionError,
                            RuntimeError,
                            ValueError,
                        ) as error:
                            st.error(f"Submission could not be recorded: {error}")
                        else:
                            st.success("Physical submission recorded.")
                            recorded_submission["student_name"] = student_options[
                                selected_student_label
                            ]["name"]
                            submissions.append(recorded_submission)

            st.markdown("#### Student submissions")
            if not submissions:
                st.info("No students have submitted yet.")
            for submission in submissions:
                with st.expander(
                    f"{submission['student_name']} · {submission['submitted_on']}",
                    expanded=False,
                ):
                    if submission.get("file_path"):
                        try:
                            submission_bytes = download_assessment_file(
                                submission["file_path"]
                            )
                        except (
                            APIError,
                            PermissionError,
                            RuntimeError,
                            StorageApiError,
                            ValueError,
                        ) as error:
                            st.error(f"Could not download the student file: {error}")
                        else:
                            st.download_button(
                                "Download student submission",
                                data=submission_bytes,
                                file_name=submission["file_name"],
                                key=f"submission_file_{submission['id']}",
                            )
                    if assessment["results_released"]:
                        st.write(
                            f"Score: {submission['score']} / {assessment['max_score']}"
                        )
                        if submission.get("feedback"):
                            st.caption(submission["feedback"])
                    else:
                        with st.form(f"grade_submission_{submission['id']}"):
                            score = st.number_input(
                                f"Score (out of {assessment['max_score']})",
                                min_value=0.0,
                                max_value=float(assessment["max_score"]),
                                value=float(submission["score"] or 0),
                                step=1.0,
                            )
                            feedback = st.text_area(
                                "Feedback",
                                value=submission.get("feedback", ""),
                            )
                            grade_clicked = st.form_submit_button("Save grade")
                        if grade_clicked:
                            try:
                                grade_assessment_submission(
                                    submission["id"],
                                    assessment["id"],
                                    teacher_id,
                                    score,
                                    feedback,
                                )
                            except (
                                APIError,
                                PermissionError,
                                RuntimeError,
                                ValueError,
                            ) as error:
                                st.error(f"Grade could not be saved: {error}")
                            else:
                                submission["score"] = score
                                submission["feedback"] = feedback.strip()
                                st.success("Grade saved.")

            if assessment["results_released"]:
                st.success("Results have been released to students.")
            elif any(submission.get("score") is None for submission in submissions):
                st.info("Grade all received submissions before releasing results.")
            elif date.today() <= date.fromisoformat(assessment["due_date"]):
                st.info("Results can be released after the submission deadline.")
            elif st.button(
                "Release results to students",
                key=f"release_results_{assessment['id']}",
                type="primary",
            ):
                try:
                    release_assessment_results(assessment["id"], teacher_id)
                except (
                    APIError,
                    PermissionError,
                    RuntimeError,
                    ValueError,
                ) as error:
                    st.error(f"Results could not be released: {error}")
                else:
                    assessment["results_released"] = True
                    st.success("Results released to students.")


def _student_assessment_tab(note: dict, student: dict) -> None:
    student_id = student.get("student_id")
    if student_id is None:
        st.error("Your student account is missing an ID. Please log in again.")
        return

    try:
        assessments = get_student_assessments(
            str(note["id"]), note["subject_id"], student_id
        )
    except APIError as error:
        st.error(f"Could not load assessments: {error}")
        return

    if not assessments:
        st.info("There are no assessments for this note yet.")
        return

    for assessment in assessments:
        with st.expander(assessment["title"], expanded=True):
            st.write(assessment.get("instructions") or "No additional instructions.")
            st.caption(
                f"Due: {assessment['due_date']} · "
                f"Maximum score: {assessment['max_score']}"
            )
            if assessment.get("assignment_file_path"):
                try:
                    assignment_bytes = download_assessment_file(
                        assessment["assignment_file_path"]
                    )
                except (
                    APIError,
                    PermissionError,
                    RuntimeError,
                    StorageApiError,
                    ValueError,
                ) as error:
                    st.error(f"Could not load the assessment sheet: {error}")
                else:
                    st.download_button(
                        "Download assessment sheet",
                        data=assignment_bytes,
                        file_name=assessment["assignment_file_name"],
                        key=f"student_assessment_file_{assessment['id']}",
                    )

            try:
                submission = get_student_submission(assessment["id"], student_id)
            except (APIError, PermissionError, RuntimeError) as error:
                st.error(f"Could not load your submission: {error}")
                continue

            if submission:
                st.success(f"Submitted on {submission['submitted_on']}.")
                if assessment["results_released"]:
                    st.metric(
                        "Your score",
                        f"{submission['score']} / {assessment['max_score']}",
                    )
                    if submission.get("feedback"):
                        st.write(f"Teacher feedback: {submission['feedback']}")
                else:
                    st.info("Your teacher has not released results yet.")
            elif date.today() > date.fromisoformat(assessment["due_date"]):
                st.warning("The deadline has passed; submissions are closed.")
            elif assessment["submission_mode"] == "physical":
                st.info(
                    "Submit your work physically to your teacher by the deadline."
                )
            else:
                with st.form(f"student_submit_{assessment['id']}"):
                    submission_file = st.file_uploader(
                        "Choose your completed assessment",
                        type=ASSESSMENT_FILE_TYPES,
                        key=f"student_file_{assessment['id']}",
                    )
                    submit_clicked = st.form_submit_button(
                        "Submit assessment", type="primary"
                    )
                if submit_clicked:
                    if submission_file is None:
                        st.error("Choose a file before submitting.")
                    elif submission_file.size > MAX_SUBMISSION_SIZE:
                        st.error("Your submission must be 20 MB or smaller.")
                    else:
                        try:
                            submit_online_assessment(
                                assessment["id"],
                                student_id,
                                submission_file.name,
                                submission_file.getvalue(),
                                submission_file.type,
                            )
                        except (
                            APIError,
                            PermissionError,
                            RuntimeError,
                            StorageApiError,
                            ValueError,
                            OSError,
                        ) as error:
                            st.error(f"Submission failed: {error}")
                        else:
                            st.success("Your assessment was submitted.")


def render_assessment_tab(note: dict) -> None:
    teacher = st.session_state.get("teacher_data")
    if teacher:
        _teacher_assessment_tab(note, teacher)
        return

    student = st.session_state.get("student_data")
    if student:
        _student_assessment_tab(note, student)
        return

    st.info("Log in as a teacher or student to access assessments.")
