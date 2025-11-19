"""
API Flask para Image Labels Generator
Integração com AWS Rekognition
"""

# ==========================================
# IMPORTS
# ==========================================
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import base64
import logging
from rekognition_service import RekognitionService

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================================
# CONFIGURAÇÃO DA APLICAÇÃO
# ==========================================
load_dotenv()
app = Flask(__name__)
CORS(app)  # Habilitar CORS para requisições do frontend

# Inicializar serviço Rekognition
rekognition_service = RekognitionService()

logger.info("Aplicação Flask iniciada com sucesso")

# ==========================================
# CONFIGURAÇÕES
# ==========================================
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# ==========================================
# ROUTES - HEALTH CHECK
# ==========================================
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Image Labels Generator',
        'version': '1.0.0'
    }), 200

# ==========================================
# ROUTES - ANALYZE IMAGE
# ==========================================
@app.route('/api/analyze', methods=['POST'])
def analyze_image():
    """
    Endpoint principal para análise de imagem
    Recebe: imagem em base64 e min_confidence (opcional)
    Retorna: labels detectados pelo Rekognition
    """
    try:
        # Validar se há dados no request
        if not request.json:
            return jsonify({
                'success': False,
                'error': 'Nenhum dado enviado'
            }), 400
        
        # Extrair dados do request
        image_base64 = request.json.get('image')
        min_confidence = request.json.get('min_confidence', 80)
        
        # Validar imagem
        if not image_base64:
            return jsonify({
                'success': False,
                'error': 'Imagem não fornecida'
            }), 400
        
        # Decodificar imagem
        try:
            image_bytes = decode_base64_image(image_base64)
        except Exception as e:
            logger.error(f"Erro ao decodificar imagem: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Erro ao processar imagem. Verifique o formato.'
            }), 400
        
        # Validar tamanho
        if len(image_bytes) > MAX_IMAGE_SIZE:
            return jsonify({
                'success': False,
                'error': f'Imagem muito grande. Tamanho máximo: {MAX_IMAGE_SIZE / (1024*1024)}MB'
            }), 400
        
        # Chamar serviço Rekognition
        logger.info(f"Processando imagem com confidence={min_confidence}")
        result = rekognition_service.detect_labels(image_bytes, min_confidence)
        
        # Verificar se houve erro
        if not result.get('success'):
            return jsonify(result), 400
        
        logger.info(f"Análise concluída: {result['label_count']} labels encontrados")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

# ==========================================
# FUNÇÕES AUXILIARES
# ==========================================
def validate_image(image_data):
    """Valida o formato e tamanho da imagem"""
    # Validação básica
    if not image_data:
        return False, "Imagem vazia"
    
    if len(image_data) > MAX_IMAGE_SIZE:
        return False, f"Imagem muito grande. Máximo: {MAX_IMAGE_SIZE / (1024*1024)}MB"
    
    return True, "OK"

def decode_base64_image(base64_string):
    """Decodifica imagem base64 para bytes"""
    # Remove o prefixo data:image se existir
    if ',' in base64_string:
        base64_string = base64_string.split(',')[1]
    
    # Decodifica
    image_bytes = base64.b64decode(base64_string)
    return image_bytes

# ==========================================
# ERROR HANDLERS
# ==========================================
@app.errorhandler(400)
def bad_request(error):
    """Handler para erros 400"""
    return jsonify({
        'success': False,
        'error': 'Requisição inválida',
        'details': str(error)
    }), 400

@app.errorhandler(500)
def internal_error(error):
    """Handler para erros 500"""
    logger.error(f"Erro 500: {str(error)}")
    return jsonify({
        'success': False,
        'error': 'Erro interno do servidor'
    }), 500

# ==========================================
# MAIN
# ==========================================
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)