<!--
Reviewer-Delegation: deleg-cr-bug0547-external
Reviewer: code_reviewer (AI Factory, независимая сессия; плейсхолдер id — ПМ заменит)
Дифф: bugfix/s9-ui-followup-2 vs main. Коммит задачи: 2fc7c15 (fix BUG-054), тест-доки 62c0cf0/22108a2.
Диапазон из задания d081bcf..HEAD шире скоупа: содержит уже влитый в main Спринт 9
(merge-base ветки с main = 42367e1, дерево ветки = main + 5 коммитов: 22108a2, 2fc7c15,
4ccda45, 361453f, 62c0cf0 — 15 файлов, +303/−20). Ревьюировался дельта-дифф ветки main..HEAD.
Дата ревью: 2026-11-04
-->

# Code Review — BUG-054 (m-view: стрелки навигации фото)

## Что проверено (Scenario)

1. **Обе стрелки в разметке и JS** — instructor-dashboard.html:679-680: `#view-prev`/`#view-next`, классы `.navarrow prev/.next`, `type="button"`, aria-label; CSS `.navarrow` (:271-273) — absolute поверх `.full` (position:relative, :342), z-index:4 над `img`. «НАД фотографией» — подтверждено: стрелки позиционированы внутри `.viewer .full` поверх `#view-img`.
2. **Листание доступного набора** — mcOpenViewCarPhotos (dashboard-instructor.js:697-704): `mcGalKeys().filter(mcGalLoaded)` — загруженные ракурсы + СТС по `has_sts`; пустой набор → `return`. Вход из плитки только при `loaded.length||c.has_sts` (:658) — значок и набор всегда согласованы.
3. **Цикличность** — mcNavView (:1153-1156): `(ix+dir+len)%len`. **Заголовок** — mcShowViewPhoto (:1148-1160): view-title/sub = название/мета ТЕКУЩЕГО кадра, через textContent.
4. **Singleton без стрелок** — в разметке инлайн `style="display:none"`; mcShowViewPhoto ставит `display:''/'none'` по `mcViewPhotos.length>1`. Документ-одиночка (вызов :1237 совместим с новой сигнатурой photos|single).
5. **Esc/крестик закрывают** — общий keydown-контур дашборда (:729) → mcCloseView; `#view-close` → mcCloseView (:1175).
6. **Клик по стрелке окно не закрывает** — stopPropagation на слушателях (:1173-1174).
7. **XSS/авторизация** — title/sub только textContent; фото через mcLoadImg (:565, XHR blob + X-Session-Token, кэш objectURL) — `<img src>` напрямую не светит токен.
8. **hintview span→button** (:659-661) — CSS `.shot .hintview` (:270) задает все визуальные свойства (фон/рамка/паддинги/радиус), `button{cursor:pointer}input{font:inherit}` — визуальной деградации нет; по плитке клик прежний (карточка-галерея, FR-63).
9. **Смок ревьюера** (реальный uvicorn + Playwright, page.route-моки): 12/12 проверок green — обе стрелки видны при 3 фото (front/rear/СТС), листание Спереди→Сзади→СТС, цикл за 3 шага вернулся на первый кадр, ‹ вернул назад, окно не закрылось по стрелке, Esc закрыл, авто без фото/СТС — без значка, одиночный документ — стрелки скрыты. Полный вывод: scratch/bug0547_smoke.py.

## Вердикт: approve

## Замечания

| # | Серьезность | Файл:строка | Замечание | Рекомендация |
|---|---|---|---|---|
| 1 | minor | tests/ (отсутствие) | Автоматизированного e2e на листание m-view в сьюте нет — test-model/BUG-054 честно заявляет только «прогон мока». Регресс этого поведения держится на ручном прогоне; TC-UI-033 покрывает лишь одиночный документ (стрелки скрыты). | Добавить e2e по образцу TC-UI-034 (page.route-моки cars+PNG): открыть m-view из плитки, обе стрелки видны, next×3 → первый кадр, Esc. Смок ревьюера (31/32) может служить референсом. |

## Не проверено

- Визуальный вид на-eye (позиция стрелок относительно реальных фото разных пропорций) — только computed-геометрия и Playwright visibility.
- Полный pytest-сьют не запускался (указание ПМ: 409 passed полный сьют); точечный регресс ревьюера — см. отчет.
