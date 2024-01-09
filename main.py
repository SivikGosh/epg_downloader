import os
import shutil
from datetime import datetime, timedelta
from ftplib import FTP
from xml.etree import ElementTree

from telebot import TeleBot
from dotenv import load_dotenv
from telebot.apihelper import ApiTelegramException
import re
import sys
import argparse

from channels import briz, wsks

load_dotenv()


def downloading_files(source: str, login: str, password: str, path: str) -> None:
    """Загрузка всех файлов во временную папку."""

    connection = FTP(source)
    connection.login(login, password)
    files = connection.nlst(path)

    for file in files:
        with open(f'epg_files/tmp/{file}', 'wb') as f:
            connection.retrbinary(f'RETR {file}', f.write)

        print(file, 'загружен')
    print('файлы загружены')

    connection.quit()


def date_checking(date: datetime.date) -> None:
    """Проверка актуальности файлов."""

    files = os.listdir(f'epg_files/tmp')

    for file in files:
        tree = ElementTree.parse(f'epg_files/tmp/{file}')
        service = tree.find('service')

        try:
            last_event_start_time = service.findall('event')[-1].attrib['start-time']
            last_event_date = datetime.strptime(last_event_start_time, '%Y-%m-%d %H:%M').date()

            if last_event_date <= date:
                os.remove(f'epg_files/tmp/{file}')

        except AttributeError:
            pass


def building_package(dst_folder: str, channel_list: list[str]) -> list[str]:
    """Сборка пакета каналов."""

    files_that_not_exist = []
    files_for_remove = os.listdir(f'epg_files/{dst_folder}')

    for file in files_for_remove:
        try:
            os.remove(f'epg_files/{dst_folder}/{file}')
        except FileNotFoundError:
            pass

    source_files = os.listdir(f'epg_files/tmp')

    for channel in channel_list:
        full_channel_name = channel.zfill(9) + '.xml'

        if full_channel_name in source_files:
            shutil.copy(
                f'epg_files/tmp/{full_channel_name}',
                f'epg_files/{dst_folder}/{full_channel_name}'
            )
        else:
            files_that_not_exist.append(full_channel_name)

    return files_that_not_exist


def uploading_files(source: str, login: str, password: str, folder: str) -> None:
    """Загрузка файлов на карту EPG."""

    connection = FTP(source)
    connection.login(login, password)
    new_files = os.listdir(f'epg_files/{folder}')

    for file in new_files:
        with open(f'epg_files/{folder}/{file}', 'rb') as f:
            connection.storbinary(f'STOR tffs0/epg_file/{file}', f)

    connection.quit()


def report_message(not_exist: list[str], card_name: str, bot: TeleBot, to: list[str]) -> None:

    for contact in to:
        if len(not_exist) > 0:
            for file in not_exist:
                try:
                    bot.send_message(contact, file)
                except ApiTelegramException:
                    pass
        else:
            try:
                bot.send_message(contact, f'файлы для {card_name} обновлены')
            except ApiTelegramException:
                pass


def get_contacts():
    """Получение id получателей сообщения."""
    ids = []
    for var in os.environ:
        if re.match(r'^TG_CONTACT_[0-9]+$', var):
            ids.append(os.getenv(var))
    return ids


if __name__ == '__main__':
    contacts = get_contacts()
    bot = TeleBot(os.getenv('TG_TOKEN'))

    src_url, src_login, src_password = os.getenv('SOURCE'), os.getenv('LOGIN'), os.getenv('PASSWORD')
    briz_url, wsks_url = os.getenv('BRIZ_IP'), os.getenv('WSKS_IP')
    epg_login, epg_password = os.getenv('EPG_LOGIN'), os.getenv('EPG_PASSWORD')

    tomorrow = datetime.today().date() + timedelta(1)

    downloading_files(src_url, src_login, src_password, '/')
    date_checking(tomorrow)
    not_exist_briz = building_package('Briz', briz)
    not_exist_wsks = building_package('wSKS', wsks)

    uploading_files(briz_url, epg_login, epg_password, 'Briz', bot)
    uploading_files(wsks_url, epg_login, epg_password, 'wSKS', bot)

    report_message(not_exist_briz, 'Бриз', bot, contacts)
    report_message(not_exist_wsks, 'wSKS', bot, contacts)
