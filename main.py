import os
import shutil
from datetime import datetime, timedelta, time
from ftplib import FTP
from xml.etree import ElementTree

from telebot import TeleBot
from dotenv import load_dotenv
from telebot.apihelper import ApiTelegramException

from channels import briz, wsks

load_dotenv()


def downloading_files(source: str, login: str, password: str, bot: TeleBot) -> None:
    """Загрузка всех файлов во временную папку."""

    connection = FTP(source)
    connection.login(login, password)
    files = connection.nlst()

    for file in files:
        with open(f'epg_files/tmp/{file}', 'wb') as f:
            connection.retrbinary(f'RETR {file}', f.write)
        print(file, 'загружен')

    connection.quit()

    bot.send_message(67471266, 'загрузка завершена')


def date_checking(date: datetime.date, bot: TeleBot) -> list[str]:
    """Проверка актуальности файлов."""

    # TODO: test

    files = os.listdir(f'epg_files/tmp')
    removed_files = []

    for file in files:
        tree = ElementTree.parse(f'epg_files/tmp/{file}')
        service = tree.find('service')

        try:
            last_event_start_time = service.findall('event')[-1].attrib['start-time']
            last_event_date = datetime.strptime(last_event_start_time, '%Y-%m-%d %H:%M').date()

            if last_event_date <= date:
                os.remove(f'epg_files/tmp/{file}')
                removed_files.append(file)
                print(file, 'устарел')

        except AttributeError:
            pass

    bot.send_message(67471266, 'проверка завершена')

    return removed_files


def building_packages(dst_folder: str, channel_list: list[str], bot: TeleBot) -> list[str]:
    """Сборка пакетов каналов."""

    files_not_exist = []
    files_for_remove = os.listdir(f'epg_files/{dst_folder}')

    for file in files_for_remove:
        try:
            os.remove(f'epg_files/{dst_folder}/{file}')
        except FileNotFoundError:
            pass

    fresh_files = os.listdir(f'epg_files/tmp')

    for channel in channel_list:
        full_channel_name = channel.zfill(9) + '.xml'

        if full_channel_name in fresh_files:
            shutil.copy(
                f'epg_files/tmp/{full_channel_name}',
                f'epg_files/{dst_folder}/{full_channel_name}'
            )
        else:
            files_not_exist.append(full_channel_name)

    print('сборка завершена')
    bot.send_message(67471266, 'сборка завершена')

    return files_not_exist


def uploading_files(source: str, login: str, password: str, folder: str, bot: TeleBot) -> None:
    """Загрузка файлов на карту EPG."""

    connection = FTP(source)
    connection.login(login, password)
    new_files = os.listdir(f'epg_files/{folder}')

    for file in new_files:
        with open(f'epg_files/{folder}/{file}', 'rb') as f:
            connection.storbinary(f'STOR tffs0/epg_file/{file}', f)
        print(f'{file} загружен')

    print('заливка завершена')
    bot.send_message(67471266, 'заливка завершена')

    connection.quit()


def report_message(not_exist, card, bot: TeleBot):
    contacts = {'Markarov': 67471266, 'Susylev': 192697803, 'Bufalov': 749444404}

    for name, chat_id in contacts.items():
        if len(not_exist) > 0:
            try:
                bot.send_message(chat_id, not_exist)
            except ApiTelegramException:
                bot.send_message(contacts['Markarov'], f'Данные контакту {name} не отправлены.')
        else:
            try:
                bot.send_message(chat_id, f'файлы для {card} обновлены')
            except ApiTelegramException:
                bot.send_message(contacts['Markarov'], f'Данные контакту {name} не отправлены.')


if __name__ == '__main__':
    url, user, passwd = os.getenv('SOURCE'), os.getenv('LOGIN'), os.getenv('PASSWORD')
    tomorrow = datetime.today().date() + timedelta(days=1)
    tgbot = TeleBot('6401346922:AAGYIr7inOWVM3tL80UWuPC9aF9_gUl4Y0Y')

    start_time = datetime.now()

    downloading_files(source='ftp.epgservice.ru', login='infokos', password='6KVy76MY', bot=tgbot)
    removed_files = date_checking(date=tomorrow, bot=tgbot)
    not_exist_briz = building_packages(dst_folder='Briz', channel_list=briz, bot=tgbot)
    not_exist_wsks = building_packages(dst_folder='wSKS', channel_list=wsks, bot=tgbot)

    uploading_files(
        source='10.20.3.22',
        login='target',
        password='target',
        folder='Briz',
        bot=tgbot
    )
    uploading_files(
        source='10.20.4.30',
        login='target',
        password='target',
        folder='wSKS',
        bot=tgbot
    )

    report_message(not_exist_briz, 'Бриз', bot=tgbot)
    report_message(not_exist_wsks, 'wSKS', bot=tgbot)

    finish_time = datetime.now() - start_time
    print(finish_time)
