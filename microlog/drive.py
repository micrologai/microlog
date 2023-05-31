import appdata
import io
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive.appdata']

APP_HOME = appdata.AppDataPaths('microlog').app_data_path


def getCredentials():
    creds = None
    tokenPath = os.path.join(APP_HOME, "token.json")
    credentialsPath = os.path.join(APP_HOME, "client_secret.json")
    if os.path.exists(tokenPath):
        creds = Credentials.from_authorized_user_file(tokenPath, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentialsPath, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(tokenPath, 'w') as token:
            token.write(creds.to_json())
    return creds


def getServiceWithCredentials():
    return build('drive', 'v3', credentials=getCredentials())


def getService():
    try:
        return getServiceWithCredentials()
    except Exception as e:
        print("No service", e)
        tokenPath = os.path.join(APP_HOME, "token.json")
        os.remove(tokenPath)
        return getServiceWithCredentials()


def upload(name, path, mimetype="application/zip"):
    file_metadata = { 'name': name, 'parents': ['appDataFolder'] }
    media = MediaFileUpload(path, mimetype=mimetype, resumable=True)
    file = getService().files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file["id"]


def getLogs():
    response = getService().files().list(spaces='appDataFolder', fields='nextPageToken, files(id, ' 'name)', pageSize=1000).execute()
    return response.get('files', [])


def download(file_id):
    request = getService().files().get_media(fileId=file_id)
    file = io.BytesIO()
    downloader = MediaIoBaseDownload(file, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print(F'Download {int(status.progress() * 100)}.')
    return file.getvalue()


def delete(file_id):
    def callback(request_id, response, exception):
        pass
    print(F'Delete {file_id}')
    return getService().files().delete(fileId=file_id).execute()


if __name__ == '__main__':
    main()