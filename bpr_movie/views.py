from django.shortcuts import render
from bpr_movie.bpr import bpr as bpr
import json,requests
from bpr_movie.bpr import get_information as gi
import pandas as pd
from bpr_movie.models import Movie,UserLike,UserWatched,User
from django.http import JsonResponse
from linebot import LineBotApi, WebhookHandler,WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotFound,HttpResponseServerError

line_bot_api = LineBotApi('KHwsb+/bft/w7SHeotwLaiZZ22THFxUVbxzEYgJV2oMLUvZ2Nv7yAbKkt+vlvzVMUPnXG0Nd/yRk14f3mD48QnD1ArMXg01/zwwwTj7YTn7Am+7ctFmoo1UTT1xeRQjPPhH71U9PmiMsgLf0tj6PclGUYhWQfeY8sLGRXgo3xvw=')
handler = WebhookHandler('a262dce10aa2b4d393eba0168dbe82e2')
parser = WebhookParser('a262dce10aa2b4d393eba0168dbe82e2')

from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage,ImageSendMessage

#line_bot_api = LineBotApi('CHANNEL_ACCESS_TOKEN')
#handler = WebhookHandler('CHANNEL_SECRET')

@csrf_exempt
def callback(request):
    
    if request.method == "POST":
        # get X-Line-Signature header value
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')
        msg = json.loads(body)
        userid = msg['events'][0]['source']['userId']
        reply_token = msg['events'][0]['replyToken']
        message_type = msg['events'][0]['message']['type']
        print(msg['events'][0]['source']['userId'])
        print(msg['events'][0]['replyToken'])
        print(msg['events'][0]['message']['type'])
        try:
            if message_type!='text':
                line_bot_api.push_message(userid,TextSendMessage(text='Hi~我現在只能處理文字的訊息喔！'))
            elif check_user_db(userid) == False:
                profile = line_bot_api.get_profile(userid)
                insert_user_db(userid,profile.display_name)
                line_bot_api.push_message(userid,TextSendMessage(text='Hi!歡迎新使用者'))
                #line_bot_api.push_message(userid,ImageSendMessage(original_content_url='https://m.media-amazon.com/images/M/MV5BMjA1MTc1NTg5NV5BMl5BanBnXkFtZTgwOTM2MDEzNzE@._V1_SX300.jpg',preview_image_url='https://m.media-amazon.com/images/M/MV5BMjA1MTc1NTg5NV5BMl5BanBnXkFtZTgwOTM2MDEzNzE@._V1_SX300.jpg'))
            else:
                #line_bot_api.push_message(userid,TextSendMessage(text='想知道什麼呢？'))
                message_text = str(msg['events'][0]['message']['text'])
                if message_text.find('我喜歡') != -1 :
                    movie_title = deal_user_like(message_text)
                    json_obj = get_information_title(movie_title)
                    response_message = '你喜歡'+ json_obj['Title']+' ('+json_obj['Year']+')'
                    response_img = json_obj['Poster']
                    line_bot_api.push_message(userid,TextSendMessage(text=response_message))
                    line_bot_api.push_message(userid,ImageSendMessage(original_content_url=response_img,preview_image_url=response_img))
                    movielens_id = search_for_movieid_imdbid_db(json_obj['imdbID'])
                    print(movielens_id)
                    print(insert_user_like(userid,movielens_id,json_obj['imdbID']))
                elif message_text.find('推薦')!=-1:
                    if(len(generate_movielens_id_list(userid))>=5):
                        response_message = '推給你好東西，讓我算一下先'
                        line_bot_api.push_message(userid,TextSendMessage(text=response_message))
                        recommendation_list = bpr_recommendation(generate_movielens_id_list(userid))
                        year = []
                        title = []
                        #for recommendation in recommendation_list:
                        clear = [x for x in recommendation_list if x != []]
                        new_recommendation = sorted(clear, key = lambda x: x[2])
                        json_obj = get_information_imdb_id(search_for_imdb_by_movielens_id(new_recommendation[-1][0]))
                        response_message = '我推薦這部給你：'+json_obj['Title']+' ('+json_obj['Year']+')'
                        response_img = json_obj['Poster']
                        line_bot_api.push_message(userid,TextSendMessage(text=response_message))
                        line_bot_api.push_message(userid,ImageSendMessage(original_content_url=response_img,preview_image_url=response_img))
                    else:
                        response_message = '請先告訴我你喜歡哪五部電影喔！'
                        line_bot_api.push_message(userid,TextSendMessage(text=response_message))
                        movie_list = random_5_movie()
                        for movie in movie_list:
                            line_bot_api.push_message(userid,TextSendMessage(text=movie))
                elif message_text.find('紀錄')!=-1:
                    history_list = get_userlike_fromdb(userid)
                    response_message = '你最近喜歡的電影'
                    line_bot_api.push_message(userid,TextSendMessage(text=response_message))
                    for i in range(0,5):
                        line_bot_api.push_message(userid,TextSendMessage(text=history_list[i]))
                elif message_text.find('相關資訊')!=-1:
                    movie_title = deal_user_like(message_text)
                    try:
                        json_obj = get_information_title(movie_title)
                        response_message = json_obj['Title']+' ('+json_obj['Year']+')'
                        response_img = json_obj['Poster']
                        line_bot_api.push_message(userid,TextSendMessage(text=response_message))
                        line_bot_api.push_message(userid,ImageSendMessage(original_content_url=response_img,preview_image_url=response_img))

                        response_message = json_obj['Actors']
                        line_bot_api.push_message(userid,TextSendMessage(text=response_message))

                        response_message= 'https://www.imdb.com/title/'+json_obj['imdbID']+'/'
                        line_bot_api.push_message(userid,TextSendMessage(text=response_message))
                    except:
                        line_bot_api.push_message(userid,TextSendMessage(text='抱歉～找不到這部電影耶～'))
                elif message_text.find('最近電影')!=-1:
                        latest_movie = get_latest_movie_tmdb()
                        line_bot_api.push_message(userid,TextSendMessage(text='給你最近很夯的電影！'))
                        for movie in latest_movie[:5]:
                            response_message= movie['original_title']
                            line_bot_api.push_message(userid,TextSendMessage(text=response_message))
                            response_img = 'https://image.tmdb.org/t/p/original'+movie['poster_path']
                            line_bot_api.push_message(userid,ImageSendMessage(original_content_url=response_img,preview_image_url=response_img))
                    
        except InvalidSignatureError:
            print('InvalidSignatureError')
            return HttpResponseBadRequest()
        return HttpResponse()
    else:
        print('HttpResponseBadRequest!')
        return HttpResponseBadRequest()


# @handler.add(MessageEvent, message=TextMessage)
# def message_text(event: MessageEvent):
#     line_bot_api.reply_message(
#         event.reply_token,
#         TextSendMessage(text=event.message.text)
# )


def insert_movie_to_db(request):
    df = pd.read_csv('./bpr_movie/bpr/movie_year_another_id.csv',dtype={'movie_id':str,'imdb_id': str,'tmdb_id': str,'title': str,'year': str})
    for index in range(0,len(df)):
        try:
            movielens_id = df.loc[[index]].values.tolist()[0][0]
            title = df.loc[[index]].values.tolist()[0][1]
            year = df.loc[[index]].values.tolist()[0][2]
            imdb_id = df.loc[[index]].values.tolist()[0][3]
            tmdb_id = df.loc[[index]].values.tolist()[0][4]
            print(movielens_id,title,year,imdb_id,tmdb_id)
            create_one_movie = Movie.objects.create(movielens_id=movielens_id,title=title,year=year,imdb_id=imdb_id,tmdb_id=tmdb_id)
            create_one_movie.save()
            print('save successful!')
        except:
            print('something wrong!')
    return JsonResponse({"status": "200"})

def insert_user_like(line_unic_id,movielens_id,imdb_id):
    create_one_record = UserLike.objects.create(line_unic_id=line_unic_id,movielens_id=movielens_id,imdb_id=imdb_id)
    create_one_record.save()
    return 'successful!'

def insert_user_watched(line_unic_id,movielens_id):
    create_one_record = UserWatched.objects.create(line_unic_id=line_unic_id,movielens_id=movielens_id)
    create_one_record.save()
    return 'successful!'

def get_movie_info_by_movielensid(movielens_id):
    movie_obj = Movie.objects.filter(movielens_id=str(movielens_id))
    for record in movie_obj:
        print(record.movielens_id)
        #print(record.title)
        #print(record.year)
        #print(record.imdb_id)
        #print(record.tmdb_id)
        information = gi.get_information(imdb_id=record.imdb_id)
        print(information)

def get_information(request):
    movielens_id = '1'
    get_movie_info_by_movielensid(movielens_id)

def check_user_db(user_id):
    user_obj = User.objects.filter(line_unic_id=str(user_id))
    if len(user_obj) == 0:
        return False
    else:
        return True

def insert_user_db(user_id,name):
    try:
        user_obj = User.objects.create(line_unic_id=user_id,nickname=name)
        user_obj.save()
        return True
    except:
        return False

def cold_start():
    #random five movies in 2012~2018 for users
    return True

def deal_user_like(original_message):
    # 我喜歡 xxx
    location = original_message.find('我喜歡')
    print(location)
    start = location
    end = location+len('我喜歡')
    movie_title = original_message[end:]
    print(movie_title)
    return movie_title

def search_for_movieid_db(movie_title):
    # 我喜歡 xxx
    movie_obj = Movie.objects.filter(title=str(movie_title)).order_by('-year')
    movie_obj[0].movielens_id
    movie_obj[0].imdb_id
    print(movie_obj[0].imdb_id)
    get_information(movie_obj[0].imdb_id)
    #return movie_title

def get_information_imdb_id(imdb_id):
    query = 'http://omdbapi.com/?'+'i='+str(imdb_id)+'&apikey=8c573e82&plot=full'
    #print(query)
    r = requests.get(query)
    json_obj = json.loads(r.text)
    print(json_obj)
    return json_obj

def get_information_title(movie_title):
    query = 'http://omdbapi.com/?'+'t='+str(movie_title)+'&apikey=8c573e82&plot=full'
    #print(query)
    r = requests.get(query)
    json_obj = json.loads(r.text)
    return json_obj

def search_for_movieid_imdbid_db(imdb_id):
    movie_obj = Movie.objects.filter(imdb_id=str(imdb_id)).order_by('-year')
    if len(movie_obj)==0:
        return 'notfound'
    else:
        movie_obj[0].movielens_id
        print(movie_obj[0].movielens_id)
        return movie_obj[0].movielens_id

#tt4154796
# Create your views here.
def bpr_recommendation(movielens_id_list):
     #p2 = [88140,102125,59315,102903,4369,46335,4370,1270,648]
     recommend_movie_id=bpr.recommend_movie(movielens_id_list)
     recommend_list = bpr.recommend5(recommend_movie_id)
     print(recommend_list)
     return recommend_list

def generate_movielens_id_list(user_id):
    #user_id = 'U17b24f3737135a4f9f0a0c7f9d96a6d6'
    id_list = UserLike.objects.filter(line_unic_id=str(user_id)).values_list('movielens_id',flat=True).distinct()
    id_list = list(id_list)
    try:
        id_list.remove('notfound')
    except:
        print('no notfound!')
    return id_list

def search_for_imdb_by_movielens_id(movielens_id):
    print(movielens_id)
    id_list = Movie.objects.filter(movielens_id=str(movielens_id))
    print(len(id_list))
    return id_list[0].imdb_id

def get_userlike_fromdb(user_id):
    print(user_id)
    id_list = UserLike.objects.filter(line_unic_id=str(user_id)).values_list('movielens_id',flat=True).distinct().order_by('-id')
    id_list = list(id_list)
    titles=[]
    index = 0
    for movielens_id in id_list:
        title = list(Movie.objects.filter(movielens_id=str(movielens_id)).values_list('title',flat=True))[0]
        if len(title)!=0:
            index = index+1
            titles.append(title)
        if index>=10:
            break
        #print(Movie.objects.filter(movielens_id=str(movielens_id)).values_list('title',flat=True))
    return  titles

def random_5_movie():
    import random
    random_2018 = list(Movie.objects.filter(year=str(2018)).values_list('title',flat=True))
    random_2017 = list(Movie.objects.filter(year=str(2017)).values_list('title',flat=True))
    random_2016 = list(Movie.objects.filter(year=str(2016)).values_list('title',flat=True))
    random_2015 = list(Movie.objects.filter(year=str(2015)).values_list('title',flat=True))
    random_2014 = list(Movie.objects.filter(year=str(2014)).values_list('title',flat=True))
    sample = random.randint(0,35)
    random_list = []
    random_list.append(random_2018[sample])
    random_list.append(random_2017[sample])
    random_list.append(random_2016[sample])
    random_list.append(random_2015[sample])
    random_list.append(random_2014[sample])
    return  random_list


def deal_information(original_message):
    # 我喜歡 xxx
    location = original_message.find('相關資訊')
    print(location)
    start = location
    end = location+len('相關資訊')
    movie_title = original_message[end:]
    print(movie_title)
    return movie_title

def get_latest_movie_tmdb():
    url = 'https://api.themoviedb.org/3/movie/popular?api_key=926770d103fd7e9324ececff35eceefa&language=en-US&page=1'
    r = requests.get(url)
    json_obj = json.loads(r.text)
    print(json_obj['results'])
    return json_obj['results']

    


