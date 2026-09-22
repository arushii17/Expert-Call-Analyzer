import asyncio
import sys
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).parent
sys.path.append(str(ROOT / "src"))

from analyzer import (
    analyze_guide_question,
    analyze_cross_call,
    ask_transcripts
)

from parser import load_all_transcripts


st.set_page_config(
    page_title="Expert Call Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: #f7f9fc;
}

[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    max-width: 1240px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #e5e7eb;
}

h1, h2, h3 {
    letter-spacing: -0.02em;
}

div[data-testid="stMetric"] {
    background: white;
    border: 1px solid #e5e7eb;
    padding: 14px 16px;
    border-radius: 12px;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: #e2e8f0;
    border-radius: 14px;
    background: white;
}

div[data-testid="stExpander"] {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
}

div[data-baseweb="tab-list"] {
    gap: 8px;
    margin-top: 10px;
}

button[data-baseweb="tab"] {
    padding-left: 15px;
    padding-right: 15px;
}

.stButton > button,
.stFormSubmitButton > button {
    border-radius: 9px;
    font-weight: 600;
}

[data-testid="stCaptionContainer"] {
    color: #64748b;
}
</style>
""", unsafe_allow_html=True)


def run_async(coro):
    return asyncio.run(coro)


def flag_for_market(market):
    if market == "France":
        return "🇫🇷"
    if market == "Germany":
        return "🇩🇪"
    return "🇬🇧"


def show_evidence(evidence):

    if not evidence:
        st.caption("No supporting transcript evidence.")
        return

    for item in evidence:

        text = item.get(
            "quote",
            item.get("text", "")
        )

        st.caption(
            f"{item['timestamp']}  ·  {item['source']}"
        )

        st.markdown(f"> {text}")


segments = load_all_transcripts()

experts = {}

for segment in segments:

    expert = segment["expert"]

    if expert not in experts:
        experts[expert] = {
            "market": segment["market"],
            "role": segment["role"],
            "source": segment["source"],
            "segments": []
        }

    experts[expert]["segments"].append(segment)


with st.sidebar:

    st.title("Expert Call Analyzer")

    st.caption(
        "European Robotic Surgery Market"
    )

    st.divider()

    st.caption("SOURCES")

    for expert, data in experts.items():

        st.markdown(
            f"**{flag_for_market(data['market'])} "
            f"{data['market']}**"
        )

        st.write(expert)
        st.caption(data["role"])

    st.divider()

    st.caption(
        "AI answers are grounded only in the supplied interview transcripts."
    )


st.caption("EXPERT RESEARCH WORKSPACE")

st.title("European Robotic Surgery Market")

st.write(
    "Compare expert perspectives, identify cross-market themes "
    "and explore the original interview evidence."
)


st.write("")

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric("Expert calls", "3")

with m2:
    st.metric("Markets", "3")

with m3:
    st.metric("Guide questions", "6")

with m4:
    st.metric(
        "Transcript segments",
        len(segments)
    )


st.write("")


guide_tab, cross_tab, ask_tab, transcript_tab = st.tabs([
    "📋 Interview Guide",
    "🔀 Cross-Call Analysis",
    "💬 Ask Transcripts",
    "📄 Source Transcripts"
])


with guide_tab:

    st.header("Interview Guide")

    st.caption(
        "Select a research question to compare expert responses."
    )

    guide_questions = [
        "How would you describe current adoption of robotic surgery in your market?",
        "What are the main barriers to adoption?",
        "How important are hospital budgets and ROI in purchasing decisions?",
        "How important are surgeon training and clinical outcomes?",
        "What adoption trend do you expect over the next 3–5 years?",
        "What is the typical hospital decision-making timeline for purchasing a new robotic system?"
    ]

    selected_question = st.selectbox(
        "Research question",
        guide_questions,
        key="guide_select"
    )

    if "guide_cache" not in st.session_state:
        st.session_state.guide_cache = {}

    if selected_question not in st.session_state.guide_cache:

        with st.spinner("Analyzing expert responses..."):

            try:

                results = run_async(
                    analyze_guide_question(
                        selected_question
                    )
                )

                st.session_state.guide_cache[
                    selected_question
                ] = results

            except Exception as error:

                st.error(
                    f"Analysis failed: {error}"
                )

    if selected_question in st.session_state.guide_cache:

        results = st.session_state.guide_cache[
            selected_question
        ]

        st.subheader("Expert perspectives")

        cols = st.columns(3)

        for col, result in zip(cols, results):

            with col:

                with st.container(border=True):

                    st.caption(
                        f"{flag_for_market(result['market'])} "
                        f"{result['market'].upper()}"
                    )

                    st.subheader(
                        result["expert"]
                    )

                    st.write(
                        result["answer"]
                    )

                with st.expander(
                    "View source evidence"
                ):

                    show_evidence(
                        result["evidence"]
                    )


with cross_tab:

    st.header("Cross-Call Analysis")

    st.caption(
        "A concise view of where experts align and where their perspectives differ."
    )

    if "cross_analysis" not in st.session_state:

        with st.spinner(
            "Comparing expert perspectives..."
        ):

            try:

                st.session_state.cross_analysis = run_async(
                    analyze_cross_call()
                )

            except Exception as error:

                st.error(
                    f"Analysis failed: {error}"
                )

    if "cross_analysis" in st.session_state:

        analysis = st.session_state.cross_analysis

        st.subheader("Shared themes")

        themes = analysis.get(
            "common_themes",
            []
        )

        if themes:

            theme_columns = st.columns(
                len(themes)
            )

            for column, theme in zip(
                theme_columns,
                themes
            ):

                with column:

                    with st.container(
                        border=True
                    ):

                        st.markdown(
                            f"### {theme['theme'].title()}"
                        )

                        st.write(
                            theme["summary"]
                        )

                        st.caption(
                            "🇫🇷 France  ·  "
                            "🇩🇪 Germany  ·  "
                            "🇬🇧 UK"
                        )

        st.divider()

        st.subheader(
            "Differences in perspective"
        )

        for item in analysis.get(
            "differences",
            []
        ):

            st.markdown(
                f"### {item['topic'].title()}"
            )

            france, germany, uk = st.columns(3)

            with france:

                with st.container(
                    border=True
                ):

                    st.caption("🇫🇷 FRANCE")

                    st.write(
                        item["france"]
                    )

            with germany:

                with st.container(
                    border=True
                ):

                    st.caption("🇩🇪 GERMANY")

                    st.write(
                        item["germany"]
                    )

            with uk:

                with st.container(
                    border=True
                ):

                    st.caption("🇬🇧 UNITED KINGDOM")

                    st.write(
                        item["uk"]
                    )

            st.info(
                f"**Key takeaway:** "
                f"{item['difference']}"
            )

            st.write("")


with ask_tab:

    st.header("Ask the Interviews")

    st.caption(
        "Ask about one expert, compare markets, "
        "or explore a topic across all three calls."
    )

    st.write("")

    st.markdown(
        "**Example questions**"
    )

    st.caption(
        "• How does training differ across markets?  "
        "• What drives purchasing decisions?  "
        "• What growth do the experts expect?"
    )

    with st.form(
        "question_form",
        clear_on_submit=False
    ):

        question = st.text_input(
            "Ask a question",
            placeholder=(
                "What do the experts say about procedure volume?"
            )
        )

        submitted = st.form_submit_button(
            "Analyze transcripts",
            type="primary"
        )

    if submitted:

        if not question.strip():

            st.warning(
                "Enter a question first."
            )

        else:

            with st.spinner(
                "Analyzing transcript evidence..."
            ):

                try:

                    result = run_async(
                        ask_transcripts(
                            question
                        )
                    )

                    st.session_state.ask_result = result
                    st.session_state.ask_question = question

                except Exception as error:

                    st.error(
                        f"Analysis failed: {error}"
                    )

    if "ask_result" in st.session_state:

        st.write("")

        result = st.session_state.ask_result

        with st.container(border=True):

            st.caption("ANALYSIS")

            st.subheader(
                st.session_state.ask_question
            )

            st.write(
                result["answer"]
            )

        if result["evidence"]:

            with st.expander(
                f"Supporting sources · "
                f"{len(result['evidence'])} excerpts"
            ):

                for item in result["evidence"]:

                    st.markdown(
                        f"**{flag_for_market(item['market'])} "
                        f"{item['expert']}**"
                    )

                    st.caption(
                        f"{item['timestamp']} · "
                        f"{item['source']}"
                    )

                    st.markdown(
                        f"> {item['text']}"
                    )

                    st.write("")

        else:

            st.caption(
                "No supporting transcript evidence."
            )


with transcript_tab:

    st.header("Source Transcripts")

    st.caption(
        "Read the original timestamped interviews used by the analysis."
    )

    expert_names = list(
        experts.keys()
    )

    selected_expert = st.selectbox(
        "Expert call",
        expert_names,
        format_func=lambda name: (
            f"{flag_for_market(experts[name]['market'])} "
            f"{name} — {experts[name]['market']}"
        ),
        key="transcript_select"
    )

    data = experts[
        selected_expert
    ]

    st.write("")

    st.subheader(
        f"{flag_for_market(data['market'])} "
        f"{selected_expert}"
    )

    st.caption(
        f"{data['role']} · "
        f"{data['market']} · "
        f"{data['source']}"
    )

    st.divider()

    for segment in data["segments"]:

        with st.container(border=True):

            if segment["speaker"] == "Interviewer":

                st.caption(
                    f"🎙️ {segment['timestamp']} · INTERVIEWER"
                )

            else:

                st.caption(
                    f"👤 {segment['timestamp']} · "
                    f"{selected_expert.upper()}"
                )

            st.write(
                segment["text"]
            )