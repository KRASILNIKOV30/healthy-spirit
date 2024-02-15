import config
import smarty
import json
import remap


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
    return list(map(lambda person: remap.tag_to_name[person["tag"]], persons))


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
