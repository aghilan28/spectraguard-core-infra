import os, sys, urllib.request, urllib.error
from pathlib import Path

base = 'http://127.0.0.1:8000/api/v1'
req = urllib.request.Request(base + '/system/health', method='GET')
with urllib.request.urlopen(req) as r:
    print('health_status', r.status)
    print(r.read().decode())

candidates = [str(p) for p in Path('.').rglob('*') if p.is_file() and p.suffix.lower() in {'.mp4','.avi','.mov','.jpg','.jpeg','.png'}]
print('samples', candidates[:10])
if not candidates:
    sys.exit(0)

path = candidates[0]
print('using', path)
body = open(path, 'rb').read()
boundary = '----boundary123'
payload = (
    b'--' + boundary.encode() + b'\r\n'
    b'Content-Disposition: form-data; name="file"; filename="' + os.path.basename(path).encode() + b'"\r\n'
    b'Content-Type: application/octet-stream\r\n\r\n' + body + b'\r\n'
    b'--' + boundary.encode() + b'--\r\n'
)
req = urllib.request.Request(base + '/predict', data=payload, method='POST')
req.add_header('Authorization', 'Bearer spectraguard_secure_validation_token_xyz')
req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
with urllib.request.urlopen(req) as r:
    print('predict_status', r.status)
    print(r.read().decode())
