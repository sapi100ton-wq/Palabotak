import os
import ipaddress
import socket
from urllib.parse import urlparse, unquote
from flask import Flask, request, jsonify, send_file
from io import BytesIO
import requests
from werkzeug.utils import secure_filename

app = Flask(__name__)
MAX_BYTES = 100 * 1024 * 1024
TIMEOUT = (8, 25)
ALLOWED_MODES = {"youtube", "pinterest", "tiktok"}

def validate_public_url(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise ValueError("Gunakan URL lengkap yang diawali http:// atau https://.")
        if parsed.username or parsed.password:
            raise ValueError("URL dengan kredensial tidak didukung.")
        host = parsed.hostname
        # Reject localhost and all non-public DNS results to reduce SSRF risk.
        infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
        if not infos:
            raise ValueError("Host tidak dapat ditemukan.")
        for info in infos:
            ip = ipaddress.ip_address(info[4][0])
            if not ip.is_global:
                raise ValueError("URL menuju alamat jaringan privat atau tidak publik, sehingga ditolak.")
        return parsed
    except ValueError:
        raise
    except Exception:
        raise ValueError("URL tidak valid atau host tidak dapat dijangkau.")

def filename_from_response(response, mode):
    raw = response.headers.get("Content-Disposition", "")
    match = __import__("re").search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)', raw, __import__("re").I)
    name = unquote(match.group(1)).strip().strip('"') if match else ""
    if not name:
        name = urlparse(response.url).path.rsplit("/", 1)[-1] or "media-unduhan"
    name = secure_filename(name)[:120] or "media-unduhan"
    if "." not in name:
        ext = {"youtube": ".media", "pinterest": ".img", "tiktok": ".video"}[mode]
        name += ext
    return name

@app.get("/health")
def health():
    return {"status": "ok"}, 200

@app.post("/api/download")
def download_media():
    data = request.get_json(silent=True) or {}
    url = str(data.get("url", "")).strip()
    mode = str(data.get("mode", "")).strip().lower()
    if mode not in ALLOWED_MODES:
        return jsonify(error="Mode unduhan tidak dikenal."), 400
    if not url or len(url) > 2048:
        return jsonify(error="Masukkan URL yang valid (maksimal 2048 karakter)."), 400

    current = url
    response = None
    try:
        # Follow redirects manually and validate every destination.
        for _ in range(6):
            parsed = validate_public_url(current)
            response = requests.get(
                current, stream=True, allow_redirects=False, timeout=TIMEOUT,
                headers={"User-Agent": "ReyzDownloader/1.0"}
            )
            if response.is_redirect or response.is_permanent_redirect:
                location = response.headers.get("Location")
                response.close()
                if not location:
                    return jsonify(error="Server sumber memberi pengalihan yang tidak valid."), 502
                from urllib.parse import urljoin
                current = urljoin(current, location)
                continue
            break
        else:
            return jsonify(error="Terlalu banyak pengalihan URL."), 400

        if response.status_code < 200 or response.status_code >= 300:
            response.close()
            return jsonify(error=f"Sumber mengembalikan HTTP {response.status_code}."), 502

        content_type = (response.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
        allowed = {
            "youtube": ("audio/", "video/"),
            "pinterest": ("image/",),
            "tiktok": ("video/",),
        }[mode]
        if not any(content_type.startswith(prefix) for prefix in allowed):
            response.close()
            return jsonify(error="Tipe berkas tidak sesuai dengan mode yang dipilih. Gunakan URL langsung ke berkas media."), 415

        length = response.headers.get("Content-Length")
        if length:
            try:
                if int(length) > MAX_BYTES:
                    response.close()
                    return jsonify(error="Ukuran berkas melebihi batas 100 MB."), 413
            except ValueError:
                pass

        chunks = []
        total = 0
        for chunk in response.iter_content(chunk_size=64 * 1024):
            if not chunk:
                continue
            total += len(chunk)
            if total > MAX_BYTES:
                response.close()
                return jsonify(error="Ukuran berkas melebihi batas 100 MB."), 413
            chunks.append(chunk)
        final_url = response.url
        filename = filename_from_response(response, mode)
        response.close()
        return send_file(
            BytesIO(b"".join(chunks)),
            mimetype=content_type or "application/octet-stream",
            as_attachment=True,
            download_name=filename,
            max_age=0
        )
    except ValueError as exc:
        if response is not None:
            response.close()
        return jsonify(error=str(exc)), 400
    except requests.RequestException:
        if response is not None:
            response.close()
        return jsonify(error="Tidak dapat mengambil berkas dari sumber. Periksa URL atau coba lagi."), 502
    except Exception:
        if response is not None:
            response.close()
        app.logger.exception("Download failed")
        return jsonify(error="Terjadi kesalahan pada server saat memproses berkas."), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
