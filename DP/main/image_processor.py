import io
import zipfile
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageOps


def validate_image(file_obj):
    """
    Проверява дали файлът е валиден JPG/PNG и дали не е повреден.
    """
    valid_extensions = ['jpg', 'jpeg', 'png']
    ext = file_obj.name.split('.')[-1].lower()

    if ext not in valid_extensions:
        return False, f"Неподдържан формат: {ext}. Разрешени са само JPG и PNG."

    try:
        # Отваряме файла и използваме verify() за проверка на целостта
        img = Image.open(file_obj)
        img.verify()
        return True, "OK"
    except Exception:
        return False, "Файлът е повреден или не е валидно изображение."


def resize_to_fhd(img, mode='fit'):
    """
    Оразмерява изображението до Full HD (1920x1080).
    mode: 'fit' (вписване), 'pad' (вписване с фон), 'crop' (изрязване)
    """
    target_size = (1920, 1080)

    # Конвертираме към RGB, ако изображението има алфа канал и искаме да го запазим като JPG
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    if mode == 'fit':
        return ImageOps.contain(img, target_size)
    elif mode == 'pad':
        return ImageOps.pad(img, target_size, color=(255, 255, 255))  # Бял фон при допълване
    elif mode == 'crop':
        return ImageOps.fit(img, target_size)

    return img


def add_text_watermark(img, text, position='bottom-right', opacity=128):
    """
    Добавя текстов воден знак с определена прозрачност.
    """
    # Създаваме прозрачно изображение със същия размер
    watermark = Image.new("RGBA", img.size)
    draw = ImageDraw.Draw(watermark)

    # В реалния проект тук ще заредим .ttf файл (напр. ImageFont.truetype('arial.ttf', 40))
    # За теста ползваме базовия шрифт
    font = ImageFont.load_default()

    # Вземаме размерите на текста (в по-новите версии на Pillow се ползва textbbox)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    padding = 20
    x, y = 0, 0

    if position == 'bottom-right':
        x = img.width - text_width - padding
        y = img.height - text_height - padding
    elif position == 'center':
        x = (img.width - text_width) // 2
        y = (img.height - text_height) // 2
    # Могат да се добавят и други позиции (top-left и т.н.)

    # Рисуваме текста (бял цвят с избраната прозрачност 0-255)
    draw.text((x, y), text, font=font, fill=(255, 255, 255, opacity))

    # Слепваме оригиналното изображение с водния знак
    img = img.convert("RGBA")
    return Image.alpha_composite(img, watermark)


def create_zip_archive(processed_files):
    """
    Създава ZIP архив в паметта от списък с обработени файлове.
    processed_files е списък от речници: [{'name': 'image1.jpg', 'content': bytes_obj}, ...]
    """
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for f in processed_files:
            zip_file.writestr(f['name'], f['content'].getvalue())

    zip_buffer.seek(0)
    return zip_buffer


def add_logo_watermark(img, logo_file, position='bottom-right', opacity=255, scale=0.15):
    """
    Добавя изображение (лого) като воден знак върху основното изображение.
    scale: каква част от ширината на основното изображение да заема логото (по подразбиране 15%).
    """
    try:
        # Отваряме логото и го конвертираме в RGBA (за да пазим прозрачността/алфа канала)
        logo = Image.open(logo_file).convert("RGBA")

        # Изчисляваме новия размер на логото спрямо основното изображение
        target_width = int(img.width * scale)
        ratio = target_width / logo.width
        target_height = int(logo.height * ratio)

        # Оразмеряваме логото (използваме LANCZOS за високо качество)
        logo = logo.resize((target_width, target_height), Image.Resampling.LANCZOS)

        # Промяна на прозрачността на логото (ако е зададена < 255)
        if opacity < 255:
            alpha = logo.split()[3]
            alpha = ImageEnhance.Brightness(alpha).enhance(opacity / 255.0)
            logo.putalpha(alpha)

        # Подготвяме прозрачен слой със същия размер като основното изображение
        watermark_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))

        padding = 20
        x, y = 0, 0

        # Изчисляваме координатите според позицията
        if position == 'bottom-right':
            x = img.width - logo.width - padding
            y = img.height - logo.height - padding
        elif position == 'center':
            x = (img.width - logo.width) // 2
            y = (img.height - logo.height) // 2
        elif position == 'top-left':
            x = padding
            y = padding

        # Поставяме логото върху прозрачния слой
        watermark_layer.paste(logo, (x, y), logo)

        # Слепваме основното изображение с водния знак
        img = img.convert("RGBA")
        return Image.alpha_composite(img, watermark_layer)
    except Exception as e:
        print(f"Грешка при добавяне на лого: {e}")
        return img  # Връщаме оригиналното изображение, ако има проблем с логото