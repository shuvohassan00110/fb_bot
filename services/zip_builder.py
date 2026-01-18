import io, zipfile, requests
def build_zip_parts(urls, timeout, max_total_images, max_each_mb, part_max_mb):
    max_each=max_each_mb*1024*1024; part_max=part_max_mb*1024*1024
    parts=[]; added=0; skipped=0
    buf=io.BytesIO(); z=zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED); size=0; i=1
    def flush():
        nonlocal buf,z,size
        z.close(); buf.seek(0); data=buf.read()
        if data: parts.append(data)
        buf=io.BytesIO(); z=zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED); size=0
    for u in urls[:max_total_images]:
        try:
            r=requests.get(u,timeout=timeout); c=r.content
            if len(c)>max_each: skipped+=1; continue
            if size+len(c)>part_max and size>0: flush()
            z.writestr(f"image_{i:04d}.jpg",c); size+=len(c); added+=1; i+=1
        except: skipped+=1
    z.close(); buf.seek(0)
    if buf.read(): parts.append(buf.getvalue())
    return parts, added, skipped
