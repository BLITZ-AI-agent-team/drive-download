"""Google Drive アップロード + ローカル削除"""

import os
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger("module3")

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


class DriveUploader:
    def __init__(self, service_account_path=None):
        sa_path = service_account_path or os.getenv(
            "GOOGLE_SA_KEY_PATH",
            os.path.join(os.path.dirname(__file__), "..", "..", "service_account.json"),
        )
        creds = service_account.Credentials.from_service_account_file(sa_path, scopes=SCOPES)
        self.service = build("drive", "v3", credentials=creds)

    def upload_file(self, local_path, drive_folder_id, mime_type=None):
        """ファイルをGoogle Driveにアップロード"""
        file_name = os.path.basename(local_path)
        if mime_type is None:
            mime_type = "video/mp4" if local_path.endswith(".mp4") else "application/octet-stream"

        file_metadata = {
            "name": file_name,
            "parents": [drive_folder_id],
        }
        media = MediaFileUpload(local_path, mimetype=mime_type, resumable=True)
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id,name,webViewLink",
            supportsAllDrives=True,
        ).execute()

        logger.info(f"アップロード完了: {file_name} → {file.get('webViewLink', file['id'])}")
        return {
            "drive_id": file["id"],
            "name": file["name"],
            "link": file.get("webViewLink", ""),
        }

    def upload_and_delete(self, local_path, drive_folder_id):
        """アップロード後にローカルファイルを削除"""
        result = self.upload_file(local_path, drive_folder_id)
        if result and result.get("drive_id"):
            os.remove(local_path)
            logger.info(f"ローカル削除: {local_path}")
            result["local_deleted"] = True
        return result
