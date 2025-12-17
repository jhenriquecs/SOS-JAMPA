from flask import request, current_app, redirect, url_for, flash, session, render_template
from ..utils_csv import read_json, write_json, append_json, ensure_json_file
from ..auth.routes import add_ban, get_all_bans, remove_ban
import datetime
from geopy.geocoders import Nominatim
from . import bp

# bp = Blueprint('admin', __name__)

def admin_required():
    """
    Verifica se o usuário logado possui privilégios de administrador.
    Retorna True se for admin, False caso contrário.
    """
    return session.get('is_admin', False)

@bp.before_request
def ensure_files():
    """
    Executado antes de cada requisição neste Blueprint.
    Garante que os arquivos JSON necessários existam.
    """
    ensure_json_file(current_app.config['POSTS_JSON'])
    ensure_json_file(current_app.config['COMMENTS_JSON'])
    ensure_json_file(current_app.config['TAGS_JSON'])
    ensure_json_file(current_app.config['COLLECTION_POINTS_JSON'])

@bp.route('/')
def dashboard():
    """
    Rota do Painel Administrativo.
    - Verifica se o usuário é admin.
    - Carrega usuários, tags e lista de banidos.
    - Organiza tags por usuário.
    - Renderiza o template admin_dashboard.html.
    """
    if not admin_required():
        flash('Acesso negado', 'error')
        return redirect(url_for('main.index'))
    
    users = read_json(current_app.config['USERS_JSON'])
    all_tags = read_json(current_app.config['TAGS_JSON'])
    banned_users = get_all_bans()
    collection_points = read_json(current_app.config['COLLECTION_POINTS_JSON'])
    
    # Organizar tags por usuário para facilitar no template
    user_tags = {}
    for t in all_tags:
        uid = t.get('user_id')
        if uid not in user_tags:
            user_tags[uid] = []
        user_tags[uid].append(t)
        
    return render_template('admin_dashboard.html', 
                           users=users, 
                           user_tags=user_tags, 
                           banned_users=banned_users,
                           collection_points=collection_points)

@bp.route('/collection-point/add', methods=['POST'])
def add_collection_point():
    if not admin_required():
        flash('Acesso negado', 'error')
        return redirect(url_for('main.index'))
        
    name = request.form.get('name')
    type_ = request.form.get('type')
    street = request.form.get('street')
    number = request.form.get('number')
    neighborhood = request.form.get('neighborhood')
    
    if not all([name, type_, street, number, neighborhood]):
        flash('Todos os campos são obrigatórios', 'error')
        return redirect(url_for('admin.dashboard'))
        
    import uuid
    
    address_str = f"{street}, {number} - {neighborhood}"
    lat, lon = 0.0, 0.0
    
    try:
        geolocator = Nominatim(user_agent="projeto_pweb_waste_app")
        # Tenta geocodificar o endereço completo. 
        # Adicionando "João Pessoa, PB, Brasil" para melhorar a precisão se for local
        location = geolocator.geocode(f"{address_str}, João Pessoa, PB, Brasil")
        if location:
            lat = location.latitude
            lon = location.longitude
    except Exception as e:
        print(f"Erro ao geocodificar: {e}")

    point = {
        'id': str(uuid.uuid4()),
        'name': name,
        'type': type_,
        'address': address_str,
        'lat': lat,
        'lon': lon
    }
    
    append_json(current_app.config['COLLECTION_POINTS_JSON'], point)
    flash('Ponto de coleta adicionado', 'success')
    return redirect(url_for('admin.dashboard'))

@bp.route('/collection-point/delete', methods=['POST'])
def delete_collection_point():
    if not admin_required():
        flash('Acesso negado', 'error')
        return redirect(url_for('main.index'))
        
    point_id = request.form.get('point_id')
    points = read_json(current_app.config['COLLECTION_POINTS_JSON'])
    points = [p for p in points if p['id'] != point_id]
    write_json(current_app.config['COLLECTION_POINTS_JSON'], points)
    
    flash('Ponto de coleta removido', 'success')
    return redirect(url_for('admin.dashboard'))

@bp.route('/give_tag', methods=['POST'])
def give_tag():
    """
    Rota para atribuir uma tag a um usuário.
    - Verifica permissão de admin.
    - Recebe ID do usuário e a tag.
    - Salva a nova tag em tags.json com timestamp.
    """
    if not admin_required():
        flash('Somente admins', 'error'); return redirect(url_for('main.index'))
    user_id = request.form.get('user_id')
    tag = request.form.get('tag')
    brasilia_tz = datetime.timezone(datetime.timedelta(hours=-3))
    if not user_id or not tag:
        flash('Dados inválidos', 'error'); return redirect(url_for('main.index'))
    append_json(current_app.config['TAGS_JSON'], {
        'user_id': user_id,
        'tag': tag,
        'given_by': session['user_id'],
        'given_at': datetime.datetime.now(brasilia_tz).strftime('%H:%M:%S %d/%m/%Y')
    })
    flash('Tag atribuída', 'success')
    return redirect(url_for('main.index'))

@bp.route('/delete_post', methods=['POST'])
def delete_post():
    """
    Rota para excluir uma postagem.
    - Verifica permissão de admin.
    - Remove a postagem do arquivo posts.json pelo ID.
    """
    if not admin_required():
        flash('Somente admins', 'error'); return redirect(url_for('main.index'))
    post_id = request.form.get('post_id')
    posts = read_json(current_app.config['POSTS_JSON'])
    posts = [p for p in posts if p['id'] != post_id]
    write_json(current_app.config['POSTS_JSON'], posts)
    flash('Post apagado', 'success')
    return redirect(url_for('posts.list_posts'))

@bp.route('/delete_comment', methods=['POST'])
def delete_comment():
    """
    Rota para excluir um comentário.
    - Verifica permissão de admin.
    - Remove o comentário do arquivo comments.json pelo ID.
    """
    if not admin_required():
        flash('Somente admins', 'error'); return redirect(url_for('main.index'))
    comment_id = request.form.get('comment_id')
    comments = read_json(current_app.config['COMMENTS_JSON'])
    comments = [c for c in comments if c['id'] != comment_id]
    write_json(current_app.config['COMMENTS_JSON'], comments)
    flash('Comentário removido', 'success')
    return redirect(url_for('main.index'))

@bp.route('/remove_tag', methods=['POST'])
def remove_tag():
    """
    Rota para remover uma tag de um usuário.
    - Verifica permissão de admin.
    - Remove a tag específica do arquivo tags.json.
    """
    if not admin_required():
        flash('Somente admins', 'error'); return redirect(url_for('main.index'))
    user_id = request.form.get('user_id')
    tag = request.form.get('tag')
    tags = read_json(current_app.config['TAGS_JSON'])
    tags = [t for t in tags if not (t.get('user_id')==user_id and t.get('tag')==tag)]
    write_json(current_app.config['TAGS_JSON'], tags)
    flash('Tag removida', 'success')
    return redirect(url_for('admin.dashboard'))

@bp.route('/ban_user', methods=['POST'])
def ban_user():
    """
    Rota para banir um usuário.
    - Verifica permissão de admin.
    - Impede banimento de outros administradores.
    - Adiciona o email à lista de banidos (banned.csv).
    """
    if not admin_required():
        flash('Somente admins', 'error'); return redirect(url_for('main.index'))
    email = request.form.get('email','').strip().lower()
    
    # Verificar se o usuário alvo é admin
    users = read_json(current_app.config['USERS_JSON'])
    target_user = next((u for u in users if u['email'].lower() == email), None)
    if target_user and target_user.get('is_admin'):
        flash('Não é possível banir um administrador', 'error')
        return redirect(url_for('admin.dashboard'))

    reason = request.form.get('reason','')
    add_ban(email, reason)
    flash('Usuário banido', 'success')
    return redirect(url_for('admin.dashboard'))

@bp.route('/promote_user', methods=['POST'])
def promote_user():
    """
    Rota para promover um usuário a administrador.
    - Verifica permissão de admin.
    - Atualiza o status 'is_admin' do usuário em users.json.
    """
    if not admin_required():
        flash('Somente admins', 'error'); return redirect(url_for('main.index'))
    user_id = request.form.get('user_id')
    users = read_json(current_app.config['USERS_JSON'])
    
    changed = False
    for u in users:
        if u['id'] == user_id:
            u['is_admin'] = True
            changed = True
            break
    
    if changed:
        write_json(current_app.config['USERS_JSON'], users)
        flash('Usuário promovido a admin', 'success')
    else:
        flash('Usuário não encontrado', 'error')
        
    return redirect(url_for('admin.dashboard'))

@bp.route('/demote_user', methods=['POST'])
def demote_user():
    """
    Rota para remover privilégios de administrador de um usuário.
    - Verifica se o usuário atual é 'dev' (session['is_dev']).
    - Atualiza o status 'is_admin' do usuário em users.json para False.
    """
    if not session.get('is_dev'):
        flash('Apenas desenvolvedores podem remover administradores', 'error')
        return redirect(url_for('admin.dashboard'))
        
    user_id = request.form.get('user_id')
    users = read_json(current_app.config['USERS_JSON'])
    
    changed = False
    for u in users:
        if u['id'] == user_id:
            u['is_admin'] = False
            changed = True
            break
            
    if changed:
        write_json(current_app.config['USERS_JSON'], users)
        flash('Privilégios de admin removidos', 'success')
    else:
        flash('Usuário não encontrado', 'error')
        
    return redirect(url_for('admin.dashboard'))

@bp.route('/unban_user', methods=['POST'])
def unban_user():
    """
    Rota para desbanir um usuário.
    - Verifica permissão de admin.
    - Remove o email da lista de banidos (banned.csv).
    """
    if not admin_required():
        flash('Somente admins', 'error'); return redirect(url_for('main.index'))
    email = request.form.get('email','').strip().lower()
    remove_ban(email)
    flash('Usuário desbanido', 'success')
    return redirect(url_for('admin.dashboard'))
