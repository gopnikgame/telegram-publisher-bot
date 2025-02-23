# Telegram Publisher Bot

Бот для автоматической публикации сообщений и медиафайлов в Telegram-канале с добавлением настраиваемых ссылок.

## Возможности

- Публикация текстовых сообщений в канал
- Публикация медиафайлов (фото, видео, аудио, документы) с подписями
- Автоматическое добавление настраиваемых ссылок к каждому сообщению
- Поддержка Markdown, HTML и современного форматирования с эмодзи
- Проверка размера загружаемых файлов
- Система прав доступа (только администраторы)
- Логирование всех действий
- Поддержка прокси

## Требования

- Docker
- Docker Compose
- Telegram Bot Token
- Права администратора в канале для бота

## Установка и настройка

1. **Клонируйте репозиторий**:
```bash
git clone https://github.com/gopnikgame/telegram-publisher-bot.git
cd telegram-publisher-bot
```

2. **Создайте файл .env и настройте переменные окружения**:
```bash
cp .env.example .env
nano .env
```

Заполните следующие параметры:
```plaintext
BOT_TOKEN=YOUR_BOT_TOKEN
CHANNEL_ID=@YourChannelName
MAIN_BOT_LINK=[Основной бот](https://t.me/YourMainBot)
SUPPORT_BOT_LINK=[Техподдержка](https://t.me/YourSupportBot)
CHANNEL_LINK=[Канал проекта](https://t.me/YourChannel)
ADMIN_IDS=123456789,987654321  # ID администраторов через запятую
DEFAULT_FORMAT=modern  # Формат сообщений: markdown, html, plain или modern
# HTTPS_PROXY=http://your-proxy:port  # Опционально
```

3. **Соберите и запустите Docker контейнер**:
```bash
docker-compose build
docker-compose up -d
```

4. **Проверьте логи**:
```bash
docker-compose logs -f
```

## Управление ботом

### Основные команды Docker Compose

- **Запуск бота**:
```bash
docker-compose up -d
```

- **Остановка бота**:
```bash
docker-compose down
```

- **Просмотр логов**:
```bash
docker-compose logs -f
```

- **Перезапуск бота**:
```bash
docker-compose restart
```

### Обновление бота

1. Остановите текущий контейнер:
```bash
docker-compose down
```

2. Получите последние изменения:
```bash
git pull --rebase
```

3. Пересоберите и запустите контейнер:
```bash
docker-compose build
docker-compose up -d
```

### Автоматическое обновление скриптом

Для автоматического обновления и управления ботом используйте следующий скрипт:

1. Загрузите и выполните скрипт:
```bash
wget -qO server_launcher.sh https://raw.githubusercontent.com/gopnikgame/telegram-publisher-bot/main/install_or_update_bot.sh && chmod +x server_launcher.sh && sudo ./server_launcher.sh
```

2. Следуйте инструкциям в меню скрипта.

## Использование бота

1. Добавьте бота в ваш канал как администратора
2. Запустите бота командой `/start`
3. Отправляйте сообщения или медиафайлы боту, и он автоматически опубликует их в канале с добавленными ссылками

### Пример форматирования сообщений

**Modern (по умолчанию):**
```text
🌟 **Уважаемые пользователи сервера UAE!** 🌟

В ближайшее время на сервере будут проводиться **срочные технические работы**. В этот период подключение будет недоступно. Сейчас мы активно готовим обновление, чтобы сделать сервер ещё лучше! 🚀

📌 **Важно:**
1. О начале работ мы уведомим в нашем паблике и через Telegram-бота.
2. Заранее остановите стримы, чтобы избежать возможных проблем.

Спасибо за ваше понимание и поддержку! 💙
Оставайтесь на связи, мы работаем для вас! 😊

#UAE #ТехническиеРаботы #Обновление
```

**Markdown:**
```text
*Заголовок жирным шрифтом*

Обычный текст в первом абзаце\.

_Текст курсивом_ и продолжение обычного текста\.

*Важное объявление\!*
\- Первый пункт
\- Второй пункт
\- Третий пункт

`Текст в виде кода`

[Ссылка на сайт](https://example\.com)

~~Зачеркнутый текст~~
```

**HTML:**
```text
<b>Заголовок жирным шрифтом</b>

Обычный текст в первом абзаце.

<i>Текст курсивом</i> и продолжение обычного текста.

<b>Важное объявление!</b>
<ul>
  <li>Первый пункт</li>
  <li>Второй пункт</li>
  <li>Третий пункт</li>
</ul>

<code>Текст в виде кода</code>

<a href="https://example.com">Ссылка на сайт</a>

<s>Зачеркнутый текст</s>
```

**Plain:**
```text
Заголовок жирным шрифтом

Обычный текст в первом абзаце.

Текст курсивом и продолжение обычного текста.

Важное объявление!
- Первый пункт
- Второй пункт
- Третий пункт

Текст в виде кода

Ссылка на сайт: https://example.com

Зачеркнутый текст
```

## Структура проекта

```
telegram-publisher-bot/
├── app/
│   ├── __init__.py
│   ├── bot.py
│   ├── config.py
│   └── utils.py
├── logs/
├── .env
├── .dockerignore
├── .gitignore
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Безопасность

- Храните токен бота и другие чувствительные данные только в файле `.env`
- Регулярно обновляйте зависимости проекта
- Используйте только HTTPS прокси при необходимости
- Ограничьте доступ к боту только доверенным администраторам

## Устранение неполадок

1. **Бот не отвечает**:
   - Проверьте правильность токена в `.env`
   - Убедитесь, что контейнер запущен
   - Проверьте логи на наличие ошибок

2. **Ошибка публикации в канал**:
   - Убедитесь, что бот добавлен в канал как администратор
   - Проверьте правильность CHANNEL_ID в `.env`

3. **Проблемы с Docker**:
   - Проверьте статус контейнера: `docker-compose ps`
   - Проверьте логи: `docker-compose logs -f`

## Лицензия

MIT License

## Автор

[gopnikgame](https://github.com/gopnikgame)

## Последнее обновление

2025-02-23 16:01:11 UTC