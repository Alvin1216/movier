# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Movie(models.Model):
    movielens_id = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    year = models.CharField(max_length=20)
    imdb_id = models.CharField(max_length=100)
    tmdb_id = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'movie'


class User(models.Model):
    line_unic_id = models.CharField(max_length=200)
    nickname = models.CharField(max_length=200)

    class Meta:
        managed = False
        db_table = 'user'


class UserLike(models.Model):
    line_unic_id = models.CharField(max_length=200)
    movielens_id = models.CharField(max_length=200, blank=True, null=True)
    imdb_id = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'user_like'


class UserWatched(models.Model):
    line_unic_id = models.CharField(max_length=200)
    movielens_id = models.CharField(max_length=100)
    rating = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'user_watched'
