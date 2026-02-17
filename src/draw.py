from PIL import Image, ImageDraw, ImageFont


def draw_border_on_faces(persons, photo_path):
    print(photo_path)
    image = Image.open(photo_path)
    draw = ImageDraw.Draw(image)
    width, height = image.size
    font_size = int(width / 70)

    file_path = "../src/fonts/Roboto-Regular.ttf"

    font = ImageFont.truetype(file_path, font_size, encoding='UTF-8')
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
        stroke_width = 3

        bbox = draw.textbbox((x, y), person_name, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        draw.rectangle(
            [(x - stroke_width, y - stroke_width), (x + text_width + stroke_width, y + text_height + stroke_width)],
            fill="black"
        )

        draw.text((x, y), person_name, font=font, fill=fill_color)
    ext = photo_path.split('.')[-1].lower()
    output_path = f"./new_photo.{ext}"
    image.save(output_path)
    return output_path

