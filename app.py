# my_photo_app/app.py

import streamlit as st
from PIL import Image
import os
import io
import zipfile
import uuid
import datetime
import sys
from botocore.exceptions import ClientError # Import ClientError specifically

# Ensure project root is in sys.path (KEEP THESE LINES)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# *** IMPORTANT: CHANGE THESE LINES TO ABSOLUTE IMPORTS ***
# REMOVE THE try-except BLOCK. It is not needed anymore.
from my_photo_app.aws_utils import get_aws_clients, upload_file_to_s3, save_metadata_to_dynamodb, get_photos_from_dynamodb, get_s3_object_data
from my_photo_app.config import S3_BUCKET_NAME # For display purposes if needed

# ... (rest of your custom CSS remains the same) ...

# --- Streamlit UI Configuration ---
st.set_page_config(
    page_title="Family Photo Share App",
    layout="centered", # Use a wide layout for better photo display
    #initial_sidebar_state="expanded" # Optional: Start with sidebar expanded
)
# ... (rest of your custom CSS remains the same) ...
st.markdown(custom_css, unsafe_allow_html=True)


# --- Initialize AWS Clients (Cached in Session State) ---
# Initialize flags for AWS connectivity
if 'aws_initialized' not in st.session_state:
    st.session_state.aws_initialized = False
    st.session_state.s3_client = None
    st.session_state.dynamodb_table = None
    st.session_state.aws_connection_error = None

if not st.session_state.aws_initialized:
    try:
        s3_c, dynamodb_t = get_aws_clients()
        
        # Check if the DynamoDB table exists and is active
        # This will raise ResourceNotFoundException if the table doesn't exist
        dynamodb_t.table_status 
        
        st.session_state.s3_client = s3_c
        st.session_state.dynamodb_table = dynamodb_t
        st.session_state.aws_initialized = True
        st.session_state.aws_connection_error = None
        st.success("Successfully connected to AWS services!")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            error_message = f"DynamoDB table not found. Please create the table named in your config. Error: {e}"
            st.session_state.aws_connection_error = error_message
            st.warning(error_message + " Functionality depending on DynamoDB will be limited.")
        elif e.response['Error']['Code'] == 'AuthFailure' or e.response['Error']['Code'] == 'UnrecognizedClientException':
            error_message = f"AWS authentication failed. Check your credentials and region. Error: {e}"
            st.session_state.aws_connection_error = error_message
            st.error(error_message)
        else:
            error_message = f"Failed to connect to AWS: {e}"
            st.session_state.aws_connection_error = error_message
            st.error(error_message)
    except Exception as e:
        error_message = f"An unexpected error occurred during AWS connection: {e}"
        st.session_state.aws_connection_error = error_message
        st.error(error_message)
    
    # Do NOT call st.stop() here. Allow the script to continue.

s3_client = st.session_state.s3_client
dynamodb_table = st.session_state.dynamodb_table
aws_connected_and_db_ready = (st.session_state.s3_client is not None and st.session_state.dynamodb_table is not None)

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
    if not aws_connected_and_db_ready:
        st.error(st.session_state.aws_connection_error or "AWS services are not fully connected. Upload and View functionality will be limited.")
        st.info("Please create the DynamoDB table as per your application's configuration to enable full functionality.")
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
                    description = st.text_area(f"Description for '{uploaded_file.name}'", key=f"desc_{i}", height=50)
                    photo_details.append({"file": uploaded_file, "description": description})
                
                st.markdown("---")

            if st.button("Upload All Photos"):
                with st.spinner("Uploading photos to AWS... This might take a moment."):
                    success_count = 0
                    for detail in photo_details:
                        photo_id = str(uuid.uuid4())
                        s3_key, s3_url = upload_file_to_s3(s3_client, detail['file'])
                        
                        if s3_key and s3_url:
                            if save_metadata_to_dynamodb(dynamodb_table, photo_id, s3_key, s3_url, detail['description'], detail['file'].name):
                                st.success(f"Uploaded '{detail['file'].name}' successfully! [View on S3]({s3_url})")
                                success_count += 1
                            else:
                                st.error(f"Failed to save metadata for '{detail['file'].name}'.")
                        else:
                            st.error(f"Failed to upload '{detail['file'].name}' to S3.")
                    
                    if success_count == len(photo_details) and success_count > 0:
                        st.balloons()
                    st.experimental_rerun() # Rerun to refresh the view photos tab with new uploads
        else:
            st.info("No files selected yet.")

# --- Tab 2: View Photos ---
with tab2:
    st.header("Your Photo Gallery")
    if not aws_connected_and_db_ready:
        st.error(st.session_state.aws_connection_error or "AWS services are not fully connected. Upload and View functionality will be limited.")
        st.info("Please create the DynamoDB table as per your application's configuration to enable full functionality.")
    else:
        st.write("Browse through all the cherished moments shared by your family.")

        # Ensure get_photos_from_dynamodb also handles the 'dynamodb_table' being None internally
        all_photos_metadata = get_photos_from_dynamodb(dynamodb_table) 
        
        st.subheader("Shared Photos:")

        # Initialize session state for selected photos if not present
        if 'selected_photos' not in st.session_state:
            st.session_state.selected_photos = []

        # --- Select All Checkbox ---
        all_current_ids = [photo['photo_id'] for photo in all_photos_metadata] if all_photos_metadata else []
        all_selected_on_page = all(photo_id in st.session_state.selected_photos for photo_id in all_current_ids) and len(all_current_ids) > 0

        select_all_checkbox = st.checkbox("Select All Visible Photos", value=all_selected_on_page, key="select_all_checkbox", disabled=not all_photos_metadata)

        # Update selection based on "Select All"
        if select_all_checkbox and not all_selected_on_page:
            st.session_state.selected_photos = list(all_current_ids)
            st.experimental_rerun()
        elif not select_all_checkbox and all_selected_on_page:
            st.session_state.selected_photos = []
            st.experimental_rerun()


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
                    st.image(photo_data['s3_url'], use_column_width=True, caption=photo_data.get('original_filename', 'N/A'))
                    st.write(f"**Desc:** {photo_data.get('description', 'No description')}")
                    
                    try:
                        timestamp = datetime.datetime.fromtimestamp(photo_data['upload_timestamp'] / 1000)
                        st.caption(f"Uploaded on: {timestamp.strftime('%Y-%m-%d %H:%M')}")
                    except (KeyError, TypeError):
                        st.caption("Upload date not available.")
                    
                    st.markdown('</div>', unsafe_allow_html=True) # Close the photo-card div
        else:
            if aws_connected_and_db_ready: # Only show this if DB is connected but empty
                 st.info("No photos uploaded yet. Go to the 'Upload Photo' tab to share one!")
            # Else, the error message above will be shown.

        # --- Download Selected Button ---
        if st.session_state.selected_photos and aws_connected_and_db_ready: # Only enable if connected
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
                mime_type="application/zip",
                key="download_button_zip"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            if aws_connected_and_db_ready:
                st.info("Select photos above to enable download.")
            # Else, error message above takes precedence


# ... (rest of your social media icons HTML and CSS remains the same) ...
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
        <img src="data:image/svg+xml;base64,PHN2ZyByb2xlPSJpbWciIHZpZXdCb3g9IjAgMCAyNCAyNCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48dGl0bGU+TWVkaXVtPC90aXRsZT48cGF0aCBkPSJNNy40NSAyLjY1bDUuMDUgMTAuN0wxOCAyLjY1aDQuMTV2MTguN0gxOFYxMC4wNWwtNC43IDEwLjcIOU4uNUw0LjUgMTAuMDVWMjEuM0gwVDIuNjVoNy40NXptMTYuNTUgMTguN2gtMy4xNVYyLjY1SDI0djE4Ljd6Ii8+PC9zdmc+" alt="Medium">
    </a>
    <a href="YOUR_LINKEDIN_PROFILE_URL" target="_blank">
        <img src="data:image/svg+xml;base64,PHN2ZyByb2xlPSJpbWciIHZpZXdCb3g9IjAgMCAyNCAyNCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48dGl0bGU+TGlua2VkSW48L3RpdGxlPjxwYXRoIGQ9Ik0yMC40NDcgMjAuNDUySC0zLjU1NHYtNS41NjljMC0xLjMyNS0uMDI4LTMuMDQ0LTEuODU0LTMuMDQ0LTEuODU1IDAtMi4xMzYgMS40NDUtMi4xMzYgMi45NXY1LjY2M0g5LjE1M1Y5LjI5OGgzLjQxNHYxLjU2MWguMDQ2Yy40NzctLjkgMS42MzctMS44NSAzLjM3LTEuODUgMy42MDEgMCA0LjI3IDIuMzc4IDQuMjcgNS40Njd2Ni4yNTN6TTUuMzM3IDcuNDMzYy0xLjE0NCAwLTIuMDYzLS45MjYtMi4wNjMtMi4wNjUgMC0xLjEzOS45Mi0yLjA2MyAyLjA2My0yLjA2MyAxLjE0IDAgMi4wNjQuOTI0IDIuMDY0IDIuMDYzIDAgMS4xMzktLjkyNSAyLjA2NS0yLjA2NCAyLjA2NXptLS4xMzcgMTMuMDE5SDEuNjY0VjkuMjk4aDMuNTM1djExLjE1NHoiLz48L3N2Zz4=" alt="LinkedIn">
    </a>
</div>
""", unsafe_allow_html=True)