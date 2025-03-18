from PIL import Image, ImageDraw, ImageFont


def draw_border_on_faces(persons):
    image = Image.open("../photo.jpg")
    draw = ImageDraw.Draw(image)
    width, height = image.size
    font_size = int(width / 80)
    font = ImageFont.truetype("/home/bogdan.krasilnikov/projects/healthy-spirit/src/fonts/Roboto-Regular.ttf", font_size, encoding='UTF-8')
    for person in persons:
        if person["person"] == "UNDEFINED":
            color = 'red'
            person_name = person["person"]
        else:
            color = 'green'
            person_full_name = person["person"].split(' ')
            person_name = person_full_name[1]
        draw.rectangle(person["coord"], outline=color, width=max(1, int(width / 400)))

        x = person["coord"][0] - 5
        y = person["coord"][3]

        fill_color = "white"
        stroke_color = "black"
        stroke_width = 3

        draw.text((x - stroke_width, y - stroke_width), person_name, font=font, fill=stroke_color)
        draw.text((x + stroke_width, y - stroke_width), person_name, font=font, fill=stroke_color)
        draw.text((x - stroke_width, y + stroke_width), person_name, font=font, fill=stroke_color)
        draw.text((x + stroke_width, y + stroke_width), person_name, font=font, fill=stroke_color)

        draw.text((x, y), person_name, font=font, fill=fill_color)
    image.save("../new_photo.jpg")
