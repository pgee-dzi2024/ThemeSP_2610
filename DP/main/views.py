from django.shortcuts import render
import io
from PIL import Image
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status

# Импортираме функциите, които създадохме в Етап 2
from .image_processor import *

class ImageBatchProcessView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        files = request.FILES.getlist('images')

        if not files:
            return Response({"error": "Не са прикачени изображения."}, status=status.HTTP_400_BAD_REQUEST)

        # Четем новите настройки
        resize_mode = request.data.get('resize_mode', 'fit')
        watermark_type = request.data.get('watermark_type', 'none')  # 'none', 'text', 'logo'
        watermark_text = request.data.get('watermark_text', '')
        watermark_logo = request.FILES.get('watermark_logo')  # Вземаме файла за логото
        watermark_position = request.data.get('watermark_position', 'bottom-right')

        # НОВО: Взимаме прозрачността в проценти (по подразбиране 50%)
        opacity_percent = int(request.data.get('watermark_opacity', 50))
        # Конвертираме процентите (0-100) в 8-битова стойност за алфа канала (0-255)
        opacity_value = int((opacity_percent / 100) * 255)

        processed_files = []
        errors = []

        for file_obj in files:
            is_valid, msg = validate_image(file_obj)
            if not is_valid:
                errors.append({"file": file_obj.name, "error": msg})
                continue

            try:
                file_obj.seek(0)
                img = Image.open(file_obj)

                # Оразмеряване
                img = resize_to_fhd(img, mode=resize_mode)

                # Добавяне на воден знак според избрания тип
                if watermark_type == 'text' and watermark_text:
                    img = add_text_watermark(img, text=watermark_text, position=watermark_position, opacity=opacity_value)
                elif watermark_type == 'logo' and watermark_logo:
                    watermark_logo.seek(0)
                    img = add_logo_watermark(img, logo_file=watermark_logo, position=watermark_position, opacity=opacity_value)
                    
                img_io = io.BytesIO()
                ext = file_obj.name.split('.')[-1].lower()
                save_format = 'PNG' if ext == 'png' else 'JPEG'

                if save_format == 'JPEG' and img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                img.save(img_io, format=save_format, quality=85)

                processed_files.append({
                    'name': f"processed_{file_obj.name}",
                    'content': img_io
                })

            except Exception as e:
                errors.append({"file": file_obj.name, "error": str(e)})

        if not processed_files:
            return Response({"error": "Нито един файл не беше обработен.", "details": errors}, status=400)

        zip_buffer = create_zip_archive(processed_files)
        response = HttpResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="batch_processed_images.zip"'
        return response

def index(request):
    return render(request, 'main/index.html')
