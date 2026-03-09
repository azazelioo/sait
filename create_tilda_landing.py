#!/usr/bin/env python3
"""
Скрипт для создания 5-блочного лендинга на Tilda
Курс: "Магия женского мира: ведьмин клубок и инициация"
Папка: Светлана Комарова
URL: magic
"""

import asyncio
import os
import sys
import time
from pathlib import Path

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
except ImportError:
    print("Playwright не установлен. Устанавливаем...")
    os.system("pip install playwright")
    os.system("playwright install chromium")
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Конфигурация
TILDA_LOGIN = "Benedictuminfo@yandex.ru"
TILDA_PASSWORD = "HisJY25x6x&iZq4"
TARGET_FOLDER = "Светлана Комарова"
PAGE_URL = "magic"
IMAGES_DIR = Path(__file__).parent / "extracted_images" / "word" / "media"

# Содержимое лендинга
LANDING_CONTENT = {
    "title": "Магия женского мира: ведьмин клубок и инициация",
    "subtitle": "Двухнедельное погружение в алгоритмы женской инициации через призму русских сказок",
    "start_date": "Старт 23 марта",
    "about": """Женская инициация в сказках — обязательный этап, превращающий девушку в женщину, способную управлять своей жизнью.

Переход происходит по трёхчастной модели: отделение → трансформация → возвращение.

Остановка на любом этапе создаёт замороженный сценарий.""",
    "symptoms": [
        "Точка изгнания — потеря привычных социальных ролей воспринимается как катастрофа",
        "Застрявшая в «тёмном лесу» — неспособность распознать проводников и важные знаки",
        "Потеря нити — отсутствие внутреннего компаса (клубок и зеркало для правды)",
        "Отказ от короны — страх взять ответственность Принцессы или мудрость Хранительницы",
    ],
    "week1": [
        {"date": "23 марта", "title": "Модель инициации", "desc": "Три стадии: отделение, трансформация, возвращение"},
        {"date": "25 марта", "title": "Архетипы и символы", "desc": "Роль Бабы-яги и сакральные инструменты: клубок, зеркало, прялка, ключ, вода"},
        {"date": "27 марта", "title": "Итоги перехода", "desc": "Маркеры зрелости и критерии нового статуса"},
    ],
    "week2": [
        {"date": "31 марта", "title": "Повторение как проверка", "desc": "Механизм подтверждения зрелости через паттерны"},
        {"date": "2 апреля", "title": "Законы обмена", "desc": "Личное счастье через служение и баланс «брать» и «давать»"},
        {"date": "3 апреля", "title": "Спецэфир", "desc": "Только для Внутреннего и Частного кругов. Александра Демьяненко — ведьмина инициация или бытовая магия"},
    ],
    "speakers": [
        {
            "name": "Светлана Комарова",
            "role": "Бизнес-психолог, автор книги «Бизнес ведьмы», основатель Академии Benedictum",
            "image": str(IMAGES_DIR / "image1.png"),
        },
        {
            "name": "Елена Соломина",
            "role": "Член ОППЛ, специалист по глубинной групповой психологии, эксперт по влиянию сказок на жизнь",
            "image": str(IMAGES_DIR / "image3.png"),
        },
        {
            "name": "Александра Демьяненко",
            "role": "Эксперт по русскому фольклору и мифологии, психолог",
            "image": str(IMAGES_DIR / "image4.png"),
        },
    ],
    "tariffs": [
        {
            "name": "Внешний круг",
            "price": "14 700 ₽",
            "early_price": "13 300 ₽",
            "features": ["Доступ к вебинарам как слушатель"],
        },
        {
            "name": "Внутренний круг",
            "price": "21 100 ₽",
            "early_price": "18 800 ₽",
            "features": [
                "Интерактивная работа с обратной связью",
                "Онлайн-встречи",
                "Эксклюзивный эфир Демьяненко о бытовой магии",
            ],
        },
        {
            "name": "Частный круг",
            "price": "33 300 ₽",
            "early_price": "30 300 ₽",
            "features": [
                "Максимальная плотность работы",
                "Индивидуальный разбор",
                "Всё из Внутреннего круга",
                "Закрытая групповая консультация со спикерами (до 10 человек)",
            ],
        },
    ],
}


async def wait_and_click(page, selector, timeout=15000):
    """Ждёт элемент и кликает по нему"""
    await page.wait_for_selector(selector, timeout=timeout)
    await page.click(selector)


async def login_to_tilda(page):
    """Вход в Tilda"""
    print("Открываем страницу входа...")
    await page.goto("https://tilda.cc/login/", wait_until="networkidle")
    await page.wait_for_timeout(2000)

    print("Вводим логин и пароль...")
    # Ищем поля ввода
    await page.fill('input[name="email"], input[type="email"], #email', TILDA_LOGIN)
    await page.fill('input[name="password"], input[type="password"], #password', TILDA_PASSWORD)

    # Кликаем кнопку входа
    await page.click('button[type="submit"], input[type="submit"], .js-form-submit, [data-form-submit]')

    await page.wait_for_load_state("networkidle")
    await page.wait_for_timeout(3000)

    current_url = page.url
    print(f"После входа URL: {current_url}")

    if "login" in current_url:
        raise Exception("Вход не выполнен — возможно неверные данные")

    print("Вход выполнен успешно!")


async def find_svetlana_folder(page):
    """Находим папку Светлана Комарова и получаем project_id"""
    print("Ищем папку 'Светлана Комарова'...")

    # Переходим на главную страницу проектов
    await page.goto("https://tilda.cc/projects/", wait_until="networkidle")
    await page.wait_for_timeout(3000)

    # Ищем папку по тексту
    folder_link = page.locator(f'text="{TARGET_FOLDER}"').first
    if not await folder_link.is_visible():
        # Пробуем другие варианты поиска
        folder_link = page.locator(f':text("{TARGET_FOLDER}")').first

    if await folder_link.is_visible():
        print(f"Папка '{TARGET_FOLDER}' найдена, кликаем...")
        await folder_link.click()
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(2000)
        project_url = page.url
        print(f"URL проекта: {project_url}")
        return project_url
    else:
        # Делаем скриншот для диагностики
        await page.screenshot(path="/tmp/tilda_projects.png")
        print("Сохранён скриншот: /tmp/tilda_projects.png")
        raise Exception(f"Папка '{TARGET_FOLDER}' не найдена")


async def get_font_from_existing_page(page, project_url):
    """Получаем шрифт из существующих лендингов (не из 'Другая')"""
    print("Определяем шрифт из существующих лендингов...")

    # Переходим обратно к проектам и ищем другой проект (не Другая) для получения шрифта
    await page.goto("https://tilda.cc/projects/", wait_until="networkidle")
    await page.wait_for_timeout(2000)

    # Ищем все проекты кроме "Другая"
    projects = await page.query_selector_all(".projects-list__item, .project-card, [data-project]")

    font_name = None
    for project in projects:
        project_text = await project.inner_text()
        if "Другая" not in project_text and TARGET_FOLDER in project_text:
            # Это наш проект, попробуем найти шрифт в его настройках
            pass

    # Возвращаем шрифт по умолчанию для аккаунта (Histori Pro указан в документе)
    # Но Роман сказал брать с других лендов - попробуем через API
    return font_name


async def find_project_id_from_url(page):
    """Извлекаем ID проекта из URL"""
    current_url = page.url
    # URL вида: https://tilda.cc/projects/?projectid=12345
    if "projectid=" in current_url:
        return current_url.split("projectid=")[1].split("&")[0]
    return None


async def create_new_page_via_ui(page, project_url):
    """Создаём новую страницу через UI Tilda"""
    print("Создаём новую страницу...")

    # Переходим в проект
    await page.goto(project_url, wait_until="networkidle")
    await page.wait_for_timeout(3000)

    await page.screenshot(path="/tmp/tilda_project.png")
    print("Скриншот проекта: /tmp/tilda_project.png")

    # Ищем кнопку создания страницы
    add_page_selectors = [
        "text=Добавить страницу",
        "text=Add page",
        ".js-add-page",
        "[data-add-page]",
        ".addpage-btn",
        "button:has-text('+')",
    ]

    clicked = False
    for selector in add_page_selectors:
        try:
            if await page.is_visible(selector, timeout=3000):
                await page.click(selector)
                clicked = True
                break
        except Exception:
            continue

    if not clicked:
        await page.screenshot(path="/tmp/tilda_no_add_btn.png")
        raise Exception("Не нашли кнопку добавления страницы")

    await page.wait_for_timeout(3000)
    await page.screenshot(path="/tmp/tilda_add_page_dialog.png")

    return True


async def configure_page_settings(page):
    """Настройка параметров новой страницы"""
    print("Настраиваем параметры страницы...")

    # Ищем поле для имени страницы
    name_selectors = [
        'input[name="title"]',
        'input[placeholder*="название"]',
        'input[placeholder*="title"]',
        '#page-title',
    ]

    for selector in name_selectors:
        try:
            if await page.is_visible(selector, timeout=3000):
                await page.fill(selector, LANDING_CONTENT["title"])
                break
        except Exception:
            continue

    # Ищем поле URL
    url_selectors = [
        'input[name="alias"]',
        'input[name="url"]',
        'input[placeholder*="url"]',
        'input[placeholder*="URL"]',
        '#page-alias',
    ]

    for selector in url_selectors:
        try:
            if await page.is_visible(selector, timeout=3000):
                await page.fill(selector, PAGE_URL)
                break
        except Exception:
            continue

    await page.wait_for_timeout(1000)


async def use_tilda_api(page):
    """Используем Tilda API для получения информации о проекте"""
    print("Получаем данные через Tilda API...")

    # Сначала нужно получить API ключи из настроек аккаунта
    await page.goto("https://tilda.cc/account/", wait_until="networkidle")
    await page.wait_for_timeout(2000)

    await page.screenshot(path="/tmp/tilda_account.png")

    # Ищем API ключи
    api_content = await page.content()

    public_key = None
    secret_key = None

    # Пробуем найти API ключи на странице
    if "publickey" in api_content.lower() or "api" in api_content.lower():
        print("Найдена информация об API ключах")

    return public_key, secret_key


async def create_landing_via_api(public_key, secret_key, project_id):
    """Создаём лендинг через Tilda API"""
    import urllib.request
    import json

    base_url = "https://api.tildacdn.com/v1/"

    # Получаем список страниц проекта
    url = f"{base_url}getpageslist/?publickey={public_key}&secretkey={secret_key}&projectid={project_id}"

    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read())

    print(f"Список страниц: {data}")
    return data


async def build_landing_blocks(page):
    """Строим блоки лендинга через редактор Tilda"""
    print("Строим блоки лендинга...")

    # Это сложная часть — нужно взаимодействовать с редактором блоков Tilda
    # Сначала делаем скриншот текущего состояния
    await page.screenshot(path="/tmp/tilda_editor.png")
    print("Скриншот редактора: /tmp/tilda_editor.png")

    # Tilda Zero Block позволяет добавить HTML напрямую
    # Это самый надёжный способ добавить кастомный контент

    # Ищем кнопку добавления блока
    add_block_selectors = [
        "text=Добавить блок",
        "text=Add block",
        ".js-addblock-btn",
        ".addblock-btn",
    ]

    for selector in add_block_selectors:
        try:
            if await page.is_visible(selector, timeout=5000):
                await page.click(selector)
                break
        except Exception:
            continue

    await page.wait_for_timeout(2000)


async def main():
    """Основная функция"""
    print("=" * 60)
    print("Создание лендинга 'Магия женского мира' на Tilda")
    print("=" * 60)

    # Проверяем наличие изображений
    for i in range(1, 5):
        img_path = IMAGES_DIR / f"image{i}.png"
        if img_path.exists():
            print(f"✓ image{i}.png ({img_path.stat().st_size // 1024} KB)")
        else:
            print(f"✗ image{i}.png НЕ НАЙДЕН")

    async with async_playwright() as p:
        # Запускаем браузер
        browser = await p.chromium.launch(
            headless=False,  # Показываем браузер для отладки
            slow_mo=500,  # Замедляем для надёжности
        )

        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="ru-RU",
        )

        page = await context.new_page()

        try:
            # Шаг 1: Вход в Tilda
            await login_to_tilda(page)

            # Шаг 2: Находим папку Светлана Комарова
            project_url = await find_svetlana_folder(page)

            # Получаем project_id
            project_id = await find_project_id_from_url(page)
            print(f"Project ID: {project_id}")

            # Шаг 3: Создаём новую страницу
            await create_new_page_via_ui(page, project_url)

            # Шаг 4: Настраиваем параметры
            await configure_page_settings(page)

            # Ждём чтобы пользователь мог видеть результат
            await page.wait_for_timeout(5000)

            print("\n✓ Скрипт завершён. Проверьте браузер.")
            print(f"Скриншоты сохранены в /tmp/tilda_*.png")

        except Exception as e:
            print(f"\n✗ Ошибка: {e}")
            await page.screenshot(path="/tmp/tilda_error.png")
            print("Скриншот ошибки: /tmp/tilda_error.png")
            raise
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
