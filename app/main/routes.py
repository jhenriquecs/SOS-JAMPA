from flask import render_template, g, session, current_app, request, jsonify, flash, redirect, url_for
from ..utils_csv import read_json, ensure_json_file
from ..auth.routes import is_banned
from . import bp
import os
import requests
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


@bp.route('/news')
def news():
    """
    Rota de Notícias.
    Busca notícias sobre meio ambiente na API newsdata.io e NewsAPI.org.
    """
    articles = []
    error = None
    # termo de busca vindo do header quando na aba de notícias
    q_param = (request.args.get('q') or '').strip()
    
    keywords = [
        "desmatamento",
        "poluição",
        "queimadas",
        "aquecimento global",
        "mudanças climáticas",
        "crise hídrica",
        "desastre ambiental",
        "garimpo ilegal",
        "vazamento de óleo",
        "extinção"
    ]
    
    # Monta query: usa o termo do usuário se fornecido; senão, usa palavras-chave padrão
    if q_param:
        composed_query = q_param
    else:
        composed_query = " OR ".join([f'"{k}"' for k in keywords])

    # --- 1. Fetch from NewsData.io ---
    nd_api_key = current_app.config.get('NEWSDATA_API_KEY')
    if nd_api_key and not nd_api_key.startswith('pub_62696790'):
        try:
            url = "https://newsdata.io/api/1/latest"
            params = {
                'apikey': nd_api_key,
                'q': composed_query,
                # 'country': 'br', # Removed to allow worldwide news
                'language': 'pt',
                'category': 'environment',
                # 'timezone': 'America/Sao_Paulo', # Removed to allow worldwide news
                'image': 1,
                'video': 0,
                'size': 10 # Max for free plan is usually 10
            }
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            if response.status_code == 200 and data.get('status') == 'success':
                articles.extend(data.get('results', []))
            else:
                print(f"NewsData Error: {data}")
        except Exception as e:
            print(f"NewsData Request Error: {e}")

    # --- 2. Fetch from NewsAPI.org ---
    na_api_key = current_app.config.get('NEWSAPI_KEY')
    if na_api_key and na_api_key != 'YOUR_NEWSAPI_KEY':
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                'apiKey': na_api_key,
                'q': composed_query,
                'language': 'pt',
                'sortBy': 'publishedAt',
                'pageSize': 40
            }
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            if response.status_code == 200 and data.get('status') == 'ok':
                # Normalize data to match NewsData format
                for item in data.get('articles', []):
                    articles.append({
                        'title': item.get('title'),
                        'link': item.get('url'),
                        'image_url': item.get('urlToImage'),
                        'source_id': item.get('source', {}).get('name'),
                        'pubDate': item.get('publishedAt'),
                        'description': item.get('description')
                    })
            else:
                print(f"NewsAPI Error: {data}")
        except Exception as e:
            print(f"NewsAPI Request Error: {e}")

    # Remove duplicates based on title
    seen_titles = set()
    unique_articles = []
    for art in articles:
        if art.get('title') and art['title'] not in seen_titles:
            seen_titles.add(art['title'])
            unique_articles.append(art)
    
    if not unique_articles:
        error = "Não foi possível carregar as notícias no momento."

    return render_template('news.html', articles=unique_articles, error=error)


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


@bp.route('/user/@<nickname>')
def view_user_profile_by_nickname(nickname):
    """
    Exibe o perfil público usando o nickname (handle).
    """
    users = read_json(current_app.config['USERS_JSON'])
    target = next((u for u in users if u.get('nickname','').lower() == (nickname or '').lower()), None)
    if not target:
        flash('Usuário não encontrado', 'error')
        return redirect(url_for('main.index'))

    posts = read_json(current_app.config['POSTS_JSON'])
    comments = read_json(current_app.config['COMMENTS_JSON'])

    # contagem de comentários por post
    comment_counts = {}
    for c in comments:
        pid = c.get('post_id')
        if pid:
            comment_counts[pid] = comment_counts.get(pid, 0) + 1

    user_posts = [p for p in posts if p.get('author_id') == target.get('id')]
    # ordena do mais recente
    user_posts.sort(key=lambda p: p.get('created_at', ''), reverse=True)

    for p in user_posts:
        p['author_nick'] = target['nickname']
        p['author_image'] = target.get('profile_image', '').replace('\\','/') if target.get('profile_image') else ''
        p['comments_count'] = comment_counts.get(p['id'], 0)
        if 'likes' not in p:
            p['likes'] = []
        if p.get('image_path'):
            p['image_path'] = p['image_path'].replace('\\', '/')

    is_owner = session.get('user_id') == target.get('id')
    # prepara joined_date
    created = target.get('created_at', '')
    joined_date = ''
    if created:
        tokens = created.replace(',', ' ').split()
        slash_date = next((t for t in tokens if t.count('/') == 2), None)
        if slash_date:
            joined_date = slash_date
        else:
            base = created.split(' ')[0]
            base = base.split('T')[0]
            if base.count('-') == 2:
                y, m, d = base.split('-')
                if len(d) >= 2:
                    d = d[:2]
                joined_date = f"{d}/{m}/{y}"
            else:
                joined_date = created

    return render_template('profile.html', user=target, posts=user_posts, is_owner=is_owner, joined_date=joined_date)


@bp.route('/user/<user_id>')
def view_user_profile(user_id):
    """
    Compatibilidade com URLs antigas por ID: redireciona para /user/@nickname.
    """
    users = read_json(current_app.config['USERS_JSON'])
    target = next((u for u in users if u['id'] == user_id), None)
    if not target:
        flash('Usuário não encontrado', 'error')
        return redirect(url_for('main.index'))
    return redirect(url_for('main.view_user_profile_by_nickname', nickname=target.get('nickname','')))

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