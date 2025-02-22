# Telegram Publisher Bot

Бот для автоматической публикации сообщений и медиафайлов в Telegram-канале с добавлением настраиваемых ссылок.

## Возможности

- Публикация текстовых сообщений в канал
- Публикация медиафайлов (фото, видео, аудио, документы) с подписями
- Автоматическое добавление настраиваемых ссылок к каждому сообщению
- Поддержка Markdown форматирования
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
git pull
```

3. Пересоберите и запустите контейнер:
```bash
docker-compose build
docker-compose up -d
```

## Использование бота

1. Добавьте бота в ваш канал как администратора
2. Запустите бота командой `/start`
3. Отправляйте сообщения или медиафайлы боту, и он автоматически опубликует их в канале с добавленными ссылками

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

2025-02-22 14:55:16 UTC