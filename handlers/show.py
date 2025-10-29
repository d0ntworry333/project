from telegram import Update
from telegram.ext import ContextTypes

from database.DataBase import get_user_by_id, get_all_user_forms, get_all_users, delete_last_user_form, delete_all_user_forms, get_user_previous_form
from error_solutions import send_long_message


def format_date(date_value):
    """Форматирует дату для отображения"""
    try:
        from datetime import datetime
        if isinstance(date_value, str):
            try:
                if 'T' in date_value:
                    # ISO формат
                    date_obj = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                else:
                    # Обычный формат SQLite
                    date_obj = datetime.strptime(date_value, '%Y-%m-%d %H:%M:%S')
                return date_obj.strftime('%Y-%m-%d %H:%M')
            except:
                return date_value
        else:
            # Если это timestamp
            try:
                # Проверяем, если timestamp очень маленький (меньше 1000000000 = 2001 год)
                if date_value < 1000000000:
                    # Возможно, это timestamp в миллисекундах
                    date_value = date_value / 1000
                elif date_value > 1000000000000:
                    # Возможно, это timestamp в микросекундах
                    date_value = date_value / 1000000
                
                # Если timestamp все еще очень маленький, используем текущее время
                if date_value < 1000000000:
                    return datetime.now().strftime('%Y-%m-%d %H:%M')
                
                date_obj = datetime.fromtimestamp(date_value)
                return date_obj.strftime('%Y-%m-%d %H:%M')
            except:
                # Если не удалось конвертировать, возвращаем текущее время
                return datetime.now().strftime('%Y-%m-%d %H:%M')
    except:
        return str(date_value)


async def show_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_data = get_user_by_id(user.id)
    if user_data:
        bmi = float(user_data[4]) / ((float(user_data[3]) / 100) ** 2)
        
        # Форматируем даты
        created_date = format_date(user_data[8])
        updated_date = format_date(user_data[9])
        
        await update.message.reply_text(
            "📋 Ваша последняя анкета:\n\n"
            f"📅 Дата заполнения: {created_date}\n"
            f"✏️ Дата обновления: {updated_date}\n"
            f"📏 Рост: {user_data[3]} см\n"
            f"⚖️ Вес: {user_data[4]} кг\n"
            f"📊 ИМТ: {bmi:.1f}\n"
            f"🏃 Уровень активности: {user_data[5]}\n"
            f"👤 Пол: {user_data[6]}\n"
            f"🎂 Возраст: {user_data[7]} лет\n\n"
            "Чтобы увидеть все ваши анкеты, используйте /my_forms"
        )
    else:
        await update.message.reply_text(
            "❌ У вас еще нет заполненных анкет.\n"
            "Заполните анкету с помощью команды /form"
        )


async def show_my_forms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    forms = get_all_user_forms(user.id)
    if not forms:
        await update.message.reply_text(
            "❌ У вас еще нет заполненных анкет.\n"
            "Заполните анкету с помощью команды /form"
        )
        return
    
    # Убираем дубликаты по ID записи
    unique_forms = []
    seen_ids = set()
    for form in forms:
        if form[0] not in seen_ids:  # form[0] - это id записи
            unique_forms.append(form)
            seen_ids.add(form[0])
    
    if not unique_forms:
        await update.message.reply_text(
            "❌ У вас еще нет заполненных анкет.\n"
            "Заполните анкету с помощью команды /form"
        )
        return
    
    # Отправляем каждую анкету отдельным сообщением
    await update.message.reply_text(f"📊 Ваш прогресс - {len(unique_forms)} анкет:")
    
    for i, form in enumerate(unique_forms, 1):
        height_cm = float(form[3])
        weight_kg = float(form[4])
        bmi = weight_kg / ((height_cm / 100) ** 2)
        
        # Форматируем дату
        date_str = format_date(form[8])
        
        if i == 1:
            # Первая анкета - показываем полностью
            response = (
                f"📋 Анкета #{i} (от {date_str}) - ПОЛНАЯ АНКЕТА:\n"
                f"📏 Рост: {form[3]} см\n"
                f"⚖️ Вес: {form[4]} кг\n"
                f"📊 ИМТ: {bmi:.1f}\n"
                f"🏃 Активность: {form[5]}\n"
                f"👤 Пол: {form[6]}\n"
                f"🎂 Возраст: {form[7]} лет\n"
                f"🎯 Цель: {form[9]}"
            )
        else:
            # Последующие анкеты - показываем только вес и активность с предыдущими значениями
            previous_form = get_user_previous_form(user.id, form[0])
            
            if previous_form:
                # Сравниваем с предыдущей анкетой
                prev_weight = previous_form[4]
                prev_activity = previous_form[5]
                
                weight_change = ""
                activity_change = ""
                
                if float(form[4]) != float(prev_weight):
                    weight_change = f" (был {prev_weight})"
                
                if form[5] != prev_activity:
                    activity_change = f" (был {prev_activity})"
                
                response = (
                    f"📋 Анкета #{i} (от {date_str}) - ОБНОВЛЕНИЕ:\n"
                    f"⚖️ Вес: {form[4]} кг{weight_change}\n"
                    f"📊 ИМТ: {bmi:.1f}\n"
                    f"🏃 Активность: {form[5]}{activity_change}"
                )
            else:
                # Если предыдущей анкеты нет (не должно происходить)
                response = (
                    f"📋 Анкета #{i} (от {date_str}) - ОБНОВЛЕНИЕ:\n"
                    f"⚖️ Вес: {form[4]} кг\n"
                    f"📊 ИМТ: {bmi:.1f}\n"
                    f"🏃 Активность: {form[5]}"
                )
        
        await update.message.reply_text(response)


async def show_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    forms = get_all_user_forms(user.id)
    if not forms:
        await update.message.reply_text(
            "❌ У вас еще нет заполненных анкет.\n"
            "Заполните анкету с помощью команды /form"
        )
        return
    
    # Убираем дубликаты по ID записи
    unique_forms = []
    seen_ids = set()
    for form in forms:
        if form[0] not in seen_ids:  # form[0] - это id записи
            unique_forms.append(form)
            seen_ids.add(form[0])
    
    if not unique_forms:
        await update.message.reply_text(
            "❌ У вас еще нет заполненных анкет.\n"
            "Заполните анкету с помощью команды /form"
        )
        return
    
    # Отправляем каждую анкету отдельным сообщением
    await update.message.reply_text(f"📊 Ваш прогресс - {len(unique_forms)} анкет:")
    
    for i, form in enumerate(unique_forms, 1):
        height_cm = float(form[3])
        weight_kg = float(form[4])
        bmi = weight_kg / ((height_cm / 100) ** 2)
        
        # Форматируем дату
        date_str = format_date(form[8])
        
        if i == 1:
            # Первая анкета - показываем полностью
            response = (
                f"📋 Анкета #{i} (от {date_str}) - ПОЛНАЯ АНКЕТА:\n"
                f"📏 Рост: {form[3]} см\n"
                f"⚖️ Вес: {form[4]} кг\n"
                f"📊 ИМТ: {bmi:.1f}\n"
                f"🏃 Активность: {form[5]}\n"
                f"👤 Пол: {form[6]}\n"
                f"🎂 Возраст: {form[7]} лет\n"
                f"🎯 Цель: {form[9]}"
            )
        else:
            # Последующие анкеты - показываем только вес и активность с предыдущими значениями
            previous_form = get_user_previous_form(user.id, form[0])
            
            if previous_form:
                # Сравниваем с предыдущей анкетой
                prev_weight = previous_form[4]
                prev_activity = previous_form[5]
                
                weight_change = ""
                activity_change = ""
                
                if float(form[4]) != float(prev_weight):
                    weight_change = f" (был {prev_weight})"
                
                if form[5] != prev_activity:
                    activity_change = f" (был {prev_activity})"
                
                response = (
                    f"📋 Анкета #{i} (от {date_str}) - ОБНОВЛЕНИЕ:\n"
                    f"⚖️ Вес: {form[4]} кг{weight_change}\n"
                    f"📊 ИМТ: {bmi:.1f}\n"
                    f"🏃 Активность: {form[5]}{activity_change}"
                )
            else:
                # Если предыдущей анкеты нет (не должно происходить)
                response = (
                    f"📋 Анкета #{i} (от {date_str}) - ОБНОВЛЕНИЕ:\n"
                    f"⚖️ Вес: {form[4]} кг\n"
                    f"📊 ИМТ: {bmi:.1f}\n"
                    f"🏃 Активность: {form[5]}"
                )
        
        await update.message.reply_text(response)


async def handle_show_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if text.startswith('show me') or 'моя' in text:
        await show_me(update, context)
    elif 'мои анкеты' in text or 'my forms' in text or 'прогресс' in text:
        await show_my_forms(update, context)
    else:
        await send_long_message(update.message.reply_text,
                                "Неизвестная команда. Используйте:\n"
                                "/form - заполнить анкету\n"
                                "/show_me - моя последняя анкета\n"
                                "/my_forms - мой прогресс (все анкеты)\n"
                                "/clear_last - удалить мою последнюю анкету\n"
                                "/clear_all - удалить все мои анкеты")


async def clear_last(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    deleted = delete_last_user_form(user.id)
    if deleted:
        await update.message.reply_text("Последняя анкета удалена.")
    else:
        await update.message.reply_text("Удалять нечего — анкет не найдено.")


async def clear_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    deleted = delete_all_user_forms(user.id)
    if deleted:
        await update.message.reply_text("Все ваши анкеты удалены.")
    else:
        await update.message.reply_text("Удалять нечего — анкет не найдено.")

