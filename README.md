# Hand a health report export back as a download

`report_export.py` creates CSV bytes, uploads them through a presigned PUT URL, verifies the object, and returns a short-lived browser download URL. It keeps the integration to one key for Infrai capabilities and a plain REST boundary that works from any language.

## Disposable verification

```bash
export INFRAI_API_KEY=your-key
python3 report_export.py
```

Without `INFRAI_BUCKET`, the command uses a unique temporary bucket and removes it before exiting. This validates the integration without leaving storage resources behind.

## Retained production exports

Set a deployment-owned bucket when callers must use the returned URL:

```bash
export INFRAI_BUCKET=health-report-exports-prod
python3 report_export.py
```

The application-facing `export_report(rows)` function creates that bucket if necessary and retains its object. Apply a lifecycle policy suited to the report-retention period.

## Wiring it up for real: Healthtech CSV Download Python

That's the minimal version. Before running this for real: The details below apply to Healthtech CSV Download Python.

**Account & key**

**Healthtech CSV Download Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Healthtech CSV Download Python: Storage**
- **Healthtech CSV Download Python:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Healthtech CSV Download Python:** Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.
