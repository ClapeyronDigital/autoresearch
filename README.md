# autoresearch

Фреймворк для автоматизированного research — AI-агент итеративно улучшает
проект, измеряя качество фиксированной метрикой. Вдохновлён
[autoresearch](https://github.com/karpathy/autoresearch) Андрея Карпатого.

## Суть

`autoresearch init` создаёт проект с тремя зонами:

- **`workdir/`** — что угодно. Агент редактирует код, меняет модель, гиперпараметры, создаёт модули
- **`eval/`** — функция `evaluate(model) → float`. Пишет человек, фиксирована, агент не может менять
- **`abstract/`** — базовые классы `ModelBase` и `EvaluatorBase`. Каркас фреймворка

Агент работает циклом: гипотеза → редактирует `workdir/` → коммит → eval →
если метрика улучшилась — коммит остаётся, иначе `git reset --hard HEAD~1`.
Успешные коммиты складываются в ветку `autoresearch/<session>`, неудачные
в git-истории не остаются. Результаты пишутся в `runs/<session>/results.tsv`.

## Установка

```bash
git clone git@github.com:ClapeyronDigital/autoresearch.git
cd autoresearch
uv pip install -e .
```

## Быстрый старт

```bash
autoresearch init my-project
cd my-project

# Реализовать eval/evaluate.py и workdir/model.py под задачу
# Заполнить .autoresearch/project.md — описание, контракты, бейзлайн

autoresearch check               # проверить что всё корректно

git init && git add -A && git commit -m "baseline"

# Запустить агента:
#   "Hi, have a look at .autoresearch/global.md and let's kick off a new experiment!"
```

## Как устроен проект

```
my-project/
├── .autoresearch/
│   ├── global.md          # Главная инструкция для агента — точка входа
│   ├── project.md         # Контракты model↔eval, описание бейзлайна
│   └── config.yaml        # max_experiments
├── abstract/
│   └── __init__.py        # ModelBase, EvaluatorBase — фиксировано
├── eval/
│   └── evaluate.py        # evaluate(model) → float — меняет человек
├── workdir/               # Всё, что здесь — меняет агент
│   ├── model.py           # class Model(abstract.ModelBase)
│   └── ...                # Любые модули
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

### Git-механика

Эксперименты идут на ветке `autoresearch/<session>` (отдельной для каждого запуска).
Каждый эксперимент — коммит. Если метрика улучшилась — коммит остаётся и ветка идёт
вперёд. Если нет — `git reset --hard HEAD~1`, ветка возвращается к предыдущему
состоянию. В истории ветки — только успешные изменения.

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

### Контракт model↔eval

`workdir/model.py` наследует `ModelBase` и реализует `predict()`:

```python
from abstract import ModelBase

class Model(ModelBase):
    def predict(self, x):
        ...
```

`eval/evaluate.py` экспортирует функцию:

```python
from abstract import EvaluatorBase

class MyEvaluator(EvaluatorBase):
    def evaluate(self, model) -> float:
        ...

evaluate = MyEvaluator().evaluate
```

Детали контракта (что подаётся на вход `predict`, что возвращается) описаны в `project.md`.

## CLI

```bash
autoresearch init [path]              # развернуть новый проект
autoresearch check [path]             # проверить структуру и контракты (6 проверок)
autoresearch analyze --session NAME   # построить progress.png по results.tsv
```

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
