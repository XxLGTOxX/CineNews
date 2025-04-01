from flask import Flask, render_template, request
import requests

app = Flask(__name__)

# API keys y configuración
TMDB_API_KEY = 'a3c16888d396e8fae0f254dfd041fd91'
MEDIASTACK_API_KEY = '0309e45842f5b810c87be862ffbaa671'
IPINFO_API_KEY = '640ab7862656e8'

@app.route('/')
def home():
    # Obtener el número de página desde la URL (por defecto, página 1)
    page = request.args.get('page', 1, type=int)
    filter_by = request.args.get('filter_by', None)  # Filtro opcional

    # Obtener ubicación del usuario y código de país
    ipinfo_url = f"https://ipinfo.io/json?token={IPINFO_API_KEY}"
    location_response = requests.get(ipinfo_url).json()
    region = location_response.get('country', 'US')  # Código de país (por ejemplo, 'MX')

    # URL base para obtener películas populares con paginación y filtros
    tmdb_url = f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API_KEY}&language=en-US&region={region}&page={page}"

    if filter_by:  # Aplicar filtro si está definido
        tmdb_url = f"https://api.themoviedb.org/3/movie/{filter_by}?api_key={TMDB_API_KEY}&language=en-US&region={region}&page={page}"

    # Obtener películas desde la API de TMDB
    movies_response = requests.get(tmdb_url).json()
    movies = movies_response.get('results', [])
    total_pages = movies_response.get('total_pages', 1)

    # Agregar URL de imágenes a las películas
    for movie in movies:
        movie['image_url'] = f"https://image.tmdb.org/t/p/w500{movie.get('poster_path', '')}"

    # Obtener noticias de cine desde Mediastack
    mediastack_url = f"http://api.mediastack.com/v1/news?access_key={MEDIASTACK_API_KEY}&categories=entertainment&languages=en"
    news_response = requests.get(mediastack_url).json()
    news = news_response.get('data', [])
    
    # Limitar las noticias a las 9 más populares
    news = news[:9]
    for article in news:
        article['image_url'] = article.get('image', '')

    # Renderizar la página principal con los datos
    return render_template(
        'index.html',
        movies=movies,
        news=news,
        region=region,
        page=page,
        total_pages=total_pages,
        filter_by=filter_by
    )

@app.route('/search')
def search():
    # Obtener el término de búsqueda y eliminar espacios innecesarios
    query = request.args.get('query', '').strip()
    if not query:  # Validar que haya un término de búsqueda
        return render_template(
            'search_results.html',
            movies=[],
            query=query,
            error="Por favor ingresa un término de búsqueda."
        )

    # URL para buscar películas en TMDB
    tmdb_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query}&language=en-US"
    search_response = requests.get(tmdb_url).json()
    movies = search_response.get('results', [])

    # Agregar URL de imágenes a las películas
    for movie in movies:
        movie['image_url'] = f"https://image.tmdb.org/t/p/w500{movie.get('poster_path', '')}"

    # Renderizar la página de resultados de búsqueda
    return render_template(
        'search_results.html',
        movies=movies,
        query=query,
        error=None
    )

if __name__ == '__main__':
    app.run(debug=True)