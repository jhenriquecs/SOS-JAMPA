from flask import render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os, uuid, datetime
from ..utils_csv import read_json, append_json, write_json, ensure_json_file
from . import bp

# bp = Blueprint('auth', __name__)

def user_by_email(email):
    """
    Busca um usuário pelo email no arquivo users.json.
    Retorna o dicionário do usuário ou None se não encontrar.
    """
    users = read_json(current_app.config['USERS_JSON'])
    for u in users:
        if u['email'].lower() == email.lower():
            return u
    return None
def sanitize_nickname(n):
    """Normaliza nickname para uso em URL/handle: remove '@', espaços e caracteres inválidos, e usa minúsculas."""
    n = (n or '').strip()
    if n.startswith('@'):
        n = n[1:]
    # mantém letras, números, underline, ponto e hífen
    import re
    n = re.sub(r"[^a-zA-Z0-9_.-]", "", n)
    return n.lower()

def nickname_in_use(nick, exclude_user_id=None):
    users = read_json(current_app.config['USERS_JSON'])
    for u in users:
        if exclude_user_id and u.get('id') == exclude_user_id:
            continue
        if (u.get('nickname','') or '').lower() == (nick or '').lower():
            return True
    return False


def user_by_id(uid):
    """
    Busca um usuário pelo ID no arquivo users.json.
    Retorna o dicionário do usuário ou None se não encontrar.
    """
    users = read_json(current_app.config['USERS_JSON'])
    for u in users:
        if u['id'] == uid:
            return u
    return None

def is_banned(email):
    """
    Verifica se um email está na lista de banidos (banned.csv).
    Retorna True se estiver banido, False caso contrário.
    """
    banned_csv = current_app.config['BANNED_CSV']
    if not os.path.exists(banned_csv):
        return False
    
    try:
        with open(banned_csv, 'r', newline='', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines[1:]:  # Pula cabeçalho
                parts = line.strip().split(',')
                if len(parts) > 0 and parts[0].lower() == email.lower():
                    return True
    except FileNotFoundError:
        return False
    
    return False

def add_ban(email, reason):
    """
    Adiciona um email ao arquivo banned.csv.
    - Cria o arquivo e cabeçalho se não existirem.
    - Registra email, motivo e data/hora do banimento.
    """
    banned_csv = current_app.config['BANNED_CSV']
    os.makedirs(os.path.dirname(banned_csv), exist_ok=True)

    # Evita duplicar banimento
    if is_banned(email):
        return False

    # Cria cabeçalho se não existir
    if not os.path.exists(banned_csv):
        with open(banned_csv, 'w', newline='', encoding='utf-8') as f:
            f.write('email,ban_reason,ban_at\n')

    # Acrescenta a linha
    with open(banned_csv, 'a', newline='', encoding='utf-8') as f:
        brasilia_tz = datetime.timezone(datetime.timedelta(hours=-3))
        ban_at = datetime.datetime.now(brasilia_tz).strftime('%H:%M:%S %d/%m/%Y')
        # Substitui vírgulas na razão para não quebrar o CSV simples
        safe_reason = (reason or '').replace(',', ' ')
        f.write(f"{email},{safe_reason},{ban_at}\n")
    return True

def get_all_bans():
    """
    Lê o arquivo banned.csv e retorna uma lista de dicionários com todos os banimentos.
    Cada item contém: email, reason (motivo) e at (data/hora).
    """
    banned_csv = current_app.config['BANNED_CSV']
    bans = []
    if os.path.exists(banned_csv):
        with open(banned_csv, 'r', newline='', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines[1:]:
                parts = line.strip().split(',')
                if len(parts) >= 3:
                    bans.append({
                        'email': parts[0],
                        'reason': parts[1],
                        'at': parts[2]
                    })
    return bans

def remove_ban(email):
    """
    Remove um email da lista de banidos (banned.csv).
    Reescreve o arquivo mantendo apenas os emails que não correspondem ao informado.
    """
    banned_csv = current_app.config['BANNED_CSV']
    if not os.path.exists(banned_csv):
        return
    
    lines = []
    with open(banned_csv, 'r', newline='', encoding='utf-8') as f:
        lines = f.readlines()
    
    with open(banned_csv, 'w', newline='', encoding='utf-8') as f:
        if lines:
            f.write(lines[0]) # Header
            for line in lines[1:]:
                parts = line.strip().split(',')
                if len(parts) > 0 and parts[0].lower() != email.lower():
                    f.write(line)

def ensure_user_upload_dirs(user_id):
    """Cria a estrutura de uploads por usuário: perfil, capa e posts."""
    base = os.path.join(current_app.config['UPLOAD_FOLDER'], user_id)
    os.makedirs(os.path.join(base, 'profile'), exist_ok=True)
    os.makedirs(os.path.join(base, 'cover'), exist_ok=True)
    os.makedirs(os.path.join(base, 'posts'), exist_ok=True)

@bp.before_request
def ensure_files():
    """
    Executado antes de cada requisição neste Blueprint.
    Garante que todos os arquivos de dados (JSON e CSV) necessários existam.
    """
    ensure_json_file(current_app.config['USERS_JSON'])
    ensure_json_file(current_app.config['POSTS_JSON'])
    ensure_json_file(current_app.config['COMMENTS_JSON'])
    ensure_json_file(current_app.config['TAGS_JSON'])
    
    # Garante que banned.csv existe com cabeçalho
    banned_csv = current_app.config['BANNED_CSV']
    os.makedirs(os.path.dirname(banned_csv), exist_ok=True)
    if not os.path.exists(banned_csv):
        with open(banned_csv, 'w', newline='', encoding='utf-8') as f:
            f.write('email,ban_reason,ban_at\n')

@bp.route('/register', methods=['GET','POST'])
def register():
    """
    Rota de Cadastro de Usuário.
    GET: Exibe o formulário de registro.
    POST: Processa o novo cadastro.
    - Valida senhas e existência do email.
    - Cria hash da senha.
    - Salva novo usuário em users.json.
    """
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        pwd = request.form['senha']
        confirm_pwd = request.form['confirmar_senha']
        nome = request.form.get('nome', '')
        nickname = sanitize_nickname(request.form.get('nome_usuario', email.split('@')[0]))
        if nickname_in_use(nickname):
            flash('Nickname já em uso, escolha outro', 'error')
            return redirect(url_for('auth.register'))
        
        # Validação
        if pwd != confirm_pwd:
            flash('As senhas não correspondem', 'error')
            return redirect(url_for('auth.register'))
        
        if user_by_email(email):
            flash('Email já cadastrado', 'error')
            return redirect(url_for('auth.register'))
        
        uid = str(uuid.uuid4())
        password_hash = generate_password_hash(pwd)
        brasilia_tz = datetime.timezone(datetime.timedelta(hours=-3))
        row = {
            'id': uid,
            'email': email,
            'password_hash': password_hash,
            'nickname': nickname,
            'nome': nome,
            'is_admin': False,
            'profile_image': '',
            'created_at': datetime.datetime.now(brasilia_tz).strftime('%H:%M:%S %d/%m/%Y')
        }
        append_json(current_app.config['USERS_JSON'], row)
        # cria estrutura de uploads do usuário
        ensure_user_upload_dirs(uid)
        flash('Conta criada! Faça login', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

@bp.route('/login', methods=['GET','POST'])
def login():
    """
    Rota de Login.
    GET: Exibe o formulário de login.
    POST: Autentica o usuário.
    - Verifica banimento.
    - Valida email e senha.
    - Cria sessão do usuário.
    """
    # Caso venha de um POST apenas para mostrar o aviso (sem credenciais)
    if request.method == 'POST' and request.form.get('reason_only'):
        reason = (request.form.get('reason') or '').strip()
        if reason:
            flash(reason, 'error')
        return render_template('login.html')

    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        pwd = request.form['password']
        if is_banned(email):
            flash('Conta banida. Contate suporte através do email: sos.jpa@gmail.com', 'error')
            return redirect(url_for('auth.login'))
        user = user_by_email(email)
        if not user or not check_password_hash(user['password_hash'], pwd):
            flash('Credenciais inválidas', 'error')
            return redirect(url_for('auth.login'))
        
        is_dev = bool(user.get('is_dev', False))

        session.clear()
        session['user_id'] = user['id']
        session['is_admin'] = bool(user.get('is_admin', False)) or is_dev
        session['is_dev'] = is_dev
        session['nickname'] = user['nickname']
        session['email'] = user['email']
        flash('Logado com sucesso', 'success')
        return redirect(url_for('main.index'))
    # GET: opcionalmente mostra um aviso vindo por querystring
    reason = (request.args.get('reason') or '').strip()
    if reason:
        flash(reason, 'error')
    return render_template('login.html')

@bp.route('/logout')
def logout():
    """
    Rota de Logout.
    Encerra a sessão do usuário e redireciona para a Home.
    """
    session.clear()
    flash('Desconectado', 'info')
    return redirect(url_for('main.index'))

@bp.route('/profile', methods=['GET','POST'])
def profile():
    """
    Rota de Perfil do Usuário.
    GET: Exibe dados do usuário logado.
    POST: Atualiza dados do perfil (apelido, imagem).
    - Processa upload de nova imagem de perfil.
    - Atualiza users.json.
    """
    if 'user_id' not in session:
        flash('Faça login primeiro', 'error')
        return redirect(url_for('auth.login'))
    users = read_json(current_app.config['USERS_JSON'])
    me = next((u for u in users if u['id'] == session['user_id']), None)
    if not me:
        session.clear()
        flash('Usuário não encontrado', 'error')
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        ensure_user_upload_dirs(me['id'])
        nickname = sanitize_nickname(request.form.get('nickname', me['nickname']))
        if nickname_in_use(nickname, exclude_user_id=me['id']):
            flash('Nickname já em uso, escolha outro', 'error')
            return redirect(url_for('auth.profile'))
        me['nickname'] = nickname
        
        # Update Name
        nome = request.form.get('nome', me.get('nome', ''))
        me['nome'] = nome

        # Handle Profile Image
        f = request.files.get('profile_image')
        if f and f.filename:
            filename = secure_filename(f.filename)
            ext = os.path.splitext(filename)[1].lower()
            newname = f"profile_{me['id']}{ext}"
            # Pasta de destino: static/uploads/<user_id>/profile
            upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], me['id'], 'profile')
            os.makedirs(upload_folder, exist_ok=True)
            path = os.path.join(upload_folder, newname)
            
            f.save(path)
            # Armazena caminho com barra normal para funcionar em URL estática
            me['profile_image'] = f"uploads/{me['id']}/profile/{newname}"
            
        # Handle Cover Image
        c = request.files.get('cover_image')
        if c and c.filename:
            filename = secure_filename(c.filename)
            ext = os.path.splitext(filename)[1].lower()
            newname = f"cover_{me['id']}{ext}"
            # Pasta de destino: static/uploads/<user_id>/cover
            upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], me['id'], 'cover')
            os.makedirs(upload_folder, exist_ok=True)
            path = os.path.join(upload_folder, newname)
            
            c.save(path)
            me['cover_image'] = f"uploads/{me['id']}/cover/{newname}"

        write_json(current_app.config['USERS_JSON'], users)
        session['nickname'] = me['nickname']
        flash('Perfil atualizado', 'success')
        return redirect(url_for('auth.profile'))
    
    # Prepara data de entrada (dd/mm/aaaa)
    created = me.get('created_at', '')
    joined_date = ''
    if created:
        # Caso tenha um token dd/mm/aaaa na string, usa ele
        tokens = created.replace(',', ' ').split()
        slash_date = next((t for t in tokens if t.count('/') == 2), None)
        if slash_date:
            joined_date = slash_date
        else:
            # Extrai parte da data antes de espaço ou 'T' e converte yyyy-mm-dd -> dd/mm/aaaa
            base = created.split(' ')[0]
            base = base.split('T')[0]
            if base.count('-') == 2:
                y, m, d = base.split('-')
                if len(d) >= 2:
                    d = d[:2]  # remove possível sufixo como '10T...'
                joined_date = f"{d}/{m}/{y}"
            else:
                joined_date = created

    # Fetch user posts
    all_posts = read_json(current_app.config['POSTS_JSON'])
    user_posts = []
    for p in all_posts:
        if p.get('author_id') == session['user_id']:
            # Enrich post with author info for the template
            p['author_nick'] = me['nickname']
            p['author_image'] = me.get('profile_image', '')
            user_posts.append(p)
            
    user_posts.reverse() # Show newest first
    
    return render_template('profile.html', user=me, posts=user_posts, is_owner=True, joined_date=joined_date)
