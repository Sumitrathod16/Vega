import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


HOME = Path.home()

KNOWN_LOCATIONS = {
    "desktop": HOME / "Desktop",
    "downloads": HOME / "Downloads",
    "documents": HOME / "Documents",
    "pictures": HOME / "Pictures",
    "videos": HOME / "Videos",
    "music": HOME / "Music",
    "home": HOME
}


# Resolve Location
def resolve_location(location):

    if not location:
        return HOME

    location = location.strip()

    lower_location = location.lower()

    if lower_location in KNOWN_LOCATIONS:
        return KNOWN_LOCATIONS[lower_location]

    path = Path(location).expanduser()

    if path.is_absolute():
        return path

    for name, known_path in KNOWN_LOCATIONS.items():

        if lower_location.startswith(name + "/"):

            relative = location[len(name):].lstrip("/\\")

            return known_path / relative

        if lower_location.startswith(name + "\\"):

            relative = location[len(name):].lstrip("/\\")

            return known_path / relative

    return HOME / location


# Create Folder
def create_folder(
    folder_name,
    location="desktop"
):

    try:

        base_path = resolve_location(
            location
        )

        folder_path = base_path / folder_name

        folder_path.mkdir(
            parents=True,
            exist_ok=True
        )

        return (
            True,
            f"Folder created at {folder_path}"
        )

    except Exception as error:

        print(
            f"Create folder error: {error}"
        )

        return (
            False,
            "I couldn't create that folder."
        )


# Create File
def create_file(
    file_name,
    location="desktop",
    content=""
):

    try:

        base_path = resolve_location(
            location
        )

        base_path.mkdir(
            parents=True,
            exist_ok=True
        )

        file_path = base_path / file_name

        if file_path.exists():

            return (
                False,
                f"{file_name} already exists."
            )

        file_path.write_text(
            content,
            encoding="utf-8"
        )

        return (
            True,
            f"File created at {file_path}"
        )

    except Exception as error:

        print(
            f"Create file error: {error}"
        )

        return (
            False,
            "I couldn't create that file."
        )


# Open File Or Folder
def open_path(path):

    try:

        target = resolve_location(
            path
        )

        if not target.exists():

            return (
                False,
                f"I couldn't find {target}."
            )

        os.startfile(
            str(target)
        )

        return (
            True,
            f"Opened {target.name}."
        )

    except Exception as error:

        print(
            f"Open path error: {error}"
        )

        return (
            False,
            "I couldn't open that file or folder."
        )


# Rename File Or Folder
def rename_path(
    source,
    new_name
):

    try:

        source_path = resolve_location(
            source
        )

        if not source_path.exists():

            return (
                False,
                "I couldn't find the file or folder."
            )

        new_path = (
            source_path.parent
            / new_name
        )

        if new_path.exists():

            return (
                False,
                f"{new_name} already exists."
            )

        source_path.rename(
            new_path
        )

        return (
            True,
            f"Renamed to {new_name}."
        )

    except Exception as error:

        print(
            f"Rename error: {error}"
        )

        return (
            False,
            "I couldn't rename that item."
        )


# Copy File Or Folder
def copy_path(
    source,
    destination
):

    try:

        source_path = resolve_location(
            source
        )

        destination_path = resolve_location(
            destination
        )

        if not source_path.exists():

            return (
                False,
                "Source file or folder doesn't exist."
            )

        destination_path.mkdir(
            parents=True,
            exist_ok=True
        )

        target = (
            destination_path
            / source_path.name
        )

        if target.exists():

            return (
                False,
                f"{target.name} already exists in destination."
            )

        if source_path.is_dir():

            shutil.copytree(
                source_path,
                target
            )

        else:

            shutil.copy2(
                source_path,
                target
            )

        return (
            True,
            f"Copied to {destination_path}."
        )

    except Exception as error:

        print(
            f"Copy error: {error}"
        )

        return (
            False,
            "I couldn't copy that item."
        )


# Move File Or Folder
def move_path(
    source,
    destination
):

    try:

        source_path = resolve_location(
            source
        )

        destination_path = resolve_location(
            destination
        )

        if not source_path.exists():

            return (
                False,
                "Source file or folder doesn't exist."
            )

        destination_path.mkdir(
            parents=True,
            exist_ok=True
        )

        target = (
            destination_path
            / source_path.name
        )

        if target.exists():

            return (
                False,
                f"{target.name} already exists in destination."
            )

        shutil.move(
            str(source_path),
            str(destination_path)
        )

        return (
            True,
            f"Moved to {destination_path}."
        )

    except Exception as error:

        print(
            f"Move error: {error}"
        )

        return (
            False,
            "I couldn't move that item."
        )


# Delete File Or Folder
def delete_path(
    path
):

    try:

        target = resolve_location(
            path
        )

        if not target.exists():

            return (
                False,
                "The file or folder doesn't exist."
            )

        protected_paths = {
            HOME,
            KNOWN_LOCATIONS["desktop"],
            KNOWN_LOCATIONS["documents"],
            KNOWN_LOCATIONS["downloads"]
        }

        if target in protected_paths:

            return (
                False,
                "I won't delete a protected system folder."
            )

        if target.is_dir():

            shutil.rmtree(
                target
            )

        else:

            target.unlink()

        return (
            True,
            f"Deleted {target.name}."
        )

    except Exception as error:

        print(
            f"Delete error: {error}"
        )

        return (
            False,
            "I couldn't delete that item."
        )


# Search Files
def search_files(
    query,
    location="home",
    limit=20
):

    try:

        base_path = resolve_location(
            location
        )

        if not base_path.exists():

            return []

        query = query.lower().strip()

        results = []

        for root, dirs, files in os.walk(
            base_path
        ):

            for item in dirs + files:

                if query in item.lower():

                    full_path = Path(root) / item

                    results.append(
                        {
                            "name": item,
                            "path": str(full_path),
                            "type": (
                                "folder"
                                if full_path.is_dir()
                                else "file"
                            )
                        }
                    )

                    if len(results) >= limit:
                        return results

        return results

    except Exception as error:

        print(
            f"Search file error: {error}"
        )

        return []


# List Folder
def list_folder(
    location="desktop",
    limit=30
):

    try:

        folder = resolve_location(
            location
        )

        if not folder.exists():
            return []

        if not folder.is_dir():
            return []

        items = []

        for item in folder.iterdir():

            items.append(
                {
                    "name": item.name,
                    "path": str(item),
                    "type": (
                        "folder"
                        if item.is_dir()
                        else "file"
                    )
                }
            )

            if len(items) >= limit:
                break

        return items

    except Exception as error:

        print(
            f"List folder error: {error}"
        )

        return []


# Recent Files
def get_recent_files(
    location="downloads",
    limit=10
):

    try:

        folder = resolve_location(
            location
        )

        if not folder.exists():
            return []

        files = [
            item
            for item in folder.iterdir()
            if item.is_file()
        ]

        files.sort(
            key=lambda item: item.stat().st_mtime,
            reverse=True
        )

        results = []

        for file_path in files[:limit]:

            modified_time = datetime.fromtimestamp(
                file_path.stat().st_mtime
            )

            results.append(
                {
                    "name": file_path.name,
                    "path": str(file_path),
                    "modified": modified_time.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                }
            )

        return results

    except Exception as error:

        print(
            f"Recent file error: {error}"
        )

        return []


# File Information
def get_file_info(path):

    try:

        file_path = resolve_location(
            path
        )

        if not file_path.exists():

            return None

        stat = file_path.stat()

        return {
            "name": file_path.name,
            "path": str(file_path),
            "type": (
                "folder"
                if file_path.is_dir()
                else "file"
            ),
            "extension": file_path.suffix,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(
                stat.st_mtime
            ).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        }

    except Exception as error:

        print(
            f"File info error: {error}"
        )

        return None


# Read Text File
def read_text_file(
    path,
    max_characters=8000
):

    try:

        file_path = resolve_location(
            path
        )

        if not file_path.exists():

            return (
                False,
                "File not found."
            )

        if not file_path.is_file():

            return (
                False,
                "That path is not a file."
            )

        supported_extensions = {
            ".txt",
            ".py",
            ".js",
            ".jsx",
            ".ts",
            ".tsx",
            ".json",
            ".md",
            ".csv",
            ".log",
            ".html",
            ".css",
            ".xml",
            ".yaml",
            ".yml"
        }

        if (
            file_path.suffix.lower()
            not in supported_extensions
        ):

            return (
                False,
                "I can't directly read that file type yet."
            )

        content = file_path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        if len(content) > max_characters:

            content = (
                content[:max_characters]
                + "\n\n[Content truncated]"
            )

        return (
            True,
            content
        )

    except Exception as error:

        print(
            f"Read file error: {error}"
        )

        return (
            False,
            "I couldn't read that file."
        )