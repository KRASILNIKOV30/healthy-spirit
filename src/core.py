import remap


def has_healthy_spirit(google_cell, healthy_spirit_list):
    return remap.google_cell_to_name[google_cell] in healthy_spirit_list


healthy_spirit_list = ['maxim_nazarov', 'yuliana_zhulitova', 'bogdan_krasilnikov', 'nikolay_kozlov', 'alisa_baryakina',
                       'danil_isupov', 'elisey_karamyshev', 'ilya_lezhnin', 'UNDEFINED', 'vladislav_pogorelov',
                       'ekaterina_rubtsova', 'maria_baranova', 'dmitriy_rybakov']

print(has_healthy_spirit('Погребникова Дарья Константиновна', healthy_spirit_list))
