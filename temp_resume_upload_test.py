import http.client
import uuid

boundary = '----WebKitFormBoundary' + uuid.uuid4().hex
body = b''
body += b'--' + boundary.encode() + b'\r\n'
body += b'Content-Disposition: form-data; name="file"; filename="test.pdf"\r\n'
body += b'Content-Type: application/pdf\r\n\r\n'
body += b'%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\r\n'
body += b'--' + boundary.encode() + b'--\r\n'

conn = http.client.HTTPConnection('127.0.0.1', 5000, timeout=10)
conn.request('POST', '/api/v1/resume/upload', body, {
    'Content-Type': f'multipart/form-data; boundary={boundary}',
    'Content-Length': str(len(body))
})
resp = conn.getresponse()
print('STATUS', resp.status)
print(resp.read().decode('utf-8', errors='ignore'))
conn.close()
