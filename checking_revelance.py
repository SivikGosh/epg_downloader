import os
from datetime import datetime
from xml.etree import ElementTree


def date_checking(work_directory):
    """функция для тестирования"""
    current_date = datetime.utcnow().date()
    files_list = os.listdir(f'{work_directory}/{current_date}')

    for file in files_list:
        if file != 'TV_Pack.xml':
            tree = ElementTree.parse(f'{work_directory}/{current_date}/{file}')
            service = tree.find('service')
            last_event = service.findall('event')[-1].attrib['start-time']
            last_event_date = datetime.strptime(last_event, '%Y-%m-%d %H:%M').date()

            if last_event_date < current_date:
                os.remove(f'{work_directory}/{current_date}/{file}')
                print(f'файл {file} устарел.')


if __name__ == '__main__':
    date_checking('epg_files')
