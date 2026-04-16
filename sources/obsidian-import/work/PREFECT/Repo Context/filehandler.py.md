from abc import ABC, abstractmethod
import io
import os
import pathlib
import shutil
from typing import Callable
import nextcloud
import nextcloud.response
import logging

logger = logging.getLogger(__name__)

def get_compounding_paths(path:str, separator:str = "/") -> list:
    compounding_paths = []
    current_path = ""
    
    for part in path.strip(separator).split(separator):
        current_path = os.path.join(current_path, part)
        compounding_paths.append(separator + current_path.replace("\\", "/"))
        
    return compounding_paths

class FileHandler(ABC):
    @abstractmethod
    def create_dir(self, path: str) -> bool:
        pass
    
    @abstractmethod
    def dir_exists(self, path: str) -> bool:
        pass

    @abstractmethod
    def write_file(self, path: str, filestream: io.StringIO) -> bool:
        pass

    @abstractmethod
    def list_files(self, path: str) -> list:
        pass

    @abstractmethod
    def copy_file_or_dir(self, src_path: str, dst_path: str):
        pass
    
    @abstractmethod
    def remove_dir(self, path: str):
        pass

    @abstractmethod
    def move_file_or_dir(self, src_path: str, dst_path: str, overwrite: bool = False):
        pass

class NextcloudFileHandler(FileHandler):
    def __init__(self):
        nextcloud_host = os.getenv("NEXTCLOUD_HOST")
        self.nextcloud_client = nextcloud.NextCloud(
            endpoint = f"https://{nextcloud_host}",
            user = os.getenv("NEXTCLOUD_USER"),
            password = os.getenv("NEXTCLOUD_PASSWORD"),
        )

        try:
            # Check connection
            logger.info(self.nextcloud_client.session)
            logger.info("Connected to Nextcloud!")
        except Exception as e:
            logger.error("Error connecting to Nextcloud:", e)
    
    def _with_retry(self, fn: Callable[[], nextcloud.response.WebDAVResponse]):
        response = fn()
        retry_count = 2
        while response.status_code >= 400 and retry_count > 0:
            logger.error(f"Nextcloud error: HTTP {response.status_code} {response.get_error_message()}")
            response = fn()
            retry_count -= 1
    
    def dir_exists(self, path: str) -> bool:
        # Check if the directory already exists so we can return early
        folder_check_response = self.nextcloud_client.list_folders(path)
        if folder_check_response.status_code >= 400:
            return False
        return True

    def create_dir(self, path: str) -> bool:
        try:
            if self.dir_exists(path):
                return True
            
            path_parts = get_compounding_paths(path, "/")
            logger.info(f"Attempting to create directory: {'/'.join(path_parts)}")
            return self.nextcloud_client.ensure_tree_exists(path_parts)
        except Exception as e:
            logger.error(f"Failed to upload {path}: {e}")
            return False

    def write_file(self, path: str, filestream: io.StringIO) -> bool:
        # Upload the file
        try:
            logger.info(f"Attempting to upload file: {path}")
            response = self.nextcloud_client.upload_file_contents(filestream.getvalue(), path)
            if response.status_code == 201:
                logger.info(f"File uploaded successfully to {path}")
                return True
            else:
                logger.error(f"Failed to upload file: {response.status_code}, {response.text}")
                return False

        except Exception as e:
            logger.error("An error occurred during file upload:", e)
            return False

    def list_files(self, path: str) -> list:
        # Get contents of the directory
        file_list = []

        folder = self.nextcloud_client.get_folder(path)
        if not folder:
            return []
        contents = folder.list()

        for item in contents:
            # Filter and print only the files
            file_list.append(item.get_relative_path())

        return file_list

    def copy_file_or_dir(self, src_path: str, dst_path: str):
        logger.info(f"Copying {src_path} to {dst_path}")
        self._with_retry(lambda: self.nextcloud_client.copy_path(src_path, dst_path))

    def remove_dir(self, path: str):
        logger.info(f"Removing {path}")
        self._with_retry(lambda: self.nextcloud_client.delete_path(path))

    def move_file_or_dir(self, src_path: str, dst_path: str, overwrite: bool = False):
        logger.info(f"Moving {src_path} to {dst_path}")
        self._with_retry(lambda: self.nextcloud_client.move_path(src_path, dst_path, overwrite = overwrite))

class LocalFileHandler(FileHandler):
    def create_dir(self, path: str) -> bool:
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)
        return True
    
    def dir_exists(self, path: str) -> bool:
        return os.path.isdir(path)

    def write_file(self, path: str, filestream: io.StringIO) -> bool:
        with open(path, "x") as f:
            filestream.seek(0)
            shutil.copyfileobj(filestream, f)
        return True

    def list_files(self, path: str) -> list:
        return list(map(lambda filename: f"{path}/{filename}",  os.listdir(path)))

    def copy_file_or_dir(self, src_path: str, dst_path: str):
        logger.info(f"Copying {src_path} to {dst_path}")
        shutil.copyfile(src_path, dst_path)
    
    def remove_dir(self, path: str):
        logger.info(f"Removing {path}")
        shutil.rmtree(path)

    def move_file_or_dir(self, src_path: str, dst_path: str, overwrite: bool = False):
        logger.info(f"Moving {src_path} to {dst_path}")
        shutil.move(src_path, dst_path)