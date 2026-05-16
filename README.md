# Autoresearch

Фреймворк для автоматизированного исследования задач с числовой метрикой.
AI-агент итеративно улучшает решение: формулирует гипотезу, редактирует код,
измеряет результат, оставляет только успешные изменения.

Вдохновлён [autoresearch](https://github.com/karpathy/autoresearch) Андрея Карпатого.

## Мотивация

У вас есть задача, качество решения которой можно измерить одним числом.
Вы хотите, чтобы AI-агент перебирал подходы автономно: писал код, запускал
оценку, фиксировал прогресс. Без фреймворка это выливается в неструктурированные
промпты, неконсистентные структуры файлов и потерю результатов.

Autoresearch решает это через:

- **Стандартную структуру проекта** — `autoresearch init` генерирует проект
  с чётким разделением зон (код агента, метрика, базовые классы), инструкциями
  и шаблонами. Не нужно каждый раз объяснять агенту, где что лежит.
- **Контракт между моделью и метрикой** — абстрактные базовые классы
  гарантируют совместимость. `autoresearch check` валидирует до запуска.
- **Историю эксперимента** — каждый эксперимент это git-коммит. Успешные
  остаются в истории, неудачные откатываются. Чистая ветка лучших решений.

## Что можно исследовать

Всё, что сводится к числовой метрике (чем больше, тем лучше):

- Классификация/регрессия (accuracy, MSE)
- Обработка сигналов (SNR, PSNR)
- Алгоритмы сжатия (compression ratio)
- Генерация текста (BLEU, perplexity)
- Оптимизация конфигов (throughput, latency)
- Любой процессинговый алгоритм с измеримым качеством

Фреймворк не привязан к ML. Единственное требование — метрика возвращается
как `float`, и она детерминирована при фиксированных входных данных.

## Как это работает

Autoresearch не запускает агента самостоятельно. Фреймворк задаёт структуру
проекта и набор правил (файл `.autoresearch/global.md`), по которым AI-агент
работает в IDE. В роли агента может выступать Claude, GPT или любая LLM,
способная редактировать файлы и выполнять команды.

Цикл одного эксперимента:

```
  Гипотеза — что и почему может улучшить метрику
      ↓
  Редактирование workdir/ — агент меняет код
      ↓
  git commit — фиксация изменений
      ↓
  evaluate() — запуск метрики
     / \
    ↓   ↓
 метрика ↑    метрика ≤ best
 commit stays  git reset --hard HEAD~1
    \          /
     ↓        ↓
  Следующая гипотеза
```

Результаты каждого эксперимента записываются в `runs/<session>/results.tsv`
с пометкой: `keep` (улучшение), `discard` (нет улучшения), `crash` (ошибка).

## Структура проекта

```
my-project/
├── .autoresearch/
│   ├── global.md          # Инструкция для AI-агента — точка входа
│   ├── project.md         # Описание задачи, контракты model↔eval, бейзлайн
│   └── config.yaml        # Параметры сессии (max_experiments)
├── abstract/
│   └── __init__.py        # ModelBase, EvaluatorBase — не редактируются
├── eval/
│   └── evaluate.py        # evaluate(model) → float — пишет человек
├── workdir/               # Песочница агента — всё, что здесь, он меняет
│   ├── model.py           # class Model(abstract.ModelBase)
│   └── ...                # Любые модули, данные, конфиги
└── runs/                  # Артефакты сессий (в .gitignore)
    └── <session>/
        ├── results.tsv
        ├── progress.png
        └── summary.md
```

| Директория | Редактирует | Содержит |
|-----------|-------------|----------|
| `abstract/` | Никто | `ModelBase`, `EvaluatorBase` |
| `eval/` | Человек | Фиксированная метрика |
| `workdir/` | Агент | Модель, обучение, любые модули |
| `.autoresearch/` | Человек | Инструкции, контракты, конфиг |

### Контракт model↔eval

`workdir/model.py` наследует `ModelBase` и реализует `predict()`:

```python
from abstract import ModelBase

class Model(ModelBase):
    def predict(self, x):
        ...
```

`eval/evaluate.py` экспортирует функцию, которая принимает инстанс модели
и возвращает `float`:

```python
from abstract import EvaluatorBase

class MyEvaluator(EvaluatorBase):
    def evaluate(self, model) -> float:
        ...

evaluate = MyEvaluator().evaluate
```

Детали контракта (формат входных/выходных данных) описываются в
`.autoresearch/project.md`.

## Быстрый старт

```bash
# Установка
git clone git@github.com:ClapeyronDigital/autoresearch.git
cd autoresearch
uv pip install -e .

# Создать новый проект
autoresearch init my-project
cd my-project

# Реализовать:
#   eval/evaluate.py   — метрика
#   workdir/model.py   — модель
#   .autoresearch/project.md — описание задачи и контракты

# Проверить, что контракты корректны
autoresearch check

# Инициализировать git
git init && git add -A && git commit -m "baseline"

# Запустить LLM-агента в IDE с инструкцией:
#   "Hi, have a look at .autoresearch/global.md and let's kick off a new experiment!"
```

### Команды

```bash
autoresearch init [path]              # развернуть новый проект
autoresearch check [path]             # проверить контракты (6 проверок)
autoresearch analyze --session NAME   # построить progress.png по results.tsv
```

## Git-механика

Каждая сессия экспериментов идёт на отдельной ветке `autoresearch/<session>`.

1. Агент создаёт ветку от текущего состояния
2. Каждый эксперимент: гипотеза → правки → коммит → evaluate()
3. Если метрика улучшилась — коммит остаётся, ветка идёт вперёд
4. Если нет — `git reset --hard HEAD~1`, ветка возвращается к предыдущему
   состоянию

В истории ветки остаются только успешные эксперименты.

### results.tsv

```
commit	metric	status	description	reasoning
abc1234	0.9771	keep	baseline MLP	Starting point
def5678	0.9650	discard	added dropout 0.5	Dropout too aggressive
```

- `keep` — метрика улучшилась
- `discard` — не улучшилась
- `crash` — упало с ошибкой

Метрика всегда один `float`. Чем больше, тем лучше.

## Разработка

```bash
git clone git@github.com:ClapeyronDigital/autoresearch.git
cd autoresearch
uv sync
uv pip install -e .
autoresearch --help
```

## Лицензия

MIT
