
from pathlib import Path
import streamlit as st

from answer_question import build_index, retrieve_chunks, build_context, generate_answer
from pipeline import build_from_pdf


PROJECT_ROOT = Path(__file__).resolve().parent
UPLOAD_PATH = PROJECT_ROOT / "data" / "uploaded_streamlit.pdf"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


st.set_page_config(page_title = "Document Q&A")
st.title("Document Q&A")
st.write("Upload a PDF, then ask questions about it.")


uploaded = st.file_uploader("Upload a PDF", type = ["pdf"])
if uploaded is not None:
    doc_key = uploaded.name + "-" + str(uploaded.size)

    if st.session_state.get("doc_key") != doc_key:
        if uploaded.size > MAX_UPLOAD_BYTES:
            st.error("File is too large (max 10 MB).")
            st.stop()

        UPLOAD_PATH.write_bytes(uploaded.getvalue())

        try:
            with st.spinner("Reading and indexing the PDF..."):
                pages, chunks, model, index = build_from_pdf(UPLOAD_PATH)
        except Exception as error:
            st.error("Could not use this PDF:" + str(error))
            st.stop()

        st.session_state["doc_key"] = doc_key
        st.session_state["chunks"] = chunks
        st.session_state["model"] = model
        st.session_state["index"] = index
        st.session_state["pages"] = len(pages)

if "index" not in st.session_state:
    st.info("Upload a PDF to begin.")
    st.stop()
st.success(
    "Ready: " + str(st.session_state["pages"]) + " pages,"
    + str(len(st.session_state["chunks"])) + " chunks."

)

question = st.chat_input(" Ask a question about the PDF")

if question:
    results = retrieve_chunks(
        question,
        st.session_state["chunks"],
        st.session_state["model"],
        st.session_state["index"],

    )
    try:
        answer = generate_answer(question, build_context(results))
        st.subheader("Answer")
        st.write(answer)

        with st.expander("View the source chunks"):
            for result in results:
                label = "Source chunk " + str(result["chunk_number"])
                label = label + "(score: " + str(round(result["score"], 3)) + ")"
                st.write(label)
                st.text(result["text"])
    except Exception as error:
        st.error("Something went wrong:" + str(error))

