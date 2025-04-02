from flask import Flask, render_template, request
import requests

app = Flask(__name__)

from dotenv import load_dotenv
import os
load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
MEDIASTACK_API_KEY = os.getenv("MEDIASTACK_API_KEY")
IPINFO_API_KEY = os.getenv("IPINFO_API_KEY") #Esta no jala
OMDB_API_KEY = os.getenv("OMDB_API_KEY")
@app.route('/')
def home():
    # Obtener el número de página desde la URL (por defecto, página 1)
    page = request.args.get('page', 1, type=int)
    filter_by = request.args.get('filter_by', None)  # Filtro opcional

    # Obtener ubicación del usuario y código de país
    ipinfo_url = f"https://ipinfo.io/json?token={IPINFO_API_KEY}" #NO JALAAA
    location_response = requests.get(ipinfo_url).json()
    region = location_response.get('country', 'US')  # Código de país (ej, 'MX'), como no jala por default US

    # URL base para obtener películas populares con paginación y filtros
    tmdb_url = f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API_KEY}&language=en-US&region={region}&page={page}"

    if filter_by:  # Aplicar filtro si está definido
        tmdb_url = f"https://api.themoviedb.org/3/movie/{filter_by}?api_key={TMDB_API_KEY}&language=en-US&region={region}&page={page}"

    # Obtener películas desde la API de TMDB
    movies_response = requests.get(tmdb_url).json() #Convertimos a json la respuesta de la api
    movies = movies_response.get('results', []) #Lo volvemos lista
    total_pages = movies_response.get('total_pages', 1) #Saca todas las pags de la api donde estan las movies

    # Agregar URL de imágenes a las películas
    for movie in movies:
        movie['image_url'] = f"https://image.tmdb.org/t/p/w500{movie.get('poster_path', '')}" #Sacamos la imagen de la lista

    # Obtener noticias de cine desde Mediastack
    mediastack_url = f"http://api.mediastack.com/v1/news?access_key={MEDIASTACK_API_KEY}&categories=entertainment&languages=en"
    news_response = requests.get(mediastack_url).json()
    news = news_response.get('data', []) #Lo mismo volvemos lista la response en JSON
    
    # Limitar las noticias a las 9 más populares
    news = news[:9] #Limitamos a que el arreglo imprima del 0 al 8
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
    query = request.args.get('query', '').strip() #Es el trim del Python
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
        omdb_url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&t={movie['title']}"
        
        try:
            omdb_response = requests.get(omdb_url).json() #A partir del url lo convertimos a JSON
            if omdb_response.get('Response') == 'True':
                # Añadimos los datos adicionales de OMDB a la película
                movie['omdb_data'] = {
                    'imdb_rating': omdb_response.get('imdbRating', 'N/A'),
                    'director': omdb_response.get('Director', 'N/A'),
                    'actors': omdb_response.get('Actors', 'N/A'),
                    'runtime': omdb_response.get('Runtime', 'N/A'),
                    'imdb_id': omdb_response.get('imdbID', '')
                } #Esto saca todo del IMBD para que jale chido
        except:
            # Si hay un error con OMDB, ps le vale madre sigue jalando
            pass
        movie['image_url'] = f"https://image.tmdb.org/t/p/w500{movie.get('poster_path', '')}"

    # Renderizar la página de resultados de búsqueda
    return render_template(
        'search_results.html',
        movies=movies,
        query=query,
        error=None
    )


@app.route('/movie/<imdb_id>') #Pa sacar los details solo le pasamos el id al endpoint
def movie_details(imdb_id):
    # Obtenemos detalles completos de OMDB usando el IMDB ID
    omdb_url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&i={imdb_id}&plot=full"
    omdb_response = requests.get(omdb_url).json()
    
    if omdb_response.get('Response') == 'True':
        return render_template('movie_details.html', movie=omdb_response)
    else:
        return render_template('error.html', message="Película no encontrada") # no existe el html xd

if __name__ == '__main__':
    app.run(debug=True)