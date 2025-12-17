import os
import shutil
from flask import Flask
from .config import Config
from .utils_csv import ensure_json_file, read_json, write_json

def migrate_uploads(app: Flask):
    """
    Migra arquivos de upload antigos para a nova estrutura por usuário:
    - Profile/Cover: de uploads/profile/* para uploads/<user_id>/(profile|cover)/*
    - Posts: de uploads/post/* para uploads/<author_id>/posts/*
    Atualiza os caminhos nos JSONs.
    """
    users_json = app.config['USERS_JSON']
    posts_json = app.config['POSTS_JSON']

    # Garante arquivos
    ensure_json_file(users_json)
    ensure_json_file(posts_json)

    # Migra usuários
    users = read_json(users_json)
    users_changed = False
    for u in users:
        uid = u.get('id')
        if not uid:
            continue
        base_rel = f"uploads/{uid}"
        base_dir = os.path.join(app.static_folder, base_rel.replace('/', os.sep))
        os.makedirs(os.path.join(base_dir, 'profile'), exist_ok=True)
        os.makedirs(os.path.join(base_dir, 'cover'), exist_ok=True)
        os.makedirs(os.path.join(base_dir, 'posts'), exist_ok=True)

        # profile image
        pi = u.get('profile_image')
        if pi and pi.startswith('uploads/profile/'):
            fn = os.path.basename(pi)
            old_full = os.path.join(app.static_folder, pi.replace('/', os.sep))
            new_rel = f"uploads/{uid}/profile/{fn}"
            new_full = os.path.join(app.static_folder, new_rel.replace('/', os.sep))
            try:
                if os.path.exists(old_full):
                    shutil.move(old_full, new_full)
                u['profile_image'] = new_rel
                users_changed = True
            except Exception:
                # não interrompe a migração
                pass

        # cover image
        ci = u.get('cover_image')
        if ci and ci.startswith('uploads/profile/'):
            fn = os.path.basename(ci)
            old_full = os.path.join(app.static_folder, ci.replace('/', os.sep))
            new_rel = f"uploads/{uid}/cover/{fn}"
            new_full = os.path.join(app.static_folder, new_rel.replace('/', os.sep))
            try:
                if os.path.exists(old_full):
                    shutil.move(old_full, new_full)
                u['cover_image'] = new_rel
                users_changed = True
            except Exception:
                pass

    if users_changed:
        write_json(users_json, users)

    # Migra posts
    posts = read_json(posts_json)
    posts_changed = False
    for p in posts:
        ip = p.get('image_path')
        if ip and ip.startswith('uploads/post/'):
            fn = os.path.basename(ip)
            author_id = p.get('author_id')
            if not author_id:
                continue
            old_full = os.path.join(app.static_folder, ip.replace('/', os.sep))
            new_rel = f"uploads/{author_id}/posts/{fn}"
            new_full = os.path.join(app.static_folder, new_rel.replace('/', os.sep))
            os.makedirs(os.path.dirname(new_full), exist_ok=True)
            try:
                if os.path.exists(old_full):
                    shutil.move(old_full, new_full)
                p['image_path'] = new_rel
                posts_changed = True
            except Exception:
                pass

    if posts_changed:
        write_json(posts_json, posts)

    # Remove diretórios antigos se estiverem vazios
    try:
        old_profile_dir = os.path.join(app.static_folder, 'uploads', 'profile')
        old_post_dir = os.path.join(app.static_folder, 'uploads', 'post')
        for d in (old_profile_dir, old_post_dir):
            if os.path.isdir(d) and not os.listdir(d):
                shutil.rmtree(d)
    except Exception:
        # não interrompe startup caso limpeza falhe
        pass

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

    # migra estrutura de uploads se necessário
    migrate_uploads(app)

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
