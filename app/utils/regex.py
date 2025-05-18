## -*- coding: utf-8 -*-

import re

# Шаблонные регулярные выражения
EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
PHONE_REGEX = r"^\+?\d[\d\s\-]+(?:\d)$"

def check_regex(regex, string):
  pattern = re.compile(regex)
  if pattern.fullmatch(string):
    return True
  else:
    return False
  


def validate_email(email: str) -> bool:
    """
    Проверяет, является ли строка корректным email-адресом.

    Args:
        email: Строка для проверки.

    Returns:
        True, если строка является валидным email, иначе False.
    """
    if not isinstance(email, str):
        return False
    return bool(re.match(EMAIL_REGEX, email))



def normolize_phone_number(phone_number: str) -> str:
  """
  Удаляет из номера телефона все тире, скобки и пробелы.
  Также добавляет "+" в начало, если его там нет.

  Args:
    phone_number: Номер телефона в строковом формате.

  Returns:
    Нормализованный номер телефона, начинающийся с "+" и содержащий только цифры.
  """

  # Удаляем все символы, кроме цифр и плюса
  cleaned_number = re.sub(r"[^0-9+]", "", phone_number)

  # Удаляем плюс, если он не в начале
  if "+" in cleaned_number and cleaned_number[0] != "+":
    cleaned_number = cleaned_number.replace("+", "")

  # Добавляем плюс в начало, если его нет
  if not cleaned_number.startswith("+"):
    cleaned_number = "+" + cleaned_number

  return cleaned_number


def validate_international_phone_number_basic(phone_number: str) -> bool:
    """
    Базовая проверка номера телефона в международном формате (без phonenumbers).
    Не рекомендуется для использования в production.

    Args:
        phone_number: Номер телефона в строковом формате (например, "+4917612345678").

    Returns:
        True, если номер телефона соответствует базовым требованиям, False в противном случае.
    """

    # 1. Проверяем наличие плюса в начале.
    if not phone_number.startswith("+"):
        return False

    # 2. Проверяем, что после плюса идут только цифры.
    digits_only = phone_number[1:]  # Убираем плюс
    if not digits_only.isdigit():
        return False

    # 3. Проверяем минимальную длину номера (например, 8 цифр после плюса).
    if len(digits_only) < 10:
        return False

    # 4. Проверяем максимальную длину номера (например, 15 цифр после плюса).
    if len(digits_only) > 15:
        return False

    # Если все проверки пройдены, считаем, что номер соответствует базовым требованиям.
    return True



def validate_phone(phone: str) -> bool:
    """
    Проверяет, является ли строка корректным номером телефона.

    Args:
        phone: Строка для проверки.

    Returns:
        True, если строка является валидным номером телефона, иначе False.
    """
    if not isinstance(phone, str):
        return False
    return bool(re.match(PHONE_REGEX, phone))


def validate_age(age: str) -> bool:
    """
    Проверяет, является ли строка корректным возрастом (целое положительное число).
    Args:
        age: Строка для проверки

    Returns:
        True, если строка является валидным возрастом, иначе False.
    """
    if not isinstance(age, str):
        return False
    try:
        age = int(age)
        return 100 > age > 10
    except ValueError:
        return False




def validate_full_name(full_name: str) -> bool:
    """
    Проверяет, является ли введенное имя и фамилия корректными.  Имя и фамилия обязательны.

    Args:
        full_name (str): Полное имя пользователя (имя и фамилия, отчество опционально).

    Returns:
        bool: True, если имя и фамилия корректны, иначе False.
    """
    if not full_name:
        return False  # Имя не может быть пустым

    parts = full_name.split()
    if len(parts) < 2:  # Должно быть минимум два слова (имя и фамилия)
        return False

    # Проверяем каждое слово на соответствие шаблону
    pattern = r"^[A-Za-zА-Яа-яёЁ\s\-]+$"
    for part in parts:
        if not re.match(pattern, part):
            return False  # Если хоть одно слово содержит невалидные символы


    return True # если все проверки пройдены имя корректно





def validate_city_name(city_name: str) -> bool:
    """
    Проверяет, является ли введенное название города корректным.

    Args:
        city_name (str): Название города.

    Returns:
        bool: True, если название города корректно, иначе False.
    """
    if not city_name:
        return False  # Название города не может быть пустым

    # Регулярное выражение для проверки:
    # ^ - начало строки
    # [A-Za-zА-Яа-яёЁ\s\-\'] - любой символ из букв, пробелов, дефисов или апострофов
    # + - как минимум один символ должен быть в названии города
    # $ - конец строки
    pattern = r"^[A-Za-zА-Яа-яёЁ\s\-\']+$"
    if not re.match(pattern, city_name):
        return False  # Если название города содержит невалидные символы

    return True  # Если все проверки пройдены, название города корректно


# --- Функции валидации ---

async def validate_price(price: str) -> float | None:
    """Проверяет, является ли введенное значение ценой."""
    try:
        price_float = float(price)
        if price_float > 0:  # Проверка на положительное значение
            return price_float
        else:
            return None  # Цена должна быть положительной
    except ValueError:
        return None  # Не удалось преобразовать в число

async def validate_size(size: str) -> str:
    """Проверяет, что размер - это строка, или 'нет'."""
    size = size.lower()
    if size == "нет":
        return "нет"
    return size #Размер может быть любым

async def validate_color(color: str) -> str:
    """Проверяет, что цвет - это строка, или 'нет'."""
    color = color.lower()
    if color == "нет":
        return "нет"
    return color #Цвет может быть любым

async def validate_link(link: str) -> str | None:
    """Проверяет, что ссылка похожа на URL. (Базовая проверка)"""
    if link.startswith("http://") or link.startswith("https://"):
        return link
    else:
        return None  # Некорректная ссылка




if __name__ == '__main__':
    # Примеры использования
    print(f"Valid email: {validate_email('test@example.com')}")       # True
    print(f"Invalid email: {validate_email('invalid_email')}")       # False
    print(f"Valid phone: {validate_phone('+(155)512-34567')}")           # True
    print(f"Invalid phone: {validate_phone('1234567')}")          # False
    print(f"Valid age: {validate_age('25')}")           # True
    print(f"Invalid age: {validate_age('-5')}")          # False
    print(f"Invalid age: {validate_age('string')}")          # False

    name1 = "Иван Иванов иванович"
    name2 = "Петр-Иванов"
    name3 = "Anna Smith"
    name4 = "Иван123"
    name5 = ""
    name6 = "Иван   Иванов"

    print(f"'{name1}': {validate_full_name(name1)}")  # Выведет: 'Иван Иванов': True
    print(f"'{name2}': {validate_full_name(name2)}")  # Выведет: 'Петр-Иванов': True
    print(f"'{name3}': {validate_full_name(name3)}")  # Выведет: 'Anna Smith': True
    print(f"'{name4}': {validate_full_name(name4)}")  # Выведет: 'Иван123': False
    print(f"'{name5}': {validate_full_name(name5)}")  # Выведет: '': False
    print(f"'{name6}': {validate_full_name(name6)}")  # Выведет: 'Иван   Иванов': True


    # Пример использования:
    phone1 = "+4917612345678"
    phone2 = "4917612345678"  # Без плюса
    phone3 = "+12345678"  # Слишком короткий
    phone4 = "+491234567890123456"  # Слишком длинный
    phone5 = "+49176abcdefgh"  # Содержит буквы

    print(f"{phone1}: {validate_international_phone_number_basic(phone1)}")  # Вывод: +4917612345678: True
    print(f"{phone2}: {validate_international_phone_number_basic(phone2)}")  # Вывод: 4917612345678: False
    print(f"{phone3}: {validate_international_phone_number_basic(phone3)}")  # Вывод: +12345678: False
    print(f"{phone4}: {validate_international_phone_number_basic(phone4)}")  # Вывод: +491234567890123456: False
    print(f"{phone5}: {validate_international_phone_number_basic(phone5)}")  # Вывод: +49176abcdefgh: False

