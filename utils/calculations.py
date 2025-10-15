def compute_brm(weight_kg: float, height_cm: float, age_years: int, activity_level_text: str, gender_text: str) -> float:
    """Расчёт BRM по методике пользователя.

    activity_level_text: Один из ["Очень высокая", "Высокая", "Средняя", "Низкая"].
    gender_text: "Мужской"/"Женский" (или man/woman).
    """
    activity_map = {
        "Очень высокая": 1.725,
        "Высокая": 1.55,
        "Средняя": 1.375,
        "Низкая": 1.2,
    }

    activity = activity_map.get(str(activity_level_text), 1.2)
    gender_norm = str(gender_text).lower()
    gender = "man" if gender_norm.startswith("муж") or gender_norm == "man" else "woman"

    if gender == 'man':
        brm = ((10 * float(weight_kg)) + (6.25 * float(height_cm)) - (5 * int(age_years)) + 5) * float(activity)
    else:
        brm = ((10 * float(weight_kg)) + (6.25 * float(height_cm)) - (5 * int(age_years)) - 161) * float(activity)

    return float(brm)


def compute_bmi(height_cm: float, weight_kg: float) -> float:
    height_m = float(height_cm) / 100.0
    if height_m <= 0:
        return 0.0
    return float(weight_kg) / (height_m * height_m)


def parse_height(text: str) -> float | None:
    try:
        value = float(text)
        if 50 <= value <= 250:
            return value
        return None
    except Exception:
        return None


def parse_weight(text: str) -> float | None:
    try:
        value = float(text)
        if 20 <= value <= 300:
            return value
        return None
    except Exception:
        return None


def validate_activity(text: str) -> str | None:
    valid = {"очень высокая", "высокая", "средняя", "низкая"}
    norm = str(text).strip().lower()
    if norm in valid:
        # вернуть в исходном регистре для вывода
        mapping = {
            "очень высокая": "Очень высокая",
            "высокая": "Высокая",
            "средняя": "Средняя",
            "низкая": "Низкая",
        }
        return mapping[norm]
    return None


def normalize_gender(text: str) -> str | None:
    low = str(text).strip().lower()
    if low.startswith("муж") or low == "man":
        return "Мужской"
    if low.startswith("жен") or low == "woman":
        return "Женский"
    return None


def parse_age(text: str) -> int | None:
    try:
        years = int(text)
        if 1 <= years <= 120:
            return years
        return None
    except Exception:
        return None


