from PIL import Image, ImageDraw, ImageFont
import numpy as np
import copy
# resize image
def resize(image : Image.Image, size : int):
    return image.resize((size, size), Image.Resampling.LANCZOS)

# paste avatar to template
def paste_avatar(template : Image.Image, avatar : Image.Image):
    template.paste(avatar, (46, 36), avatar)
    return template

# crop image to circle
def crop_image_circle(image : Image.Image):
    height,width = image.size
    if image.mode != 'RGB':
        image = image.convert('RGB')
    alpha = Image.new('L', image.size , 0)

    draw = ImageDraw.Draw(alpha)
    draw.pieslice(((0,0), (height,width)), 0, 360,
                fill = 255, outline = "white")

    img_arr =np.array(image)
    alpha_arr =np.array(alpha)
    final_img_arr = np.dstack((img_arr, alpha_arr))

    return Image.fromarray(final_img_arr)

# make round corners
def make_round_corners(image : Image.Image, radius : int):
    width, height = image.size
    if image.mode != 'RGB':
        image = image.convert('RGB')
    circle = Image.new('L', (radius * 2, radius * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, radius * 2, radius * 2), fill = 255)
    alpha = Image.new('L', image.size , 'white')
    alpha.paste(circle.crop((0, 0, radius, radius)), (0, 0))
    alpha.paste(circle.crop((0, radius, radius, radius * 2)), (0, height - radius))
    alpha.paste(circle.crop((radius, 0, radius * 2, radius)), (width - radius, 0))
    alpha.paste(circle.crop((radius, radius, radius * 2, radius * 2)), (width - radius, height - radius))
    image.putalpha(alpha)
    return image

# make round corners with circle png
def make_round_corners_circle(image : Image.Image, template : Image.Image):
    if image.mode != 'RGB':
        image = image.convert('RGB')
    template_arr = np.array(template)
    alpha = Image.new('L', image.size , 'white')
    circle = Image.fromarray(template_arr[:,:,1])
    radius = circle.width // 2
    width, height = image.size
    alpha.paste(circle.crop((0, 0, radius, radius)), (0, 0))
    alpha.paste(circle.crop((0, radius, radius, radius * 2)), (0, height - radius))
    alpha.paste(circle.crop((radius, 0, radius * 2, radius)), (width - radius, 0))
    alpha.paste(circle.crop((radius, radius, radius * 2, radius * 2)), (width - radius, height - radius))
    image.putalpha(alpha)
    return image

# get text dimensions
def get_text_dimensions(text_string : str, font : ImageFont.FreeTypeFont):
    # https://stackoverflow.com/a/46220683/9263761
    ascent, descent = font.getmetrics()

    text_width = font.getmask(text_string).getbbox()[2]
    text_height = font.getmask(text_string).getbbox()[3] + descent

    return (text_width, text_height)

# add text to picture
def add_text(image : Image.Image, nickname : str, level : int, role_name : str, exp : int, exp_next : int, fonts_path : str):
    current_font_size = 40
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(fonts_path + 'Rubik-Light.ttf', current_font_size)
    while (get_text_dimensions(nickname, font)[0] > 450):
        current_font_size -= 1
        font = ImageFont.truetype(fonts_path + 'Rubik-Light.ttf', current_font_size)
    draw.text((225, 33), f'{nickname}', (255, 255, 255), font=font, align='left')

    font = ImageFont.truetype(fonts_path + 'Rubik-Light.ttf', 23)
    draw.text((225, 138), f'LVL', (255, 255, 255), font=font, align='left')

    font = ImageFont.truetype(fonts_path + 'Rubik-Regular.ttf', 23)
    if level < 10:
        text = f'0{level} /'
    else:
        text = f'{level} /'
    draw.text((270, 138), text, (255, 255, 255), font=font, align='left')

    font = ImageFont.truetype(fonts_path + 'Rubik-Light.ttf', 23)
    draw.text((270+get_text_dimensions(text, font)[0]+10, 138), f'{role_name}', (255, 255, 255), font=font, align='left')
    draw.text((795, 138), 'XP', (255, 255, 255), font=font, align='right')

    distance = 7
    current_x = 785
    font = ImageFont.truetype(fonts_path + 'Rubik-Regular.ttf', 23)
    while 795-current_x-get_text_dimensions(f'{exp} / {exp_next}', font)[0] < distance:
        current_x -= 1
    draw.text((current_x, 138), f'{exp} / {exp_next}', (255, 255, 255), font=font, align='right')

    return image

def add_progress_bar(image : Image.Image, percentage : int, circle : Image.Image):
    if percentage <= 0:
        return image
    draw = ImageDraw.Draw(image)
    starting_x = 230
    starting_y = 105
    ending_x = int((824-starting_x)*percentage)+starting_x
    ending_y = starting_y + 20
    image.paste(circle, (starting_x-circle.width//2, starting_y), circle)
    draw.rectangle((starting_x, starting_y, ending_x, ending_y), fill=(255, 255, 255))
    image.paste(circle, (ending_x-circle.width//2, starting_y), circle)
    return image

def prepare_image(user_id : int, nickname : str, level : int, role_name : str, exp : int, exp_next : int, little_circle_template : Image.Image, big_circle_template : Image.Image, main_template : Image.Image, temp_folder_path : str, fonts_path : str):
    image = Image.open(f"{temp_folder_path}{user_id}_resized.png")
    template = main_template.copy()
    image_with_corners = make_round_corners_circle(image, little_circle_template)
    image_with_avatar = paste_avatar(template, image_with_corners)
    image_with_text = add_text(image_with_avatar, nickname, level, role_name, exp, exp_next, fonts_path)
    final = add_progress_bar(image_with_text, percentage=exp/exp_next, circle=big_circle_template)
    final.save(f'{temp_folder_path}{user_id}_ready.png')