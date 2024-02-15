from PIL import Image, ImageDraw, ImageFont


def draw_border_on_faces(persons):
    image = Image.open("../photo.jpg")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("Roboto-Regular.ttf", 10, encoding='UTF-8')
    for person in persons:
        if person["person"] == "UNDEFINED":
            color = 'red'
            person_name = person["person"]
        else:
            color = 'green'
            person_full_name = person["person"].split(' ')
            person_name = person_full_name[0] + ' ' + person_full_name[1]
        draw.rectangle(person["coord"], outline=color, width=3)
        draw.text((person["coord"][0] - 5, person["coord"][3]), person_name, font=font)
    image.save("../new_photo.jpg")
