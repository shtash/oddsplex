import streamlit as st
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import json
import os

def authenticate():
    # Prepare credentials.json content from secrets
    credentials_json = {
        "installed": {
            "client_id": st.secrets["google_drive"]["client_id"],
            "project_id": st.secrets["google_drive"]["project_id"],
            "auth_uri": st.secrets["google_drive"]["auth_uri"],
            "token_uri": st.secrets["google_drive"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["google_drive"]["auth_provider_x509_cert_url"],
            "client_secret": st.secrets["google_drive"]["client_secret"],
            "redirect_uris": st.secrets["google_drive"]["redirect_uris"]
        }
    }

    # Save the credentials to a temporary file
    with open('credentials.json', 'w') as creds_file:
        json.dump(credentials_json, creds_file)

    gauth = GoogleAuth()
    gauth.LoadClientConfigFile('credentials.json')

    # Load credentials from Streamlit secrets if available
    if "mycreds" in st.secrets["google_drive"]:
        creds_content = st.secrets["google_drive"]["mycreds"]
        with open('mycreds.txt', 'w') as creds_file:
            creds_file.write(creds_content)
        gauth.LoadCredentialsFile('mycreds.txt')

    if gauth.credentials is None or gauth.access_token_expired:
        gauth.LocalWebserverAuth()
        with open('mycreds.txt', 'r') as creds_file:
            creds = creds_file.read()
        # Handle saving the updated credentials securely if needed
    else:
        gauth.Authorize()

    # Clean up temporary files
    os.remove('credentials.json')
    if os.path.exists('mycreds.txt'):
        os.remove('mycreds.txt')

    drive = GoogleDrive(gauth)
    return drive

def upload_file(file_path, drive):
    if not os.path.exists(file_path):
        st.write(f"File '{file_path}' does not exist.")
        return

    file = drive.CreateFile({'title': os.path.basename(file_path)})
    file.SetContentFile(file_path)
    file.Upload()
    st.write(f"File '{file_path}' uploaded successfully.")

def download_file(file_id, destination_path, drive):
    file = drive.CreateFile({'id': file_id})
    file.GetContentFile(destination_path)
    st.write(f"File downloaded successfully to '{destination_path}'.")

def main():
    st.title("Google Drive File Upload and Download")

    drive = authenticate()

    # Upload file based on file path
    st.header("Upload File")
    file_path_to_upload = st.text_input("Enter the file path to upload:")
    if st.button("Upload"):
        if file_path_to_upload:
            upload_file(file_path_to_upload, drive)
        else:
            st.write("Please enter a file path.")

    # Download file based on file ID
    st.header("Download File")
    file_id = st.text_input("Enter the file ID to download")
    if file_id:
        destination_path = st.text_input("Enter the destination path to save the file")
        if destination_path and st.button("Download"):
            download_file(file_id, destination_path, drive)

if __name__ == "__main__":
    main()
