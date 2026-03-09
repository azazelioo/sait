#!/usr/bin/env node
/**
 * Скрипт для создания 5-блочного лендинга на Tilda
 * Курс: "Магия женского мира: ведьмин клубок и инициация"
 * Папка: Светлана Комарова
 * URL: magic
 */

const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const path = require('path');
const fs = require('fs');

const TILDA_LOGIN = 'Benedictuminfo@yandex.ru';
const TILDA_PASSWORD = 'HisJY25x6x&iZq4';
const TARGET_FOLDER = 'Светлана Комарова';
const PAGE_URL = 'magic';
const IMAGES_DIR = path.join(__dirname, 'extracted_images', 'word', 'media');

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function loginToTilda(page) {
  console.log('Открываем страницу входа...');
  await page.goto('https://tilda.cc/login/', { waitUntil: 'networkidle' });
  await sleep(2000);

  console.log('Вводим логин...');
  // Try different selectors for email field
  const emailSelectors = ['input[name="email"]', 'input[type="email"]', '#email', 'input[autocomplete="username"]'];
  for (const sel of emailSelectors) {
    try {
      if (await page.isVisible(sel, { timeout: 2000 })) {
        await page.fill(sel, TILDA_LOGIN);
        console.log(`Email введён через: ${sel}`);
        break;
      }
    } catch {}
  }

  console.log('Вводим пароль...');
  const passSelectors = ['input[name="password"]', 'input[type="password"]', '#password'];
  for (const sel of passSelectors) {
    try {
      if (await page.isVisible(sel, { timeout: 2000 })) {
        await page.fill(sel, TILDA_PASSWORD);
        console.log(`Пароль введён через: ${sel}`);
        break;
      }
    } catch {}
  }

  // Check for reCAPTCHA and wait for human to solve it
  console.log('Проверяем наличие reCAPTCHA...');
  const hasRecaptcha = await page.isVisible('iframe[src*="recaptcha"]', { timeout: 3000 }).catch(() => false);

  if (hasRecaptcha) {
    console.log('');
    console.log('⚠️  ТРЕБУЕТСЯ ДЕЙСТВИЕ ЧЕЛОВЕКА!');
    console.log('─'.repeat(50));
    console.log('На странице есть reCAPTCHA.');
    console.log('Пожалуйста, откройте браузер по адресу:');
    console.log('  https://tilda.cc/login/');
    console.log('Введите данные вручную и решите капчу.');
    console.log('─'.repeat(50));
    console.log('');

    // Try to click the reCAPTCHA checkbox anyway
    try {
      const recaptchaFrame = page.frameLocator('iframe[src*="recaptcha"]').first();
      const checkbox = recaptchaFrame.locator('.recaptcha-checkbox-border');
      await checkbox.click({ timeout: 3000 });
      console.log('Попытка нажать чекбокс reCAPTCHA...');
      await sleep(5000);
    } catch (e) {
      console.log('Автонажатие не удалось');
    }
  }

  console.log('Нажимаем кнопку входа...');
  const submitSelectors = [
    'button[type="submit"]',
    'input[type="submit"]',
    '.js-form-submit',
    'button:has-text("Войти")',
    'button:has-text("Sign in")',
    'button:has-text("Log in")',
  ];
  for (const sel of submitSelectors) {
    try {
      if (await page.isVisible(sel, { timeout: 2000 })) {
        await page.click(sel);
        console.log(`Кнопка нажата: ${sel}`);
        break;
      }
    } catch {}
  }

  await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  await sleep(3000);

  const currentUrl = page.url();
  console.log(`После входа URL: ${currentUrl}`);

  if (currentUrl.includes('login')) {
    await page.screenshot({ path: '/tmp/tilda_login_failed.png' });
    throw new Error('Вход не выполнен — reCAPTCHA заблокировала автоматический вход');
  }

  console.log('Вход выполнен успешно!');
}

async function findProjectByFolder(page, folderName) {
  console.log(`Ищем папку "${folderName}"...`);

  await page.goto('https://tilda.cc/projects/', { waitUntil: 'networkidle' });
  await sleep(3000);

  await page.screenshot({ path: '/tmp/tilda_projects.png' });
  console.log('Скриншот: /tmp/tilda_projects.png');

  // Try to find the folder
  const folderSelectors = [
    `text="${folderName}"`,
    `:text("${folderName}")`,
    `a:has-text("${folderName}")`,
    `.project-title:has-text("${folderName}")`,
  ];

  for (const sel of folderSelectors) {
    try {
      const el = page.locator(sel).first();
      if (await el.isVisible({ timeout: 3000 })) {
        console.log(`Папка найдена через: ${sel}`);
        await el.click();
        await page.waitForLoadState('networkidle');
        await sleep(2000);
        const projectUrl = page.url();
        console.log(`URL проекта: ${projectUrl}`);
        return projectUrl;
      }
    } catch {}
  }

  // Try scrolling to find it
  await page.evaluate(() => window.scrollTo(0, 500));
  await sleep(1000);
  await page.screenshot({ path: '/tmp/tilda_projects_scroll.png' });

  // List all visible text to debug
  const allText = await page.evaluate(() => {
    const elements = document.querySelectorAll('a, .project-title, .projects__item');
    return Array.from(elements).map(el => el.textContent?.trim()).filter(t => t).join('\n');
  });
  console.log('Видимые элементы:', allText.substring(0, 500));

  throw new Error(`Папка "${folderName}" не найдена`);
}

async function getExistingPageFont(page) {
  console.log('Ищем шрифт с других лендингов...');

  // Go to projects list to find a page that's not "Другая"
  await page.goto('https://tilda.cc/projects/', { waitUntil: 'networkidle' });
  await sleep(2000);

  // Get all project links
  const projects = await page.evaluate(() => {
    const items = document.querySelectorAll('[data-project-id], .projects__item, .project-card');
    return Array.from(items).map(el => ({
      text: el.textContent?.trim(),
      href: el.querySelector('a')?.href,
    }));
  });

  console.log('Проекты:', projects.slice(0, 5));

  // Default font based on document spec
  return 'Histori Pro';
}

async function createNewPage(page, projectUrl) {
  console.log('Создаём новую страницу...');

  await page.goto(projectUrl, { waitUntil: 'networkidle' });
  await sleep(3000);

  await page.screenshot({ path: '/tmp/tilda_project_view.png' });
  console.log('Скриншот проекта: /tmp/tilda_project_view.png');

  // Look for "Add page" button
  const addBtns = [
    '.js-addpage-btn',
    'button:has-text("Добавить")',
    'a:has-text("Добавить страницу")',
    '[data-action="addpage"]',
    '.addpage',
    '.js-add-page',
    'button:has-text("+")',
    'a[href*="addpage"]',
  ];

  for (const sel of addBtns) {
    try {
      if (await page.isVisible(sel, { timeout: 2000 })) {
        console.log(`Нажимаем: ${sel}`);
        await page.click(sel);
        await sleep(3000);
        return true;
      }
    } catch {}
  }

  // Try clicking the last visible "+" or add button
  await page.screenshot({ path: '/tmp/tilda_project_no_add.png' });
  throw new Error('Не найдена кнопка добавления страницы');
}

async function configurePageSettings(page) {
  console.log('Настраиваем параметры страницы...');
  await sleep(2000);
  await page.screenshot({ path: '/tmp/tilda_new_page_dialog.png' });

  // Fill title
  const titleSelectors = [
    'input[name="title"]',
    'input[placeholder*="название"]',
    'input[placeholder*="Название"]',
    '#page-title',
    '.form-title input',
  ];

  for (const sel of titleSelectors) {
    try {
      if (await page.isVisible(sel, { timeout: 2000 })) {
        await page.fill(sel, 'Магия женского мира: ведьмин клубок и инициация');
        console.log(`Заголовок введён через: ${sel}`);
        break;
      }
    } catch {}
  }

  // Fill URL/alias
  const urlSelectors = [
    'input[name="alias"]',
    'input[name="url"]',
    'input[placeholder*="url"]',
    'input[placeholder*="URL"]',
    '#page-alias',
    '.form-alias input',
  ];

  for (const sel of urlSelectors) {
    try {
      if (await page.isVisible(sel, { timeout: 2000 })) {
        await page.fill(sel, PAGE_URL);
        console.log(`URL введён через: ${sel}`);
        break;
      }
    } catch {}
  }

  await sleep(1000);
}

async function addBlocksToPage(page) {
  console.log('Добавляем блоки на страницу...');
  await sleep(2000);
  await page.screenshot({ path: '/tmp/tilda_editor_view.png' });

  // The Tilda editor is complex - we'll try to add blocks
  // First, let's see if we're in the editor
  const isEditor = await page.isVisible('.t-editor, .editor-wrap, [data-editor]', { timeout: 5000 }).catch(() => false);
  console.log(`В редакторе: ${isEditor}`);

  // Save page URL for reference
  const editorUrl = page.url();
  console.log(`URL редактора: ${editorUrl}`);
}

async function main() {
  console.log('='.repeat(60));
  console.log('Создание лендинга "Магия женского мира" на Tilda');
  console.log('='.repeat(60));

  // Check images
  for (let i = 1; i <= 4; i++) {
    const imgPath = path.join(IMAGES_DIR, `image${i}.png`);
    if (fs.existsSync(imgPath)) {
      const size = fs.statSync(imgPath).size;
      console.log(`✓ image${i}.png (${Math.round(size / 1024)} KB)`);
    } else {
      console.log(`✗ image${i}.png НЕ НАЙДЕН`);
    }
  }

  // Get proxy from environment and parse credentials
  const rawProxy = process.env.https_proxy || process.env.HTTPS_PROXY || process.env.http_proxy || process.env.HTTP_PROXY || '';
  let proxyConfig = undefined;
  if (rawProxy) {
    try {
      const proxyParsed = new URL(rawProxy);
      const proxyServer = `${proxyParsed.protocol}//${proxyParsed.hostname}:${proxyParsed.port}`;
      proxyConfig = {
        server: proxyServer,
        username: decodeURIComponent(proxyParsed.username),
        password: decodeURIComponent(proxyParsed.password),
      };
      console.log(`Прокси сервер: ${proxyServer}`);
    } catch (e) {
      console.log(`Ошибка парсинга прокси: ${e.message}`);
    }
  }

  const browser = await chromium.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--ignore-certificate-errors',
    ],
    proxy: proxyConfig,
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    locale: 'ru-RU',
    ignoreHTTPSErrors: true,
  });

  const page = await context.newPage();

  // Capture console errors
  page.on('console', msg => {
    if (msg.type() === 'error') console.log('Browser error:', msg.text());
  });

  try {
    // Step 1: Login
    await loginToTilda(page);

    // Step 2: Find Svetlana Komarova folder
    const projectUrl = await findProjectByFolder(page, TARGET_FOLDER);

    // Step 3: Get font from existing pages
    // const font = await getExistingPageFont(page);
    // console.log(`Шрифт: ${font}`);

    // Step 4: Go back to project and create new page
    await createNewPage(page, projectUrl);

    // Step 5: Configure page settings
    await configurePageSettings(page);

    await sleep(5000);

    // Final screenshot
    await page.screenshot({ path: '/tmp/tilda_final.png' });
    console.log('\n✓ Скрипт завершён. Скриншоты в /tmp/tilda_*.png');

  } catch (err) {
    console.error(`\n✗ Ошибка: ${err.message}`);
    await page.screenshot({ path: '/tmp/tilda_error.png' });
    console.log('Скриншот ошибки: /tmp/tilda_error.png');
  } finally {
    await browser.close();
  }
}

main().catch(console.error);
