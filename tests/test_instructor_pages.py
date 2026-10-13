"""Задачи 4.1–4.4 — статика инструктора: дословные тексты и wiring.
# Change: add-instructor-flow
# (sdd.md §15.1, §15.6; design.md, потоки 1/3/4; FR-10…FR-13, FR-17).

Трассировка TC (контракт 6, rule 6): кейсы test-model/approved/add-auth-cabinet/
TC-CAB-001…TC-CAB-006, TC-CAB-010 (браузерная часть — контроль wiring-фрагментов
в HTML, статус manual/toBeAutomated, паттерн tests/test_cabinet_page.py и
test_static.py: TC-REG-018, шаг 3) — здесь применяется тот же контроль к новым
страницам инструктора. Кейсы add-instructor-flow создаются QA-циклом (раздел 6);
эта autotest-база — wiring-часть TC-CAB-класса для новых страниц.

Маршруты статики появятся в задаче 5.1 — TestClient не участвует: файлы
frontend/ читаются напрямую и сверяются с мокапами design/mocks/ (тексты и
стили — дословно; отличия ТОЛЬКО wiring, sdd §15.6) и с wiring-фрагментами
(по паттерну test_cabinet_page.py / test_static.py).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
MOCKS = ROOT / "design" / "mocks"


def page(name: str) -> str:
    return (FRONTEND / name).read_text(encoding="utf-8")


# --- 4.1: frontend/instructors.html -------------------------------------------


def test_instructors_page_exists():
    """Готовность 4.1: файл существует; различия с мокапом — только wiring
    (CTA -> /instructors/apply, модалка контактов удалена, sdd §15.6)."""
    html = page("instructors.html")
    mockup = (MOCKS / "landing-instructors.html").read_text(encoding="utf-8")
    # грубая оценка: страница длиннее мокапа минус модалка — дословность
    # проверяется фрагментами в следующем тесте
    assert len(html) > 10_000
    assert "<!doctype html>" in html and "</html>" in html
    # модалка мокапа удалена (единственные удаления), остальное перенесено
    assert mockup.count("backdrop") > 0  # в мокапе модалка была



def test_instructors_landing_texts_verbatim():
    """FR-10: тексты/структура мокапа перенесены дословно (заголовок, hero,
    форматы, возможности, нижний CTA, футер) и CSS мокапа сохранен."""
    html = page("instructors.html")
    mockup = (MOCKS / "landing-instructors.html").read_text(encoding="utf-8")
    fragments = [
        "<title>СберАвтошкола — для инструкторов</title>",
        '<span><b style="color:var(--green);font-weight:650">Сбер</b>Автошкола<small>Платформа для инструкторов</small></span>',
        "Учи водить.<br><span>Меняй подход.</span>",
        "Подключайся к СберАвтошколе, работай с учениками и управляй занятиями в удобном цифровом формате. Выбирай, на каком автомобиле работать.",
        "Понятный процесс подключения · Цифровые инструменты · Прозрачные условия",
        "Два формата подключения",
        "Выбирай, как тебе удобнее работать",
        "У меня есть свой автомобиль",
        "Хочу работать на автомобиле Сбера",
        "Узнать условия и подать заявку",
        "Работа в новом формате",
        "Больше, чем расписание",
        "Поток учеников",
        "Гибкое расписание",
        "Прогресс обучения",
        "Готов подключиться?",
        "Оставь заявку — обсудим подходящий формат и условия сотрудничества.",
        "Стать инструктором ↗",
        "© СберАвтошкола · Концепт лендинга для инструкторов",
        "Условия подключения уточняются при рассмотрении заявки",
    ]
    for fragment in fragments:
        assert fragment in html, fragment
        assert fragment in mockup, f"фрагмент не из мокапа: {fragment}"

    # все CSS-правила мокапа — дословно (блочные строки <style>)
    mockup_css = mockup.split("<style>", 1)[1].split("</style>", 1)[0]
    page_css = html.split("<style>", 1)[1].split("</style>", 1)[0]
    for line in mockup_css.splitlines():
        if not line.strip():
            continue
        assert line in page_css, f"CSS-строка мокапа изменена/удалена: {line[:60]}"


def test_instructors_cta_wiring_to_apply():
    """FR-10: CTA («Стать инструктором» в шапке/hero, карточки форматов,
    нижний CTA) ведут на /instructors/apply (href, не fetch). Модальное окно
    сбора контактов не используется (форма заявки — отдельная страница)."""
    html = page("instructors.html")
    # шапка
    assert '<a class="header-cta" href="/instructors/apply">Стать инструктором ↗</a>' in html
    # hero
    assert '<a class="btn primary" href="/instructors/apply">Выбрать формат работы ↗</a>' in html
    # карточки форматов (обе)
    assert '<a href="/instructors/apply" class="choice" data-type="own">' in html
    assert '<a href="/instructors/apply" class="choice" data-type="sber">' in html
    # нижний CTA — редирект, не fetch
    assert "location.href='/instructors/apply'" in html
    assert "fetch(" not in html
    # модальное окно мокапа не используется как форма
    assert 'id="lead-form"' not in html
    assert 'id="modal"' not in html


def test_instructors_footer_without_driver_login():
    """Proposal: футер без входа водителей (out of scope)."""
    html = page("instructors.html")
    assert "Вход для водителей" not in html


# --- 4.2: frontend/instructor-apply.html --------------------------------------


def test_apply_page_texts_verbatim():
    """FR-11: анкета перенесена из мокапа дословно — тексты (ФИО одним полем,
    форматы, ВУ, согласие) и все CSS-строки мокапа."""
    html = page("instructor-apply.html")
    mockup = (MOCKS / "registration-instructor.html").read_text(encoding="utf-8")
    fragments = [
        "<title>Регистрация инструктора — СберАвтошкола</title>",
        "Подключение инструкторов",
        "Начнём<br>с <span style=\"color:#70efa5\">простого.</span>",
        "Оставь данные, выбери формат работы — команда СберАвтошколы свяжется с тобой и расскажет о следующих шагах.",
        "01 · Анкета",
        "02 · Проверка",
        "03 · Подключение",
        "Заявка инструктора",
        "Заполни поля, отмеченные звёздочкой. Остальные данные можно уточнить позднее.",
        "Этап 1 из 2",
        "Личные данные",
        'placeholder="Иванов Иван Иванович" required>',
        "Номер телефона",
        "Электронная почта",
        "Адрес фактического проживания",
        "Формат работы и автомобиль",
        "У меня есть свой автомобиль",
        "Хочу работать на автомобиле Сбера",
        "Государственный регистрационный номер автомобиля",
        "Если автомобиля нет, оставь поле пустым.",
        "Номер водительского удостоверения",
        "Дата выдачи удостоверения",
        "Категория прав",
        "Стаж вождения",
        "Документы",
        "Прикрепить фото или скан",
        "макет без реальной загрузки",
        "Я подтверждаю, что указал(а) корректные данные, и соглашаюсь на обработку персональных данных для рассмотрения заявки.",
        "Продолжить →",
        "© СберАвтошкола · Концепция экрана регистрации",
    ]
    for fragment in fragments:
        assert fragment in html, fragment
        assert fragment in mockup, f"фрагмент не из мокапа: {fragment}"

    mockup_css = mockup.split("<style>", 1)[1].split("</style>", 1)[0]
    page_css = html.split("<style>", 1)[1].split("</style>", 1)[0]
    for line in mockup_css.splitlines():
        if not line.strip():
            continue
        assert line in page_css, f"CSS-строка мокапа изменена/удалена: {line[:60]}"


def test_apply_password_fields_added():
    """Задача 4.2: пароль + подтверждение — два поля по спецификации задачи
    (макет их не содержит; контракт sdd §15.1: password, password_confirm)."""
    html = page("instructor-apply.html")
    assert 'id="password"' in html
    assert 'id="password-confirm"' in html
    assert 'name="password"' in html
    assert 'name="password-confirm"' in html
    # оба — password-инпуты с обязательной отметкой
    assert '<input id="password" name="password" type="password"' in html
    assert '<input id="password-confirm" name="password-confirm" type="password"' in html
    assert "Минимум 8 символов" in html


def test_apply_links_to_landing():
    """Задача 4.2: логотип/назад ведут на /instructors."""
    html = page("instructor-apply.html")
    assert '<a class="brand" href="/instructors">' in html
    assert '<a class="back" href="/instructors">← Вернуться на лендинг</a>' in html
    assert 'href="landing-instructors.html"' not in html


def test_apply_work_format_toggles_plate():
    """FR-11 (поведение мокапа): переключение own/sber управляет полем
    госномера (disabled при sber, очистка значения)."""
    js = page("instructor-apply.html").split("<script>", 1)[1]
    assert 'input[name="format"]' in js
    assert "updateFormat" in js
    assert "plate.disabled=!own" in js
    assert "if(!own)plate.value=''" in js


def test_apply_submit_wiring():
    """FR-11/FR-12: сабмит -> POST /api/instructors/apply по контракту
    sdd §15.1; 200 -> редирект /instructors/pending; 422 -> сообщение под
    формой (текст из ответа); sessionStorage НЕ используется; файл ВУ в тело
    запроса не входит."""
    html = page("instructor-apply.html")
    js = html.split("<script>", 1)[1]
    assert "fetch('/api/instructors/apply'" in js
    assert "method:'POST'" in js
    assert "'Content-Type':'application/json'" in js
    # поля контракта sdd §15.1 в теле запроса
    for field in (
        "fio:", "phone:", "email:", "address:", "work_format:", "plate:",
        "license_number:", "license_date:", "license_category:", "experience:",
        "password:", "password_confirm:", "consent:",
    ):
        assert field in js, field
    # 200 -> редирект на экран ожидания
    assert "location.href='/instructors/pending'" in js
    # 422 -> сообщение из ответа под формой
    assert "res.data.error" in js
    assert "notice.classList.add('show')" in js
    # consent читается из чекбокса согласия
    assert ".checkline input" in js
    # sessionStorage не нужен (сессия по заявке не выдается)
    assert "sessionStorage" not in html
    # файл ВУ не входит в тело запроса: FormData не используется,
    # license-file в payload отсутствует
    assert "FormData" not in js
    assert "license-file" not in js.split("payload={", 1)[1].split("};", 1)[0]
    # id полей совпадают с макетом (кроме добавленных password-полей)
    for element_id in (
        "fio", "phone", "email", "address", "plate", "license-number",
        "license-date", "license-category", "experience", "notice",
    ):
        assert f'id="{element_id}"' in html, element_id


# --- 4.3: pending / rejected ----------------------------------------------------


def test_pending_page_exists_and_text():
    """FR-12/FR-17: экран «заявка на рассмотрении» — в тоне анкеты/лендинга;
    при загрузке статус НЕ проверяется (проверка при логине, FR-13)."""
    html = page("instructor-pending.html")
    assert "Заявка на рассмотрении" in html
    assert "Заявка инструктора" in html
    assert "СберАвтошкола" in html
    assert "Анкета отправлена" in html
    # ссылка «На главную» -> /
    assert 'href="/">На главную</a>' in html
    # страница — просто экран: ни fetch, ни sessionStorage
    assert "fetch(" not in html
    assert "sessionStorage" not in html


def test_rejected_page_exists_and_reason_wiring():
    """FR-13/FR-17: экран «отклонено» с причиной из ответа логина
    (sessionStorage); пусто/нет — без персональной причины (чужую не
    раскрываем, design); статус при загрузке НЕ проверяется."""
    html = page("instructor-rejected.html")
    assert "Заявка отклонена" in html
    assert "Причина отказа" in html
    assert 'href="/">На главную</a>' in html
    assert "fetch(" not in html
    # причина — из sessionStorage (пишет модалка входа при route=rejected)
    assert "sessionStorage" in html
    assert "instructor_rejected_reason" in html
    # пусто/нет ключа -> блок причины скрыт
    assert "reason-block" in html
    assert "style.display = ''" in html


# --- 4.4: instructor-cabinet-stub -----------------------------------------------


def test_cabinet_stub_exists_and_text():
    """FR-13: заглушка «кабинет скоро» в стиле кабинета (референс
    dashboard-instructor.html: сайдбар/шапка), БЕЗ функциональных блоков."""
    html = page("instructor-cabinet-stub.html")
    assert "Кабинет скоро" in html
    assert "Кабинет инструктора" in html
    assert "СберАвтошкола" in html
    # функциональных блоков dashboard-макета нет (вне объема)
    for forbidden in (
        "Расписание занятий", "Ближайшее занятие", "Мой автомобиль",
        "Последние операции", "Быстрые действия", "Заработано за месяц",
    ):
        assert forbidden not in html, forbidden
    assert 'href="/">На главную</a>' in html


def test_cabinet_stub_session_guard_wiring():
    """FR-13: JS читает токен из sessionStorage, GET /api/auth/me
    (X-Session-Token) -> 401 -> редирект на вход; 200 -> показ заглушки
    (по паттерну cabinet.html Спринта 1)."""
    js = page("instructor-cabinet-stub.html").split("<script>", 1)[1]
    assert "sessionStorage" in js
    assert "session_token" in js
    assert "fetch('/api/auth/me'" in js
    assert "'X-Session-Token'" in js
    assert "location.href = '/'" in js
