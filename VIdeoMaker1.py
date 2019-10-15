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
from gtts import gTTS


def download_youtube_video(video_url, name, path='./'):
    """Скачивает видео с ютуба по ссылке."""
    yt = YouTube(video_url)
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
    return title


def get_genre(soup):
    """Парсером получает жанры."""
    genres = soup.find('td').find('div').find('span', text='Genres:') \
        .findParent().find_all('a')
    genres_txt = 'Genres: '
    # Создает строку жанров
    for i, genre in enumerate(genres):
        if i == len(genres) - 1:
            genres_txt += genre.text
        else:
            genres_txt += genre.text + ', '
    return genres_txt


def get_studios(soup):
    """Достает студии."""
    studios = soup.find('td').find('div').find('span', text='Studios:') \
        .findParent().find_all('a')
    studios_txt = 'Studios: '

    for i, studio in enumerate(studios):
        if i == len(studios) - 1:
            studios_txt += studio.text
        else:
            studios_txt += studio.text + ', '

    return studios_txt


def get_source(soup):
    return soup.find('td').find('div').find('span', text='Source:') \
        .findParent().text.replace('\n', '').replace('  ', ' ')


def set_information(soup, region, duration_):
    text = get_title(soup) + '\n' + get_genre(soup) + '\n' \
           + get_studios(soup) + '\n' + get_source(soup)

    return mpe.TextClip(text, fontsize=24, color='white',
                        size=(region.size[0] - 100,
                              region.size[1] - 100), method='caption',
                        align='West') \
        .set_duration(duration_).set_pos((region.screenpos[0] + 50,
                                          region.screenpos[1]))


def set_synopsis(soup, region, duration_):
    text = 'SYNOPSIS' + '\n' + get_synopsis(soup)
    return mpe.TextClip(text, fontsize=24,
                        color='white', size=region.size,
                        method='caption', align='North') \
        .set_duration(duration_).set_pos(region.screenpos)


def set_background(background, duration_):
    return mpe.ImageClip(background).set_opacity(0.4) \
        .set_duration(duration_)


def make_video(soup, regions):
    """Создает массив видеоклипов из html-страницы."""
    video = [0] * 4

    background = 'BG.jpg'

    video[2] = mpe.VideoFileClip(get_page_data(soup)).subclip(15, 45) \
        .resize(regions[2].size).set_mask(regions[2].mask) \
        .set_pos(regions[2].screenpos).volumex(0.2)

    print('Видео скачано')
    duration_ = video[2].duration


    #доделать текст в речь
    gTTS(get_synopsis(soup)).save('synopsis.mp3')
    print('Записана речь')

    audio = mpe.AudioFileClip('synopsis.mp3')
    audio.write_audiofile('syn.mp3', ffmpeg_params=['-filter:a',
                                                    'atempo=1.25'])

    newaudio = mpe.AudioFileClip('syn.mp3').subclip(0, 30).volumex(2)




    video[0] = set_background(background, duration_) \
        .resize(regions[0].size).set_pos(regions[0].screenpos)
    video[1] = set_information(soup, regions[1], duration_)
    video[3] = set_synopsis(soup, regions[3], duration_).set_audio(newaudio)

    print('Создан массив видео')

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



    final_video = mpe.CompositeVideoClip(video)
    # final_video = final_video.set_audio(newaudio)
    final_video.write_videofile("composition.mp4")


compose_video('https://myanimelist.net/anime/37521/')
