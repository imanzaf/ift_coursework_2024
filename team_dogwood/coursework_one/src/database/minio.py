"""
TODO -
    - Methods for writing and reading pdf object from minio database.
"""

from ift_global import MinioFileSystemRepo


class MinioFileSystem(MinioFileSystemRepo):
    """
    Overwrite file read and file write methods in MinioFileSystemRepo to add functionality to process pdf files.

    Useful methods from parent class:
        - upload_file
        - download_file
        - list_dir
        - list_files
        - dir_exists
        - file_exists
    """

    def read_file():
        """
        Read a pdf file from the minio database.
        """
        pass

    def write_file():
        """
        Write a pdf file to the minio database.
        """
        pass


if __name__ == "__main__":
    minio = MinioFileSystem("test-bucket")
