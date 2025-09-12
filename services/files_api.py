from __future__ import annotations

import os
import mimetypes
from urllib.parse import unquote

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse

from src.utils.config import config

app = FastAPI(title="Decipher Files API", version="0.1.0")


def _allowed_roots():
    return [
        os.path.abspath(config.reports_path),
        os.path.abspath(os.path.join(config.data_path, "extracted", "synthesis")),
        os.path.abspath(os.path.join(config.data_path, "extracted", "transformation")),
        os.path.abspath(os.path.join(config.data_path, "ingest", "figures")),
    ]


def _is_allowed(path: str) -> bool:
    ap = os.path.abspath(path)
    for root in _allowed_roots():
        if ap.startswith(root):
            return True
    return False


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/files/raw")
def get_raw(path: str = Query(..., description="Absolute or repo-relative path to a local file")):
    path = unquote(path)
    # Allow repo-relative path
    if not os.path.isabs(path):
        path = os.path.abspath(path)
    if not _is_allowed(path):
        raise HTTPException(status_code=403, detail="Path not allowed")
    if not os.path.exists(path) or not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File not found")
    media_type, _ = mimetypes.guess_type(path)
    return FileResponse(path, media_type=media_type or "application/octet-stream", filename=os.path.basename(path))


@app.get("/files/pdf_view")
def pdf_view(path: str = Query(...), page: int = Query(1)):
    path = unquote(path)
    if not os.path.isabs(path):
        path = os.path.abspath(path)
    if not _is_allowed(path):
        raise HTTPException(status_code=403, detail="Path not allowed")
    if not os.path.exists(path) or not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File not found")
    # Serve a tiny HTML wrapper that embeds the PDF with a page anchor
    from urllib.parse import quote
    raw_url = f"/files/raw?path={quote(path)}#page={page}"
    html = f"""
    <!doctype html>
    <html>
      <head>
        <meta charset='utf-8'/>
        <title>{os.path.basename(path)} - Page {page}</title>
        <style>html,body,iframe{{height:100%;margin:0;padding:0;border:0}}</style>
      </head>
      <body>
        <iframe src="{raw_url}" width="100%" height="100%"></iframe>
      </body>
    </html>
    """
    return HTMLResponse(html)

# Run with: uvicorn services.files_api:app --reload --port 9002

