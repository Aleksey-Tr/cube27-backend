from typing import Any


ERROR_MESSAGES = {
    "missing": "Обязательное поле",
    "extra_forbidden": "Лишнее поле",
    "string_type": "Введите строку",
    "string_too_short": "Минимальное количество символов: {min_length}",
    "string_too_long": "Максимальное количество символов: {max_length}",
    "string_pattern_mismatch": "Значение не соответствует требуемому формату: {pattern}",
    "int_type": "Введите целое число",
    "int_parsing": "Введите целое число",
    "int_from_float": "Введите целое число без дробной части",
    "float_type": "Введите число",
    "float_parsing": "Введите число",
    "decimal_type": "Введите десятичное число",
    "decimal_parsing": "Введите десятичное число",
    "decimal_max_places": "Максимум знаков после запятой: {decimal_places}",
    "decimal_max_digits": "Максимальное количество цифр: {max_digits}",
    "decimal_whole_digits": "Максимум цифр в целой части: {whole_digits}",
    "finite_number": "Введите конечное число",
    "greater_than": "Значение должно быть больше {gt}",
    "greater_than_equal": "Значение должно быть не меньше {ge}",
    "less_than": "Значение должно быть меньше {lt}",
    "less_than_equal": "Значение должно быть не больше {le}",
    "multiple_of": "Значение должно быть кратно {multiple_of}",
    "bool_type": "Введите логическое значение (true или false)",
    "bool_parsing": "Введите логическое значение (true или false)",
    "list_type": "Введите список",
    "dict_type": "Введите объект",
    "model_type": "Введите объект",
    "model_attributes_type": "Введите объект",
    "too_short": "Минимальное количество элементов: {min_length}",
    "too_long": "Максимальное количество элементов: {max_length}",
    "enum": "Допустимые значения: {expected}",
    "literal_error": "Допустимые значения: {expected}",
    "date_type": "Введите дату",
    "date_parsing": "Некорректная дата. Используйте формат ГГГГ-ММ-ДД",
    "date_from_datetime_parsing": "Некорректная дата. Используйте формат ГГГГ-ММ-ДД",
    "date_from_datetime_inexact": "Укажите дату без времени",
    "datetime_type": "Введите дату и время",
    "datetime_parsing": "Некорректные дата и время",
    "datetime_from_date_parsing": "Некорректные дата и время",
    "uuid_type": "Введите UUID",
    "uuid_parsing": "Некорректный UUID",
    "json_invalid": "Некорректный JSON",
    "json_type": "Введите JSON в виде строки",
}


def translate_validation_error(error: dict[str, Any]) -> str:
    """Переводит известные ошибки, сохраняя исходный текст неизвестных."""
    error_type = error["type"]
    message = error["msg"]
    context = error.get("ctx") or {}

    # EmailStr использует общий код value_error, как и пользовательские валидаторы.
    if error_type == "value_error":
        if message.startswith("value is not a valid email address"):
            return "Некорректный email"
        if isinstance(context.get("error"), ValueError):
            return str(context["error"])

    template = ERROR_MESSAGES.get(error_type)
    if template is None:
        return message
    try:
        return template.format(**context)
    except (KeyError, ValueError):
        return message
