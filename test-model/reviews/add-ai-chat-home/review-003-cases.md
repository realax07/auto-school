<!-- Запись ПМ (составлено из сессии ревьюера): перевод вердикта review-002-cases
     (verdict: approve, сессия 20261119_165739_193dd6, commit ef687c7) в форму
     контракта 5 — для ворот approved-партии требуется вердикт дословно
     «одобрить». Машинные проверки ревью — в review-002-cases.md. -->

# Review-003-cases — утвержденная партия TC-кейсов add-ai-chat-home

- Ревьюер: qa_case_reviewer (сессия 20261119_165739_193dd6, review-002-cases)
- Объект: фикс fe90b00 (MAJ-1 MAN-001 + MIN-1 UNIT-001) поверх review-001-cases
- Партия: 9 TC-кейсов + checklist.md, перенесены вербатим в
  test-model/approved/add-ai-chat-home/ (commit ef687c7)

## Проверки (наследуются из review-002-cases)

- MAJ-1 закрыт: команда боевого smoke исполнима (`hermes chat -Q --query-file -
  --oneshot --run-budget 25`; NFR ≤30 с = бюджет hermes 25 с + таймаут
  адаптера 30 с).
- MIN-1 закрыт: ссылка TC-S19-UNIT-001 на план прогонов поправлена.
- Остальные 7 кейсов — без повторной сверки (зафиксированы review-001).

## Вердикт: одобрить
