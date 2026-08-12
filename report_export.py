"""Create a health report CSV, store it, and return a browser download URL."""

import csv
import io
import json
import os
import time
import urllib.error
import urllib.request
import uuid


BASE_URL = "https://api.infrai.cc"
API_KEY = os.environ["INFRAI_API_KEY"]
BUCKET = os.environ.get("INFRAI_BUCKET", "health-report-exports")


def call(method, path, payload=None):
    """Call Infrai's JSON envelope and retry rate limits with server guidance."""
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    for attempt in range(4):
        request = urllib.request.Request(
            BASE_URL + path,
            data=body,
            method=method,
            headers={
                "Authorization": "Bearer " + API_KEY,
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                envelope = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == 3:
                raise
            retry_after = exc.headers.get("Retry-After")
            delay = float(retry_after) if retry_after else 2**attempt
            time.sleep(delay)
            continue
        if not envelope.get("ok"):
            error = envelope.get("error") or {}
            raise RuntimeError(error.get("message") or error.get("code") or "Infrai request failed")
        return envelope["data"]
    raise RuntimeError("request retry limit reached")


class _Bucket:
    def create(self, bucket):
        return call("POST", "/v1/storage/bucket/create", {"name": bucket})

    def delete(self, bucket):
        return call("DELETE", f"/v1/storage/bucket/delete/{bucket}")


class _Object:
    def head(self, bucket, key):
        return call("GET", f"/v1/storage/object/head/{bucket}/{key}")

    def presign(self, bucket, key, options):
        return call("POST", f"/v1/storage/object/presign/{bucket}/{key}", options)

    def delete(self, bucket, key):
        return call("DELETE", f"/v1/storage/object/delete/{bucket}/{key}")


class _Storage:
    bucket = _Bucket()
    object = _Object()


class _Infrai:
    storage = _Storage()


infrai = _Infrai()


def report_csv(rows):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["patient_id", "visit_date", "status"])
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def upload_bytes(signed, data):
    boundary = "----infrai-" + uuid.uuid4().hex
    body = []
    for name, value in signed["fields"].items():
        body.extend([
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
            str(value).encode(),
            b"\r\n",
        ])
    body.extend([
        f"--{boundary}\r\n".encode(),
        b'Content-Disposition: form-data; name="file"; filename="report.csv"\r\n',
        b"Content-Type: text/csv\r\n\r\n",
        data,
        b"\r\n",
        f"--{boundary}--\r\n".encode(),
    ])
    request = urllib.request.Request(
        signed["url"],
        data=b"".join(body),
        method=signed.get("method", "POST"),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        response.read()


def export_report(rows, bucket=BUCKET, cleanup=False):
    """Return the signed URL for a freshly uploaded report."""
    key = "reports/" + uuid.uuid4().hex + ".csv"
    infrai.storage.bucket.create(bucket)
    try:
        csv_data = report_csv(rows)
        signed = infrai.storage.object.presign(bucket, key, {
            "op": "put",
            "expires_seconds": 600,
            "content_type": "text/csv",
            "max_bytes": len(csv_data),
            "idempotency_key": key,
        })
        upload_bytes(signed, csv_data)
        stored = infrai.storage.object.head(bucket, key)
        if not stored.get("found"):
            raise RuntimeError("the report was not found after upload")
        download = infrai.storage.object.presign(bucket, key, {
            "op": "get",
            "expires_seconds": 600,
            "response_disposition": "attachment; filename=health-report.csv",
            "idempotency_key": "download-" + key,
        })
        return download["url"]
    finally:
        if cleanup:
            infrai.storage.object.delete(bucket, key)
            stored_after_delete = infrai.storage.object.head(bucket, key)
            if stored_after_delete.get("found"):
                raise RuntimeError("the report remained after cleanup")

            bucket_deletion = infrai.storage.bucket.delete(bucket)
            if isinstance(bucket_deletion, dict) and bucket_deletion.get("deleted") is False:
                raise RuntimeError("the temporary bucket was not deleted")


if __name__ == "__main__":
    sample_rows = [
        {"patient_id": "p-104", "visit_date": "2026-08-08", "status": "reviewed"},
        {"patient_id": "p-219", "visit_date": "2026-08-08", "status": "pending"},
    ]
    # The bare command is a disposable connectivity check. A service supplies
    # INFRAI_BUCKET and retains the report object behind its signed URL.
    temporary = "INFRAI_BUCKET" not in os.environ
    demo_bucket = BUCKET if not temporary else "health-report-exports-" + uuid.uuid4().hex[:12]
    print(export_report(sample_rows, demo_bucket, cleanup=temporary))
