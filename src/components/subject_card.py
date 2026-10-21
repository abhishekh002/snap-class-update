from collections.abc import Callable, Sequence

import streamlit as st


def subject_card(
    name: str,
    code: str,
    section: str,
    stats: Sequence[tuple[str, str, object]],
    footer_callback: Callable[[], None] | None = None,
) -> None:
    with st.container(border=True):
        st.subheader(name)
        st.caption(f"Code: {code} · Section: {section}")

        if stats:
            columns = st.columns(len(stats))
            for column, (icon, label, value) in zip(columns, stats):
                with column:
                    st.metric(label=f"{icon} {label}", value=value)

        if footer_callback is not None:
            footer_callback()
