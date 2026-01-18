import io, zipfile, requests

def build_zip_parts(urls, part_max_mb: int = 45, max_files: int = 200):
    """
    Returns list of (filename, BytesIO)
    Splits into multiple zip parts when size exceeds part_max_mb.
    """
    parts = []
    part_idx = 1
    current = io.BytesIO()
    z = zipfile.ZipFile(current, "w", zipfile.ZIP_DEFLATED)

    def close_part():
        nonlocal z, current, part_idx
        z.close()
        current.seek(0)
        parts.append((f"images_part{part_idx}.zip", current))
        part_idx += 1
        current = io.BytesIO()
        z = zipfile.ZipFile(current, "w", zipfile.ZIP_DEFLATED)

    limit_bytes = part_max_mb * 1024 * 1024
    files_added = 0

    for i, u in enumerate(urls[:max_files], 1):
        try:
            content = requests.get(u, timeout=25).content
        except:
            continue

        # if adding this file crosses limit, close and start new
        if current.tell() + len(content) > limit_bytes and current.tell() > 0:
            close_part()

        z.writestr(f"img_{i}.jpg", content)
        files_added += 1

    # finalize last part if it has data
    if current.tell() > 0:
        close_part()

    return parts, files_added
