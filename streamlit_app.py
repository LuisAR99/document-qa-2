import streamlit as st
from openai import OpenAI
import pdfplumber 

# Show title and description.
st.title("📄 Document question answering")
st.write(
    "Upload a document below and ask a question about it – GPT will answer! "
    "To use this app, you need to provide an OpenAI API key, which you can get [here](https://platform.openai.com/account/api-keys). "
)
uploaded_file = None
question = ""
# Ask user for their OpenAI API key via `st.text_input`.
# Alternatively, you can store the API key in `./.streamlit/secrets.toml` and access it
# via `st.secrets`, see https://docs.streamlit.io/develop/concepts/connections/secrets-management
openai_api_key = st.text_input("OpenAI API Key", type="password")
openai_api_key = openai_api_key.strip()  
client = OpenAI(api_key=openai_api_key, timeout=30, max_retries=2)
if not openai_api_key:
    st.info("Please add your OpenAI API key to continue.", icon="🗝️")
else:

    # Create an OpenAI client.
    client = OpenAI(api_key=openai_api_key)

    # Let the user upload a file via `st.file_uploader`.
    uploaded_file = st.file_uploader(
        "Upload a document (.txt or .pdf)", type=("txt", "pdf")
    )

    # Ask the user for a question via `st.text_area`.
    question = st.text_area(
        "Now ask a question about the document!",
        placeholder="Can you give me a short summary?",
        disabled=not uploaded_file,
    )

if uploaded_file and question:
    document = ""

    # Make sure the buffer is at the start for every rerun
    if hasattr(uploaded_file, "seek"):
        uploaded_file.seek(0)

    if uploaded_file.type == "text/plain":
        # Handle .txt files
        document = uploaded_file.read().decode("utf-8", errors="ignore")

    elif uploaded_file.type == "application/pdf":
        # Handle .pdf files using pdfplumber
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                document += page.extract_text() or ""  # safe for blank pages

    else:
        st.error("Unsupported file type. Please upload a .txt or .pdf.")
        document = ""

    if document:
        messages = [
            {
                "role": "user",
                "content": f"Here's a document: {document} \n\n---\n\n {question}",
            }
        ]

        stream = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            stream=True,
            timeout=30
        )

from openai import APIConnectionError, APIStatusError, RateLimitError, AuthenticationError

try:
    # 1) Try NON-streaming with a timeout
    resp = client.chat.completions.create(
        model="gpt-5",
        messages=[{"role": "user", "content": f"Here's a document: {document}\n\n---\n\n{question}"}],
        timeout=30,  # seconds
    )
    st.write(resp.choices[0].message.content)

except APIConnectionError as e:
    st.error(f"Network/connection problem to OpenAI: {e}")
except AuthenticationError:
    st.error("Authentication failed. Check your API key (no spaces, correct key).")
except RateLimitError:
    st.error("Rate limited. Try again or reduce request frequency.")
except APIStatusError as e:
    st.error(f"OpenAI API returned status {e.status_code}: {e.message}")
except Exception as e:
    st.error(f"Unexpected error: {e}")

