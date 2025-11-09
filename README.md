# 🔍 Telegram Chat Parser

Мощный парсер для поиска Telegram чатов и каналов по ключевым словам. Находит сотни каналов через Telegram API, DuckDuckGo и Google Custom Search API.

## ⚡ Быстрый старт

### 1. Установка

```bash
pip install -r requirements.txt
```

### 2. Настройка

Скопируй `config_example.py` в `config.py` и заполни данные:

```bash
cp config_example.py config.py
```

**config.py:**
```python
# Telegram API (обязательно)
API_ID = 12345678  # Получить на https://my.telegram.org/apps
API_HASH = 'your_api_hash'
PHONE = '+1234567890'

# Google API (опционально, для большего охвата)
GOOGLE_API_KEY = None  # Или твой ключ
GOOGLE_SEARCH_ENGINE_ID = None  # Или твой CX
```

### 3. Запуск

```bash
python tg_chat_parser.py
```

Выбери тип поиска:
- **1** - Telegram API (основной, 100-200 результатов)
- **2** - Веб-поиск (DuckDuckGo + Google API)
- **3** - Все методы сразу (максимум результатов)

## 🔑 Где взять ключи

### Telegram API (обязательно)
1. Иди на https://my.telegram.org/apps
2. Войди в аккаунт
3. Создай приложение
4. Скопируй `API_ID` и `API_HASH`

### Google Custom Search API (опционально)
1. **Google Cloud Console**: https://console.cloud.google.com/
   - Создай проект
   - Включи "Custom Search API"
   - Создай API ключ → `GOOGLE_API_KEY`

2. **Programmable Search Engine**: https://programmablesearchengine.google.com/
   - Создай поисковик
   - Выбери "Search the entire web"
   - Скопируй Search Engine ID (CX) → `GOOGLE_SEARCH_ENGINE_ID`

**Без Google API** программа всё равно работает, просто найдёт меньше результатов.

## 🎯 Возможности

- ✅ **Telegram API поиск** - ищет напрямую по базе Telegram (100-200 результатов)
- ✅ **DuckDuckGo поиск** - веб-поиск без API ключей (30-50 результатов)
- ✅ **Google API поиск** - официальный API Google (до 100 результатов)
- ✅ **Автоматические вариации** - для "crypto" ищет: bitcoin, ethereum, btc, eth и т.д.
- ✅ **Дедупликация** - автоматически убирает дубликаты
- ✅ **Полная информация** - название, описание, количество участников
- ✅ **Сохранение в JSON** - результаты сохраняются автоматически
- ✅ **Режим отладки** - для диагностики проблем

## 📊 Пример работы

```bash
$ python tg_chat_parser.py

🔍 TELEGRAM CHAT PARSER v2.2
================================================================================

Введите ключевое слово: crypto

Выберите тип поиска:
1. Telegram API поиск
2. Веб-поиск (DuckDuckGo + Google API)
3. Все методы сразу (рекомендуется)

Ваш выбор: 1

🔍 Поиск через Telegram API по запросу: 'crypto'
   Будет выполнено 20 запросов для максимального охвата
   [1/20] Поиск: 'crypto' → найдено 15 чатов
   [2/20] Поиск: 'bitcoin' → найдено 45 чатов
   [3/20] Поиск: 'ethereum' → найдено 28 чатов
   ...
   [20/20] Поиск: 'криптовалют' → найдено 12 чатов
   Найдено через API: 130 уникальных чатов

✅ Найдено 130 чат(ов) по запросу 'crypto'

1. Bitcoin News
   Тип: Канал
   Ссылка: https://t.me/bitcoinnews
   Участников: 50,234
   Описание: Latest crypto news and updates
   ✓ Найдено: в названии, в описании
--------------------------------------------------------------------------------
...

Сохранить результаты в файл? (y/n): y
💾 Результаты сохранены в файл: search_results_crypto_20251109_192820.json
```

## 🚀 Советы для максимальных результатов

### 1. Используй конкретные запросы
❌ Плохо: `crypto`  
✅ Хорошо: `bitcoin`, `ethereum`, `nft trading`

### 2. Попробуй разные языки
- `крипта` (русский)
- `crypto` (английский)
- `加密货币` (китайский)

### 3. Используй опцию 3 (все методы)
Комбинация всех источников даёт максимум результатов.

### 4. Настрой Google API
Telegram API даёт 100-150 результатов, Google API добавит ещё 20-50 уникальных.

## 🔧 Параметры поиска

Программа автоматически расширяет запрос. Например, для `crypto` ищет:
- crypto, bitcoin, btc, ethereum, eth
- blockchain, cryptocurrency, altcoin
- token, coin, defi, nft, web3
- doge, usdt, trading, binance, coinbase
- крипто, криптовалют

Всего **20 разных запросов** → больше результатов!

## 📁 Структура проекта

```
tg chat parser/
├── tg_chat_parser.py       # Основной скрипт
├── config.py               # Твои ключи (НЕ коммитить!)
├── config_example.py       # Пример конфига
├── requirements.txt        # Зависимости
├── README.md              # Документация
├── .gitignore             # Игнор для git
└── search_results_*.json  # Результаты (автоматически)
```

## ⚠️ Важно

1. **Не коммить config.py** - там твои секретные ключи!
2. **Файлы сессий** - `.session` файлы содержат данные авторизации
3. **Лимиты Google API** - 100 запросов в день бесплатно
4. **Rate limits Telegram** - не спамь слишком часто

## 🐛 Решение проблем

### "Файл config.py не найден"
Скопируй `config_example.py` в `config.py` и заполни данные.

### "Мало результатов от Google API"
Проверь настройки Programmable Search Engine - должен быть включен "Search the entire web".

### "DuckDuckGo возвращает 0 результатов"
Это нормально, DuckDuckGo часто блокирует ботов. Telegram API работает отлично!

### "Telegram API находит мало"
Используй более популярные/общие запросы: `bitcoin` вместо `bitcoin cash`.

## 📝 Лицензия

MIT License - делай что хочешь.

## 🤝 Вклад

Pull requests приветствуются! Для больших изменений сначала открой issue.

---

**Сделано с ❤️ для поиска в Telegram**
