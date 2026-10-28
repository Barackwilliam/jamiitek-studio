"""Streaming private files to their owner, with HTTP range support.

Callers must check ownership first. Range requests let browsers seek in
videos and resume downloads; only single byte ranges are supported.
"""

import mimetypes
import re

from django.http import FileResponse, Http404, HttpResponse, StreamingHttpResponse
from django.utils.http import content_disposition_header

RANGE_PATTERN = re.compile(r"^bytes=(\d*)-(\d*)$")
CHUNK_SIZE = 64 * 1024


def _parse_range(header, size):
    """Return (start, end) inclusive, None for no/ignored range, or "invalid"."""
    match = RANGE_PATTERN.match(header.strip())
    if not match:
        return None  # malformed or multiple ranges: send the whole file
    first, last = match.groups()
    if first == "" and last == "":
        return None
    if first == "":
        length = int(last)
        if length == 0:
            return "invalid"
        return max(0, size - length), size - 1
    start = int(first)
    end = min(int(last), size - 1) if last else size - 1
    if start >= size or start > end:
        return "invalid"
    return start, end


def _chunks(handle, remaining):
    try:
        while remaining > 0:
            data = handle.read(min(CHUNK_SIZE, remaining))
            if not data:
                break
            remaining -= len(data)
            yield data
    finally:
        handle.close()


def stream_private_file(request, field, filename, download=False):
    try:
        size = field.size
        handle = field.open("rb")
    except (FileNotFoundError, OSError, ValueError):
        raise Http404("File missing")
    content_type = mimetypes.guess_type(field.name)[0] or "application/octet-stream"
    byte_range = _parse_range(request.headers.get("Range", ""), size) if request.headers.get("Range") else None

    if byte_range == "invalid":
        handle.close()
        response = HttpResponse(status=416)
        response["Content-Range"] = f"bytes */{size}"
    elif byte_range is None:
        response = FileResponse(handle, content_type=content_type, as_attachment=download, filename=filename)
    else:
        start, end = byte_range
        handle.seek(start)
        response = StreamingHttpResponse(_chunks(handle, end - start + 1), status=206, content_type=content_type)
        response["Content-Range"] = f"bytes {start}-{end}/{size}"
        response["Content-Length"] = str(end - start + 1)
        response["Content-Disposition"] = content_disposition_header(download, filename)
    response["Accept-Ranges"] = "bytes"
    response["Cache-Control"] = "private, max-age=300"
    return response
