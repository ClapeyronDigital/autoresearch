# autoresearch

Фреймворк для автоматизированного research с измеримым результатом. Внешний AI-агент
итеративно улучшает кодовую базу: предлагает гипотезы, редактирует код, запускает оценку,
сохраняет успешные изменения.

## Установка

```bash
pip install autoresearch
```

Или из исходников:

```bash
git clone git@github.com:ClapeyronDigital/autoresearch.git
cd autoresearch
uv pip install -e .
```

## Быстрый старт

```bash
# 1. Развернуть новый проект
autoresearch init my-project
cd my-project

# 2. Реализовать eval/evaluate.py и workdir/model.py под свою задачу
# 3. Заполнить .autoresearch/project.md — описание, контракты, бейзлайн

# 4. Проверить что всё корректно
autoresearch check

# 5. Закоммитить бейзлайн
git init && git add -A && git commit -m "baseline"

# 6. Запустить агента
#    "Hi, have a look at .autoresearch/global.md and let's kick off a new experiment!"
```

## Как это работает

### Проект после `autoresearch init`

```
my-project/
├── .autoresearch/
│   ├── global.md          # Главная точка входа для агента — все правила
│   ├── project.md         # Описание проекта, контракты, бейзлайн
│   └── config.yaml        # max_experiments
├── abstract/
│   └── __init__.py        # ModelBase, EvaluatorBase (фиксировано)
├── eval/
│   └── evaluate.py        # evaluate(model) → float (фиксировано)
├── workdir/               # Рабочая область агента (EDITABLE)
│   └── model.py            # Model(abstract.ModelBase) — точка входа
│   └── ...                 # Агент создаёт любые модули
└── runs/                   # Сессии экспериментов (gitignored)
    └── <session>/
        ├── results.tsv
        ├── progress.png
        └── summary.md
```

### Разделение ответственности

| Директория | Кто редактирует | Содержит |
|-----------|----------------|----------|
| `abstract/` | Никто (фиксирован) | Базовые классы `ModelBase`, `EvaluatorBase` |
| `eval/` | Человек (до старта) | Функция оценки `evaluate(model) → float` |
| `workdir/` | Агент | Модель, обучение, любые модули |
| `.autoresearch/` | Человек (до старта) | Инструкции агенту, контракты, конфиг |

### Цикл работы агента

1. **Изучить контекст** — прочитать `global.md`, `project.md`, `config.yaml`
2. **Гипотеза** — придумать, что попробовать, и записать reasoning (почему)
3. **Редактировать `workdir/`** — менять модель, гиперпараметры, создавать новые модули
4. **Закоммитить** — `git commit`
5. **Запустить оценку** — выполнить код модели и вызвать `evaluate(model)`
6. **Извлечь метрику** — grep `^metric:` из вывода
7. **Записать в `results.tsv`** — commit, metric, status, description, reasoning
8. **Принять решение:**
   - `metric > best` → keep (оставить коммит)
   - `metric <= best` → discard (`git reset --hard HEAD~1`)
   - Краш → crash (откатить, попробовать починить)
9. **Повторить** до `max_experiments` или остановки

Агент не спрашивает разрешения — работает автономно.

### Контракты

`workdir/model.py` должен содержать класс `Model`, наследующий `abstract.ModelBase`:

```python
class Model(ModelBase):
    def predict(self, x):
        ...  # реализация
```

`eval/evaluate.py` должен экспортировать функцию `evaluate`, которая принимает модель
и возвращает `float` (чем больше, тем лучше):

```python
evaluate = MyEvaluator().evaluate
```

Контракт между ними (что `predict` принимает и возвращает) описан в `project.md`.

### Формат результатов

`runs/<session>/results.tsv` (tab-separated):

| commit | metric | status | description | reasoning |
|--------|--------|--------|-------------|-----------|
| abc1234 | 0.9771 | keep | baseline MLP | Starting point |
| def5678 | 0.9650 | discard | added dropout 0.5 | Dropout too aggressive |

## CLI

```bash
autoresearch init [path]              # Развернуть новый проект
autoresearch check [path]             # Проверить проект (6 проверок)
autoresearch analyze --session NAME   # График прогресса
```

## Пример: MNIST

На ветке `mnist` лежит полный пример — классификация цифр MNIST:

- `workdir/model.py` — конфигурируемый MLP
- `workdir/train.py` — тренировочный цикл с фиксированным бюджетом 60 сек
- `eval/evaluate.py` — accuracy на тестовом наборе

```bash
git checkout mnist
uv pip install torch torchvision
PYTHONPATH=. python workdir/train.py
```

## Что дальше

Фреймворк — минималистичный. Возможные направления развития:

- Несколько параллельных агентов на разных ветках
- Более сложные constraint-ы (time/token budget)
- Live-дашборд прогресса
- Менеджмент примеров

## Лицензия

MIT
