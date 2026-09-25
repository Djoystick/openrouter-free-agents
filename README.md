# 🤖 OpenRouter Free Agents Swarm

> **Zero-Cost Multi-Agent Orchestrator powered by OpenRouter's live free models catalog (`:free`).**  
> Автоматический мониторинг бесплатных нейросетей OpenRouter, ролевая диспетчеризация субагентов и отказоустойчивый каскадный fallback.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Cost](https://img.shields.io/badge/Cost-$0.00-brightgreen.svg)](https://openrouter.ai/)
[![Architecture](https://img.shields.io/badge/Multi--Agent-Swarm-orange.svg)](#architecture)

---

## 🌟 Возможности (Features)

* 🔍 **Live Free Models Monitor:** автоматический опрос каталога `openrouter.ai/api/v1/models`, фильтрация моделей с тегом `:free` и нулевой тарификацией (`prompt: 0`, `completion: 0`), ранжирование по размеру контекстного окна.
* 🎭 **Ролевые субагенты (Role Presets):** готовые системные промпты и параметры под задачи:
  * `coder` — написание чистого продакшн-кода, рефакторинг, алгоритмы;
  * `architect` — проектирование системной архитектуры, схем БД и API-контрактов;
  * `security` — аудит уязвимостей, проверка OWASP Top 10, безопасный парсинг;
  * `motion_ui` — верстка в стиле швейцарского минимализма (Linear style), CSS/Tailwind, 60 FPS микроанимации;
  * `reviewer` — скептический аудит кода, поиск мертвого кода и генерация тестов.
* 🛡️ **Отказоустойчивый Fallback (Zero-429 Downtime):** если выбранная модель перегружена или возвращает `429 Too Many Requests`, оркестратор мгновенно и прозрачно перенаправляет запрос на следующую доступную бесплатную модель из пула.
* ⛓️ **Multi-Agent Pipeline:** запуск последовательных конвейеров (например, `Architect -> Coder -> Security Reviewer`), где каждый субагент обогащает контекст предыдущего.
* 💾 **Автоматическое сохранение артефактов:** каждый ответ субагента фиксируется в Markdown-файл в директории `outputs/` с указанием модели и таймстемпа.
* 🌐 **Поддержка Прокси (Proxy-ready):** встроенная поддержка HTTP/HTTPS прокси для работы в регионах с сетевыми ограничениями.

---

## 📐 Архитектура (How It Works)

```
                       ┌───────────────────────────────┐
                       │   OpenRouter API Catalog      │
                       │   (https://openrouter.ai)     │
                       └──────────────┬────────────────┘
                                      │ (GET /models)
                                      ▼
                       ┌───────────────────────────────┐
                       │     OpenRouterMonitor         │
                       │  • Фильтрация по ":free"      │
                       │  • Сортировка по context_len  │
                       │  • Проверка доступности       │
                       └──────────────┬────────────────┘
                                      │ Live Free Pool
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             AgentSwarm Core                                 │
│                                                                             │
│   Задача (Task) ──> Выбор роли (Role) ──> Приоритетная модель               │
│                                                   │                         │
│                                      [HTTP 200 OK?]                         │
│                                      ├── ДА ──> Сохранение в outputs/*.md   │
│                                      └── НЕТ (429/503/Timeout)              │
│                                           │                                 │
│                                           └──> Авто-ротация на следующую    │
│                                                бесплатную модель            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Быстрый старт (Quickstart)

### 1. Клонирование и установка зависимостей

```bash
git clone https://github.com/your-username/openrouter-free-agents.git
cd openrouter-free-agents

# Создание виртуального окружения (рекомендуется)
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Настройка окружения

Скопируйте пример файла конфигурации:

```bash
cp .env.example .env
```

Откройте `.env` и укажите ваш бесплатный ключ OpenRouter (получить можно на [openrouter.ai/keys](https://openrouter.ai/keys)):

```env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxx

# При необходимости укажите локальный прокси:
# HTTP_PROXY=http://127.0.0.1:7890
# HTTPS_PROXY=http://127.0.0.1:7890
```

---

## 💻 Использование через CLI

### Сканирование каталога бесплатных моделей
```bash
python cli.py scan --min-context 16000
```
Выведет список всех актуальных бесплатных моделей с контекстом от 16 000 токенов.

### Проверка скорости отклика (Benchmark)
```bash
python cli.py benchmark --limit 5
```

### Запуск субагента для решения задачи
```bash
python cli.py run --role coder --task "Напиши асинхронный Telegram-бот на Python (aiogram 3) для приёма заявок на ремонт авто"
```

### Запуск мультиагентного конвейера (Pipeline)
```bash
python cli.py pipeline --task "Спроектируй сервис бронирования отелей" --roles architect,coder,security
```

---

## 🐍 Использование в Python-коде

### 1. Простой запуск субагента

```python
from core.swarm import AgentSwarm

swarm = AgentSwarm()
result = swarm.dispatch(
    task="Напиши функцию безопасного хеширования паролей на bcrypt",
    role="coder"
)

print(f"Модель: {result['model_used']}")
print(f"Файл: {result['artifact_file']}")
print(result["content"])
```

### 2. Мониторинг моделей в коде

```python
from core.monitor import OpenRouterMonitor

monitor = OpenRouterMonitor()
free_models = monitor.get_free_models(min_context=32000)

for m in free_models[:5]:
    print(f"- {m['id']} (Контекст: {m['context_length']:,})")
```

---

## 🔒 Безопасность при публикации на GitHub

Перед публикацией репозитория убедитесь:
1. Файл `.env` **НИКОГДА** не должен попадать в коммиты (он уже внесён в `.gitignore`).
2. В файлах репозитория нет захардкоженных токенов вида `sk-or-v1-...`.
3. Все ключи передаются исключительно через переменные окружения.

---

## 📄 Лицензия

Проект распространяется под открытой лицензией [MIT](LICENSE).
Приглашаем к участию (PR, Issues, добавление новых ролевых пресетов)!
