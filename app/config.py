import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """
    Classe de configuração da aplicação.
    Define caminhos de arquivos, chaves secretas e limites de upload.
    """
    SECRET_KEY = os.environ.get('SOS_JAMPA_SECRET', 's0s_j4mp4_s3cr3t_k3y_t00_5tr0ng_t0_b3_gu3ss3d')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    DATA_FOLDER = os.path.join(BASE_DIR, 'data')
    
    # JSON Files
    # Caminhos para os arquivos de dados JSON
    USERS_JSON = os.path.join(DATA_FOLDER, 'users.json')
    POSTS_JSON = os.path.join(DATA_FOLDER, 'posts.json')
    COMMENTS_JSON = os.path.join(DATA_FOLDER, 'comments.json')
    TAGS_JSON = os.path.join(DATA_FOLDER, 'tags.json')
    
    # API Keys
    NEWSDATA_API_KEY = os.environ.get('NEWSDATA_API_KEY', 'pub_75d0f8133078426595f22f22e71631b3')
    NEWSAPI_KEY = os.environ.get('NEWSAPI_KEY', 'cc2b5389cfb049ba8d27f2b171fa843b') # https://newsapi.org
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
