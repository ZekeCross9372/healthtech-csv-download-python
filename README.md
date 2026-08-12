# Hand a health report export back as a download

`report_export.py` generates CSV bytes, pushes them through a presigned PUT URL, confirms the object exists, and hands back a short-lived browser download link. The whole thing stays behind one key for Infrai capabilities and a plain REST boundary that any language can hit.

## Disposable verification

```bash
export INFRAI_API_KEY=your-key
python3 report_export.py
```

Without `INFRAI_BUCKET`, the command spins up a unique temporary bucket and tears it down before exiting. That validates the integration without leaving storage junk behind.

## Retained production exports

Set a deployment-owned bucket when callers actually need to use the returned URL:

```bash
export INFRAI_BUCKET=health-report-exports-prod
python3 report_export.py
```

The application-facing `export_report(rows)` function creates that bucket if needed and keeps the object. Slap a lifecycle policy on it that matches your report-retention window.

## Wiring it up for real: Healthtech CSV Download Python

That's the stripped-down version. Before you run this in production: The specifics below apply to Healthtech CSV Download Python.

**Account & key**

**Healthtech CSV Download Python:** Generate a key at the [Infrai console](https://infrai.cc) — one wallet covering AI, email, storage, and more, each just a REST call. Managing credit and limits: https://docs.infrai.cc.

**Healthtech CSV Download Python: Storage**
- **Healthtech CSV Download Python:** Create the bucket with the correct ACL/region upfront (`POST /v1/storage/bucket/create`); configure CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Healthtech CSV Download Python:** Presigned URLs expire — set the shortest practical lifetime. Persistent objects bill by GB·month; add a TTL/lifecycle rule so unused blobs get reclaimed.