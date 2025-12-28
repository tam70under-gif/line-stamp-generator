import streamlit as st
from PIL import Image
import utils
import io
import os
from dotenv import load_dotenv

load_dotenv()

# --- Page Config ---
st.set_page_config(
    page_title="LINE Stamp Generator",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS for Mobile & Dark Mode ---
st.markdown("""
<style>
    /* Global Styles */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* Bigger Buttons for Touch */
    .stButton > button {
        width: 100%;
        height: 3rem;
        font-size: 1.2rem;
        border-radius: 12px;
        background-color: #4CAF50;
        color: white;
        border: none;
        transition: 0.3s;
    }
    .stButton > button:hover {
        background-color: #45a049;
    }
    
    /* Input Fields */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        background-color: #262730;
        color: white;
        border-radius: 10px;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #262730;
    }
    
    /* Headers */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
    }
    
    /* Grid Layout Helper */
    .grid-container {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
        gap: 1rem;
        padding: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar: Settings ---
with st.sidebar:
    st.header("⚙️ Settings")
    default_api_key = os.getenv("GOOGLE_API_KEY", "")
    api_key = st.text_input("Gemini API Key", value=default_api_key, type="password", help="Enter your Google Gemini API Key")
    
    if api_key:
        success, msg = utils.init_gemini(api_key)
        if success:
            st.success("API Key configured!")
        else:
            st.error(f"Error: {msg}")
    
    st.markdown("---")
    st.markdown("### About")
    st.info("Generates LINE stickers using Gemini 3 Pro (Imagen 3).")

# --- Main Interface ---
st.title("🎨 LINE Stamp Generator")
st.markdown("Upload a character, choose settings, and generate a sticker pack!")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("1. Base Character")
    uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
    base_image = None
    if uploaded_file:
        base_image = Image.open(uploaded_file)
        st.image(base_image, caption="Base Character", use_container_width=True)

with col2:
    st.subheader("2. Configuration")
    
    # Stamp Count
    stamp_count = st.select_slider(
        "Number of Stamps",
        options=[8, 16, 24, 32, 40],
        value=8
    )
    
    # Text Input
    st.markdown("### 3. Sticker Texts")
    default_texts = "Hello\nThank you\nOK\nGood night\nSorry\nCongrats\nLOL\nWait"
    text_input = st.text_area(
        "Enter text for each stamp (one per line)", 
        value=default_texts, 
        height=200
    )
    
    lines = [line.strip() for line in text_input.split('\n') if line.strip()]
    
    st.caption(f"Count Check: You have {len(lines)} lines of text. (Target: {stamp_count})")

# --- Generation Logic ---
if st.button("🚀 Generate Stamps"):
    if not api_key:
        st.error("Please enter your API Key in the sidebar.")
    elif not uploaded_file:
        st.error("Please upload a base character image.")
    elif len(lines) == 0:
        st.error("Please enter at least one line of text.")
    else:
        st.markdown("---")
        st.subheader("Results")
        
        # Prepare Progress Bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        generated_images = {}
        
        # Grid layout for display
        cols = st.columns(4) # 4 columns grid
        
        MAX_ITEMS = min(stamp_count, len(lines))
        
        for i in range(MAX_ITEMS):
            text = lines[i]
            status_text.text(f"Generating stamp {i+1}/{MAX_ITEMS}: '{text}'...")
            
            # Generate
            img = utils.generate_stamp(base_image, text, style_prompt="Anime style, cute, expressive")
            
            if img:
                generated_images[f"sticker_{i+1:02d}.png"] = img
                
                # Display in grid
                with cols[i % 4]:
                    st.image(img, caption=text, use_container_width=True)
            else:
                st.warning(f"Failed to generate: {text}")
            
            # Update Progress
            progress_bar.progress((i + 1) / MAX_ITEMS)
            
        status_text.text("Generation Complete!")
        
        # Download Button
        if generated_images:
            zip_data = utils.create_zip(generated_images)
            st.download_button(
                label="📦 Download All (ZIP)",
                data=zip_data,
                file_name="line_stamps.zip",
                mime="application/zip",
                key="download-btn"
            )

st.markdown("---")
st.caption("Powered by Google Gemini 3 Pro & Streamlit")
