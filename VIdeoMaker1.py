# -*- coding: utf-8 -*-
# Cкачивает видео с myanimelist.net по ссылке.
# Получает название, жанры и описание
# делает из них 2 видео.
# Разделяет изображение на части и в каждую часть
# записывает видое.

import os
import requests
import time

from pytube import YouTube
from bs4 import BeautifulSoup
import moviepy.editor as mpe
from moviepy.video.tools.segmenting import findObjects
from gtts import gTTS

# PARAMS = ['-vcodec', 'h264_qsv', '-movflags', 'faststart'] 751s 8.4mb
# PARAMS = ['-vcodec', 'nvenc', '-movflags', 'faststart'] 697s 8.4mb
# PARAMS = ['-preset', 'ultrafast', '-movflags', 'faststart'] 757s 45.7mb
# PARAMS = [] 827s 15.9mb
# PARAMS = ['-movflags', 'faststart'] 835s 15.9mb
# PARAMS = ['-vcodec', 'h264_qsv'] 791s 15.9mb
# PARAMS = ['-vcodec', 'nvenc'] 725s 17.4mb
# PARAMS = ['-vcodec', 'nvenc', '-movflags', 'faststart'] 735s 17.4mb
PARAMS = ['-vcodec', 'nvenc', '-movflags', 'faststart']


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
    name = soup.find('title').text.split(' ', 1)[0].replace('\n', '')\
        .replace('.', '')
    link = soup.find('a', 'video-unit').get('href')
    download_youtube_video(link, name)
    return name + ".mp4"


def get_synopsis(soup):
    """Парсером получает описние."""
    synopsis = soup.find(itemprop="description").text \
        .replace('[Written by MAL Rewrite]', '')
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
    """Достает источники."""
    source = soup.find('td').find('div').find('span', text='Source:') \
        .findParent().text.replace('\n', '').replace('  ', ' ')
    return source


def set_information(soup, region, duration_):
    """Создает клип с инфой."""
    text = get_title(soup) + '\n' + get_genre(soup) + '\n' \
           + get_studios(soup) + '\n' + get_source(soup)
    information = mpe.TextClip(text, fontsize=24, color='white',
                               size=(region.size[0] - 100,
                                     region.size[1] - 100),
                               method='caption',
                               align='West') \
        .set_duration(duration_).set_pos((region.screenpos[0] + 50,
                                          region.screenpos[1]))

    return information


def set_synopsis(soup, region, duration_):
    """Создает клип описания."""
    text = 'SYNOPSIS' + '\n' + get_synopsis(soup)
    synopsis = mpe.TextClip(text, fontsize=24,
                            color='white', size=region.size,
                            method='caption', align='North') \
        .set_duration(duration_).set_pos(region.screenpos)
    return synopsis


def set_background(background, duration_):
    bg = mpe.ImageClip(background).set_opacity(0.4) \
        .set_duration(duration_)
    return bg


def anime_preview(video, title):
    """Создает превью для каждого места."""
    # title = "Top 1 in 2019 year\n" + title
    tts = gTTS(title, lang='en')
    tts.save('title.mp3')
    audio = mpe.AudioFileClip('title.mp3')

    time = audio.duration
    preview_video = video.subclip(0, time).resize((1920, 1080)) \
        .set_opacity(0.4).volumex(0.2)
    # .resize(region.size) \
    #     .set_pos(region.screenpos)
    name = mpe.TextClip(title, fontsize=72, color='white',
                        size=preview_video.size,
                        method='caption',
                        align='center').set_duration(time)

    name = name.set_audio(audio)

    preview = mpe.CompositeVideoClip([preview_video, name])
    return preview


def video_preview(video, title, time):
    """Создает превью для каждого места."""
    # title = "Top 1 in 2019 year\n" + title
    tts = gTTS(title, lang='en')
    tts.save('title.mp3')
    audio = mpe.AudioFileClip('title.mp3')

    # time = audio.duration
    preview_video = video.subclip(0, time).resize((1920, 1080)) \
        .set_opacity(0.4).volumex(0.2)
    # .resize(region.size) \
    #     .set_pos(region.screenpos)
    name = mpe.TextClip(title, fontsize=72, color='white',
                        size=preview_video.size,
                        method='caption',
                        align='center').set_duration(time)

    name = name.set_audio(audio)

    preview = mpe.CompositeVideoClip([preview_video, name])
    return preview


def make_video(soup, regions, place):
    """Создает массив видеоклипов из html-страницы."""
    video = [0] * 5

    background = 'BG.jpg'

    video[2] = mpe.VideoFileClip(get_page_data(soup)).subclip(15, 45)

    title = soup.find('title').text.replace('\n', '') \
        .replace(' - MyAnimeList.net', '')

    text = 'Top ' + place + '\n' + title
    video[4] = anime_preview(video[2], text)
    time = video[4].duration

    video[2] = video[2].subclip(time, ).resize(regions[2].size) \
        .set_pos(regions[2].screenpos).set_mask(regions[2].mask)
    print('Видео скачано')
    duration_ = video[2].duration

    video[0] = set_background(background, duration_) \
        .resize(regions[0].size).set_pos(regions[0].screenpos)
    video[1] = set_information(soup, regions[1], duration_)
    video[3] = set_synopsis(soup, regions[3], duration_)

    print('Создан массив видео')

    return video


def compose_video(url, regions, place):
    """Собирает видео."""
    html = get_html(url)
    soup = BeautifulSoup(html, 'lxml')
    print('Получен html')

    video = make_video(soup, regions, place)

    final_video = mpe.CompositeVideoClip([video[0], video[1],
                                          video[2], video[3]])
    final_video.write_videofile('video.mp4', ffmpeg_params=PARAMS)
    print('Создано video.mp4')
    vid = mpe.VideoFileClip('video.mp4')

    video[4].write_videofile('preview.mp4', ffmpeg_params=PARAMS)
    print('Создано preview.mp4')
    prev = mpe.VideoFileClip('preview.mp4')

    concat = mpe.concatenate_videoclips([prev, vid])
    name = place + '.mp4'
    concat.write_videofile(name, ffmpeg_params=PARAMS)


def create_video(url, video_name):
    # Загрузка изображения для деления на части
    start_time = time.time()
    im = mpe.ImageClip('Form1.png')
    regions = findObjects(im)

    last = len(url)
    clips = [0] * (last + 1)


    for temp, anime in enumerate(url):
        place = temp + 1
        name = str(place)
        compose_video(anime, regions, name)
        clips[last - temp] = mpe.VideoFileClip(name + '.mp4')


    background = 'BG.jpg'
    duration_ = 5
    audio_clip = clips[last]
    audio = audio_clip.subclip(4, duration_).audio
    bg = set_background(background, duration_) \
        .resize(regions[0].size).set_pos(regions[0].screenpos)\
        .set_audio(audio)

    clips[0] = video_preview(bg, video_name, duration_)


    concat = mpe.concatenate_videoclips(clips)
    concat.write_videofile('full.mp4', ffmpeg_params=PARAMS)

    print("--- %s seconds ---" % (time.time() - start_time))


# compose_video('https://myanimelist.net/anime/37521/')

create_video(['https://myanimelist.net/anime/37521/',
              'https://myanimelist.net/anime/38691/Dr_Stone'],
             'Top Anime'

             )

