from channels import briz, wsks
import os
from datetime import datetime
import shutil
import telebot
from telebot.apihelper import ApiTelegramException


def building_packages(work_directory, dst_folder, channel_list):
    """Сборка пакетов каналов."""
    not_exist_list = f'Следующие файлы для {dst_folder} отсутствуют:\n\n'

    files_for_remove = os.listdir(f'{work_directory}/{dst_folder}')
    for file in files_for_remove:
        try:
            os.remove(f'{work_directory}/Briz/{file}')
        except FileNotFoundError:
            pass

    current_date = str(datetime.utcnow().date())
    uploading_files = os.listdir(f'{work_directory}/{current_date}')

    for channel in channel_list:
        full_channel_name = channel.zfill(9) + '.xml'

        if full_channel_name in uploading_files:
            shutil.copy(
                f'{work_directory}/{current_date}/{full_channel_name}',
                f'{work_directory}/{dst_folder}/{full_channel_name}'
            )
        else:
            not_exist_list += full_channel_name

    return not_exist_list


if __name__ == '__main__':
    briz_doesnt_exist_files = building_packages(
        'epg_files', 'Briz', briz
    )
    wsks_doesnt_exist_files = building_packages(
        'epg_files', 'wSKS', wsks
    )

    bot = telebot.TeleBot('6401346922:AAGYIr7inOWVM3tL80UWuPC9aF9_gUl4Y0Y')
    contacts = {'Markarov': 67471266, 'Susylev': 192697803, 'Bufalov': 749444404}

    for name, chat_id in contacts.items():
        try:
            bot.send_message(chat_id, briz_doesnt_exist_files)
            bot.send_message(chat_id, wsks_doesnt_exist_files)
        except ApiTelegramException:
            bot.send_message(contacts['Markarov'], f'Данные контакту {name} не отправлены.')
