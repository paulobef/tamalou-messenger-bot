import zipfile

from dropbox.exceptions import ApiError


class DropboxConnector:

    def __init__(self, app_folder: str, dbx_client):
        self.app_folder = app_folder
        self.client = dbx_client

    def download_folder(self, from_path, to_path, to_directory='./', unzip=True):
        self.client.files_download_zip_to_file(to_path, self.app_folder + '/' + from_path)

        if unzip:
            with zipfile.ZipFile(to_path, 'r') as zip_ref:
                zip_ref.extractall(to_directory)
        return "ok"


"""
    def download_file(self, from_path, to_path):
        return

    def listen_for_folder_updates(self, path):
        return
"""
