from flask import Flask
import os

def create_app():
    # Caminho da pasta raiz PROJETO-PWEB (cada dirname sobe um nível na hierarquia)
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    app = Flask(
        __name__,
        template_folder=os.path.join(ROOT_DIR, "templates"),
        static_folder=os.path.join(ROOT_DIR, "static")
    )

    # Importa e registra o blueprint principal
    from .main import main_bp
    app.register_blueprint(main_bp)
    from .users import users_bp
    app.register_blueprint(users_bp)

    return app
