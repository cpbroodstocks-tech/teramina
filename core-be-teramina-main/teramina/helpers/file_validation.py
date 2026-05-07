"""File upload validation helpers."""

ALLOWED_CSV_TYPES = {"text/csv", "application/csv", "text/plain", "application/octet-stream"}
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}

MAX_CSV_SIZE_BYTES = 10 * 1024 * 1024   # 10 MB
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def validate_csv_file(file) -> str | None:
    """Return an error message string if the file is invalid, None if valid."""
    if file.size > MAX_CSV_SIZE_BYTES:
        return f"File too large. Maximum allowed size is {MAX_CSV_SIZE_BYTES // (1024 * 1024)} MB."
    if file.content_type not in ALLOWED_CSV_TYPES:
        return f"Invalid file type '{file.content_type}'. Only CSV files are accepted."
    return None


def validate_image_file(file) -> str | None:
    """Return an error message string if the file is invalid, None if valid."""
    if file is None:
        return None
    if file.size > MAX_IMAGE_SIZE_BYTES:
        return f"Image too large. Maximum allowed size is {MAX_IMAGE_SIZE_BYTES // (1024 * 1024)} MB."
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        return f"Invalid image type '{file.content_type}'. Allowed types: JPEG, PNG, WebP."
    return None
