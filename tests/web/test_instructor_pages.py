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

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
MOCKS = ROOT / "design" / "mocks"


def page(name: str) -> str:
    return (FRONTEND / name).read_text(encoding="utf-8")


# --- 4.1: лендинг инструкторов — вход каркаса Vue (Спринт 14, change
# add-vue-s14-instructor-loop, задача 4.1): источник чтения переключен с
# удаленного legacy instructors.html + js/instructors.js на вход
# frontend/vue/instructors.html + App.vue + styles.css (прецедент 2.3
# пилота, 3.1 С11 и 4.1 С12); тексты/якоря/контракты не меняются,
# стековые wiring-фрагменты — задокументированные эквиваленты Vue
# (design.md «Границы правок тестов»); фрагменты контракта входа —
# дословно в App.vue/loginWiring.js.


def vue_instructors_page() -> str:
    """Вход лендинга каркаса Vue (статическая разметка 1:1) + styles.css
    (носитель CSS — подключаемый файл, перенос дословный) — эквивалент
    легаси page("instructors.html") (HTML с инлайн-<style>)."""
    base = FRONTEND / "vue"
    return "\n".join([
        (base / "instructors.html").read_text(encoding="utf-8"),
        (base / "src" / "pages" / "instructors" / "styles.css").read_text(
            encoding="utf-8"),
    ])


def vue_instructors_source() -> str:
    """Вход + App.vue (wiring js/instructors.js 1:1) + композабл входа
    shared/loginWiring.js (консолидация wiring — задача 3.1) — эквивалент
    frontend_source("instructors.html") (HTML + модуль)."""
    base = FRONTEND / "vue"
    return "\n".join([
        (base / "instructors.html").read_text(encoding="utf-8"),
        (base / "src" / "pages" / "instructors" / "App.vue").read_text(
            encoding="utf-8"),
        (base / "src" / "shared" / "loginWiring.js").read_text(
            encoding="utf-8"),
    ])


def test_instructors_page_exists():
    """Готовность 4.1: вход каркаса Vue существует (с styles.css);
    различия с мокапом — только wiring (CTA -> /instructors/apply,
    модалка контактов удалена, sdd §15.6)."""
    html = vue_instructors_page()
    mockup = (MOCKS / "landing-instructors.html").read_text(encoding="utf-8")
    # грубая оценка: страница длиннее мокапа минус модалка — дословность
    # проверяется фрагментами в следующем тесте
    assert len(html) > 10_000
    assert "<!doctype html>" in html and "</html>" in html
    # модалка мокапа удалена (единственные удаления), остальное перенесено
    assert mockup.count("backdrop") > 0  # в мокапе модалка была



def test_instructors_landing_texts_verbatim():
    """FR-10: тексты/структура мокапа перенесены дословно (заголовок, hero,
    форматы, возможности, нижний CTA, футер) и CSS мокапа сохранен
    (носитель CSS — styles.css страницы каркаса, перенос дословный)."""
    html = (FRONTEND / "vue" / "instructors.html").read_text(encoding="utf-8")
    mockup = (MOCKS / "landing-instructors.html").read_text(encoding="utf-8")
    fragments = [
        "<title>СберАвтошкола — для инструкторов</title>",
        '<span><em style="font-style:normal;color:var(--green)">Сбер</em>Автошкола<small>Платформа для инструкторов</small></span>',
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

    # все CSS-правила мокапа — дословно (носитель — styles.css страницы
    # каркаса; блочные строки <style> мокапа)
    mockup_css = mockup.split("<style>", 1)[1].split("</style>", 1)[0]
    page_css = (FRONTEND / "vue" / "src" / "pages" / "instructors"
                / "styles.css").read_text(encoding="utf-8")
    for line in mockup_css.splitlines():
        if not line.strip():
            continue
        assert line in page_css, f"CSS-строка мокапа изменена/удалена: {line[:60]}"


def test_instructors_cta_wiring_to_apply():
    """FR-10: CTA («Стать инструктором» в шапке/hero, карточки форматов,
    нижний CTA) ведут на /instructors/apply (href, не fetch). Модальное окно
    сбора контактов не используется (форма заявки — отдельная страница).
    Спринт 6 Партия B: клик-редирект нижнего CTA — в модуле js/instructors.js
    (проверяем HTML + модуль, см. frontend_source). Спринт 14 (задача 4.1):
    носитель — вход + App.vue + loginWiring.js (vue_instructors_source);
    фрагменты контракта дословны."""
    html = (FRONTEND / "vue" / "instructors.html").read_text(encoding="utf-8")
    src = vue_instructors_source()
    # шапка
    assert '<a class="header-cta" href="/instructors/apply">Стать инструктором ↗</a>' in html
    # hero
    assert '<a class="btn primary" href="/instructors/apply">Выбрать формат работы ↗</a>' in html
    # карточки форматов (обе)
    assert '<a href="/instructors/apply" class="choice" data-type="own">' in html
    assert '<a href="/instructors/apply" class="choice" data-type="sber">' in html
    # нижний CTA — редирект, не fetch (редирект — в модуле)
    assert "location.href='/instructors/apply'" in src
    # BUG-055: «Войти» открывает логин-модалку НА МЕСТЕ (без редиректа на /),
    # сабмит модалки — POST /api/auth/login через fetch (легитимный fetch
    # контура логина; CTA apply по-прежнему редиректом)
    assert 'data-open-login' in src
    assert "postJSON('/api/auth/login'" in src
    assert "location.href='/';" not in src
    # модальное окно мокапа не используется как форма
    assert 'id="lead-form"' not in html
    assert 'id="modal"' not in html


def test_instructors_footer_without_driver_login():
    """Proposal: футер без входа водителей (out of scope)."""
    html = (FRONTEND / "vue" / "instructors.html").read_text(encoding="utf-8")
    assert "Вход для водителей" not in html


# --- 4.2: анкета инструктора — вход каркаса Vue (Спринт 12, change
# add-vue-s12-landing-apply, задача 4.1): источник чтения переключен с
# удаленного legacy instructor-apply.html + js/apply.js на вход
# frontend/vue/instructor-apply.html + App.vue + styles.css (прецедент
# 2.3 пилота и 3.1 С11); тексты/якоря/контракты не меняются, стековые
# wiring-фрагменты — задокументированные эквиваленты Vue (design.md
# «Границы правок тестов»).


def vue_apply_page() -> str:
    """Вход анкеты каркаса Vue (статическая разметка 1:1)."""
    return (FRONTEND / "vue" / "instructor-apply.html").read_text(
        encoding="utf-8"
    )


def vue_apply_source() -> str:
    """Вход анкеты + App.vue (wiring) — эквивалент frontend_source
    легаси (HTML + модуль)."""
    base = FRONTEND / "vue"
    return "\n".join([
        (base / "instructor-apply.html").read_text(encoding="utf-8"),
        (base / "src" / "pages" / "instructor-apply" / "App.vue").read_text(
            encoding="utf-8"),
    ])


def test_apply_page_texts_verbatim():
    """FR-11: анкета перенесена из мокапа дословно — тексты (ФИО одним полем,
    форматы, ВУ, согласие) и все CSS-строки мокапа (носитель CSS —
    styles.css страницы каркаса, перенос дословный)."""
    html = vue_apply_page()
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
        'placeholder="Иванов" required>',
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
        "Я подтверждаю, что указал(а) корректные данные, и соглашаюсь на обработку персональных данных для рассмотрения заявки.",
        "Продолжить →",
        "© СберАвтошкола · Концепция экрана регистрации",
    ]
    for fragment in fragments:
        assert fragment in html, fragment
        assert fragment in mockup, f"фрагмент не из мокапа: {fragment}"
    # BUG-048: реальная загрузка вместо макета — дословная подпись макета
    # «макет без реальной загрузки» убрана (Заказчик 2026-10-21)
    assert "макет без реальной загрузки" not in html

    mockup_css = mockup.split("<style>", 1)[1].split("</style>", 1)[0]
    page_css = (FRONTEND / "vue" / "src" / "pages" / "instructor-apply"
                / "styles.css").read_text(encoding="utf-8")
    for line in mockup_css.splitlines():
        if not line.strip():
            continue
        assert line in page_css, f"CSS-строка мокапа изменена/удалена: {line[:60]}"


def test_apply_password_fields_added():
    """Задача 4.2: пароль + подтверждение — два поля по спецификации задачи
    (макет их не содержит; контракт sdd §15.1: password, password_confirm)."""
    html = vue_apply_page()
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
    html = vue_apply_page()
    assert '<a class="brand" href="/instructors">' in html
    assert '<a class="back" href="/instructors">← Вернуться на лендинг</a>' in html
    assert 'href="landing-instructors.html"' not in html


def test_apply_work_format_toggles_plate():
    """FR-11 (поведение мокапа): переключение own/sber управляет полем
    госномера (disabled при sber, очистка значения). Спринт 12 (задача
    4.1): носитель — вход + App.vue; фрагменты updateFormat/plate.disabled/
    if(!own)plate.value='' заменены эквивалентами Vue — реактивная связь
    radio формата с состоянием поля госномера (disabled/очистка/
    приглушение — design.md «Границы правок тестов»)."""
    js = vue_apply_source()
    assert 'input[name="format"]' in js
    # эквивалент plate.disabled=!own — :disabled от реактивного состояния
    assert ":disabled=\"plateDisabled\"" in js
    # эквивалент if(!own)plate.value='' — очистка при sber (watch формата)
    assert "plate.value = ''" in js
    # эквивалент приглушения (plateWrap.style.opacity .55 при sber)
    assert "opacity" in js and "'.55'" in js


def test_apply_submit_wiring():
    """FR-11/FR-12 + BUG-048 (Заказчик 2026-10-21): сабмит -> POST
    /api/instructors/apply, multipart/form-data со всеми полями анкеты и
    файлом ВУ (license_photo); 200 -> редирект /instructors/pending;
    413/415/422 -> видимое сообщение у поля загрузки и под формой;
    sessionStorage НЕ используется; клиентская валидация файла
    (JPEG/PNG <= 5 МБ) блокирует отправку. Спринт 12 (задача 4.1):
    носитель — вход + App.vue; фрагмент notice.classList.add('show')
    заменен эквивалентом Vue — класс show notice из реактивного
    состояния (design.md «Границы правок тестов»), остальные фрагменты
    дословны."""
    js = vue_apply_source()
    assert "fetch('/api/instructors/apply'" in js
    assert "method:'POST'" in js
    # BUG-048: multipart FormData с файлом ВУ (JSON больше не используется)
    assert "new FormData()" in js
    assert "fd.append('license_photo'" in js
    # поля контракта sdd §15.1 в теле запроса
    for field in (
        "fd.append('surname'", "fd.append('phone'", "fd.append('email'",
        "fd.append('address'", "fd.append('work_format'", "fd.append('plate'",
        "fd.append('license_number'", "fd.append('license_date'",
        "fd.append('license_category'", "fd.append('experience'",
        "fd.append('password'", "fd.append('password_confirm'",
        "fd.append('consent'",
    ):
        assert field in js, field
    # 200 -> редирект на экран ожидания
    assert "location.href='/instructors/pending'" in js
    # 422 -> сообщение из ответа под формой
    assert "res.data.error" in js
    # эквивалент Vue «notice.classList.add('show')»: класс show notice
    # из реактивного состояния
    assert 'noticeShow.value=true' in js
    assert ':class="{show: noticeShow}"' in js
    # consent читается из чекбокса согласия
    assert ".checkline input" in js
    # sessionStorage не нужен (сессия по заявке не выдается) — ни во
    # входе, ни в App.vue
    assert "sessionStorage" not in js
    # клиентская валидация файла: тип и размер до отправки
    assert "5*1024*1024" in js
    assert "validateLicenseFile" in js
    # id полей совпадают с макетом (кроме добавленных password-полей)
    html = vue_apply_page()
    for element_id in (
        "surname", "name", "patronymic", "phone", "email", "address", "plate", "license-number",
        "license-date", "license-category", "experience", "notice",
    ):
        assert f'id="{element_id}"' in html, element_id


# --- 4.3: pending / rejected ----------------------------------------------------


def test_pending_page_exists_and_text():
    """FR-12/FR-17: экран «заявка на рассмотрении» — в тоне анкеты/лендинга;
    при загрузке статус НЕ проверяется (проверка при логине, FR-13).
    Спринт 9 (change add-vue-framework-pilot, задача 2.3): источник чтения
    переключен с удаленного legacy instructor-pending.html на вход пилотной
    страницы каркаса Vue frontend/vue/instructors-pending.html — проверяемые
    тексты/селекторы/URL не меняются, маршрут сохранен (design.md
    «Миграция legacy-тестов страницы ожидания»)."""
    html = (FRONTEND / "vue" / "instructors-pending.html").read_text(
        encoding="utf-8"
    )
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
    раскрываем, design); статус при загрузке НЕ проверяется. Спринт 11
    (change add-vue-s11-status-forms, задача 3.1): источник чтения
    переключен с удаленного legacy instructor-rejected.html на вход экрана
    каркаса Vue frontend/vue/instructors-rejected.html + компонент App.vue
    (прецедент 2.3 пилота) — тексты/ключ sessionStorage дословны;
    «style.display = ''» — стековый фрагмент legacy, эквивалент Vue —
    v-show (design.md «Границы правок тестов»)."""
    html = (FRONTEND / "vue" / "instructors-rejected.html").read_text(
        encoding="utf-8"
    )
    src = "\n".join([
        html,
        (FRONTEND / "vue" / "src" / "pages" / "instructor-rejected"
         / "App.vue").read_text(encoding="utf-8"),
    ])
    assert "Заявка отклонена" in html
    assert "Причина отказа" in html
    assert 'href="/">На главную</a>' in html
    # страница — просто экран: ни fetch, ни статусного запроса при загрузке
    assert "fetch(" not in src
    # причина — из sessionStorage (пишет модалка входа при route=rejected)
    assert "sessionStorage" in src
    assert "instructor_rejected_reason" in src
    # пусто/нет ключа -> блок причины скрыт
    assert "reason-block" in src
    # эквивалент Vue стекового фрагмента legacy «style.display = ''»:
    # блок показывается только при наличии причины (v-show)
    assert 'v-show="reason"' in src


# --- 4.4 (заглушка кабинета инструктора): тесты страницы удалены вместе со
# страницей (Спринт 14, change add-vue-s14-instructor-loop, задача 1.1 —
# прецедент «судьба legacy-тестов удаленной страницы», arch-review-002
# MAJ-1 пилота: заглушка недостижима с Спринта 2.2, удалена решением
# Заказчика; маршрут снят из _PAGE_ROUTES backend/app.py).
