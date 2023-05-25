from flask import Flask, render_template, request, redirect, url_for, abort, send_from_directory
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import requests
import os
import base64

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024  # Лимит на размер загружаемых файлов (1 МБ)
UPLOAD_FOLDER = './uploads'  # Папка для загруженных файлов
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
RECAPTCHA_SITE_KEY = '6LcsDD0mAAAAABBTVNKqdZPgVLFGSK_Jrt9HxbgJ'


# Маршрут для поворота изображения
@app.route('/rotate', methods=['POST'])
def rotate():
    # Получаем загруженный файл и угол поворота из запроса
    file = request.files.get('file')
    angle = float(request.form.get('angle'))

    # Проверяем, загружен ли файл
    if not file:
        abort(400, 'Файл не был загружен')

    # Проверяем, является ли загруженный файл изображением
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        abort(400, 'Файл не является изображением')

    # Проверяем верификацию reCAPTCHA
    recaptcha_response = request.form.get('g-recaptcha-response')
    if not recaptcha_response:
        abort(400, 'Проверка reCAPTCHA не пройдена')
    payload = {
        'secret': '6LcsDD0mAAAAALXBYTwlLEnfjejQYTID4E3sINKe',
        'response': recaptcha_response
    }
    response = requests.post('https://www.google.com/recaptcha/api/siteverify', payload).json()
    if not response['success']:
        abort(400, 'Проверка reCAPTCHA не пройдена')

    # Загружаем изображение и применяем поворот
    img = Image.open(file)
    rotated_img = img.rotate(angle)

    # Вычисляем распределение цветов исходного и повернутого изображений
    orig_colors = get_color_distribution(img)
    rotated_colors = get_color_distribution(rotated_img)

    # Создаем графики распределения цветов
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    fig.suptitle('Распределение цветов')
    ax1.bar(np.arange(len(orig_colors)), [c[0] / 255 for c in orig_colors], color=[tuple(np.array(c[1]) / 255) for c in orig_colors])
    ax1.set_xticks(np.arange(len(orig_colors)))
    ax1.set_xticklabels([c[1] for c in orig_colors], rotation=45)
    ax1.set_title('Исходное изображение')
    ax2.bar(np.arange(len(rotated_colors)), [c[0] / 255 for c in rotated_colors], color=[tuple(np.array(c[1]) / 255) for c in rotated_colors])
    ax2.set_xticks(np.arange(len(rotated_colors)))
    ax2.set_xticklabels([c[1] for c in rotated_colors], rotation=45)
    ax2.set_title('Повернутое изображение')
    plt.tight_layout()

    # Сохраняем графики в файл
    plot_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'plot.png')
    plt.savefig(plot_filename)

    # Сохраняем повернутое изображение в файл
    rotated_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'rotated.png')
    rotated_img.save(rotated_filename)

    # Сохраняем исходное изображение в файл
    orig_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'orig.png')
    img.save(orig_filename)

    # Отображаем страницу с результатами
    result_filename = os.path.basename(plot_filename)  # Получаем только имя файла из пути
    with open(plot_filename, 'rb') as f:
        plot_bytes = f.read()

    # Кодируем график в формат base64 для отображения на HTML-странице
    plot_base64 = base64.b64encode(plot_bytes).decode('utf-8')

    return render_template('result.html', orig=orig_filename, plot=plot_base64, result_filename=result_filename)


# Главная страница
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', sitekey=RECAPTCHA_SITE_KEY)


# Вспомогательная функция для получения распределения цветов изображения
def get_color_distribution(img):
    colors = img.getcolors(img.size[0] * img.size[1])
    return sorted(colors, key=lambda x: x[0], reverse=True)[:10]


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.config['UPLOAD_FOLDER'] = 'uploads'
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
