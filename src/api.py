import config
import smarty
import json
import remap
import httplib2
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import datetime
from converter import number_to_string
import os


def find_name_index(name: str, array: list[str]):
    for value in array:
        if value and value[0].strip() == name:
            return array.index(value) + 1


def recognize(file_name) -> list:
    body = {
        "url": f"https://smarty.mail.ru/api/v1/persons/recognize?oauth_provider=mcs&oauth_token={config.TOKEN}",
        "path": file_name,
        "meta": {
            "space": "1",
            "create_new": False,
        },
        "verbose": True,
        "timeout": 60,
    }

    try:
        response = json.loads(smarty.vk_api(body))
    except json.JSONDecodeError as e:
        raise ValueError(f"Невалидный JSON ответ от VK API: {e}")
    
    if response.get("status") != 200:
        raise ValueError(f"Ошибка VK API: status {response.get('status', 'unknown')}")
    
    body_data = response.get("body", {})
    objects = body_data.get("objects", [])
    
    if not objects:
        raise ValueError("Пустой массив objects в ответе VK API")
    
    first_object = objects[0]
    
    if first_object.get("status") != 0:
        raise ValueError(f"Ошибка обработки файла: status {first_object.get('status')}")
    
    persons = first_object.get("persons", [])
    spirits = []
    for person in persons:
        spirits.append({
            'person': remap.tag_to_name[person["tag"]],
            'coord': person["coord"]
        })

    return spirits


def set(id, file_name):
    body = {
        "url": f"https://smarty.mail.ru/api/v1/persons/set?oauth_provider=mcs&oauth_token={config.TOKEN}",
        "path": file_name,
        "meta": {
            "space": "1",
            "images": [{"person_id": id}],
        },
        "verbose": True,
        "timeout": 60,
    }

    response = json.loads(smarty.vk_api(body))
    return response


def delete(ids):
    images = list(map(lambda id: {"name": f"person{id}", "person_id": id}, ids))
    print(images)
    body = {
        "url": f"https://smarty.mail.ru/api/v1/persons/delete?oauth_provider=mcs&oauth_token={config.TOKEN}",
        "meta": {
            "space": "1",
            "images": images,
        },
        "verbose": True,
        "timeout": 60,
    }

    response = json.loads(smarty.vk_api(body))
    return response


def mark_visit(photo_path, date=None):
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        config.CREDENTIALS_FILE,
        ['https://www.googleapis.com/auth/spreadsheets',
         'https://www.googleapis.com/auth/drive'])
    http_auth = credentials.authorize(httplib2.Http())
    service = build('sheets', 'v4', http=http_auth)
    values = service.spreadsheets().values().get(
        spreadsheetId=config.spreadsheet_id,
        range=f"{config.spreadsheet_list}!{config.spreadsheet_range}",
        majorDimension='ROWS'
    ).execute()['values']

    if not date:
        if os.name == 'nt':
            date = datetime.datetime.now().strftime("%#d-%b-%Y")
        else:
            date = datetime.datetime.now().strftime("-%d-%b-%Y")

    column = number_to_string(values[1].index(date) + 2)

    records = list()
    persons = recognize(photo_path)
    for person in persons:
        person = person["person"]
        if person == 'UNDEFINED':
            continue
        row = str(find_name_index(person, values))
        if row == 'None':
            raise Exception(f"{person} not found")
        records.append({
            "range": f"{config.spreadsheet_list}!" + column + row,
            "majorDimension": "ROWS",
            "values": [[1]],
        })

    service.spreadsheets().values().batchUpdate(
        spreadsheetId=config.spreadsheet_id,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": records
        }
    ).execute()
    return persons
