# Автотесты — add-registration-admin

Запуск: `python3 -m pytest tests/ -q` (без сети; API — через TestClient
из tests/conftest.py; time.sleep запрещен — детерминизм через прямой
контроль тестовой БД в tmp_path).

Окружение тестов: ADMIN_USER/ADMIN_PASSWORD_HASH/SECRET задаются
фикстурой `client`; БД — `AUTOSCHOOL_DB_PATH` в tmp_path (чистая на
каждый тест).

Матрица approved-кейс → тест (38/38 покрыто; источник —
test-model/approved/add-registration-admin/):

| TC-ID | Тест(ы) |
|---|---|
| TC-REG-001 | test_register.py::test_tc_reg_001_health_then_register_success; test_db.py::test_tc_reg_001_db_created_in_tmp_path, test_tc_reg_001_users_table_has_all_schema_columns, test_tc_reg_001_created_at_defaults_to_utc_now, test_tc_reg_001_wal_mode, test_tc_reg_001_row_factory_is_row, test_tc_reg_001_init_db_idempotent |
| TC-REG-002 | test_register.py::test_tc_reg_002_values_stored_verbatim_no_normalization |
| TC-REG-003 | test_register.py::test_tc_reg_003_password_not_stored_in_plaintext |
| TC-REG-004 | test_register.py::test_tc_reg_004_each_empty_required_field_rejected |
| TC-REG-005 | test_register.py::test_tc_reg_005_missing_json_key_gives_contract_422 |
| TC-REG-006 | test_register.py::test_tc_reg_006_email_without_at_and_domain_rejected |
| TC-REG-007 | test_register.py::test_tc_reg_007_email_format_boundaries, test_tc_reg_007_email_with_space_current_behavior |
| TC-REG-008 | test_register.py::test_tc_reg_008_no_record_created_on_any_rejection |
| TC-REG-009 | test_register.py::test_tc_reg_009_password_lower_bound_7_and_1_chars |
| TC-REG-010 | test_register.py::test_tc_reg_010_password_exactly_8_chars_accepted |
| TC-REG-011 | test_register.py::test_tc_reg_011_password_confirm_mismatch_rejected |
| TC-REG-012 | test_register.py::test_tc_reg_012_duplicate_email_rejected_not_500; test_db.py::test_tc_reg_012_email_unique_at_db_level |
| TC-REG-013 | test_register.py::test_tc_reg_013_exact_repeat_of_same_data_rejected |
| TC-REG-014 | test_register.py::test_tc_reg_014_bcrypt_hash_cost_12_no_plaintext |
| TC-REG-015 | test_register.py::test_tc_reg_015_hash_verifiable_with_bcrypt_checkpw |
| TC-REG-016 | test_static.py::test_tc_reg_016_health_and_registered_page_available, test_tc_reg_016_lifespan_initializes_db (браузерные шаги — Playwright/ручной прогон) |
| TC-REG-017 | test_static.py::test_tc_reg_017_rejected_registration_no_redirect_target (браузерные шаги — Playwright/ручной прогон) |
| TC-REG-018 | test_static.py::test_tc_reg_018_static_pages_return_200_with_mock_texts, test_tc_reg_018_register_modal_has_password_fields_wiring, test_tc_reg_018_health_endpoint (побайтовый diff с макетами — мануально, D9) |
| TC-ADM-001 | test_admin.py::test_tc_adm_001_admin_login_success_opens_admin_api |
| TC-ADM-002 | test_admin.py::test_tc_adm_002_wrong_password_no_token_no_access |
| TC-ADM-003 | test_admin.py::test_tc_adm_003_unknown_login_rejected_with_any_password |
| TC-ADM-004 | test_admin.py::test_tc_adm_004_empty_credentials_rejected (3 прогона, parametrize) |
| TC-ADM-005 | test_admin_users.py::test_tc_adm_005_users_list_columns_and_values |
| TC-ADM-006 | test_admin_users.py::test_tc_adm_006_fresh_records_first_no_sleep |
| TC-ADM-007 | test_admin_users.py::test_tc_adm_007_same_created_at_higher_id_first_deterministic |
| TC-ADM-008 | test_admin_users.py::test_tc_adm_008_csv_format_bom_delimiter_header_role |
| TC-ADM-009 | test_admin_users.py::test_tc_adm_009_csv_sanitizes_dangerous_prefixes |
| TC-ADM-010 | test_admin_users.py::test_tc_adm_010_csv_safe_values_untouched |
| TC-ADM-011 | test_admin_users.py::test_tc_adm_011_csv_date_is_local_calendar_day |
| TC-ADM-012 | test_admin_users.py::test_tc_adm_012_csv_empty_with_no_users |
| TC-ADM-013 | test_admin.py::test_tc_adm_013_valid_token_returns_data_matching_db, test_tc_adm_013_db_isolated_between_tests |
| TC-ADM-014 | test_admin.py::test_tc_adm_014_request_without_token_rejected, test_tc_adm_014_export_without_token_empty_body |
| TC-ADM-015 | test_admin.py::test_tc_adm_015_forged_token_rejected |
| TC-ADM-016 | test_admin.py::test_tc_adm_016_expired_token_rejected |
| TC-ADM-017 | test_admin.py::test_tc_adm_017_token_only_after_successful_login |
| TC-NFR-001 | test_register.py::test_tc_nfr_001_register_response_time_under_500ms |
| TC-NFR-002 | test_register.py::test_tc_nfr_002_sql_injection_stored_as_literal_data, test_tc_nfr_002_no_sql_concatenation_in_db_layer; test_db.py::test_tc_nfr_002_no_sql_concatenation_in_db_module |
| TC-NFR-003 | test_static.py::test_tc_nfr_003_env_gitignored_and_example_present |

## Отклонения от буквы кейсов (зафиксировано в docstring тестов)

- TC-REG-007 вариант C («ivanov example@mail.com» с пробелом): правило
  sdd 3.1 («@» и точка в домене) его пропускает; фактическое поведение
  (200) зафиксировано отдельным тестом, отклонение — дефект правила D1,
  эскалация qa_case_reviewer.
- TC-ADM-016 (истечение TTL): время не инъецируется на уровне API —
  проверка через прямой доступ к реестру backend.admin._tokens (D6).
- TC-ADM-009 шаг 5 (ручной контроль Excel/LibreOffice) и TC-REG-018
  побайтовый diff с design/mocks — вне автотестов (D9).
- TC-NFR-001: бюджет ≤ 500 мс применяется к медиане 5 прогонов (bcrypt
  cost 12 на раннере ~330–430 мс; единичный max-выброс прогрева — не
  дефект); медиана и max печатаются в выводе теста.
