"""
Serviço de integração com AWS Rekognition
Responsável por toda comunicação com a API da AWS
"""

# ==========================================
# IMPORTS
# ==========================================
import boto3
from botocore.exceptions import ClientError
import os
import logging

# ==========================================
# CONFIGURAÇÃO DE LOGGING
# ==========================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================================
# CLASSE REKOGNITION SERVICE
# ==========================================
class RekognitionService:
    """
    Classe para gerenciar operações do AWS Rekognition
    """
    
    def __init__(self):
        """Inicializa o cliente Rekognition"""
        try:
            self.client = boto3.client(
                'rekognition',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
            )
            logger.info("Cliente Rekognition inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar cliente Rekognition: {str(e)}")
            raise
    
    def detect_labels(self, image_bytes, min_confidence=80, max_labels=10):
        """
        Detecta labels em uma imagem usando AWS Rekognition
        
        Args:
            image_bytes: Imagem em formato bytes
            min_confidence: Confiança mínima (0-100)
            max_labels: Número máximo de labels a retornar
            
        Returns:
            dict: Dicionário com labels detectados
        """
        try:
            logger.info(f"Analisando imagem com min_confidence={min_confidence}")
            
            response = self.client.detect_labels(
                Image={'Bytes': image_bytes},
                MaxLabels=max_labels,
                MinConfidence=min_confidence
            )
            
            logger.info(f"Análise concluída. {len(response['Labels'])} labels encontrados")
            return self.format_labels_response(response)
            
        except ClientError as e:
            logger.error(f"Erro do AWS Rekognition: {str(e)}")
            return handle_rekognition_error(e)
        except Exception as e:
            logger.error(f"Erro inesperado: {str(e)}")
            raise
    
    def format_labels_response(self, rekognition_response):
        """
        Formata a resposta do Rekognition para o formato esperado pelo frontend
        
        Args:
            rekognition_response: Resposta bruta do Rekognition
            
        Returns:
            dict: Resposta formatada
        """
        labels = []
        
        for label in rekognition_response['Labels']:
            formatted_label = {
                'name': label['Name'],
                'confidence': round(label['Confidence'], 2),
                'parents': [parent['Name'] for parent in label.get('Parents', [])]
            }
            labels.append(formatted_label)
        
        return {
            'success': True,
            'labels': labels,
            'label_count': len(labels)
        }
    
    def validate_aws_credentials(self):
        """
        Valida se as credenciais AWS estão configuradas corretamente
        
        Returns:
            bool: True se credenciais válidas
        """
        try:
            # Tenta fazer uma chamada simples para validar credenciais
            self.client.describe_collection(CollectionId='test-validation')
        except ClientError as e:
            # Se o erro for de coleção não encontrada, as credenciais estão OK
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return True
            # Outros erros indicam problema com credenciais
            logger.error(f"Credenciais AWS inválidas: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Erro ao validar credenciais: {str(e)}")
            return False
        
        return True

# ==========================================
# FUNÇÕES AUXILIARES
# ==========================================
def handle_rekognition_error(error):
    """
    Trata erros específicos do Rekognition
    
    Args:
        error: Exceção do boto3
        
    Returns:
        dict: Mensagem de erro formatada
    """
    error_code = error.response['Error']['Code']
    error_message = error.response['Error']['Message']
    
    error_map = {
        'InvalidImageFormatException': 'Formato de imagem inválido. Use JPG ou PNG.',
        'ImageTooLargeException': 'Imagem muito grande. Tamanho máximo: 5MB.',
        'InvalidS3ObjectException': 'Erro ao acessar imagem no S3.',
        'InvalidParameterException': 'Parâmetros inválidos na requisição.',
        'AccessDeniedException': 'Acesso negado. Verifique suas credenciais AWS.',
        'ProvisionedThroughputExceededException': 'Limite de requisições excedido. Tente novamente.'
    }
    
    user_message = error_map.get(error_code, f'Erro ao processar imagem: {error_message}')
    
    return {
        'success': False,
        'error': user_message,
        'error_code': error_code
    }