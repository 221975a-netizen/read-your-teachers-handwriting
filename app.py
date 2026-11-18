
import base64
import hashlib
from pathlib import Path

import streamlit as st
from PIL import Image
from streamlit_cropper import st_cropper

from recognizer import recognise_handwriting


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Read Your Teachers' Handwriting",
    page_icon="📝",
    layout="wide"
)


# --------------------------------------------------
# SESSION STATE FUNCTIONS
# --------------------------------------------------

def clear_recognition_results():
    """Clear previous transcription and confidence results."""

    keys = [
        "recognised_text",
        "average_confidence",
        "recognition_image",
        "editable_transcription"
    ]

    for key in keys:
        st.session_state.pop(key, None)


# --------------------------------------------------
# CUSTOM STYLING
# --------------------------------------------------

st.markdown("""
<style>

    .stApp {
        background-color: #FAF9F6;
    }

    /* Hide Streamlit header and menu */
    header[data-testid="stHeader"] {
        display: none !important;
    }

    #MainMenu,
    footer {
        display: none !important;
    }

    /* Remove unnecessary top spacing */
    [data-testid="stMainBlockContainer"] {
        padding-top: 0 !important;
        padding-bottom: 2rem !important;
        max-width: none !important;
    }

    [data-testid="stAppViewContainer"] {
        padding-top: 0 !important;
    }

    /* Main content width */
    .block-container {
        padding-left: 5vw !important;
        padding-right: 5vw !important;
    }

    /* Buttons */
    div.stButton > button {
        background-color: #438A85;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
    }

    div.stButton > button:hover {
        background-color: #34736F;
        color: white;
    }

    /* Section headings */
    h1, h2, h3 {
        color: #174C5A;
    }

</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# NEW WEBSITE HERO BANNER
# --------------------------------------------------

image_path = (
    Path(__file__).parent /
    "handwriting_hero_background.png"
)

if image_path.exists():

    hero_image = base64.b64encode(
        image_path.read_bytes()
    ).decode("utf-8")

    st.html(f"""
        <style>
            .hero-banner {{
                width: 100vw;
                margin-left: calc(50% - 50vw);
                margin-top: 0;
                padding: 0;
                line-height: 0;
            }}

            .hero-banner img {{
                display: block;
                width: 100%;
                height: auto;
                margin: 0;
                padding: 0;
            }}
        </style>

        <div class="hero-banner">
            <img
                src="data:image/png;base64,{hero_image}"
                alt="Read your teachers handwriting"
            >
        </div>
    """)

else:

    st.error(
        "Hero image not found. Please ensure "
        "handwriting_hero_background.png is in the "
        "same folder as app.py."
    )


# --------------------------------------------------
# IMAGE UPLOAD
# --------------------------------------------------

st.markdown("---")

st.header("Upload Handwriting")

st.write(
    "Upload an image of your teacher's handwriting "
    "to get an AI-generated transcription."
)

uploaded_file = st.file_uploader(
    "Choose a handwriting image",
    type=["png", "jpg", "jpeg"],
    key="handwriting_uploader"
)


# --------------------------------------------------
# DETECT NEW UPLOAD
# --------------------------------------------------

if uploaded_file is not None:

    uploaded_bytes = uploaded_file.getvalue()

    current_image_hash = hashlib.sha256(
        uploaded_bytes
    ).hexdigest()

    previous_image_hash = st.session_state.get(
        "previous_image_hash"
    )

    if current_image_hash != previous_image_hash:

        clear_recognition_results()

        st.session_state["previous_image_hash"] = (
            current_image_hash
        )

        st.session_state.pop(
            "previous_crop_hash",
            None
        )

    original_image = Image.open(
        uploaded_file
    ).convert("RGB")

    st.success("Image uploaded successfully!")


    # --------------------------------------------------
    # CROP IMAGE
    # --------------------------------------------------

    st.markdown("---")

    st.header("Crop Handwriting")

    st.write(
        "Adjust the crop box to select the handwriting "
        "you want the AI to recognise."
    )

    cropped_image = st_cropper(
        original_image,
        realtime_update=True,
        box_color="#438A85",
        aspect_ratio=None,
        return_type="image"
    )

    if cropped_image is None:
        cropped_image = original_image

    cropped_image = cropped_image.convert("RGB")


    # --------------------------------------------------
    # DETECT CHANGES TO CROP
    # --------------------------------------------------

    current_crop_hash = hashlib.sha256(
        cropped_image.tobytes()
    ).hexdigest()

    previous_crop_hash = st.session_state.get(
        "previous_crop_hash"
    )

    if current_crop_hash != previous_crop_hash:

        clear_recognition_results()

        st.session_state["previous_crop_hash"] = (
            current_crop_hash
        )


    # --------------------------------------------------
    # CROPPED IMAGE PREVIEW
    # --------------------------------------------------

    st.subheader("Selected Handwriting")

    st.image(
        cropped_image,
        use_container_width=True
    )

    st.caption(
        "Make sure the selected area contains the handwriting "
        "you want to recognise."
    )


    # --------------------------------------------------
    # RECOGNITION
    # --------------------------------------------------

    st.markdown("---")

    if st.button(
        "Recognise Handwriting",
        use_container_width=True
    ):

        with st.spinner(
            "Analysing handwriting... Please wait."
        ):

            try:

                recognised_text, average_confidence = (
                    recognise_handwriting(cropped_image)
                )

                st.session_state["recognised_text"] = (
                    recognised_text
                )

                st.session_state["average_confidence"] = (
                    average_confidence
                )

                st.session_state["recognition_image"] = (
                    cropped_image.copy()
                )

            except Exception as e:

                st.error(
                    f"An error occurred during recognition: {e}"
                )


    # --------------------------------------------------
    # DISPLAY RESULTS
    # --------------------------------------------------

    if "recognised_text" in st.session_state:

        st.markdown("---")

        st.header("Recognition Results")

        col1, col2 = st.columns(2)

        with col1:

            st.subheader("Original Handwriting")

            st.image(
                st.session_state["recognition_image"],
                use_container_width=True
            )

        with col2:

            st.subheader("Recognised Transcription")

            edited_text = st.text_area(
                "You can edit the recognised text below:",
                value=st.session_state["recognised_text"],
                height=250,
                key="editable_transcription"
            )

            st.caption(
                "Review and edit the transcription where necessary."
            )

            st.download_button(
                label="Download Transcription",
                data=edited_text,
                file_name="handwriting_transcription.txt",
                mime="text/plain",
                use_container_width=True
            )

            st.code(
                edited_text,
                language=None
            )


        # --------------------------------------------------
        # CONFIDENCE DISPLAY
        # --------------------------------------------------

        st.markdown("---")

        st.subheader("Estimated Recognition Confidence")

        confidence = st.session_state.get(
            "average_confidence"
        )

        if confidence is not None:

            confidence_percentage = confidence * 100

            st.metric(
                label="Estimated Confidence",
                value=f"{confidence_percentage:.1f}%"
            )

            st.progress(
                max(0.0, min(float(confidence), 1.0))
            )

            if confidence >= 0.70:

                st.success(
                    "The model produced a relatively high confidence "
                    "estimate. Please still review the transcription."
                )

            else:

                st.warning(
                    "The model produced a lower confidence estimate. "
                    "Carefully check the transcription against the "
                    "original handwriting."
                )

            st.caption(
                "This is an approximate model-generated confidence "
                "score, not a measure of guaranteed transcription accuracy."
            )

        else:

            st.info(
                "A confidence estimate is not available for this result."
            )


# --------------------------------------------------
# CLEAR RESULTS WHEN UPLOAD IS REMOVED
# --------------------------------------------------

else:

    if st.session_state.get("previous_image_hash") is not None:

        clear_recognition_results()

        st.session_state.pop(
            "previous_image_hash",
            None
        )

        st.session_state.pop(
            "previous_crop_hash",
            None
        )


# --------------------------------------------------
# DISCLAIMER
# --------------------------------------------------

st.markdown("---")

st.info(
    "**Disclaimer:** This tool uses artificial intelligence "
    "to assist with handwriting transcription. Its output may "
    "contain errors and should be checked against the original "
    "handwriting."
)


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown("---")

st.markdown(
    """
    <div style="
        text-align: center;
        color: #718096;
        font-size: 14px;
        padding: 10px;
    ">
        Read Your Teachers' Handwriting |
        AI-powered handwriting recognition
    </div>
    """,
    unsafe_allow_html=True
)
