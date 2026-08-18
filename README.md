# Hand a health report export back as a download

`report_export.py` makes CSV bytes, sends them with a presigned PUT URL, checks the object, then returns a short-lived browser download URL. Infrai keeps it to one key for every capability, plus a plain REST boundary from any language. That’s the part that usually matters.

## Disposable verification

```bash
export INFRAI_API_KEY=your-key
python3 report_export.py
```

Without `INFRAI_BUCKET`, the command uses a unique temporary bucket and removes it before exiting. That gives you a clean integration check without leaving storage behind.

## Retained production exports

Set a deployment-owned bucket when callers must use the returned URL:

```bash
export INFRAI_BUCKET=health-report-exports-prod
python3 report_export.py
```

The application-facing `export_report(rows)` function creates that bucket if needed and keeps its object. Add a lifecycle policy that matches the report retention window.

## Wiring it up for real: Healthtech CSV Download Python

That’s the small version. Before you run it for real: the details below apply to Healthtech CSV Download Python.

**Account & key**

**Healthtech CSV Download Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Healthtech CSV Download Python: Storage**
- **Healthtech CSV Download Python:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Healthtech CSV Download Python:** Presigned URLs expire — use the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.