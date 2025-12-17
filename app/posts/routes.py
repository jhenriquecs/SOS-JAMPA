from flask import request, render_template, redirect, url_for, flash, current_app, session, jsonify, g
from ..utils_csv import read_json, append_json, ensure_json_file, write_json
import uuid, datetime, os
from werkzeug.utils import secure_filename
from . import bp

# bp = Blueprint('posts', __name__)

def login_required():
    """
    Verifica se o usuário está logado (se 'user_id' está na sessão).
    Retorna True se logado, False caso contrário.
    """
    return 'user_id' in session

@bp.before_request
def ensure_files():
    """
    Executado antes de cada requisição neste Blueprint.
    Garante que os arquivos JSON de posts e comentários existam.
    """
    ensure_json_file(current_app.config['POSTS_JSON'])
    ensure_json_file(current_app.config['COMMENTS_JSON'])

@bp.route('/create', methods=['GET','POST'])
def create_post():
    """
    Rota para criar uma nova postagem (denúncia).
    GET: Exibe o formulário de criação.
    POST: Processa a nova postagem.
    - Verifica login.
    - Recebe dados (descrição, endereço, tags).
    - Processa upload de imagem.
    - Salva postagem em posts.json com timestamp.
    """
    if not login_required():
        flash('Faça login para criar denúncia', 'error')
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        desc = request.form.get('description','').strip()
        address = request.form.get('address','').strip()
        tags = request.form.get('tags','').strip()
        f = request.files.get('image')
        imgpath = ''
        if f and f.filename:
            fn = secure_filename(f.filename)
            newname = f"post_{uuid.uuid4().hex}_{fn}"
            
            # Pasta de destino: static/uploads/<author_id>/posts
            upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], session['user_id'], 'posts')
            os.makedirs(upload_folder, exist_ok=True)
            savepath = os.path.join(upload_folder, newname)
            
            f.save(savepath)
            # Use forward slash para URLs
            imgpath = f"uploads/{session['user_id']}/posts/{newname}"
        pid = str(uuid.uuid4())
        # Horário de Brasília (UTC-3)
        brasilia_tz = datetime.timezone(datetime.timedelta(hours=-3))
        timestamp = datetime.datetime.now(brasilia_tz).strftime('%H:%M:%S %d/%m/%Y')
        row = {
            'id': pid,
            'author_id': session['user_id'],
            'image_path': imgpath,
            'description': desc,
            'address': address,
            'created_at': timestamp,
            'tags': tags
        }
        append_json(current_app.config['POSTS_JSON'], row)
        flash('Denúncia criada. Procure o órgão responsável: Tel: (83) 3214-XXXX / email: meioambiente@joaopessoa.pb.gov.br', 'info')
        return redirect(url_for('posts.view_post', post_id=pid))
    # Se for GET, redireciona para a home onde está o formulário
    return redirect(url_for('main.index'))

@bp.route('/<post_id>', methods=['GET','POST'])
def view_post(post_id):
    """
    Rota para visualizar uma postagem específica e seus comentários.
    GET: Exibe a postagem e lista de comentários.
    POST: Adiciona um novo comentário à postagem.
    - Carrega dados do post e do autor.
    - Carrega comentários associados.
    - Processa novo comentário (se POST).
    """
    posts = read_json(current_app.config['POSTS_JSON'])
    post = next((p for p in posts if p['id']==post_id), None)
    if not post:
        flash('Post não encontrado', 'error')
        return redirect(url_for('main.index'))
    users = read_json(current_app.config['USERS_JSON'])
    author = next((u for u in users if u['id']==post['author_id']), None)
    post['author_nick'] = author['nickname'] if author else 'Anônimo'
    post['author_image'] = author['profile_image'].replace('\\','/') if author and author.get('profile_image') else ''
    comments = [c for c in read_json(current_app.config['COMMENTS_JSON']) if c['post_id']==post_id]
    
    # Prepara dados para o post_card
    post['comments_count'] = len(comments)
    if 'likes' not in post:
        post['likes'] = []
    if post.get('image_path'):
        post['image_path'] = post['image_path'].replace('\\', '/')

    for c in comments:
        u = next((x for x in users if x['id']==c['author_id']), None)
        c['author_nick'] = u['nickname'] if u else 'Anônimo'
        c['author_image'] = u['profile_image'].replace('\\','/') if u and u.get('profile_image') else ''
    if request.method == 'POST':
        if not login_required():
            flash('Faça login para comentar', 'error')
            return redirect(url_for('auth.login'))
        text = request.form.get('comment','').strip()
        if text:
            cid = str(uuid.uuid4())
            # Horário de Brasília (UTC-3)
            brasilia_tz = datetime.timezone(datetime.timedelta(hours=-3))
            timestamp = datetime.datetime.now(brasilia_tz).strftime('%H:%M:%S %d/%m/%Y')
            row = {
                'id': cid,
                'post_id': post_id,
                'author_id': session['user_id'],
                'text': text,
                'created_at': timestamp
            }
            append_json(current_app.config['COMMENTS_JSON'], row)
            flash('Comentário adicionado', 'success')
            return redirect(url_for('posts.view_post', post_id=post_id))
    return render_template('post_view.html', post=post, comments=comments, current_user=g.current_user)

@bp.route('/list')
def list_posts():
    """
    Rota para listar postagens com filtros (busca e tags).
    - Filtra postagens por termo de busca (q) ou tag.
    - Ordena por data (mais recente primeiro).
    - Renderiza index.html com os resultados filtrados.
    """
    q = request.args.get('q','').lower()
    tag = request.args.get('tag','').lower()
    posts = read_json(current_app.config['POSTS_JSON'])
    users = read_json(current_app.config['USERS_JSON'])
    if q:
        posts = [p for p in posts if q in (p.get('description','') or '').lower() or q in (p.get('address','') or '').lower() or q in (p.get('tags','') or '').lower()]
    if tag:
        posts = [p for p in posts if tag in (p.get('tags','') or '').lower()]
    posts.sort(key=lambda p: p.get('created_at',''), reverse=True)
    for p in posts:
        author = next((u for u in users if u['id']==p['author_id']), None)
        p['author_nick'] = author['nickname'] if author else 'Anônimo'
        p['author_image'] = author['profile_image'].replace('\\','/') if author and author.get('profile_image') else ''
        # Normaliza image_path para usar / em vez de \
        if p.get('image_path'):
            p['image_path'] = p['image_path'].replace('\\', '/')
    return render_template('index.html', posts=posts)

@bp.route('/like/<post_id>', methods=['POST'])
def toggle_like(post_id):
    """
    Rota para curtir/descurtir uma postagem.
    - Verifica login.
    - Adiciona ou remove o ID do usuário da lista de likes do post.
    - Retorna JSON com o novo número de likes e status.
    """
    if not login_required():
        return jsonify({'error': 'Login required'}), 401
    
    user_id = session['user_id']
    posts = read_json(current_app.config['POSTS_JSON'])
    
    post_index = next((i for i, p in enumerate(posts) if p['id'] == post_id), None)
    if post_index is None:
        return jsonify({'error': 'Post not found'}), 404
    
    post = posts[post_index]
    if 'likes' not in post:
        post['likes'] = []
        
    liked = False
    if user_id in post['likes']:
        post['likes'].remove(user_id)
        liked = False
    else:
        post['likes'].append(user_id)
        liked = True
        
    write_json(current_app.config['POSTS_JSON'], posts)
    
    return jsonify({
        'likes_count': len(post['likes']),
        'liked': liked
    })

@bp.route('/delete/<post_id>', methods=['POST'])
def delete_post(post_id):
    """
    Rota para excluir um post.
    - Verifica se é o autor ou admin.
    - Remove imagem associada.
    - Remove post do JSON.
    - Remove comentários associados.
    """
    if not login_required():
        flash('Login necessário', 'error')
        return redirect(url_for('auth.login'))
    
    posts = read_json(current_app.config['POSTS_JSON'])
    post = next((p for p in posts if p['id'] == post_id), None)
    
    if not post:
        flash('Post não encontrado', 'error')
        return redirect(url_for('main.index'))
        
    # Verifica permissões
    is_author = post['author_id'] == session['user_id']
    is_admin = session.get('is_admin', False)
    
    if not (is_author or is_admin):
        flash('Você não tem permissão para excluir este post', 'error')
        return redirect(url_for('main.index'))
        
    # Deleta imagem se existir
    if post.get('image_path'):
        try:
            # image_path ex: "uploads/post/arquivo.jpg"
            full_path = os.path.join(current_app.static_folder, post['image_path'])
            if os.path.exists(full_path):
                os.remove(full_path)
        except Exception as e:
            print(f"Erro ao deletar imagem: {e}")
            
    # Remove post
    posts = [p for p in posts if p['id'] != post_id]
    write_json(current_app.config['POSTS_JSON'], posts)
    
    # Remove comentários órfãos
    comments = read_json(current_app.config['COMMENTS_JSON'])
    new_comments = [c for c in comments if c['post_id'] != post_id]
    if len(comments) != len(new_comments):
        write_json(current_app.config['COMMENTS_JSON'], new_comments)
    
    flash('Post excluído com sucesso', 'success')
    return redirect(url_for('main.index'))

@bp.route('/comment/<comment_id>/delete', methods=['DELETE', 'POST'])
def delete_comment_api(comment_id):
    """
    API para excluir um comentário.
    """
    if not login_required():
        return jsonify({'error': 'Login required'}), 401
        
    comments = read_json(current_app.config['COMMENTS_JSON'])
    comment = next((c for c in comments if c['id'] == comment_id), None)
    
    if not comment:
        return jsonify({'error': 'Comment not found'}), 404
        
    is_author = comment['author_id'] == session['user_id']
    is_admin = session.get('is_admin', False)
    
    if not (is_author or is_admin):
        return jsonify({'error': 'Permission denied'}), 403
        
    comments = [c for c in comments if c['id'] != comment_id]
    write_json(current_app.config['COMMENTS_JSON'], comments)
    
    return jsonify({'success': True})

@bp.route('/<post_id>/comments', methods=['GET'])
def get_comments(post_id):
    """
    Retorna os comentários de um post em formato JSON.
    """
    comments = read_json(current_app.config['COMMENTS_JSON'])
    users = read_json(current_app.config['USERS_JSON'])
    
    post_comments = [c for c in comments if c['post_id'] == post_id]
    
    current_user_id = session.get('user_id')
    is_admin = session.get('is_admin', False)
    
    results = []
    for c in post_comments:
        author = next((u for u in users if u['id'] == c['author_id']), None)
        results.append({
            'id': c['id'],
            'post_id': c['post_id'], # Adicionado para o frontend saber qual post atualizar
            'text': c['text'],
            'created_at': c['created_at'],
            'author_nick': author['nickname'] if author else 'Anônimo',
            'author_image': author['profile_image'].replace('\\', '/') if author and author.get('profile_image') else '',
            'can_delete': (current_user_id == c['author_id']) or is_admin
        })
        
    return jsonify(results)

@bp.route('/<post_id>/comment', methods=['POST'])
def add_comment_api(post_id):
    """
    Adiciona um comentário via AJAX.
    """
    if not login_required():
        return jsonify({'error': 'Login required'}), 401
        
    data = request.get_json()
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'error': 'Empty comment'}), 400
        
    comments = read_json(current_app.config['COMMENTS_JSON'])
    posts = read_json(current_app.config['POSTS_JSON'])
    
    post_index = next((i for i, p in enumerate(posts) if p['id'] == post_id), None)
    if post_index is None:
        return jsonify({'error': 'Post not found'}), 404
        
    new_comment = {
        'id': str(uuid.uuid4()),
        'post_id': post_id,
        'author_id': session['user_id'],
        'text': text,
        'created_at': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3))).strftime('%H:%M:%S %d/%m/%Y')
    }
    comments.append(new_comment)
    write_json(current_app.config['COMMENTS_JSON'], comments)
    
    # Atualiza contador no post (opcional, já que calculamos dinamicamente no index, mas bom manter sincronizado)
    posts[post_index]['comments_count'] = posts[post_index].get('comments_count', 0) + 1
    write_json(current_app.config['POSTS_JSON'], posts)
    
    users = read_json(current_app.config['USERS_JSON'])
    author = next((u for u in users if u['id'] == session['user_id']), None)
    
    return jsonify({
        'id': new_comment['id'],
        'post_id': post_id,
        'text': new_comment['text'],
        'created_at': new_comment['created_at'],
        'author_nick': author['nickname'] if author else 'Anônimo',
        'author_image': author['profile_image'].replace('\\', '/') if author and author.get('profile_image') else '',
        'comments_count': posts[post_index]['comments_count'],
        'can_delete': True # O próprio autor acabou de criar
    })
