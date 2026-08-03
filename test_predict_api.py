import urllib.request
import urllib.parse
import json
import os

def send_post_file(url, file_path, headers):
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    
    # Read file content
    with open(file_path, 'rb') as f:
        file_content = f.read()
        
    filename = os.path.basename(file_path)
    
    # Construct multipart request body
    body = []
    body.append(f'--{boundary}'.encode('utf-8'))
    body.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode('utf-8'))
    body.append(b'Content-Type: video/mp4')
    body.append(b'')
    body.append(file_content)
    body.append(f'--{boundary}--'.encode('utf-8'))
    body.append(b'')
    
    request_data = b'\r\n'.join(body)
    
    req = urllib.request.Request(url, data=request_data)
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    for k, v in headers.items():
        req.add_header(k, v)
        
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"HTTPError: {e.code} - {e.read().decode('utf-8')}")
        raise

def get_json(url, headers):
    req = urllib.request.Request(url)
    for k, v in headers.items():
        req.add_header(k, v)
    with urllib.request.urlopen(req) as response:
        return response.status, json.loads(response.read().decode('utf-8'))

def main():
    predict_url = "http://127.0.0.1:8000/api/v1/predict"
    clear_path = "data/uploads/TEST VIDEO.mp4"
    blur_path = "data/uploads/TEST VIDEO EXTREME BLUR.mp4"
    
    headers = {
        "Authorization": "Bearer spectraguard_secure_validation_token_xyz"
    }
    
    print("1. Sending CLEAR CCTV Video to API...")
    status, response = send_post_file(predict_url, clear_path, headers)
    print(f"Prediction Trigger Status: {status}")
    print(f"Prediction Trigger Response: {response}")
    
    pred_id = response["prediction_id"]
    details_url = f"http://127.0.0.1:8000/api/v1/predictions/{pred_id}"
    status_details, details = get_json(details_url, headers)
    print(f"Clear Prediction Result: {details['prediction']} (Expected: nominal)")
    print(f"Clear Confidence Score: {details['confidence']:.4f}")
    print(f"Clear Severity: {details['severity']}")
    
    print("\n2. Sending BLURRY Video to API...")
    status_blur, response_blur = send_post_file(predict_url, blur_path, headers)
    print(f"Prediction Trigger Status: {status_blur}")
    print(f"Prediction Trigger Response: {response_blur}")
    
    pred_id_blur = response_blur["prediction_id"]
    details_blur_url = f"http://127.0.0.1:8000/api/v1/predictions/{pred_id_blur}"
    status_details_blur, details_blur = get_json(details_blur_url, headers)
    print(f"Blurry Prediction Result: {details_blur['prediction']} (Expected: tampering_suspected)")
    print(f"Blurry Confidence Score: {details_blur['confidence']:.4f}")
    print(f"Blurry Severity: {details_blur['severity']}")

if __name__ == "__main__":
    main()
