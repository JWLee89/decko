import os


def cleanup_files(*file_paths) -> bool:
    """
    Clean un files created during the process of the unit test
    Args:
        *file_paths: A tuple of file paths

    Returns:
        True if cleanup was successful.
        Otherwise, raise error

    """
    num_of_files: int = len(file_paths)
    number_of_files_deleted: int = 0
    for file_path in file_paths:
        if not os.path.exists(file_path):
            raise RuntimeError(f"File to clean up: '{file_path}' does not exist")
        os.remove(file_path)
        number_of_files_deleted += 1

    # Return true only if number of files deleted
    # equals actual number of files passed in
    return number_of_files_deleted == num_of_files
