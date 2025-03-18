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


def find_name_index(name, array):
    for value in array:
        if value and value[0] == name:
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

    response = json.loads(smarty.vk_api(body))
    persons = response["body"]["objects"][0]["persons"]
    spirits = list()
    for person in persons:
        spirits.append(
            {
                'person': remap.tag_to_name[person["tag"]],
                'coord': person["coord"]
            }
        )
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


def mark_visit(date=None):
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
    persons = recognize("../photo.jpg")
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
