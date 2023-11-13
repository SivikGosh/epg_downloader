import os
from datetime import datetime
from ftplib import FTP


def download(source, login, password):
    """загрузка всех файлов в папку с текущей датой в общей папке EPG файлов"""
    connection = FTP(source)
    connection.login(login, password)
    files = connection.nlst()
    date_today = str(datetime.today().date())

    if not os.path.exists(f'epg_files/{date_today}'):
        os.makedirs(f'epg_files/{date_today}')

    for file in files:
        with open(f'epg_files/{date_today}/{file}', 'wb') as f:
            connection.retrbinary(f'RETR {file}', f.write)

    connection.quit()


def test():
    """функция для тестирования"""
    pass


if __name__ == '__main__':
    download('ftp.epgservice.ru', 'infokos', '6KVy76MY')
