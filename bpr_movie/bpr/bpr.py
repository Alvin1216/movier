# -*- coding: utf-8 -*-
"""
Created on Wed Dec 18 14:44:23 2019

@author: Sophie
"""

# code for loading the format for the notebook
import os
"""
%load_ext watermark
%load_ext autoreload
%autoreload 2
"""

import sys
import random
import numpy as np
import pandas as pd
from collections import Counter
from math import ceil
from tqdm import trange
from subprocess import call
from itertools import islice
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import normalize
from sklearn.neighbors import NearestNeighbors
from scipy.sparse import csr_matrix, dok_matrix


"""
%watermark -a 'Ethen' -d -t -v -p numpy,pandas,scipy,sklearn,tqdm
"""



def create_matrix(data, users_col, items_col, ratings_col, threshold = None):
    #print(data[ratings_col])
    #print(data[items_col])
    if threshold is not None:
        data = data[data[ratings_col] >= threshold]
        data[ratings_col] = 1
    
    for col in (items_col, users_col, ratings_col):
        data[col] = data[col].astype('category')

    ratings = csr_matrix((data[ratings_col],
                          (data[users_col].astype('category').cat.codes, data[items_col].astype('category').cat.codes)))
    #ratings.eliminate_zeros()
    ratings_array = csr_matrix((data[ratings_col],
                          (data[users_col].astype('category').cat.codes, data[items_col].astype('category').cat.codes))).toarray()
    #ratings.eliminate_zeros()
    #print(data[users_col].astype('category').cat.codes)
    #print(ratings[1].shape[1])
    return ratings, data, ratings_array

   

def pearson(p,q):
    
    same_or_not=[l for l in p if l in q]
    if len(same_or_not)==0:
        r=0
    else:
#只計算兩者共同有的
        same = 0
        for i in p:
            if i in q:
                same +=1

        n = same
        #分別求p，q的和
        sumx = sum([p[i] for i in range(n)])
        sumy = sum([q[i] for i in range(n)])
        #分別求出p，q的平方和
        sumxsq = sum([p[i]**2 for i in range(n)])
        sumysq = sum([q[i]**2 for i in range(n)])
        #求出p，q的乘積和
        sumxy = sum([p[i]*q[i] for i in range(n)])
        # print sumxy
        #求出pearson相關係數
        up = sumxy - sumx*sumy/n
        down = ((sumxsq - pow(sumxsq,2)/n)*(sumysq - pow(sumysq,2)/n))**.5
        #若down為零則不能計算，return 0
        if down == 0 :return 0
        r = up/down
    return r

# user from 0

def similarity_user(p):
    similarity_array=[]
    for i in range(0,len(array)):
        q = user_like[i][1]
        #print(A)
        similarity_per=pearson(p,q)
        similarity_array.append(similarity_per)

    find = max(similarity_array)
    max_array=[i for i,v in enumerate(similarity_array) if v==find]
    
    choice=random.randint(0,len(max_array)-1)
    same_user=max_array[choice] 

    #print(choice)
    #print(same_user)
    return same_user

def create_train_test(ratings, test_size = 0.2, seed = 1234):
   
    
    #like if
    assert test_size < 1.0 and test_size > 0.0

    train = ratings.copy().todok()
    test = dok_matrix(train.shape)
    
    rstate = np.random.RandomState(seed)
    for u in range(ratings.shape[0]):
        split_index = ratings[u].indices
        n_splits = ceil(test_size * split_index.shape[0])
        test_index = rstate.choice(split_index, size = n_splits, replace = False)
        test[u, test_index] = ratings[u, test_index]
        train[u, test_index] = 0
    
    train, test = train.tocsr(), test.tocsr()
    return train, test


class BPR:
    
    def __init__(self, learning_rate = 0.01, n_factors = 15, n_iters = 10, 
                 batch_size = 1000, reg = 0.01, seed = 1234, verbose = True):
        self.reg = reg
        self.seed = seed
        self.verbose = verbose
        self.n_iters = n_iters
        self.n_factors = n_factors
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        
        # to avoid re-computation at predict
        self._prediction = None
        
    def fit(self, ratings):
        
        indptr = ratings.indptr
        indices = ratings.indices
        n_users, n_items = ratings.shape
        #print(ratings.shape)
        
        # ensure batch size makes sense, since the algorithm involves
        # for each step randomly sample a user, thus the batch size
        # should be smaller than the total number of users or else
        # we would be sampling the user with replacement
        batch_size = self.batch_size
        if n_users < batch_size:
            batch_size = n_users
            sys.stderr.write('WARNING: Batch size is greater than number of users,'
                             'switching to a batch size of {}\n'.format(n_users))

        batch_iters = n_users // batch_size
        
        # initialize random weights
        rstate = np.random.RandomState(self.seed)
        #print(n_users)
        #print(self.n_factors)
        self.user_factors = rstate.normal(size = (n_users, self.n_factors))
        self.item_factors = rstate.normal(size = (n_items, self.n_factors))
        #print(self.user_factors)
        #print(self.item_factors)
        
        
        # progress bar for training iteration if verbose is turned on
        loop = range(self.n_iters)
        if self.verbose:
            loop = trange(self.n_iters, desc = self.__class__.__name__)
        
        for _ in loop:
            for _ in range(batch_iters):
                sampled = self._sample(n_users, n_items, indices, indptr)###
                #print(sampled[0])
                sampled_users, sampled_pos_items, sampled_neg_items = sampled
                self._update(sampled_users, sampled_pos_items, sampled_neg_items)

        return self
    
    def _sample(self, n_users, n_items, indices, indptr):
        """sample batches of random triplets u, i, j"""
        sampled_pos_items = np.zeros(self.batch_size, dtype = np.int)
        sampled_neg_items = np.zeros(self.batch_size, dtype = np.int)
        sampled_users = np.random.choice(
            n_users, size = self.batch_size, replace = False)
        i=0
        for idx, user in enumerate(sampled_users):
            pos_items = indices[indptr[user]:indptr[user + 1]]
            i+=1
            #print(pos_items[18])
            #print(pos_items[19])
          
            if len(pos_items) !=0:
                pos_item = np.random.choice(pos_items)##
                neg_item = np.random.choice(n_items)
                while neg_item in pos_items:
                    neg_item = np.random.choice(n_items)

                sampled_pos_items[idx] = pos_item
                sampled_neg_items[idx] = neg_item
                
        #print(pos_item,neg_item)
        #print(pos_items)
        
        return sampled_users, sampled_pos_items, sampled_neg_items
                
    def _update(self, u, i, j):
        
        user_u = self.user_factors[u]
        item_i = self.item_factors[i]
        item_j = self.item_factors[j]
        
        r_uij = np.sum(user_u * (item_i - item_j), axis = 1)
        sigmoid = np.exp(-r_uij) / (1.0 + np.exp(-r_uij))
        
        sigmoid_tiled = np.tile(sigmoid, (self.n_factors, 1)).T

        grad_u = sigmoid_tiled * (item_j - item_i) + self.reg * user_u
        grad_i = sigmoid_tiled * -user_u + self.reg * item_i
        grad_j = sigmoid_tiled * user_u + self.reg * item_j
        self.user_factors[u] -= self.learning_rate * grad_u
        self.item_factors[i] -= self.learning_rate * grad_i
        self.item_factors[j] -= self.learning_rate * grad_j
        return self

    def predict(self):
       
        if self._prediction is None:
            self._prediction = self.user_factors.dot(self.item_factors.T)

        return self._prediction

    def _predict_user(self, user):
        
        user_pred = self.user_factors[user].dot(self.item_factors.T)
        return user_pred

    def recommend(self, ratings, N = 5):
        
        n_users = ratings.shape[0]
        recommendation = np.zeros((n_users, N), dtype = np.uint32)
        for user in range(n_users):
            top_n = self._recommend_user(ratings, user, N)
            recommendation[user] = top_n

        return recommendation

    def _recommend_user(self, ratings, user, N):
        """the top-N ranked items for a given user"""
        scores = self._predict_user(user)

        liked = set(ratings[user].indices)
        count = N + len(liked)
        if count < scores.shape[0]:

            ids = np.argpartition(scores, -count)[-count:]
            best_ids = np.argsort(scores[ids])[::-1]
            best = ids[best_ids]
        else:
            best = np.argsort(scores)[::-1]

        top_n = list(islice((rec for rec in best if rec not in liked), N))
        return top_n
    
    def get_similar_items(self, N = 5, item_ids = None):
        
        normed_factors = normalize(self.item_factors)
        knn = NearestNeighbors(n_neighbors = N + 1, metric = 'euclidean')
        knn.fit(normed_factors)

        if item_ids is not None:
            normed_factors = normed_factors[item_ids]

        _, items = knn.kneighbors(normed_factors)
        similar_items = items[:, 1:].astype(np.uint32)
        return similar_items


def auc_score(model, ratings):
    auc = 0.0
    n_users, n_items = ratings.shape
    try:
        for user, row in enumerate(ratings):
            y_pred = model._predict_user(user)
            y_true = np.zeros(n_items)
            y_true[row.indices] = 1
            auc += roc_auc_score(y_true, y_pred)
    except ValueError:
        pass
    auc /= n_users
    return auc

#print(auc_score(bpr, X_train))
#print(auc_score(bpr, X_test))


#user id & movie id from 1
#add 1= moive id
def recommend_movie(p):
    same_user=similarity_user(p)
    print(same_user)
    #0-user
    user_like5=bpr.recommend(X_train, N = 10)[same_user]
    print(user_like5)
    #add 1= moive id
    user_like5=user_like5+1
    print(user_like5)
    return(user_like5)

#id轉換
def itemid_translate(input_id):
    item = rating_df.item_id.tolist()
    #print(names)
    counts=Counter(item)
    sort_count=sorted(counts.items())
    #print(A)
    item=[]
    #origin transform
    i=0
    for i in range(0,len(sort_count)):
        per=[]
        movie_id=sort_count[i][0]
        per.append(movie_id)
        per.append(i)
        item.append(per)
        i+=1
    #input_id=0
    for i in range(0,len(item)):
        if item[i][0]==input_id :
            return_id_translate=item[i][1]
    return return_id_translate

#print(item[0])
def id_movie(input_id):
    return_id_movie = []
    movie_array=[]#len(movie)
    for i in range(0,len(movie)):
        per=[]
        item_id=item[i]
        genres_class=genres[i]
        #print(result)
        movie_name = movie[i][:-7]
        movie_year = movie[i][-5:-1]
        per.append(item_id)
        per.append(movie_name)
        per.append(movie_year)
        per.append(genres_class)
        movie_array.append(per)
        #print(item_id)
        #print(movie_name)
        #print(movie_year)
#     print(movie_array[0])
    #input_id=20
    
    for i in range(0,len(movie_array)):
        if movie_array[i][0] == input_id:
            return_id_movie = movie_array[i]
    return return_id_movie

#0:id 1:name 2:year 3:class
#from sparse id to movie detail
def id_sparse_movie(input_num):
    #print(item)
    if input_num not in item:
        r_movie=[]
    else:
        sparse_id=itemid_translate(input_num)+1
    #id_movie(sparse_id)
        r_movie=id_movie(sparse_id)
    return r_movie

#input EX.[6045  325  598 6817 7281]
def recommend5(recommend_movie_id):
    R1=id_sparse_movie(recommend_movie_id[0])
    R2=id_sparse_movie(recommend_movie_id[1])
    R3=id_sparse_movie(recommend_movie_id[2])
    R4=id_sparse_movie(recommend_movie_id[3])
    R5=id_sparse_movie(recommend_movie_id[4])
    R6=id_sparse_movie(recommend_movie_id[5])
    R7=id_sparse_movie(recommend_movie_id[6])
    R8=id_sparse_movie(recommend_movie_id[7])
    R9=id_sparse_movie(recommend_movie_id[8])
    R10=id_sparse_movie(recommend_movie_id[9])
    return R1,R2,R3,R4,R5,R6,R7,R8,R9,R10

def get_userlike_list(array):
    #per user like movie >3
    #input form 1 to len
    user_like=[]
    for i in range(0,len(array)):
        per=[]
        user_id=i+1
        per.append(user_id)
        #user_like.append(per)
        per_like=[]
        for j in range(0,len(array[i])):
            
        #print("A")
        #print(i)
            
            if array[i][j]==1:
                
                B=j+1
                per_like.append(B)
        per.append(per_like)
        user_like.append(per)  
        #per.append(B)
        #print(user_like)
        #print(len(user_like))
    return user_like

names = ['user_id', 'item_id', 'rating', 'timestamp']
#df = pd.read_csv(file_path, sep = '\t', names = names)#\t
rating_df = pd.read_csv('./bpr_movie/bpr/ratings.csv',sep=',',names = names,skiprows=1)#
#df = pd.read_table('C:/Users/Sophie/Desktop/ml-1m/ratings.dat', sep = '::', names = names)#\t
#print('data dimension: \n', rating_df.shape)
rating_df.head()
#print(rating_df)

items_col = 'item_id'
users_col = 'user_id'
ratings_col = 'rating'
threshold = 3
X, df, array = create_matrix(rating_df, users_col, items_col, ratings_col, threshold)
X_train, X_test = create_train_test(X, test_size = 0.2, seed = 1234)
#X_train
#print(X_train)
#print(X_test)

user_like = get_userlike_list(array)


#parameters were randomly chosen
bpr_params = {'reg': 0.01,
             'learning_rate': 0.1,
             'n_iters': 160,
             'n_factors': 15,
             'batch_size': 100}

bpr = BPR(**bpr_params)
bpr.fit(X_train)
print("load finished!")

#moive對應
names = ['item_id', 'movie_name', 'genres']
#df = pd.read_csv(file_path, sep = '\t', names = names)#\t
movie_df = pd.read_csv('./bpr_movie/bpr/movies.csv',sep=',',names = names,skiprows=1)#
#df = pd.read_table('C:/Users/Sophie/Desktop/ml-1m/ratings.dat', sep = '::', names = names)#\t
#print('data dimension: \n', movie_df.shape)
#movie_df.head()
#print(movie_df)

#9742 item
item = movie_df.item_id.tolist()
movie = movie_df.movie_name.tolist()
genres = movie_df.genres.tolist()