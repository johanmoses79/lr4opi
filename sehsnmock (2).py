from datetime import datetime


class CheckIn:
    """Представляє одну сесію присутності учасника в локації."""

    def __init__(self, location_id):
        self.location_id = location_id
        self.timestamp = datetime.now()
        self.active = True

    def end_session(self):
        """Завершує сесію — позначає її як неактивну."""
        self.active = False


class Member:
    """
    Активний учасник платформи Seshn Networks.
    Відповідає за чекін, пошук сусідів та надсилання запитів на знайомство.
    """

    ALLOWED_SKILLS = {"design", "dev", "marketing", "pm", "data", "other"}
    MAX_SKILLS = 5

    def __init__(self, user_id, name, email):
        # Перевіряємо обов'язкові поля перед збереженням
        if not user_id or not isinstance(user_id, str):
            raise ValueError("user_id must be a non-empty string")
        if "@" not in email:
            raise ValueError(f"Invalid email: {email}")

        self.user_id = user_id
        self.name = name
        self.email = email
        self.skills = []
        self.check_in = None          # активний об'єкт CheckIn або None
        self._pending_requests = []   # user_id надісланих запитів

    def check_in_location(self, location_id):
        """
        Виконує чекін у локації.
        Якщо вже зареєстрований у тій самій — повертає поточну сесію.
        Якщо змінює локацію — спочатку закриває попередню сесію.
        """
        if not location_id:
            raise ValueError("location_id cannot be empty")

        if self.check_in and self.check_in.active:
            # Та сама локація — нічого не робимо
            if self.check_in.location_id == location_id:
                return self.check_in
            # Інша локація — закриваємо попередню сесію
            self.check_in.end_session()

        self.check_in = CheckIn(location_id)
        return self.check_in

    def get_nearby_members(self, all_members, skill_filter=None):
        """
        Повертає учасників, які зараз зареєстровані в тій самій локації.
        Опційно фільтрує за навичкою.
        Генерує виняток, якщо поточний учасник не зареєстрований.
        """
        if not self.check_in or not self.check_in.active:
            raise RuntimeError("You must be checked in to see nearby members")

        nearby = []
        for m in all_members:
            # Пропускаємо себе
            if m.user_id == self.user_id:
                continue
            # Пропускаємо тих, хто не зареєстрований
            if not m.check_in or not m.check_in.active:
                continue
            # Пропускаємо учасників з іншої локації
            if m.check_in.location_id != self.check_in.location_id:
                continue
            # Застосовуємо фільтр за навичкою, якщо вказано
            if skill_filter and skill_filter not in m.skills:
                continue
            nearby.append(m)

        return nearby

    def send_connection_request(self, target):
        """
        Надсилає запит на знайомство іншому учаснику.
        Правила:
          - Не можна надіслати запит самому собі.
          - Обидва учасники мають бути в одній активній локації.
          - Повторний запит ігнорується — повертається повідомлення про статус.
        """
        if target.user_id == self.user_id:
            raise ValueError("Cannot send a request to yourself")

        # Обидві сторони мають бути присутні в одній локації
        if (
            not self.check_in or not self.check_in.active
            or not target.check_in or not target.check_in.active
            or self.check_in.location_id != target.check_in.location_id
        ):
            raise RuntimeError("Both members must be at the same active location")

        # Запобігаємо дублюванню запитів
        if target.user_id in self._pending_requests:
            return f"Request to {target.name} already pending"

        self._pending_requests.append(target.user_id)
        return f"Request sent to {target.name}"

    def update_skills(self, skills):
        """
        Валідує та замінює список навичок учасника.
        Перевіряє максимальну кількість та допустимі значення.
        """
        if len(skills) > self.MAX_SKILLS:
            raise ValueError(f"Max {self.MAX_SKILLS} skills allowed")

        validated = []
        for s in skills:
            s = s.lower().strip()
            # Відхиляємо навички поза дозволеним переліком
            if s not in self.ALLOWED_SKILLS:
                raise ValueError(f"Unknown skill: '{s}'")
            validated.append(s)

        self.skills = validated
# test_member.py — Seshn Networks, модульні тести
# Фреймворк: pytest
# Патерн: AAA (Arrange / Act / Assert)

import pytest
from member import Member, CheckIn


# ──────────────────────────────────────────────
# __init__
# ──────────────────────────────────────────────

def test_init_valid():
    # EP / позитивний — допустимі значення user_id та email
    # Arrange
    user_id, name, email = "u1", "Ivan", "ivan@test.com"
    # Act
    m = Member(user_id, name, email)
    # Assert
    assert m.user_id == "u1"
    assert m.email == "ivan@test.com"


def test_init_empty_user_id():
    # EP / негативний — порожній рядок є недопустимим класом для user_id
    # Arrange
    user_id = ""
    # Act / Assert
    with pytest.raises(ValueError):
        Member(user_id, "Ivan", "ivan@test.com")


def test_init_none_user_id():
    # EP / негативний — None є недопустимим типом для user_id
    # Arrange
    user_id = None
    # Act / Assert
    with pytest.raises(ValueError):
        Member(user_id, "Ivan", "ivan@test.com")


def test_init_valid_email():
    # EP / позитивний — email містить символ "@"
    # Arrange
    email = "a@b.com"
    # Act
    m = Member("u2", "Ivan", email)
    # Assert
    assert m.email == email


def test_init_invalid_email():
    # EP / негативний — email без символу "@"
    # Arrange
    email = "notanemail"
    # Act / Assert
    with pytest.raises(ValueError):
        Member("u3", "Ivan", email)


# ──────────────────────────────────────────────
# check_in_location
# ──────────────────────────────────────────────

def test_checkin_empty_location_id():
    # EP / негативний — порожній рядок є недопустимим значенням location_id
    # Arrange
    m = Member("u1", "Ivan", "ivan@test.com")
    # Act / Assert
    with pytest.raises(ValueError):
        m.check_in_location("")


def test_checkin_first_time():
    # EP / позитивний — перший чекін, сесії ще немає
    # Arrange
    m = Member("u1", "Ivan", "ivan@test.com")
    # Act
    checkin = m.check_in_location("loc1")
    # Assert
    assert checkin.active is True
    assert checkin.location_id == "loc1"


def test_checkin_same_location_returns_same_object():
    # BVA / позитивний — межа: повторний чекін у ту саму локацію
    # Arrange
    m = Member("u1", "Ivan", "ivan@test.com")
    first = m.check_in_location("loc1")
    # Act
    second = m.check_in_location("loc1")
    # Assert
    assert first is second


def test_checkin_different_location_closes_old_session():
    # BVA / позитивний — межа: зміна локації закриває попередню сесію
    # Arrange
    m = Member("u1", "Ivan", "ivan@test.com")
    old = m.check_in_location("loc1")
    # Act
    new = m.check_in_location("loc2")
    # Assert
    assert old.active is False
    assert new.active is True
    assert new.location_id == "loc2"


# ──────────────────────────────────────────────
# get_nearby_members
# ──────────────────────────────────────────────

def test_nearby_raises_when_not_checked_in():
    # EP / негативний — виклик без активної сесії
    # Arrange
    m = Member("u1", "Ivan", "ivan@test.com")
    # Act / Assert
    with pytest.raises(RuntimeError):
        m.get_nearby_members([])


def test_nearby_empty_list():
    # BVA / позитивний — межа: 0 учасників у списку
    # Arrange
    m = Member("u1", "Ivan", "ivan@test.com")
    m.check_in_location("loc1")
    # Act
    result = m.get_nearby_members([])
    # Assert
    assert result == []


def test_nearby_different_location_excluded():
    # EP / позитивний — учасник в іншій локації не потрапляє у результат
    # Arrange
    m = Member("u1", "Ivan", "ivan@test.com")
    m.check_in_location("loc1")
    other = Member("u2", "Olena", "olena@test.com")
    other.check_in_location("loc2")
    # Act
    result = m.get_nearby_members([other])
    # Assert
    assert result == []


def test_nearby_same_location_included():
    # EP / позитивний — учасник у тій самій локації потрапляє у результат
    # Arrange
    m = Member("u1", "Ivan", "ivan@test.com")
    m.check_in_location("loc1")
    other = Member("u2", "Olena", "olena@test.com")
    other.check_in_location("loc1")
    # Act
    result = m.get_nearby_members([other])
    # Assert
    assert other in result


def test_nearby_skill_filter_match():
    # BVA / позитивний — межа: skill_filter збігається зі скілом учасника
    # Arrange
    m = Member("u1", "Ivan", "ivan@test.com")
    m.check_in_location("loc1")
    other = Member("u2", "Olena", "olena@test.com")
    other.check_in_location("loc1")
    other.skills = ["dev"]
    # Act
    result = m.get_nearby_members([other], skill_filter="dev")
    # Assert
    assert other in result


def test_nearby_skill_filter_no_match():
    # BVA / негативний — межа: skill_filter не збігається зі скілом учасника
    # Arrange
    m = Member("u1", "Ivan", "ivan@test.com")
    m.check_in_location("loc1")
    other = Member("u2", "Olena", "olena@test.com")
    other.check_in_location("loc1")
    other.skills = ["dev"]
    # Act
    result = m.get_nearby_members([other], skill_filter="pm")
    # Assert
    assert result == []


# ──────────────────────────────────────────────
# send_connection_request
# ──────────────────────────────────────────────

def test_request_to_self_raises():
    # EP / негативний — запит самому собі є недопустимим
    # Arrange
    m = Member("u1", "Ivan", "ivan@test.com")
    m.check_in_location("loc1")
    # Act / Assert
    with pytest.raises(ValueError):
        m.send_connection_request(m)


def test_request_target_not_checked_in():
    # BVA / негативний — межа: target не має активної сесії
    # Arrange
    m = Member("u1", "Ivan", "ivan@test.com")
    m.check_in_location("loc1")
    target = Member("u2", "Olena", "olena@test.com")
    # Act / Assert
    with pytest.raises(RuntimeError):
        m.send_connection_request(target)


def test_request_different_locations():
    # EP / негативний — учасники в різних локаціях
    # Arrange
    m = Member("u1", "Ivan", "ivan@test.com")
    m.check_in_location("loc1")
    target = Member("u2", "Olena", "olena@test.com")
    target.check_in_location("loc2")
    # Act / Assert
    with pytest.raises(RuntimeError):
        m.send_connection_request(target)


def test_request_success():
    # EP / позитивний — обидва учасники в одній локації
    # Arrange
    m = Member("u1", "Ivan", "ivan@test.com")
    m.check_in_location("loc1")
    target = Member("u2", "Olena", "olena@test.com")
    target.check_in_location("loc1")
    # Act
    result = m.send_connection_request(target)
    # Assert
    assert result == "Request sent to Olena"


def test_request_duplicate():
    # BVA / негативний — межа: повторний запит до того самого учасника
    # Arrange
    m = Member("u1", "Ivan", "ivan@test.com")
    m.check_in_location("loc1")
    target = Member("u2", "Olena", "olena@test.com")
    target.check_in_location("loc1")
    m.send_connection_request(target)
    # Act
    result = m.send_connection_request(target)
    # Assert
    assert result == "Request to Olena already pending"




def test_skills_empty_list():
    # BVA / позитивний — межа: 0 навичок є допустимим значенням
    # Arrange
    m = Member("u1", "Ivan", "ivan@test.com")
    # Act
    m.update_skills([])
    # Assert
    assert m.skills == []


def test_skills_max_allowed():
    # BVA / позитивний — межа: рівно MAX_SKILLS (5) навичок
    # Arrange
    m = Member("u1", "Ivan", "ivan@test.com")
    skills = ["dev", "pm", "design", "data", "other"]
    # Act
    m.update_skills(skills)
    # Assert
    assert len(m.skills) == 5


def test_skills_over_max():
    # BVA / негативний — межа+1: 6 навичок перевищують MAX_SKILLS
    # Arrange
    m = Member("u1", "Ivan", "ivan@test.com")
    skills = ["dev", "pm", "design", "data", "other", "marketing"]
    # Act / Assert
    with pytest.raises(ValueError):
        m.update_skills(skills)


def test_skills_invalid_value():
    # EP / негативний — значення поза ALLOWED_SKILLS
    # Arrange
    m = Member("u1", "Ivan", "ivan@test.com")
    # Act / Assert
    with pytest.raises(ValueError):
        m.update_skills(["hacking"])