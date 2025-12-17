import os
from flask import Flask
from .config import Config

def create_app():
    """
    Cria e configura a instância da aplicação Flask.
    
    Esta função:
    1. Inicializa o app Flask.
    2. Carrega as configurações do objeto Config.
    3. Garante que as pastas de upload e dados existam.
    4. Registra os Blueprints (módulos) da aplicação.
    """
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    # ensure folders
    # Garante que os diretórios necessários existam
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['DATA_FOLDER'], exist_ok=True)

    # register blueprints
    # Importa e registra os módulos (Blueprints)
    from .auth import bp as auth_bp
    from .posts import bp as posts_bp
    from .admin import bp as admin_bp
    from .main import bp as main_bp   # <=== IMPORTANTE

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(posts_bp, url_prefix='/posts')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(main_bp)   # <=== REGISTRA O /

    return app
