import pandas as pd
import re
df = pd.read_csv('movies.csv')
linker = pd.read_csv('links.csv',dtype={'imdbId': str,'tmdbId': str})

data = []
for index in range(0,len(df)):
#for index in range(0,10):
    try:
        one_movie = []
        temp = df.loc[[index]].values.tolist()[0][1]
        new = re.split(r'[()]', temp)
        movie_title = re.split(r'[,]', new[0])[0]
        movie_year = new[-2]
        movie_id = df.loc[[index]].values.tolist()[0][0]
        one_movie.append(movie_id)
        one_movie.append(movie_title)
        one_movie.append(movie_year)
        imdbid = str(linker.loc[df['movieId'] == movie_id]['imdbId'].tolist()[0])
        imdb_id = 'tt'+str(imdbid)
        tmdb_id = linker.loc[df['movieId'] == movie_id]['tmdbId'].tolist()[0]
        one_movie.append(imdb_id)
        one_movie.append(tmdb_id)
        data.append(one_movie)
        print(movie_title,movie_year,movie_id,imdb_id,tmdb_id)
    except:
        print('Something wrong!')
df_new = pd.DataFrame(data, columns = ['movie_id', 'title', 'year','imdb_id','tmdb_id'])
df_new.to_csv('movie_year_another_id.csv',index=False)
#print(df['title']) 