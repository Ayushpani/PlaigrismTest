import streamlit as st
import spacy
import fitz  # PyMuPDF
import io
from PyPDF2 import PdfReader
import plotly.graph_objects as go

# Load spaCy model
@st.cache_resource
def load_spacy_model():
    return spacy.load("en_core_web_sm")

nlp = load_spacy_model()

def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def preprocess_text(text):
    doc = nlp(text)
    tokens = [token.lemma_.lower() for token in doc if not token.is_stop and not token.is_punct and token.is_alpha]
    return " ".join(tokens)

def calculate_plagiarism(user_text, target_text):
    user_doc = nlp(user_text)
    target_doc = nlp(target_text)
    
    user_tokens = set([token.text.lower() for token in user_doc])
    target_tokens = set([token.text.lower() for token in target_doc])
    
    common_tokens = user_tokens.intersection(target_tokens)
    plagiarism_percentage = (len(common_tokens) / len(user_tokens)) * 100 if user_tokens else 0
    
    return plagiarism_percentage, common_tokens

def create_donut_chart(plagiarism_percentage):
    fig = go.Figure(go.Pie(
        values=[plagiarism_percentage, 100 - plagiarism_percentage],
        labels=['Plagiarized', 'Original'],
        hole=0.7,
        marker_colors=['#FF6B6B', '#4ECDC4']
    ))
    fig.update_layout(
        title_text="Plagiarism Percentage",
        annotations=[dict(text=f'{plagiarism_percentage:.1f}%', x=0.5, y=0.5, font_size=20, showarrow=False)]
    )
    return fig

def highlight_pdf(pdf_file, common_tokens):
    pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
    for page in pdf_document:
        words = page.get_text("words")
        for word in words:
            if word[4].lower() in common_tokens:
                highlight = page.add_highlight_annot(word[:4])
                highlight.set_colors({"stroke": (1, 0, 0), "fill": (1, 0.8, 0.8)})
                highlight.update()
    
    pdf_output = io.BytesIO()
    pdf_document.save(pdf_output)
    pdf_output.seek(0)
    return pdf_output

# Streamlit UI
st.title("Plagiarism Checker")
st.sidebar.title("Upload Documents")

# Upload user document
user_file = st.sidebar.file_uploader("Upload your document", type="pdf")

# Upload or select target document
target_option = st.sidebar.radio("Choose target document option:", ("Upload target document", "Use default target document"))

if target_option == "Upload target document":
    target_file = st.sidebar.file_uploader("Upload target document", type="pdf")
else:
    target_file = "target.pdf"  # Make sure this file exists in your directory

if user_file is not None and (target_file is not None or target_option == "Use default target document"):
    # Extract text from uploaded files
    user_text = extract_text_from_pdf(user_file)
    
    if target_option == "Upload target document":
        target_text = extract_text_from_pdf(target_file)
    else:
        try:
            target_text = extract_text_from_pdf(open(target_file, "rb"))
        except FileNotFoundError:
            st.error(f"Target file '{target_file}' not found. Please make sure it exists in the current directory.")
            st.stop()

    # Preprocess texts
    user_text_processed = preprocess_text(user_text)
    target_text_processed = preprocess_text(target_text)

    # Calculate plagiarism
    plagiarism_percentage, common_tokens = calculate_plagiarism(user_text_processed, target_text_processed)

    # Display interactive donut chart
    fig = create_donut_chart(plagiarism_percentage)
    st.plotly_chart(fig)

    # Create highlighted PDF
    user_file.seek(0)  # Reset file pointer
    highlighted_pdf = highlight_pdf(user_file, common_tokens)

    # Provide download option for highlighted PDF
    st.download_button(
        label="Download Highlighted PDF",
        data=highlighted_pdf,
        file_name="highlighted_plagiarism.pdf",
        mime="application/pdf"
    )

else:
    st.write("Please upload both user and target documents to check for plagiarism.")