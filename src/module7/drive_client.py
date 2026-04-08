"""Google Drive API クライアント - サービスアカウント認証 + 再帰的ファイル操作"""

import os
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


class DriveClient:
    def __init__(self, service_account_path=None):
        sa_path = service_account_path or os.getenv(
            "GOOGLE_SA_KEY_PATH",
            os.path.join(os.path.dirname(__file__), "..", "..", "service_account.json"),
        )
        creds = service_account.Credentials.from_service_account_file(sa_path, scopes=SCOPES)
        self.service = build("drive", "v3", credentials=creds)

    def get_file_metadata(self, file_id):
        return (
            self.service.files()
            .get(
                fileId=file_id,
                fields="id,name,mimeType,size,modifiedTime",
                supportsAllDrives=True,
            )
            .execute()
        )

    def list_folder(self, folder_id):
        """フォルダ内のファイル/サブフォルダを全件取得（ページネーション対応）"""
        items = []
        page_token = None
        while True:
            resp = (
                self.service.files()
                .list(
                    q=f"'{folder_id}' in parents and trashed = false",
                    fields="nextPageToken, files(id, name, mimeType, size, modifiedTime)",
                    pageSize=1000,
                    pageToken=page_token,
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                )
                .execute()
            )
            items.extend(resp.get("files", []))
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
        return items

    def list_folder_recursive(self, folder_id, path=""):
        """フォルダを再帰的に辿り、全ファイルを (相対パス, メタデータ) のリストで返す"""
        results = []
        items = self.list_folder(folder_id)
        for item in items:
            rel_path = os.path.join(path, item["name"]) if path else item["name"]
            if item["mimeType"] == "application/vnd.google-apps.folder":
                results.extend(self.list_folder_recursive(item["id"], rel_path))
            else:
                item["_rel_path"] = rel_path
                results.append(item)
        return results

    def download_file(self, file_id, dest_path):
        """ファイルをダウンロードしてdest_pathに保存"""
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        request = self.service.files().get_media(fileId=file_id, supportsAllDrives=True)
        with open(dest_path, "wb") as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()

    def export_google_doc(self, file_id, dest_path, mime_type="application/pdf"):
        """Google Docs/Sheets等をエクスポート"""
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        request = self.service.files().export_media(fileId=file_id, mimeType=mime_type)
        with open(dest_path, "wb") as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
