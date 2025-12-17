import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """
    Classe de configuração da aplicação.
    Define caminhos de arquivos, chaves secretas e limites de upload.
    """
    SECRET_KEY = os.environ.get('SOS_JAMPA_SECRET', 'best_secret_key_ever_truste_me')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    DATA_FOLDER = os.path.join(BASE_DIR, 'data')
    
    # JSON Files
    # Caminhos para os arquivos de dados JSON
    USERS_JSON = os.path.join(DATA_FOLDER, 'users.json')
    POSTS_JSON = os.path.join(DATA_FOLDER, 'posts.json')
    COMMENTS_JSON = os.path.join(DATA_FOLDER, 'comments.json')
    TAGS_JSON = os.path.join(DATA_FOLDER, 'tags.json')
    COLLECTION_POINTS_JSON = os.path.join(DATA_FOLDER, 'collection_points.json')
    
    # CSV File (only banned)
    # Caminho para o arquivo CSV de usuários banidos
    BANNED_CSV = os.path.join(DATA_FOLDER, 'banned.csv')

    # limits
    # Limites para uploads de arquivos
    MAX_PROFILE_MB = 2
    MAX_IMAGE_MB = 5
    MAX_IMAGE_DIM = 1600

    REMEMBER_COOKIE_DURATION = timedelta(days=7)
