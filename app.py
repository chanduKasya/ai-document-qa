import streamlit as st

from answer_question import build_index, retrieve_chunks, build_context, generate_answer
from search_document import load_chunks, CHUNKS_PATH


st.set_page_config(page_title = "Document Q&A")
st.title("Document Q&A")
st.write("Ask a question about the PDF used in this project.")


@st.cache_resource
def load_search_tools():
    chunks = load_chunks(CHUNKS_PATH)
    model, index = build_index(chunks)
    return chunks, model, index

chunks , model, index = load_search_tools()

question = st.chat_input("Your question")

if question:
    results = retrieve_chunks(question, chunks, model, index)
    try:
        answer = generate_answer(question, build_context(results))
        st.subheader("Answer")
        st.write(answer)

        with st.expander("View the source chunks"):
            for result in results:
                label = "Source chunk " + str(result["chunk_number"])
                label = label + " (score: " + str(round(result["score"], 3)) + ")"
                st.write(label)
                st.text(result["text"])
    except Exception as error:
        st.error("Something went wrong: " + str(error))