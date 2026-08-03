import urllib.request

prediction_id = 'pred_a916f2'
req = urllib.request.Request('http://127.0.0.1:8000/api/v1/predictions/' + prediction_id, method='GET')
req.add_header('Authorization', 'Bearer spectraguard_secure_validation_token_xyz')
with urllib.request.urlopen(req) as r:
    print(r.read().decode())
