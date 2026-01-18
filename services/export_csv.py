import io
import csv

def export_users_csv(user_ids):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["user_id"])
    for uid in sorted(user_ids):
        w.writerow([uid])
    data = io.BytesIO(buf.getvalue().encode("utf-8"))
    data.seek(0)
    return data
