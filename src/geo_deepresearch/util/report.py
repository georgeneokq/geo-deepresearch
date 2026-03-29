import time
from pathlib import Path
from typing import Optional


def generate_report_output_path(
    file_name_base: Optional[str] = None, ext: str = "md"
) -> Path:
    """
    Generate the output path for a report file.

    Args:
        file_name_base: Base name for the file. If None, uses current timestamp.
        ext: File extension (default: "md")

    Returns:
        Path: Absolute path for the report file
    """
    save_dir = Path("./outputs").absolute()
    filename = f"{file_name_base if file_name_base else int(time.time())}.{ext}"
    return save_dir / filename


def save_report(
    file_contents: str, file_name_base: Optional[str] = None, ext: str = "md"
) -> Path:
    """
    Save report contents to a file.

    Args:
        file_contents: The content to write to the report file
        file_name_base: Base name for the file. If None, uses current timestamp.
        ext: File extension (default: "md")

    Returns:
        Path: Absolute path to the saved report file
    """
    # Ensure directory exists
    path = generate_report_output_path(file_name_base=file_name_base, ext=ext)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        f.write(file_contents)

    return path
