import requests
import base64

# Ler uma imagem local
with open('test_image.jpg', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

# Fazer requisição
response = requests.post('http://localhost:5000/api/analyze', json={
    'image': image_data,
    'min_confidence': 80
})

print(response.json())