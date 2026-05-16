# Autoresearch Framework — Design Plan

## 1. Концепция

Фреймворк позволяет применять автоматизированный research (авторисерч) к проектам с измеримым результатом. Внешний AI-агент (например, OpenCode) итеративно улучшает кодовую базу: предлагает гипотезы, редактирует код, запускает оценку, сохраняет успешные изменения.

### Ключевые принципы

- **Минимализм.** Не переусложнять. Добавлять только необходимое. Существующие design choices (git-based tracking, single scalar metric) сохраняются.
- **Агент контролирует `workdir/`.** Никаких принудительных тренировочных циклов. Агент сам решает, как устроена модель (обучаемая, необучаемая, числодробилка — что угодно), исходя из контекста `project.md`.
- **Один скаляр качества.** `evaluate(model) -> float`. Чем больше, тем лучше. Под капотом может быть что угодно — accuracy, F1, bool прошел/не прошел, — но наружу отдаётся одно число для простоты принятия решений (keep/discard).
- **Фреймворк — pip-пакет** с CLI для быстрого развёртывания новых проектов.
- **Агент полностью внешний.** Фреймворк предоставляет только инфраструктуру.

---

## 2. Сущности

### 2.1. Агент (Agent)

Внешний AI-агент (OpenCode или аналогичный). Умеет читать файлы, редактировать код, выполнять shell-команды, работать с git. Фреймворк не реализует агента — только предоставляет ему среду и контракты.

### 2.2. Модель (Model)

Изменяемая агентом часть кодовой базы. Всё, что лежит в директории `workdir/`, агент может создавать, редактировать, удалять. Единственное жёсткое требование: в `workdir/model.py` должен быть класс `Model`, наследующий `abstract.ModelBase` и реализующий метод `predict()`.

```python
# abstract/__init__.py — фиксированный код фреймворка

from abc import ABC, abstractmethod
from typing import Any

class ModelBase(ABC):
    """Агент наследует этот класс в workdir/model.py."""
    @abstractmethod
    def predict(self, x: Any) -> Any: ...
```

Агент волен:
- Менять архитектуру `Model` как угодно
- Добавлять любые модули в `workdir/` (слои, утилиты, тренировочные скрипты, ...)
- Импортировать их из `model.py` или использовать иначе
- Добавлять метод `train()` или не добавлять — модель может быть как обучаемой, так и нет

### 2.3. Оценщик (Evaluator)

Фиксированная, неизменяемая в течение сессии часть. Директория `eval/`. Содержит `evaluate.py` с классом `MyEvaluator`, наследующим `abstract.EvaluatorBase`, и экспортированным инстансом `evaluate`.

```python
# abstract/__init__.py — фиксированный код фреймворка

class EvaluatorBase(ABC):
    """Пользователь наследует этот класс в eval/evaluate.py."""
    @abstractmethod
    def evaluate(self, model: ModelBase) -> float: ...
```

```python
# eval/evaluate.py — пример для MNIST

from abstract import EvaluatorBase, ModelBase

class MyEvaluator(EvaluatorBase):
    def evaluate(self, model: ModelBase) -> float:
        # Загрузка данных, вызов model.predict(), подсчёт accuracy
        ...
        return accuracy

evaluate = MyEvaluator().evaluate
```

Агент НЕ может редактировать `eval/`. Он может только:
- Передать свою модель в `evaluate(model)`
- Получить скаляр метрики

### 2.4. Контекст

Три слоя инструкций для агента. Flow: пользователь отправляет агента к `global.md` → `global.md` содержит все правила работы и отсылает к `project.md` и `config.yaml` за проектным контекстом.

| Уровень | Файл | Описание | Изменяемость |
|---------|------|----------|-------------|
| Глобальный | `.autoresearch/global.md` | **Главная точка входа.** Полные правила фреймворка: workflow экспериментов, работа с git (ветки, коммиты, reset), формат результатов (`results.tsv`), keep/discard логика, формат вывода метрики, simplicity criterion. Внутри также инструкция: «прочитай `.autoresearch/project.md` и `.autoresearch/config.yaml` для контекста проекта». | Статичен всегда |
| Проектный | `.autoresearch/project.md` | Описание проекта, контракты model↔eval, описание бейзлайна, известные инсайты | Статичен в течение сессии; может обновляться после успешной сессии |
| Конфиг | `.autoresearch/config.yaml` | Параметры фреймворка: `max_experiments` | Статичен |
| Пользовательский | Передаётся агенту напрямую | Триггер-промпт вида «посмотри global.md и начни эксперименты». Может включать цель, направление, пожелания, на что обратить внимание | Каждый раз новый |

**Паттерн запуска (как в оригинальном program_mnist.md):**
```
User → Agent: "Hi, have a look at .autoresearch/global.md and let's kick off a new experiment!"
Agent → читает global.md → получает все правила + инструкцию читать project.md и config.yaml → читает project.md, config.yaml → начинает эксперименты
```

### 2.5. Метрика

Один скаляр `float`. Чем больше, тем лучше. Keep/discard решение принимается простым сравнением: новая метрика > лучшая предыдущая → keep, иначе → discard.

### 2.6. Сессия (Session)

Серия экспериментов на одной git-ветке `autoresearch/<session_name>`. Все артефакты сессии хранятся в `runs/<session_name>/`.

### 2.7. Эксперимент (Run)

Одна итерация: гипотеза → редактирование → коммит → запуск оценки → запись результата → keep/discard. Каждый эксперимент — одна строка в `results.tsv`.

---

## 3. Структура директорий

### 3.1. Проект после `autoresearch init`

```
my-project/
├── .autoresearch/
│   ├── global.md              # Главная точка входа: все правила фреймворка (статичен)
│   ├── project.md             # Описание проекта, контракты, бейзлайн
│   └── config.yaml            # Параметры фреймворка (max_experiments)
├── abstract/
│   └── __init__.py            # ModelBase(ABC), EvaluatorBase(ABC) — фиксировано
├── eval/
│   └── evaluate.py            # MyEvaluator + экспорт инстанса evaluate (фиксирован)
├── workdir/                   # Рабочая область агента (EDITABLE)
│   └── model.py               # class Model(abstract.ModelBase) — точка входа
│   └── ...                    # Агент создаёт любые модули
├── runs/                      # Сессии экспериментов (в .gitignore)
│   └── <session>/
│       ├── results.tsv
│       ├── progress.png
│       └── summary.md
├── .gitignore
├── pyproject.toml
└── README.md
```

### 3.2. Структура репозитория фреймворка

```
autoresearch/
├── pyproject.toml
│   # [project]
│   # name = "autoresearch"
│   # [project.scripts]
│   # autoresearch = "autoresearch.cli:main"
├── src/
│   └── autoresearch/
│       ├── __init__.py
│       ├── cli.py             # Точка входа CLI
│       ├── init_cmd.py        # Команда 'init'
│       ├── check_cmd.py       # Команда 'check'
│       ├── analyze_cmd.py     # Команда 'analyze'
│       └── templates/
│           ├── abstract/
│           │   └── __init__.py
│           ├── eval/
│           │   └── evaluate.py
│           ├── workdir/
│           │   └── model.py
│           ├── .autoresearch/
│           │   ├── global.md
│           │   ├── project.md
│           │   └── config.yaml
│           └── .gitignore
├── tests/
├── DESIGN_PLAN.md
└── README.md
```

---

## 4. CLI

### `autoresearch init [path]`

Разворачивает шаблон проекта в указанной директории (по умолчанию — текущая). Копирует файлы из `templates/`.

```
$ autoresearch init my-mnist
  Created my-mnist/
  Created my-mnist/abstract/__init__.py
  Created my-mnist/eval/evaluate.py
  Created my-mnist/workdir/model.py
  Created my-mnist/.autoresearch/global.md
  Created my-mnist/.autoresearch/project.md
  Created my-mnist/.autoresearch/config.yaml
  Created my-mnist/.gitignore
  Done. Edit eval/evaluate.py and .autoresearch/project.md, then run:
    autoresearch check
```

### `autoresearch check [path]`

Валидирует проект:

1. `from abstract import ModelBase, EvaluatorBase` — импорты работают
2. `from workdir.model import Model` — модель импортируется
3. `issubclass(Model, abstract.ModelBase)` — модель наследует правильный класс
4. `Model()` — инстанцируется без ошибок
5. `from eval.evaluate import evaluate` — оценщик импортируется
6. `evaluate(Model())` — возвращает `float`
7. Всё вместе не падает

Возвращает 0 если всё ок, 1 если есть ошибки, с описанием проблемы.

### `autoresearch analyze [path] --session <name>`

Генерирует `runs/<session>/progress.png` по `runs/<session>/results.tsv`. График: scatter всех экспериментов (цвет по статусу) + линия keep-экспериментов.

---

## 5. Контракты

### 5.1. model.py ↔ evaluate.py

Контракт описывается в `.autoresearch/project.md`. Пример:

```markdown
## Контракт model↔eval

Model.predict(x) принимает:
  - x: torch.Tensor формы (B, 1, 28, 28), значения [0, 1]
Возвращает:
  - torch.Tensor формы (B, 10) — логиты по классам

evaluate(model) вызывает model.predict() на тестовых данных MNIST,
считает accuracy и возвращает float от 0 до 1.
```

### 5.2. Формат вывода evaluate

Стандартный формат для grep'а агентом:

```
---
metric: 0.9771
```

Агент ищет `^metric:` в выводе и парсит число.

---

## 6. Экспериментальный флоу

### 6.1. Подготовка

1. Пользователь настраивает проект: `autoresearch init`, пишет `eval/evaluate.py`, заполняет `.autoresearch/project.md`
2. `autoresearch check` проходит
3. Всё коммитится в `main`

### 6.2. Запуск сессии

Пользователь обращается к агенту с промптом:

> Улучши метрику на MNIST. Попробуй CNN, нормализацию, learning rate scheduling. Сделай 30 экспериментов. Бейзлайн — простой MLP с accuracy ~0.977.

### 6.3. Работа агента

1. **Изучение контекста:**
   - Читает `.autoresearch/global.md`
   - Читает `.autoresearch/project.md`
   - Изучает `workdir/` и `eval/`

2. **Создание сессии:**
   ```bash
   git checkout -b autoresearch/<session_name>
   mkdir -p runs/<session_name>/
   ```

3. **Цикл экспериментов (до max_experiments или прерывания):**

   a. **Гипотеза.** Агент решает, что попробовать, и формулирует reasoning — почему эта гипотеза может улучшить метрику.

   b. **Редактирование.** Агент меняет файлы в `workdir/`. Может создавать новые модули, менять архитектуру, гиперпараметры, добавлять/убирать обучение — полная свобода в пределах `workdir/`.

   c. **Коммит:**
   ```bash
   git add workdir/
   git commit -m "краткое описание гипотезы"
   ```

   d. **Запуск оценки.** Запускает модель и evaluation. Может использовать любой подход — от `python -c "from eval.evaluate import evaluate; from workdir.model import Model; ..."` до собственного скрипта в `workdir/`.

   e. **Извлечение метрики.** grep'ает `^metric:` из вывода.

   f. **Запись результата.** Дописывает строку в `runs/<session>/results.tsv`:
   ```
   <commit>\t<metric>\t<status>\t<description>\t<reasoning>
   ```

   g. **Keep/discard:**
   - Если `metric > best_metric`: keep (оставляем коммит, обновляем best)
   - Если `metric <= best_metric` или краш: discard (`git reset --hard HEAD~1`, статус = crash если краш)

4. **Завершение сессии:**
   - Пишет `runs/<session>/summary.md` — саммари находок, лучшие эксперименты, динамика
   - Запускает `autoresearch analyze --session <session>`
   - При желании обновляет `.autoresearch/project.md` (новый бейзлайн, инсайты)

---

## 7. Формат results.tsv

Tab-separated, 5 колонок:

| Колонка | Тип | Пример | Описание |
|---------|-----|--------|----------|
| `commit` | str (7 hex) | `abc1234` | Хеш коммита |
| `metric` | float (4 знака) | `0.9771` | Значение метрики |
| `status` | str | `keep` / `discard` / `crash` | Статус эксперимента |
| `description` | str | `baseline MLP 128 hidden, ReLU` | Краткое описание эксперимента |
| `reasoning` | str | `Starting point for comparison. MLP is the simplest...` | Почему агент решил проверить эту гипотезу |

Пример:
```
abc1234	0.9771	keep	baseline MLP 128h ReLU	Starting point to measure from
def5678	0.9650	discard	added dropout 0.5	Dropout should reduce overfitting but may be too aggressive
fgh9012	0.9812	keep	switched to GELU activation	GELU smooths gradients, often improves convergence in small nets
```

---

## 8. Процесс оценки (evaluate)

Агент придумывает как запустить оценку. Минимальный способ — встроенный в `workdir/` скрипт или прямая команда:

```bash
python -c "
from eval.evaluate import evaluate
from workdir.model import Model
import torch
model = Model()
# если модель обучаемая — обучить
metric = evaluate(model)
print(f'---\nmetric: {metric:.4f}')
"
```

Или агент может создать `workdir/run.py` со своим процессом (тренировка + вызов evaluate) и запускать его:

```bash
python workdir/run.py
```

---

## 9. Шаблоны для `autoresearch init`

### `abstract/__init__.py`

```python
from abc import ABC, abstractmethod
from typing import Any


class ModelBase(ABC):
    @abstractmethod
    def predict(self, x: Any) -> Any: ...


class EvaluatorBase(ABC):
    @abstractmethod
    def evaluate(self, model: ModelBase) -> float: ...
```

### `eval/evaluate.py`

```python
from abstract import EvaluatorBase, ModelBase


class MyEvaluator(EvaluatorBase):
    def evaluate(self, model: ModelBase) -> float:
        # TODO: реализовать оценку модели
        # Вызвать model.predict() на тестовых данных, посчитать метрику
        # Возвращает float, чем больше тем лучше
        raise NotImplementedError("Implement evaluate() for your project")


evaluate = MyEvaluator().evaluate
```

### `workdir/model.py`

```python
from abstract import ModelBase


class Model(ModelBase):
    def predict(self, x):
        # TODO: реализовать логику модели
        raise NotImplementedError("Implement predict() for your project")
```

### `.autoresearch/global.md`

**Главная точка входа для агента** (аналог `program_mnist.md` из оригинального проекта). Содержит полную инструкцию:

- **Вход:** инструкция прочитать `project.md` и `config.yaml` для проектного контекста
- **Setup:** создать бранч `autoresearch/<tag>`, создать `runs/<session>/`, инициализировать `results.tsv`
- **Что можно редактировать:** только `workdir/`
- **Что нельзя:** `eval/`, `abstract/`, `.autoresearch/`, датасеты
- **Цикл экспериментов:** пошаговая инструкция (гипотеза → редактирование → коммит → запуск → grep метрики → keep/discard)
- **Формат вывода метрики:** `---` разделитель, `metric: <float>` для grep'а
- **Логика keep/discard:** если метрика улучшилась — keep, иначе `git reset --hard HEAD~1`
- **Crash handling:** читать лог ошибки, попытаться починить
- **Simplicity criterion:** при равной метрике предпочитать более простой код
- **Формат `results.tsv`:** колонки `commit`, `metric`, `status`, `description`, `reasoning`
- **Завершение:** написать `summary.md`, запустить `autoresearch analyze`

### `.autoresearch/project.md`

Содержит:
- Название и краткое описание проекта
- Что делает модель, какую задачу решает
- Контракт `predict()` ↔ `evaluate()`
- Описание бейзлайна и его метрики
- Известные инсайты (что пробовали, что работает/не работает)
- Специфичные для проекта правила (если есть)

### `.autoresearch/config.yaml`

```yaml
# Параметры фреймворка (статичны в течение сессии)
max_experiments: 30    # максимальное число экспериментов (0 = без ограничений)
```

---

## 10. План реализации

### Фаза 1: Структура фреймворка

- Создать структуру `src/autoresearch/` в репозитории
- Настроить `pyproject.toml` как pip-пакет с CLI
- Реализовать `autoresearch init`
- Реализовать `autoresearch check`
- Создать и заполнить шаблоны в `templates/`
- `global.md` — полные правила фреймворка

### Фаза 2: Аналитика

- Перенести `analysis.py` в `src/autoresearch/analyze_cmd.py`
- Обобщить: поддержка колонки `reasoning`, работа с `runs/<session>/`
- Реализовать `autoresearch analyze --session <name>`

### Фаза 3: Миграция MNIST

- Создать MNIST-проект по новой структуре, используя `autoresearch init`
- Заполнить `eval/evaluate.py` (перенести логику из `prep_mnist.py`)
- Заполнить `workdir/model.py` (перенести логику из `train_mnist.py`)
- Заполнить `.autoresearch/project.md` (перенести из `program_mnist.md`)
- Убедиться, что `autoresearch check` проходит
- Прогнать несколько экспериментов для проверки

### Фаза 4: Документация и полировка

- README: описание фреймворка, quickstart, примеры
- Дополнить тесты

---

## 11. Что остаётся без изменений

- **Git как стейт-машина** — ветка = история успешных изменений, reset = отклонение
- **Keep/discard по одному скаляру** — простота в принятии решений
- **Агент внешний** — фреймворк не реализует агента
- **Subprocess + grep** — способ коммуникации агента с evaluate
- **Simplicity criterion** — при равной метрике предпочитать более простой код

---

## 12. Чего пока НЕ делаем

- Менеджмент примеров (examples/) — позже
- Поддержка параллельных агентов — позже
- Чекпоинты экспериментов — позже
- Live-дашборд — позже
- Интеграция агента в фреймворк — агент остаётся внешним
