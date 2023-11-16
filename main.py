import os
import shutil
from datetime import datetime
from ftplib import FTP
from xml.etree import ElementTree

import telebot
from dotenv import load_dotenv
from telebot.apihelper import ApiTelegramException

from channels import briz, wsks

load_dotenv()


def downloading_files(source: str, login: str, password: str, date: datetime.date) -> None:
    """Загрузка всех файлов в папку с текущей датой."""

    connection = FTP(source)
    connection.login(login, password)
    files = connection.nlst()

    if not os.path.exists(f'epg_files/{date}'):
        os.makedirs(f'epg_files/{date}')

    for file in files:
        with open(f'epg_files/{date}/{file}', 'wb') as f:
            connection.retrbinary(f'RETR {file}', f.write)

    os.remove(f'epg_files/{date}/TV_Pack.xml')

    connection.quit()


def date_checking(folder: str, date: datetime.date) -> None:
    """Проверка актуальности файлов."""

    files = os.listdir(f'{folder}/{date}')

    for file in files:
        tree = ElementTree.parse(f'{folder}/{date}/{file}')
        service = tree.find('service')

        try:
            last_event_st_time = service.findall('event')[-1].attrib['start-time']
            last_event_date = datetime.strptime(last_event_st_time, '%Y-%m-%d %H:%M').date()

            if last_event_date < current_date:
                os.remove(f'{folder}/{date}/{file}')

        except AttributeError:
            pass


def building_packages(work_directory, dst_folder, channel_list, date):
    """Сборка пакетов каналов."""
    not_exist_list = []

    files_for_remove = os.listdir(f'{work_directory}/{dst_folder}')
    for file in files_for_remove:
        try:
            os.remove(f'{work_directory}/{dst_folder}/{file}')
        except FileNotFoundError:
            pass

    fresh_files = os.listdir(f'{work_directory}/{date}')

    for channel in channel_list:
        full_channel_name = channel.zfill(9) + '.xml'

        if full_channel_name in fresh_files:
            shutil.copy(
                f'{work_directory}/{date}/{full_channel_name}',
                f'{work_directory}/{dst_folder}/{full_channel_name}'
            )
        else:
            not_exist_list += full_channel_name

    return not_exist_list


def uploading_files(source, login, password, not_refresh, folder) -> None:
    with FTP(source) as connection:
        connection.login(login, password)
        old_files = connection.nlst('tffs0/epg_file/')
        new_files = os.listdir(f'epg_files/{folder}')

        for file in old_files:
            print(file)
            if file not in not_refresh:
                connection.delete(f'tffs0/epg_file/{file}')
        #
        # for file in new_files:
        #     with open(file, 'rb') as f:
        #         connection.storbinary(f'STOR tffs0/epg_file/{file}', f)

        connection.quit()


def report_message(not_exist, folder):
    bot = telebot.TeleBot('6401346922:AAGYIr7inOWVM3tL80UWuPC9aF9_gUl4Y0Y')
    contacts = {'Markarov': 67471266, 'Susylev': 192697803, 'Bufalov': 749444404}

    for name, chat_id in contacts.items():
        if len(not_exist) > 0:
            try:
                bot.send_message(chat_id, not_exist)
            except ApiTelegramException:
                bot.send_message(contacts['Markarov'], f'Данные контакту {name} не отправлены.')
        else:
            try:
                bot.send_message(chat_id, 'файлы обновлены')
            except ApiTelegramException:
                bot.send_message(contacts['Markarov'], f'Данные контакту {name} не отправлены.')


if __name__ == '__main__':
    url, user, passwrd = os.getenv('SOURCE'), os.getenv('LOGIN'), os.getenv('PASSWORD')
    current_date = datetime.today().date()

    # downloading_files(source=url, login=user, password=passwrd, date=current_date)
    # date_checking(folder='epg_files', date=current_date)

    not_exist_briz = building_packages(
        work_directory='epg_files', dst_folder='Briz', channel_list=briz, date=current_date
    )
    not_exist_wsks = building_packages(
        work_directory='epg_files', dst_folder='wSKS', channel_list=wsks, date=current_date
    )

    briz_folder = 'Briz'
    wsks_folder = 'wSKS'

    uploading_files(
        source='10.20.3.22',
        login='target',
        password='target',
        not_refresh=not_exist_briz,
        folder=briz_folder
    )
    # uploading_files(
    #     source='10.20.4.30',
    #     login='target',
    #     password='target',
    #     not_refresh=not_exist_wsks,
    #     folder=wsks_folder
    # )

    # report_message(not_exist_briz, briz_folder)
    # report_message(not_exist_wsks, wsks_folder)
