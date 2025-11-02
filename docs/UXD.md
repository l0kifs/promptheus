# UI/UX Design Specifications (UXD)
## Promptheus - Telegram Bot for Prompt Engineering Education

### 1. Design Philosophy

**Mobile-First**: Optimized for Telegram mobile clients with thumb-friendly navigation
**Minimalist**: Clean interfaces with essential information only
**Conversational**: Natural dialogue flow with clear progression
**Immediate Feedback**: Instant visual confirmation of user actions

---

### 2. Interface Layouts

#### 2.1 Message Formatting Standards

**Text Constraints**:
- Theory: 50-80 words per message
- Examples: 2-3 sentences (150-200 chars)
- Exercises: Max 100 words
- Feedback: 2-3 structured messages

**Typography**:
```
📘 *Lesson Title* (Bold, emoji prefix)
Regular text for main content
_Italic_ for emphasis
`Code` for prompt examples
```

**Visual Hierarchy**:
```
[Emoji Icon] Section Header
Body text with proper spacing

• Bullet point
• Bullet point

[Keyboard Button Grid]
```

#### 2.2 Inline Keyboard Patterns

**Primary Actions** (Full Width):
```
┌──────────────────────────────┐
│  ▶️ Начать обучение          │
└──────────────────────────────┘
```

**Binary Choices** (2 columns):
```
┌──────────────┬──────────────┐
│ ✅ Да        │ ❌ Нет       │
└──────────────┴──────────────┘
```

**Navigation Grid** (2-3 columns):
```
┌──────────┬──────────┬──────────┐
│ ⬅️ Назад │ 📚 Меню  │ Далее ➡️ │
└──────────┴──────────┴──────────┘
```

**Skill Selection** (Vertical Stack):
```
┌──────────────────────────────┐
│ 🌱 Новичок                   │
├──────────────────────────────┤
│ 📈 Средний уровень           │
├──────────────────────────────┤
│ 🚀 Продвинутый               │
└──────────────────────────────┘
```

---

### 3. User Scenarios

#### 3.1 First-Time User Journey

**Step 1: Welcome**
```
👋 Добро пожаловать в Promptheus!

Я помогу вам освоить искусство общения с AI.

Готовы начать?

[▶️ Начать обучение]
```

**Step 2: Assessment Intro**
```
📊 Давайте определим ваш уровень

Ответьте на 5 коротких вопросов.
Это займет 2 минуты.

[🚀 Начать тест]  [❓ Зачем это нужно]
```

**Step 3: Assessment Question** (x5)
```
❓ Вопрос 1/5

Что такое "роль" в промпте?

A) Описание задачи
B) Персона для AI (например, "учитель")
C) Формат ответа

[A] [B] [C]
```

**Step 4: Goal Selection**
```
🎯 Ваша цель обучения?

[🎓 Учеба]
[💼 Работа]
[🎨 Творчество]
```

**Step 5: Personalized Path**
```
✨ Ваш путь готов!

Уровень: 🌱 Новичок
Фокус: 💼 Работа

Рекомендуем начать с:
1️⃣ Определение роли AI
2️⃣ Формулировка задачи
3️⃣ Контекст и примеры

[🚀 К первому уроку]  [📊 Посмотреть все]
```

#### 3.2 Lesson Learning Flow

**Lesson Start**
```
📘 Урок 1: Определение роли AI

В этом уроке:
• Что такое "роль" в промпте
• Почему роль улучшает ответы
• Практика с ролевыми промптами

Время: ~5 минут

[▶️ Начать]  [📋 К списку уроков]
```

**Theory Section** (chunked)
```
💡 Теория

Роль — это персона, которую вы задаете AI.
Например: "Ты опытный программист" или
"Ты учитель физики".

[Далее ➡️]
```

```
Зачем нужна роль?

AI подстраивает стиль, лексику и глубину
под заданную персону. Результат становится
точнее и релевантнее.

[⬅️ Назад]  [Далее ➡️]
```

**Example Comparison**
```
📊 Пример: Плохой промпт

❌ "Расскажи о Python"

Проблема: Слишком общо, непонятен
контекст и глубина ответа.

[Показать хороший ➡️]
```

```
📊 Пример: Хороший промпт

✅ "Ты — Python-разработчик с 10-летним
опытом. Объясни новичку, что такое
декораторы, на простом примере."

Почему лучше:
• Роль: опытный разработчик
• Цель: объяснение для новичка
• Тема: конкретная (декораторы)

[⬅️ Назад]  [К практике ➡️]
```

**Practice Exercise**
```
✏️ Практика

Сценарий:
Вам нужен совет по здоровому питанию
для занятий спортом.

Задача:
Напишите промпт с ролью специалиста.

Отправьте ваш промпт следующим сообщением.

[💡 Показать подсказку]  [⏭️ Пропустить]
```

**User Submits Prompt** → Bot Shows Loader
```
⏳ Анализирую ваш промпт...
```

**AI Feedback** (structured)
```
📝 Ваш промпт:
"Дай совет по питанию для спорта"

🔍 Оценка: 4/10

❌ Что не хватает:
• Роли специалиста
• Конкретики (вид спорта, цель)

[Посмотреть улучшенный ➡️]
```

```
✅ Улучшенная версия:

"Ты — спортивный диетолог с 15-летним
опытом. Составь план питания для
начинающего бегуна, цель — похудение.
Укажи калории и время приемов пищи."

Добавлено:
• Роль: спортивный диетолог
• Контекст: начинающий бегун, похудение
• Формат: план с калориями и временем

[🔄 Попробовать еще]  [✅ Урок завершен]
```

**Lesson Completion**
```
🎉 Урок завершен!

Урок 1: Определение роли AI ✅
Попыток: 2
Оценка: 8/10

[📚 К следующему уроку]  [📊 Мой прогресс]
```

#### 3.3 Navigation & Progress

**Main Menu**
```
📚 Главное меню

[📖 Продолжить обучение]
[📋 Все уроки]
[📊 Мой прогресс]
[⚙️ Настройки]
```

**Lesson List**
```
📋 Все уроки

🌱 Новичок:
✅ 1. Определение роли AI
⏳ 2. Формулировка задачи
🔒 3. Контекст и примеры

[▶️ К уроку 2]  [⬅️ Назад]
```

**Progress Dashboard**
```
📊 Ваш прогресс

Уровень: 🌱 Новичок
Завершено: 1/5 уроков
Средняя оценка: 8/10

Последний урок:
✅ Определение роли AI (сегодня)

[▶️ Продолжить]  [📋 Все уроки]
```

**Resume Capability**
```
👋 С возвращением!

Вы остановились на:
📘 Урок 2: Формулировка задачи
Раздел: Практика

[▶️ Продолжить]  [📚 Главное меню]
```

---

### 4. Interaction Patterns

#### 4.1 State Transitions

```
[Новый пользователь]
       ↓
   Приветствие
       ↓
   Оценка уровня → Выбор цели
       ↓
Персональный путь
       ↓
   Изучение урока (теория → примеры → практика)
       ↓
   Следующий урок / Меню
```

#### 4.2 User Input Handling

**Text Input Expected**:
- Exercise prompts → AI evaluation
- Free-form feedback → Store for analytics

**Callback Queries** (Buttons):
- Navigation actions → Update message
- Selection choices → Store + next step
- Menu commands → New message

**Error Handling**:
```
❌ Неверный формат

Пожалуйста, отправьте текст промпта
(не файл или медиа).

[💡 Показать пример]
```

#### 4.3 Loading States

**Short Operations** (<2s):
- No loader, instant response

**AI Operations** (3-10s):
```
⏳ Генерирую персональный путь...
```
```
⏳ Анализирую ваш промпт...
```

**Long Operations** (>10s):
```
⏳ Обрабатываю запрос...

Это может занять до 15 секунд.

[❌ Отменить]
```

---

### 5. Visual Design System

#### 5.1 Emoji Legend

**Categories**:
- 📘 📖 📚 Lessons/Learning
- ✏️ ✅ ❌ Actions/Status
- 📊 📈 Progress/Stats
- 💡 ⚡ Tips/Insights
- 🌱 🚀 Skill Levels
- 🎯 🎓 💼 🎨 Goals
- ⏳ 🔄 Loading/Process
- ⬅️ ➡️ ⏭️ Navigation

**Usage Rules**:
- One emoji per button/section
- Consistent emoji for same action types
- Avoid emoji overload (max 1 per line)

#### 5.2 Message Templates

**Information Block**:
```
[Icon] *Title*

Body text with spacing.
Max 3-4 sentences.

[Action Buttons]
```

**Comparison Block**:
```
❌ *Before*
Short example

✅ *After*
Improved version

💡 *Key Change*
Brief explanation

[Next Step]
```

**Feedback Block**:
```
📝 *Your Work*
User submission

🔍 *Evaluation*
Score + key issues

✅ *Improvement*
Concrete suggestions

[Action Options]
```

---

### 6. Accessibility Considerations

**Screen Reader Friendly**:
- Descriptive button labels (avoid "Click here")
- Emoji + text labels for clarity
- Logical reading order

**Cognitive Load**:
- One concept per message
- Max 2-3 choices per decision
- Clear back/cancel options

**Internationalization Ready**:
- Separate text from code
- Unicode support for Cyrillic
- Date/time in user timezone

---

### 7. Error & Edge Cases

#### 7.1 Network Issues

**Bot Unavailable**:
```
⚠️ Временные проблемы с подключением

Попробуйте через несколько минут.

Ваш прогресс сохранен.
```

**AI API Timeout**:
```
⏱️ Запрос занял слишком много времени

Попробуйте:
• Упростить промпт
• Повторить попытку

[🔄 Попробовать снова]  [⏭️ Пропустить]
```

#### 7.2 Rate Limiting

```
⏸️ Слишком много запросов

Подождите 1 минуту перед следующим
действием.

Это помогает сохранить качество для всех.
```

#### 7.3 Invalid State

```
🔄 Что-то пошло не так

Начнем сначала:

[📚 Главное меню]  [🆘 Помощь]
```

---

### 8. Design Validation

**Mobile Usability Checklist**:
- ✅ Buttons min 44x44px touch target
- ✅ Max 3 buttons per row
- ✅ Messages fit single screen (no scroll for core info)
- ✅ Back button always available
- ✅ Clear current location indicator

**Content Readability**:
- ✅ Sentence length <25 words
- ✅ Paragraph breaks every 2-3 sentences
- ✅ Active voice preferred
- ✅ Technical terms explained

**User Flow Efficiency**:
- ✅ Max 3 taps to any feature
- ✅ Resume from interruption
- ✅ Skip/back always available
- ✅ Progress visible at any point

---

### 9. Implementation Notes

**Telegram API Constraints**:
- Max 64 callback_data bytes → use short IDs
- Inline keyboards max 8 columns × rows
- Message edit 48 hours limit → send new for old messages
- Parse modes: Markdown/HTML for formatting

**Bot Commands** (Slash):
```
/start     - Начало работы
/menu      - Главное меню
/progress  - Показать прогресс
/help      - Справка
/cancel    - Отменить текущее действие
```

**Button Callback Patterns**:
```
lesson_start_{id}
lesson_next_{id}_{section}
practice_submit_{lesson_id}
menu_main
progress_view
```

---

### 10. Metrics & Optimization

**Track User Interactions**:
- Button click rates per screen
- Message read time (proxy: next action delay)
- Back button usage (indicates confusion)
- Skip rates per exercise

**A/B Testing Opportunities**:
- Button label wording
- Emoji usage density
- Message chunking (2 vs 3 messages)
- Example format (side-by-side vs sequential)

**Performance Targets**:
- Message send: <500ms
- Keyboard update: <200ms
- State persistence: <100ms
- AI response: 3-10s (with loader)
