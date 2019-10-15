# -*- coding: utf-8 -*-
# Cкачивает видео с myanimelist.net по ссылке.
# Получает название, жанры и описание
# делает из них 2 видео.
# Разделяет изображение на части и в каждую часть
# записывает видое.

import os
import requests

from pytube import YouTube
from bs4 import BeautifulSoup
import moviepy.editor as mpe
from moviepy.video.tools.segmenting import findObjects

def download_youtube_video(videourl, name, path='./'):
    """Скачивает видео с ютуба по ссылке."""
    yt = YouTube(videourl)
    # Выбор потока видео для скачивания
    yt = yt.streams.filter(progressive=True, file_extension='mp4') \
           .order_by('resolution').desc().first()
    if not os.path.exists(path):
        os.makedirs(path)
    yt.download(path, name)

def get_html(url):
    """Получает ссылку, возвращает html-страницу."""
    return requests.get(url).text

def get_page_data(soup):
    """Парсером получает ссылку на ютуб и название для видео."""
    name = soup.find('title').text.split(' ', 1)[0].replace('\n', '')
    link = soup.find('a', 'video-unit').get('href')
    download_youtube_video(link, name)
    return name + ".mp4"

def get_synopsis(soup):
    """Парсером получает описние."""
    synopsis = soup.find(itemprop="description").text
    return synopsis

def get_title(soup):
    """Парсером получает название."""
    title = 'Name: ' + soup.find('title').text.replace('\n', '') \
                           .replace(' - MyAnimeList.net', '')
    return(title)

def get_genre(soup):
    """Парсером получает жанры."""
    genres = soup.find('td').find('div') \
                  .find('span', text='Genres:') \
                  .findParent().find_all('a')
    genres_txt = 'Genres: '
    # Создает строку жанров
    for i, genre in enumerate(genres):
        if i == len(genres) - 1:
            genres_txt += genre.text
        else:
            genres_txt += genre.text + ', '
    return genres_txt

def make_video(soup, regions):
    """Создает массив видеоклипов из html-страницы."""
    video = [0] * 4
    video[2] = mpe.VideoFileClip(get_page_data(soup)) \
                  .subclip(6, 9)
    print('Видео скачано')

    duration_ = video[2].duration

    text = get_title(soup) + '\n' + get_genre(soup)
    video[1] = mpe.TextClip(text, fontsize=24, color='white',
                            size=(regions[1].size), method='caption',
                            align='West').set_duration(duration_)

    video[3] = mpe.TextClip(get_synopsis(soup), fontsize=24,
                            color='white', size=(regions[3].size),
                            method='caption',
                            align='North').set_duration(duration_)

    print('Созданы видео с информацией')

    background = mpe.ImageClip('BG.jpg').set_opacity(0.4)
    video[0] = background.set_duration(duration_)
    return video


def compose_video(url):
    """Собирает видео."""
    html = get_html(url)
    soup = BeautifulSoup(html, 'lxml')
    print('Получен html')

    # Загрузка изображения для деления на части
    im = mpe.ImageClip('Form1.png')
    regions = findObjects(im)

    video = make_video(soup, regions)

    # Соотношение видео c частью изображения

    for i, v in enumerate(video):
        if i == 2:
            video[i] = v.resize(regions[i].size) \
                        .set_mask(regions[i].mask) \
                        .set_pos(regions[i].screenpos)
        else:
            video[i] = v.resize(regions[i].size) \
                .set_pos(regions[i].screenpos)

    # video[0] = video[0].resize(regions[0].size) \
    #                    .set_pos(regions[0].screenpos)
    # #
    # video[1] = video[1].resize(regions[1].size) \
    #                    .set_mask(regions[1].mask) \
    #                    .set_pos(regions[1].screenpos)
    #
    # # video[1] = mpe.CompositeVideoClip([video[1], regions[1]])
    #
    # video[2] = video[2].resize(regions[2].size) \
    #                    .set_pos(regions[2].screenpos)
    #
    # video[3] = video[3].resize(regions[3].size) \
    #                    .set_pos(regions[3].screenpos)

    # comp_clips = [c.resize(r.size)
    #                .set_pos(r.screenpos)
    #               for c, r in zip(video, regions)]

    final_video = mpe.CompositeVideoClip(video)
    final_video.write_videofile("composition.mp4")

compose_video('https://myanimelist.net/anime/37521/')