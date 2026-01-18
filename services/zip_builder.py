import io
import zipfile
import requests
from typing import List, Tuple

def _guess_ext(content_type: str) -> str:
    ct = (content_type or "").lower()
    if "png" in ct: return "png"
    if "webp" in ct: return "webp"
    if "gif" in ct: return "gif"
    if "jpeg" in ct or "jpg" in ct: return "jpg"
    return "jpg"

def build_zip_parts(
    urls: List[str],
    timeout: int,
    max_total_images: int,
    max_each_mb: int,
    part_max_mb: int
) -> Tuple[List[bytes], int, int]:
    """
    Returns (zip_parts_bytes_list, added_count, skipped_count)
    """
    max_each = max_each_mb * 1024 * 1024
    part_max = part_max_mb * 1024 * 1024

    parts: List[bytes] = []
    added = 0
    skipped = 0

    current_buf = io.BytesIO()
    current_zip = zipfile.ZipFile(current_buf, "w", compression=zipfile.ZIP_DEFLATED)
    current_size = 0
    file_index = 1

    def finalize_part():
        nonlocal current_buf, current_zip, current_size
        try:
            current_zip.close()
        except Exception:
            pass
        current_buf.seek(0)
        data = current_buf.read()
        if len(data) > 0:
            parts.append(data)
        current_buf = io.BytesIO()
        current_zip = zipfile.ZipFile(current_buf, "w", compression=zipfile.ZIP_DEFLATED)
        current_size = 0

    for url in urls[:max_total_images]:
        try:
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
            content = r.content
            if len(content) > max_each:
                skipped += 1
                continue

            ext = _guess_ext(r.headers.get("Content-Type", ""))
            fname = f"image_{file_index:04d}.{ext}"

            # if adding this file pushes us over part limit, finalize and start new part
            if current_size + len(content) > part_max and current_size > 0:
                finalize_part()

            current_zip.writestr(fname, content)
            current_size += len(content)
            added += 1
            file_index += 1

        except Exception:
            skipped += 1
            continue

    # finalize last part
    try:
        current_zip.close()
    except Exception:
        pass
    current_buf.seek(0)
    last = current_buf.read()
    if len(last) > 0:
        parts.append(last)

    return parts, added, skipped
