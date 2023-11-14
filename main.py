import os
from datetime import datetime
from ftplib import FTP

from dotenv import load_dotenv

load_dotenv()


def download(source: str, login: str, password: str) -> None:
    """Загрузка всех файлов в папку с текущей датой."""

    cur_date = str(datetime.today().date())

    connection = FTP(source)
    connection.login(login, password)
    files = connection.nlst()

    os.makedirs(f'epg_files/{cur_date}')

    for file in files:
        with open(f'epg_files/{cur_date}/{file}', 'wb') as f:
            connection.retrbinary(f'RETR {file}', f.write)

    connection.quit()


if __name__ == '__main__':
    url, user, passwrd = os.getenv('SOURCE'), os.getenv('LOGIN'), os.getenv('PASSWORD')

    download(source=url, login=user, password=passwrd)
