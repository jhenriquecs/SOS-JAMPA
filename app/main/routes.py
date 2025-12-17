from flask import render_template, g, session, current_app, request, jsonify
from ..utils_csv import read_json, ensure_json_file
from ..auth.routes import is_banned
from . import bp
import os
from geopy.geocoders import Nominatim

# Inicializa o Blueprint para as páginas principais da aplicação
# bp = Blueprint('main', __name__)

@bp.before_app_request
def check_ban_and_load_user():
    """
    Executado antes de cada requisição na aplicação.
    - Carrega o usuário logado na variável global 'g.current_user'.
    - Verifica se o usuário está banido (consultando banned.csv).
    - Garante que os arquivos de dados (JSON e CSV) existam.
    Se o usuário estiver banido ou não encontrado, limpa a sessão.
    """
    g.current_user = None

    # Garante arquivos existentes
    ensure_json_file(current_app.config['USERS_JSON'])
    ensure_json_file(current_app.config['POSTS_JSON'])
    ensure_json_file(current_app.config['COMMENTS_JSON'])
    banned_csv = current_app.config['BANNED_CSV']
    os.makedirs(os.path.dirname(banned_csv), exist_ok=True)
    if not os.path.exists(banned_csv):
        with open(banned_csv, 'w', newline='', encoding='utf-8') as f:
            f.write('email,ban_reason,ban_at\n')

    if 'user_id' in session:
        users = read_json(current_app.config['USERS_JSON'])
        user_id = session['user_id']
        me = next((u for u in users if u['id'] == user_id), None)

        if me:
            if is_banned(me['email']):
                session.clear()
            else:
                g.current_user = me
        else:
            session.clear()


@bp.route('/')
def index():
    """
    Rota da página inicial (Home).
    - Carrega usuários e postagens dos arquivos JSON.
    - Ordena as postagens da mais recente para a mais antiga.
    - Enriquece os dados das postagens com informações do autor (apelido, imagem).
    - Renderiza o template index.html.
    """
    users = read_json(current_app.config['USERS_JSON'])
    posts = read_json(current_app.config['POSTS_JSON'])
    comments = read_json(current_app.config['COMMENTS_JSON'])
    
    # Pre-calcula contagem de comentários
    comment_counts = {}
    for c in comments:
        pid = c.get('post_id')
        if pid:
            comment_counts[pid] = comment_counts.get(pid, 0) + 1

    # ordena por created_at string (já no formato HH:MM:SS YYYY-MM-DD) em ordem decrescente
    posts.sort(key=lambda p: p.get('created_at',''), reverse=True)

    current_user_id = session.get('user_id')

    for p in posts:
        author = next((u for u in users if u['id'] == p.get('author_id')), None)
        p['author_nick'] = author['nickname'] if author else 'Anônimo'
        p['author_image'] = author['profile_image'].replace('\\','/') if author and author.get('profile_image') else ''
        
        # Atualiza contagem de comentários dinamicamente
        p['comments_count'] = comment_counts.get(p['id'], 0)

        # Garante que a lista de likes exista
        if 'likes' not in p:
            p['likes'] = []
            
        # Verifica se o usuário atual curtiu o post
        p['user_liked'] = current_user_id in p['likes'] if current_user_id else False

        # Normaliza image_path para usar / em vez de \
        if p.get('image_path'):
            p['image_path'] = p['image_path'].replace('\\', '/')

    return render_template('index.html', posts=posts, current_user=g.current_user)


@bp.route('/waste-info')
def waste_info():
    """
    Rota para a página de informações sobre resíduos.
    - Define uma lista de resíduos com informações (título, imagem, descrição, locais de coleta).
    - Renderiza o template waste_info.html passando essa lista.
    """
    # Carrega pontos de coleta do JSON
    ensure_json_file(current_app.config['COLLECTION_POINTS_JSON'])
    all_points = read_json(current_app.config['COLLECTION_POINTS_JSON'])
    
    # Agrupa pontos por tipo
    points_by_type = {}
    for p in all_points:
        t = p.get('type')
        if t not in points_by_type:
            points_by_type[t] = []
        points_by_type[t].append(p)

    # Dados base dos tipos de resíduos
    # Imagens placeholder usadas caso não existam locais
    wastes = [
        {
            'id': 'pilhas',
            'title': 'Pilhas e baterias',
            'icon': 'fa-battery-full',
            'color': '#f39c12',
            'desc': 'Leve até pontos de coleta autorizados. Nunca descarte em lixo comum.',
            'locations': points_by_type.get('pilhas', [])
        },
        {
            'id': 'oleo',
            'title': 'Óleo de cozinha',
            'icon': 'fa-bottle-droplet',
            'color': '#f1c40f',
            'desc': 'Armazene em garrafa plástica e entregue em pontos de coleta.',
            'locations': points_by_type.get('oleo', [])
        },
        {
            'id': 'eletronico',
            'title': 'Lixo Eletrônico',
            'icon': 'fa-plug',
            'color': '#7f8c8d',
            'desc': 'Computadores, celulares e cabos devem ser reciclados separadamente.',
            'locations': points_by_type.get('eletronico', [])
        },
        {
            'id': 'plastico',
            'title': 'Plástico',
            'icon': 'fa-bottle-water',
            'color': '#e74c3c',
            'desc': 'Lave as embalagens antes de descartar na coleta seletiva.',
            'locations': points_by_type.get('plastico', [])
        },
        {
            'id': 'vidro',
            'title': 'Vidro',
            'icon': 'fa-wine-bottle',
            'color': '#27ae60',
            'desc': 'Separe vidros quebrados em caixas de papelão para evitar acidentes.',
            'locations': points_by_type.get('vidro', [])
        },
        {
            'id': 'papel',
            'title': 'Papel',
            'icon': 'fa-newspaper',
            'color': '#3498db',
            'desc': 'Papéis secos e limpos podem ser reciclados. Evite amassar.',
            'locations': points_by_type.get('papel', [])
        },
        {
            'id': 'metal',
            'title': 'Metal',
            'icon': 'fa-gears',
            'color': '#e67e22',
            'desc': 'Latas de alumínio e aço são 100% recicláveis.',
            'locations': points_by_type.get('metal', [])
        }
    ]
    
    return render_template('waste_info.html', wastes=wastes)

@bp.route('/geocode', methods=['POST'])
def geocode_address():
    data = request.get_json()
    address = data.get('address')
    
    if not address:
        return jsonify({'error': 'Endereço não fornecido'}), 400
        
    try:
        geolocator = Nominatim(user_agent="projeto_pweb_waste_app")
        # Adiciona contexto para melhorar a busca
        location = geolocator.geocode(f"{address}, João Pessoa, PB, Brasil")
        
        if location:
            return jsonify({
                'lat': location.latitude,
                'lon': location.longitude,
                'display_name': location.address
            })
        else:
            return jsonify({'error': 'Endereço não encontrado'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500