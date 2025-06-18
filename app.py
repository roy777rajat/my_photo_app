# my_photo_app/app.py

import streamlit as st
from PIL import Image
import os
import io
import zipfile
import uuid
import datetime
import sys

# Ensure project root is in sys.path (KEEP THESE LINES)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# *** IMPORTANT: CHANGE THESE LINES TO ABSOLUTE IMPORTS ***
# REMOVE THE try-except BLOCK. It is not needed anymore.
from my_photo_app.aws_utils import get_aws_clients, upload_file_to_s3, save_metadata_to_dynamodb, get_photos_from_dynamodb, get_s3_object_data
from my_photo_app.config import S3_BUCKET_NAME # For display purposes if needed

# --- Custom CSS for Professional Look & Feel ---
# Define custom_css variable FIRST
custom_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Roboto', sans-serif;
    color: #333;
    background-color: #f0f2f6; /* Light gray background for the entire app */
}

/* Main app container styling for a polished look */
.stApp {
    background-color: #f0f2f6; /* Ensure background matches body */
}

div.stApp > header {
    background-color: #007bff; /* Professional blue for the header */
    color: white;
    padding: 1rem;
    border-bottom: 5px solid #0056b3; /* Darker blue border */
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    border-radius: 0 0 10px 10px; /* Rounded bottom corners */
}

h1 {
    color: #007bff; /* Main app title color */
    text-align: center;
    font-weight: 700;
    margin-bottom: 1rem;
    padding-top: 1rem;
    background: linear-gradient(45deg, #007bff, #00c6ff); /* Gradient effect */
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 3.5em;
    letter-spacing: 1.5px;
}

h2, h3 {
    color: #444;
    border-bottom: 2px solid #e0e0e0;
    padding-bottom: 0.5rem;
    margin-top: 2.5rem;
    font-weight: 600;
}

/* Streamlit specific elements */
.css-1d391kg { /* This targets the main content wrapper */
    background-color: #ffffff; /* White background for the content area */
    padding: 2rem 3rem;
    border-radius: 12px;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1); /* Deeper shadow */
    margin: 2rem auto; /* Center the content */
    max-width: 1300px;
}

/* Custom button styling */
.stButton>button {
    background-color: #28a745; /* Green for action buttons */
    color: white;
    border: none;
    padding: 0.8rem 2rem;
    border-radius: 8px;
    font-weight: bold;
    font-size: 1.1em;
    transition: background-color 0.3s ease, transform 0.2s ease;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    cursor: pointer;
}
.stButton>button:hover {
    background-color: #218838;
    transform: translateY(-2px);
}
.stButton>button:active {
    transform: translateY(0);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* File Uploader */
.stFileUploader label {
    font-weight: bold;
    color: #555;
    font-size: 1.1em;
}
.stFileUploader div[data-testid="stFileUploaderDropzone"] {
    border: 3px dashed #007bff; /* Blue dashed border */
    border-radius: 10px;
    background-color: #e9f5ff; /* Very light blue background */
    padding: 2.5rem;
    text-align: center;
    transition: border-color 0.3s ease, background-color 0.3s ease;
}
.stFileUploader div[data-testid="stFileUploaderDropzone"]:hover {
    border-color: #0056b3; /* Darker blue on hover */
    background-color: #d0e7ff; /* Slightly darker light blue on hover */
}
.stFileUploader div[data-testid="stFileUploaderFile] {
    background-color: #f8f9fa;
    border-radius: 5px;
    margin-top: 10px;
    padding: 10px;
    border: 1px solid #ddd;
}


/* Text area for descriptions */
.stTextArea>label {
    font-weight: bold;
    color: #555;
}
.stTextArea textarea {
    border-radius: 8px;
    border: 1px solid #ccc;
    padding: 0.8rem;
    box-shadow: inset 0 1px 4px rgba(0,0,0,0.08);
    transition: border-color 0.3s ease;
}
.stTextArea textarea:focus {
    border-color: #007bff;
    box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25); /* Focus highlight */
}

/* Tabs styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 15px; /* More space between tabs */
    justify-content: center;
    border-bottom: none; /* Remove default bottom border */
    margin-bottom: 2rem;
}
.stTabs [data-baseweb="tab"] {
    background-color: #f8f9fa; /* Light background for inactive tabs */
    border-radius: 10px; /* More rounded corners */
    padding: 12px 25px;
    font-weight: bold;
    color: #666;
    border: 1px solid #e0e0e0;
    transition: all 0.3s ease-in-out;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
}
.stTabs [data-baseweb="tab"]:hover {
    background-color: #e9ecef;
    color: #333;
    transform: translateY(-2px);
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}
.stTabs [aria-selected="true"] {
    background-color: #007bff; /* Blue for active tab */
    color: white;
    border-color: #007bff;
    box-shadow: 0 4px 15px rgba(0, 123, 255, 0.3); /* Stronger shadow for active */
    transform: translateY(-2px); /* Slight lift */
}

/* Photo Card Styling */
.photo-card {
    background-color: #ffffff;
    border-radius: 15px; /* More rounded corners */
    box-shadow: 0 6px 15px rgba(0, 0, 0, 0.1); /* Nicer shadow */
    padding: 20px;
    margin-bottom: 25px; /* Space between cards */
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    transition: transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out;
    border: 1px solid #eee; /* Subtle border */
}
.photo-card:hover {
    transform: translateY(-8px); /* More pronounced lift on hover */
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.25); /* Stronger shadow on hover */
}
.photo-card img {
    border-radius: 12px; /* Rounded image corners */
    max-width: 100%;
    height: auto;
    object-fit: contain;
    margin-bottom: 15px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1); /* Image specific shadow */
}
.photo-card .stCheckbox { /* Adjust checkbox position within card */
    margin-top: -10px;
    margin-bottom: 10px;
    font-size: 1.1em;
}
.photo-card p { /* Description text */
    font-size: 1em;
    color: #555;
    margin-bottom: 5px;
}
.photo-card .st-emotion-cache-nahz7x { /* Caption for upload date */
    font-size: 0.85em;
    color: #777;
    margin-top: 5px;
}

/* Download button container below photos */
.download-button-container {
    text-align: center;
    margin-top: 40px;
    margin-bottom: 30px;
}

/* Progress bar styling */
.stProgress > div > div > div > div {
    background-color: #28a745; /* Green progress bar */
    border-radius: 5px;
}

/* Sidebar styling (if you decide to use it later) */
.css-1lcbmhc, .css-1qxtsq7 { /* Common Streamlit sidebar classes */
    background-color: #343a40; /* Dark grey sidebar */
    color: white;
    box-shadow: 2px 0 10px rgba(0,0,0,0.2);
}
.css-1qxtsq7 > div > h2 { /* Sidebar title */
    color: white;
    text-align: center;
    padding-top: 1rem;
}
</style>
"""

# --- Streamlit UI Configuration ---
st.set_page_config(
    page_title="Family Photo Share App",
    layout="centered", # Use a wide layout for better photo display
    #initial_sidebar_state="expanded" # Optional: Start with sidebar expanded
)

# --- Inject ALL Custom CSS NOW ---
# Inject the custom_css variable first (the long one)
st.markdown(custom_css, unsafe_allow_html=True)

# Then, inject the second inline CSS block (for red color & shorter UI)
st.markdown("""
<style>
/* Change various text elements to red */
h1, h2, h3, h4, h5, h6,
.stMarkdown, .stText, .stButton > button, .stDownloadButton > button,
.st-emotion-cache-1wmptj3 { /* Targets some default Streamlit text containers */
    color: red !important; /* !important ensures it overrides default styles */
}

/* Optional: Change Streamlit's primary theme color to red */
/* This affects buttons, links, sliders, etc. */
:root {
    --primary-color: #FF0000; /* Pure Red */
    --primary-color-80: #FF3333; /* For hover/active states */
    --primary-color-50: #FF6666;
    --primary-color-30: #FF9999;
}

/* Make the main content block even narrower than 'centered' layout */
/* You might need to adjust this class name if Streamlit updates their internal CSS */
/* Try checking your browser's developer tools for the main container class */
.st-emotion-cache-z5fcl4 { /* This is a common class for the main block container */
    max-width: 500px; /* Example: make it 500px wide. Adjust as desired. */
    padding-left: 2rem;
    padding-right: 2rem;
}
/* Another common class for the main content container: */
.main .block-container {
    max-width: 500px; /* Also try this one if the above doesn't work well */
    padding-left: 2rem;
    padding-right: 2rem;
}

</style>
""", unsafe_allow_html=True)


# --- Initialize AWS Clients (Cached in Session State) ---
# IMPORTANT: This block previously had a `st.stop()` which would terminate the app.
# If `get_aws_clients()` raises a *critical* error (like NoCredentialsError),
# it's re-raised as an Exception in aws_utils.py. We need to handle that here
# so the Streamlit app can display a graceful message instead of crashing entirely.
if 's3_client' not in st.session_state or 'dynamodb_table' not in st.session_state:
    try:
        st.session_state.s3_client, st.session_state.dynamodb_table = get_aws_clients()
        
        # Check if S3 client failed critically (e.g., NoCredentialsError)
        if st.session_state.s3_client is None:
            st.error("Fatal Error: S3 client could not be initialized. Please check AWS credentials.")
            st.stop() # If S3 is truly unavailable, the app cannot function.

        if st.session_state.dynamodb_table is None:
            st.warning("DynamoDB table not found or failed to initialize. Photo viewing and metadata saving will be unavailable.")
            # Allow the app to continue, but with limited functionality.
        else:
            st.success("Successfully connected to AWS services!")

    except Exception as e:
        # This catches exceptions re-raised from aws_utils.py (e.g., AuthFailure, S3 init errors)
        st.error(f"Failed to connect to AWS. A critical error occurred: {e}")
        st.warning("Please ensure your AWS credentials (environment variables or IAM role) and configuration in my_photo_app/config.py are correct.")
        st.stop() # Stop the app execution if a critical AWS connection fails

s3_client = st.session_state.s3_client
dynamodb_table = st.session_state.dynamodb_table # This might be None if DynamoDB table not found

# --- Initialize session state for upload messages ---
if 'upload_messages' not in st.session_state:
    st.session_state.upload_messages = []


# --- Header Section ---
st.title("Family Photo Share App")
st.markdown("""
    Welcome to your private family photo sharing space!
    Upload your cherished memories and view them all.
""")


# --- Tabs for Navigation ---
tab1, tab2 = st.tabs(["Upload Photo", "View Photos"])

# --- Tab 1: Upload Photo ---
with tab1:
    st.header("Upload Your Family Photos")
    
    # Check if S3 is available before allowing uploads
    if s3_client is None:
        st.error("Cannot upload photos: S3 service is not available due to a critical AWS connection error.")
    else:
        st.write("Select image files to upload. You can add a short description for each.")

        uploaded_files = st.file_uploader(
            "Choose image files...",
            type=["jpg", "jpeg", "png", "gif"],
            accept_multiple_files=True
        )

        if uploaded_files:
            st.subheader("Preview and Add Description:")
            photo_details = []
            
            for i, uploaded_file in enumerate(uploaded_files):
                col1, col2 = st.columns([1, 2])

                with col1:
                    image_bytes = uploaded_file.getvalue()
                    image = Image.open(io.BytesIO(image_bytes))
                    st.image(image, caption=f"Preview of {uploaded_file.name}", width=200)

                with col2:
                    # FIX 1: Changed height from 50 to 80
                    description = st.text_area(f"Description for '{uploaded_file.name}'", key=f"desc_{i}", height=80)
                    photo_details.append({"file": uploaded_file, "description": description})
                
                st.markdown("---")

            if st.button("Upload All Photos"):
                st.session_state.upload_messages = [] # Clear previous messages on new upload attempt
                with st.spinner("Uploading photos to AWS... This might take a moment."):
                    success_count = 0
                    for detail in photo_details:
                        photo_id = str(uuid.uuid4())
                        s3_key, s3_url = upload_file_to_s3(s3_client, detail['file'])
                        
                        if s3_key and s3_url:
                            # Only try to save metadata if DynamoDB is available
                            if dynamodb_table:
                                if save_metadata_to_dynamodb(dynamodb_table, photo_id, s3_key, s3_url, detail['description'], detail['file'].name):
                                    st.session_state.upload_messages.append(f"✅ Uploaded '{detail['file'].name}' successfully! [View on S3]({s3_url})")
                                    success_count += 1
                                else:
                                    st.session_state.upload_messages.append(f"❌ Failed to save metadata for '{detail['file'].name}'. (DynamoDB might be unavailable)") #
                            else:
                                st.session_state.upload_messages.append(f"⚠️ Uploaded '{detail['file'].name}' to S3, but metadata was NOT saved to DynamoDB (table not found). [View on S3]({s3_url})")
                                success_count += 1 # Count S3 upload as success even if no DB
                        else:
                            st.session_state.upload_messages.append(f"❌ Failed to upload '{detail['file'].name}' to S3.")
                    
                    if success_count == len(photo_details) and success_count > 0:
                        st.balloons()
                    
                # Display all accumulated messages after the loop and spinner
                for msg in st.session_state.upload_messages:
                    if "✅" in msg:
                        st.success(msg)
                    elif "❌" in msg:
                        st.error(msg)
                    elif "⚠️" in msg:
                        st.warning(msg)
                
                # Clear messages after displaying them (optional, can keep for user to review)
                # st.session_state.upload_messages = [] 
                
                # FIX 2: Changed st.experimental_rerun() to st.rerun()
                st.rerun() # Rerun to refresh the view photos tab with new uploads
        else:
            st.info("No files selected yet.")

# --- Tab 2: View Photos ---
with tab2:
    st.header("Your Photo Gallery")
    
    # Check if DynamoDB is available before trying to fetch photos
    if dynamodb_table is None:
        st.error("Cannot display photos: DynamoDB table is not available.")
        st.write("Please ensure the DynamoDB table is created correctly in AWS.")
    else:
        st.write("Browse through all the cherished moments shared by your family.")

        all_photos_metadata = get_photos_from_dynamodb(dynamodb_table)
        
        st.subheader("Shared Photos:")

        # Initialize session state for selected photos if not present
        if 'selected_photos' not in st.session_state:
            st.session_state.selected_photos = []

        # --- Select All Checkbox ---
        all_current_ids = [photo['photo_id'] for photo in all_photos_metadata]
        all_selected_on_page = all(photo_id in st.session_state.selected_photos for photo_id in all_current_ids) and len(all_current_ids) > 0

        select_all_checkbox = st.checkbox("Select All Visible Photos", value=all_selected_on_page, key="select_all_checkbox")

        # Update selection based on "Select All"
        if select_all_checkbox and not all_selected_on_page:
            st.session_state.selected_photos = list(all_current_ids)
            st.rerun()
        elif not select_all_checkbox and all_selected_on_page:
            st.session_state.selected_photos = []
            st.rerun()


        # --- Display Photos with Checkboxes ---
        if all_photos_metadata:
            num_cols = 3 # Adjust number of columns as needed
            
            # Create columns outside the loop to maintain fixed layout
            cols = st.columns(num_cols)

            for i, photo_data in enumerate(all_photos_metadata):
                with cols[i % num_cols]: # Distribute photos across columns
                    # Wrap each photo in a div for custom card styling
                    st.markdown(f'<div class="photo-card">', unsafe_allow_html=True)
                    
                    # Checkbox for individual photo selection
                    is_selected = photo_data['photo_id'] in st.session_state.selected_photos
                    checkbox_checked = st.checkbox(
                        label="", # No label next to checkbox itself
                        value=is_selected,
                        key=f"photo_checkbox_{photo_data['photo_id']}"
                    )
                    
                    # Update session state based on individual checkbox change
                    if checkbox_checked and photo_data['photo_id'] not in st.session_state.selected_photos:
                        st.session_state.selected_photos.append(photo_data['photo_id'])
                    elif not checkbox_checked and photo_data['photo_id'] in st.session_state.selected_photos:
                        st.session_state.selected_photos.remove(photo_data['photo_id'])
                    
                    # Display the image from its S3 URL
                    # DEPRECATED WARNING: The use_column_width parameter has been deprecated.
                    # FIX: Change use_column_width to use_container_width
                    st.image(photo_data['s3_url'], use_container_width=True, caption=photo_data.get('original_filename', 'N/A'))
                    st.write(f"**Desc:** {photo_data.get('description', 'No description')}")
                    
                    try:
                        timestamp = datetime.datetime.fromtimestamp(photo_data['upload_timestamp'] / 1000)
                        st.caption(f"Uploaded on: {timestamp.strftime('%Y-%m-%d %H:%M')}")
                    except (KeyError, TypeError):
                        st.caption("Upload date not available.")
                    
                    st.markdown('</div>', unsafe_allow_html=True) # Close the photo-card div
        else:
            st.info("No photos uploaded yet. Go to the 'Upload Photo' tab to share one!")

        # --- Download Selected Button ---
        if st.session_state.selected_photos:
            # Get metadata for selected photos
            selected_photo_metadata = [
                photo for photo in all_photos_metadata if photo['photo_id'] in st.session_state.selected_photos
            ]
            
            # Create a BytesIO buffer to hold the zip file in memory
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                download_progress_bar = st.progress(0, text="Preparing download...")
                for idx, photo_data in enumerate(selected_photo_metadata):
                    try:
                        s3_key = photo_data['s3_key']
                        filename_in_zip = photo_data.get('original_filename', f"{photo_data['photo_id']}.jpg")
                        
                        image_data = get_s3_object_data(s3_client, s3_key)
                        if image_data:
                            zf.writestr(filename_in_zip, image_data)
                        else:
                            st.warning(f"Could not retrieve data for {filename_in_zip} from S3. Skipping.")
                    except Exception as e:
                        st.warning(f"Error adding {filename_in_zip} to zip: {e}. Skipping.")
                    
                    progress = (idx + 1) / len(selected_photo_metadata)
                    download_progress_bar.progress(progress, text=f"Adding {filename_in_zip} to zip...")
                download_progress_bar.empty() # Remove progress bar after completion

            zip_buffer.seek(0) # Rewind the buffer to the beginning

            # Container for centering the download button
            st.markdown('<div class="download-button-container">', unsafe_allow_html=True)
            st.download_button(
                label=f"Download {len(st.session_state.selected_photos)} Selected Photos (.zip)",
                data=zip_buffer,
                file_name="selected_photos.zip",
                mimetype="application/zip", # FIX: Changed from mime_type to mimetype
                key="download_button_zip"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Select photos above to enable download.")


st.markdown("""
<style>
/* CSS to style the social media icons */
.social-icons-container {
    display: flex; /* Use flexbox to arrange items horizontally */
    justify-content: center; /* Center the icons horizontally */
    gap: 25px; /* Space between the icons */
    margin-top: 30px; /* Space above the icons */
    margin-bottom: 20px; /* Space below the icons */
    padding: 10px;
}
.social-icons-container img {
    width: 25px; /* Adjust the size of the logos */
    height: 25px;
    border-radius: 50%; /* Optional: Make icons circular */
    transition: transform 0.2s ease-in-out; /* Smooth hover effect */
    box-shadow: 0 2px 5px rgba(0,0,0,0.2); /* Optional: subtle shadow */
}
.social-icons-container img:hover {
    transform: scale(1.1); /* Slightly enlarge icon on hover */
}
</style>

<div class="social-icons-container">
    <a href="YOUR_FACEBOOK_PROFILE_URL" target="_blank">
        <img src="https://upload.wikimedia.org/wikipedia/commons/5/51/Facebook_f_logo_%282019%29.svg" alt="Facebook">
    </a>
    <a href="YOUR_TWITTER_PROFILE_URL" target="_blank">
        <img src="https://upload.wikimedia.org/wikipedia/commons/6/6f/Logo_of_Twitter.svg" alt="Twitter (X)">
    </a>
    <a href="YOUR_MEDIUM_PROFILE_URL" target="_blank">
        <img src="data:image/svg+xml;base64,PHN2ZyByb2xlPSJpbWciIHZpZXdCb3g9IjAgMCAyNCAyNCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48dGl0bGU+TWVkaXVtPC90aXRsZT48cGF0aCBkPSJNNy40NSAyLjY1bDUuMDUgMTAuN0wxOCAyLjY1aDQuMTV2MTguN0gxOFYxMC4wNWwtNC43IDEwLjdeMDUgMjEuM0gwVDIuNjVoNy40NXptMTYuNTUgMTguN2gtMy4xNVYyLjY1SDI0djE4Ljd6Ii8+PC9zdmc+" alt="Medium">
    </a>
    <a href="YOUR_LINKEDIN_PROFILE_URL" target="_blank">
        <img src="data:image/svg+xml;base64,PHN2ZyByb2xlPSJpbWciIHZpZXdCb3g9IjAgMCAyNCAyNCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48dGl0bGU+TGlua2VkSW48L3RpdGxlPjxwYXRoIGQ9Ik0wIDYuNjVoMy41MjV2MTEuMTVoLTMuNTI1di0xMS4xNXptNi45NDYgMEgxMC40NzF2Mi4wNDZoLjAxNGMwLjQyMy0uNzYgMS40NDctMi4wNDYgMy45Ni0yLjA0NiAzLjg2NyAwIDQuNTc5IDIuNTQ4IDQuNTc5IDUuODY2djcuMjgzSDE1LjQ5VjE0LjEzYy0uMDAxLTEuMzA2LS4wMjctMi45NTMtMS42MDctMi45NTMtMS41ODYgMC0xLjgzMiAxLjE4OC0xLjgzMiAyLjg2NHYzLjEwNkg3LjU4OFY2LjY1eiIvPjwvc3ZnPg==" alt="LinkedIn">
    </a>
</div>
""", unsafe_allow_html=True)