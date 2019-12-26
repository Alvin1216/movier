import requests,json

def get_information(imdb_id):
    query = 'http://omdbapi.com/?'+'i='+str(imdb_id)+'&apikey=8c573e82&plot=full'
    #print(query)
    r = requests.get(query)
    json_obj = json.loads(r.text)
    return json_obj

movie_obj = get_information(imdb_id='tt0113497')
print(movie_obj['Plot'])

