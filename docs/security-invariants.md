---
record_type: register
id: security-invariants
status: ratified
process_version: v6.6
date: 2026-10-04
---
# Security invariants

**The release's security invariants, one list, each held by a negative test** (#89, W-131). A
negative test is one that fails when the invariant is removed. The milestone closure's security
seat starts from this list, and Stage 5.1 needs it before any deploy. Until M18 there was no such
list: the M16 and M17 closure seats each rebuilt one from the ADRs and the reviews
(`docs/reviews/m16-closure-security-review.md`, `docs/reviews/m17-closure-security-review.md` §3).
This list folds in both, the M18 waves, and every security clause of the ADRs.

**How it is held.** `tests/unit/test_security_invariants.py` reads this file and fails closed:
- on a row whose test names a file or a test function that does not exist, or a `make` target the
  Makefile does not have;
- on a row with no test, unless it names a gap below, and on a gap that names no issue;
- on an `INV-n` written anywhere in `src/`, `scripts/`, `tests/` or `ios/` that is neither a row
  here nor a retired id;
- on a number skipped, or used twice.

It cannot prove that a cited test fails when its invariant is removed. That is what the mutation
samples did: each M16 and M17 closure row was mutated, and M18-W6 mutated more ("Mutation samples" below).

**Numbering.** INV-1 to INV-24 were given by the M1 to M5 security reviews and are cited across the
code and the records (INV-23, the read-only rule, in 18 places). Where one still holds, it keeps its
number. The ones that are not security invariants, or were merged, are retired below, and their
numbers are not reused. New rows are INV-25 and up, grouped by where they hold.

**Adding a row.** Give it the next number, cite the ADR or issue it comes from, and cite at least
one test that fails without it. Run the mutation by hand once: remove the invariant, see the test
fail, restore.

## The list

### The engine's network surface

| INV | Invariant | Source | Negative test(s) |
|---|---|---|---|
| INV-25 | With no Host list, the engine refuses any request that arrived on a network address. It serves loopback only, whatever started it. | D-171 cl. 2, note 1 (W1 review B1); #89 comment R2 | `tests/unit/test_engine_host.py::test_without_a_list_a_request_arriving_on_a_network_address_is_refused`<br>`tests/unit/test_engine_host.py::test_every_path_is_behind_the_host_check`<br>`tests/unit/test_engine_host.py::test_without_a_list_a_connection_with_no_local_address_is_not_called_a_network_one` |
| INV-26 | With a Host list set, a request whose Host is not on it gets 400 `unknown_host` on every path, before any route runs. | D-171 cl. 1 (M17 closure I-4, DNS rebinding) | `tests/unit/test_engine_host.py::test_a_host_not_on_the_list_is_refused`<br>`tests/unit/test_engine_host.py::test_every_path_is_behind_the_host_check`<br>`tests/unit/test_engine_host.py::test_an_empty_host_is_refused_when_a_list_is_set`<br>`tests/unit/test_engine_host.py::test_an_ipv6_host_is_compared_without_its_brackets_or_port` |
| INV-27 | The launcher refuses to start the engine when the startup checks report any problem. A bind beyond loopback with no Host list is one such problem. | D-171 cl. 2; W-042 preflight; #86 (M17 MINOR-4, L2) | `tests/unit/test_engine_host.py::test_a_bind_beyond_loopback_needs_a_list_of_hosts`<br>`tests/unit/test_engine_service.py::test_the_launchers_preflight_refuses_a_bind_beyond_loopback_without_hosts`<br>`tests/unit/test_engine_service.py::test_the_launcher_refuses_an_artifact_past_a_serving_bound` |
| INV-28 | Every way of starting the engine binds loopback unless the owner opted in. The launcher passes exactly one `--host`, from `MODEL_RANKING_BIND`, default 127.0.0.1. The wrapper binds loopback unless `--lan`. A reinstall keeps the mode it finds, and `--no-lan` closes it. `make run` binds 127.0.0.1. | D-171 cl. 2-3, notes 1-2, 7; D-170 cl. 1; #86 (M17 MINOR-4, L1); #89 comment R2 | `tests/unit/test_engine_service.py::test_the_launcher_binds_exactly_one_host_and_reads_it_from_the_bind_variable`<br>`tests/unit/test_engine_service.py::test_the_wrapper_binds_loopback_and_names_its_hosts_by_default`<br>`tests/unit/test_engine_service.py::test_the_home_network_is_opt_in_and_names_the_macs_own_names`<br>`tests/unit/test_engine_service.py::test_a_reinstall_keeps_the_home_network_unless_told_to_close_it`<br>`tests/unit/test_engine_service.py::test_a_plain_reinstall_writes_the_mode_it_found_and_says_so`<br>`tests/unit/test_engine_service.py::test_no_lan_closes_the_home_network_on_the_install_the_owner_runs`<br>`tests/unit/test_engine_service.py::test_make_run_binds_loopback`<br>`tests/unit/test_engine_host.py::test_an_unset_bind_is_loopback` |
| INV-29 | The service runs only a deployed release of `origin/main`, nothing it touches is under `~/Desktop`, and its wrapper is the owner's alone (mode 700). | D-170 cl. 1-2; #36; #86 (M17 MINOR-4, L3, L4) | `tests/unit/test_engine_service.py::test_the_service_runs_only_a_deployed_release`<br>`tests/unit/test_engine_service.py::test_a_deploy_takes_origin_main_whatever_is_checked_out`<br>`tests/unit/test_engine_service.py::test_launchd_touches_nothing_under_desktop`<br>`tests/unit/test_engine_service.py::test_the_installed_wrapper_is_the_owners_alone` |

### The HTTP surface

| INV | Invariant | Source | Negative test(s) |
|---|---|---|---|
| INV-30 | The engine serves exactly its five declared GET routes. No route mutates. | REQ-API-001; baseline §2; M17 row 28 | `tests/unit/test_api_v1.py::test_no_mutating_route_exists`<br>`tests/unit/test_api_v1.py::test_the_shipped_surface_is_exactly_the_declared_surface`<br>`tests/unit/test_api_config.py::test_a_preflight_is_answered_for_get_and_refuses_a_mutating_verb` |
| INV-31 | CORS is an explicit allowlist. A wildcard is refused at startup, unset means no cross-origin access, and credentials are never allowed. | Baseline §3 (`bootstrap-check` C9) | `tests/unit/test_api_config.py::test_a_wildcard_origin_is_refused_not_warned_about`<br>`tests/unit/test_api_config.py::test_a_wildcard_is_refused_in_development_too`<br>`tests/unit/test_api_config.py::test_unset_means_no_cross_origin_access`<br>`tests/unit/test_api_config.py::test_credentials_are_never_allowed_across_origins` |
| INV-32 | A strict environment (production, or an unknown or unset `APP_ENV`) refuses to boot on a missing database, a missing build stamp or any other startup problem. | Baseline §4; D-116 cl. 1, 3 | `tests/unit/test_api_config.py::test_production_refuses_to_boot_without_its_evidence_database`<br>`tests/unit/test_api_config.py::test_production_refuses_to_boot_without_a_build_stamp`<br>`tests/unit/test_api_config.py::test_an_unrecognised_environment_is_treated_as_strict`<br>`tests/unit/test_api_config.py::test_a_production_process_refuses_to_import_with_broken_config` |
| INV-33 | The engine refuses to boot on an artifact that would publish past a serving bound (ranked models, standings). | D-167 (the boot bound); W-042; M17 row 16 | `tests/unit/test_board_standings.py::test_an_artifact_that_would_publish_too_many_standings_refuses_to_boot`<br>`tests/unit/test_board_standings.py::test_a_payload_the_route_would_refuse_refuses_the_boot_instead`<br>`tests/unit/test_stage40_minors.py::test_an_artifact_with_too_many_ranked_models_refuses_to_boot` |
| INV-34 | Error responses are generic: no path, no exception text, echoed input bounded. Every response, the 400 and the 500 included, carries `nosniff`. | Baseline §6 | `tests/unit/test_api_v1.py::test_missing_database_fails_closed_and_leaks_no_path`<br>`tests/unit/test_stage40_minors.py::test_an_unhandled_error_does_not_leak_its_exception_text`<br>`tests/unit/test_api_v1.py::test_echoed_input_is_bounded`<br>`tests/unit/test_api_v1.py::test_responses_forbid_content_type_sniffing` |
| INV-35 | A response carries only declared fields. | REQ-API (field allowlist) | `tests/unit/test_api_config.py::test_the_public_payload_carries_only_declared_fields`<br>`tests/unit/test_api_config.py::test_no_engine_field_reaches_the_public_surface_undeclared`<br>`tests/unit/test_api_config.py::test_the_allowlist_actually_filters_an_undeclared_field` |
| INV-36 | `/v1/boards` takes no parameter and carries no score. A query string changes nothing. | D-167 cl. 1-2; D-160 cl. 1; M17 rows 15, 28 | `tests/unit/test_board_standings.py::test_a_query_string_changes_nothing`<br>`tests/unit/test_board_standings.py::test_the_payload_carries_no_score_at_all`<br>`tests/unit/test_board_standings.py::test_the_key_sets_are_frozen` |
| INV-37 | A request never copies the artifact into memory, and the engine caps how many requests run at once. | D-116 (W-017, a go-live condition) | `tests/unit/test_api_config.py::test_w017_is_closed_by_deletion_not_by_a_bounded_copy`<br>`tests/unit/test_api_config.py::test_the_concurrency_cap_is_applied_to_the_running_loop`<br>`tests/unit/test_stage40_minors.py::test_an_unusable_concurrency_value_is_refused` |

### The served artifact

| INV | Invariant | Source | Negative test(s) |
|---|---|---|---|
| INV-23 | Every reader opens the served artifact read-only, through `open_readonly`, whose URI no path can rewrite. Only named writers call `sqlite3.connect`, each once. | D-116 cl. 1; M5; M10 closure; M16 MINOR-2; M17 MINOR-1, rows 17-19; #92 | `tests/unit/test_readonly_uri.py::test_read_only_holds_against_a_path_that_rewrites_the_query_string`<br>`tests/unit/test_readonly_uri.py::test_read_only_still_refuses_a_write_on_an_ordinary_path`<br>`tests/unit/test_readonly_uri.py::test_nothing_in_the_repository_builds_a_read_only_uri_by_hand`<br>`tests/unit/test_readonly_uri.py::test_nothing_opens_a_database_but_the_named_writers_and_the_read_only_opener`<br>`tests/unit/test_readonly_uri.py::test_each_named_writer_opens_as_many_times_as_it_is_allowed`<br>`tests/unit/test_readonly_uri.py::test_every_reader_opens_the_artifact_read_only_at_run_time`<br>`tests/unit/test_carry_forward.py::test_the_carry_opens_the_served_artifact_read_only`<br>`tests/unit/test_api_v1.py::test_the_api_never_writes_to_the_database`<br>`tests/unit/test_api_v1.py::test_the_routes_m17_added_or_changed_never_write_the_database`<br>`tests/unit/test_coverage.py::test_coverage_cli_read_only_survives_a_path_containing_a_question_mark` |
| INV-4 | A build or refresh that fails, crashes or is killed leaves the live artifact byte-identical. A publish is one atomic rename. | M1; D-154 cl. 1; D-116 cl. 1 | `tests/unit/test_refresh.py::test_a_failed_build_leaves_the_live_artifact_untouched`<br>`tests/unit/test_refresh.py::test_a_builder_that_raises_leaves_the_live_artifact_untouched`<br>`tests/unit/test_refresh.py::test_a_sigkilled_cycle_leaves_the_live_artifact_byte_identical`<br>`tests/unit/test_refresh.py::test_a_candidate_that_cannot_be_read_back_is_not_published`<br>`tests/unit/test_build_artifact_safety.py::test_a_failed_rebuild_leaves_the_previous_artifact_untouched`<br>`tests/unit/test_nightly_refresh.py::test_a_cycle_killed_mid_publish_leaves_the_live_artifact_and_the_lock_usable` |
| INV-38 | The refresh refuses to run in an artifact directory that group or others can write. | Stage 4.0 finding (V3C-51) | `tests/unit/test_refresh.py::test_a_world_writable_artifact_directory_stops_the_cycle`<br>`tests/unit/test_refresh.py::test_a_group_writable_artifact_directory_stops_the_cycle_too` |

### The nightly refresh, a child of the engine

| INV | Invariant | Source | Negative test(s) |
|---|---|---|---|
| INV-39 | The nightly switch is refused outside the relaxed environments, at boot and again when the schedule starts. A strict engine's `/health` says only `refresh: off`. | D-154 cl. 2 and its first amendment; M16 rows 1, 2, 8 | `tests/unit/test_nightly_refresh.py::test_production_refuses_to_boot_with_the_switch_on`<br>`tests/unit/test_nightly_refresh.py::test_the_switch_is_on_only_where_ingestion_may_run`<br>`tests/unit/test_nightly_refresh.py::test_the_schedule_rechecks_the_switch_when_it_starts`<br>`tests/unit/test_nightly_refresh.py::test_health_says_off_when_the_switch_is_off` |
| INV-40 | Every child process (the refresh, and the parquet reader it starts) gets an allowlisted environment and runs with `-P`. | D-154 first amendment; D-165 cl. 4; D-173 cl. 4 (the bound variables join the list); M16 rows 3, 6; M17 row 3 | `tests/unit/test_nightly_refresh.py::test_the_child_inherits_no_secret_from_the_server`<br>`tests/unit/test_nightly_refresh.py::test_the_environment_builds_the_refreshs_own_command`<br>`tests/unit/test_arena_slices.py::test_the_reader_gets_no_secret_from_the_environment`<br>`tests/unit/test_arena_slices.py::test_a_module_planted_in_the_working_directory_is_not_imported` |
| INV-41 | What a child says is bounded before the engine holds it. The refresh's output is kept as a 64 KiB tail. The reader's answer is cut at 8 MiB. A quoted reason is short and printable. | D-154 first amendment; D-165 cl. 4; M16 row 4; M17 rows 2, 5 | `tests/unit/test_nightly_refresh.py::test_the_tail_never_holds_more_than_its_limit`<br>`tests/unit/test_nightly_refresh.py::test_a_child_that_floods_its_output_is_kept_to_a_tail`<br>`tests/unit/test_arena_slices.py::test_the_parent_stops_reading_at_the_bound_rather_than_after_it`<br>`tests/unit/test_arena_slices.py::test_only_the_tail_of_the_readers_stderr_is_quoted_and_it_is_printable`<br>`tests/unit/test_arena_slices.py::test_a_reason_is_quoted_short_and_printable` |
| INV-42 | A refresh is bounded in time by three limits. Its downloads share a 20-minute budget, after which the sources left carry. The kernel ends it at 27 minutes, and it ends itself within seconds when its engine is gone. The engine kills its whole process group at 30 minutes, whether or not the cycle has exited, and keeps answering meanwhile. | D-154 cl. 1 as amended 2026-10-04 (W-126, W-130, fixed in `654ba80`); M16 row 5, MINOR-3 | `tests/unit/test_nightly_refresh.py::test_a_cycle_that_hangs_is_killed_at_the_timeout`<br>`tests/unit/test_nightly_refresh.py::test_the_server_answers_while_a_cycle_hangs`<br>`tests/unit/test_nightly_refresh.py::test_the_timeout_kill_takes_a_grandchild_that_holds_the_output`<br>`tests/unit/test_nightly_refresh.py::test_a_cycle_that_ends_at_its_limit_is_reported_as_timed_out`<br>`tests/unit/test_nightly_refresh.py::test_the_kill_takes_the_group_even_when_the_cycle_has_already_exited`<br>`tests/unit/test_nightly_refresh.py::test_the_cycle_ends_its_fetches_then_itself_before_the_engine_kills_it`<br>`tests/unit/test_refresh.py::test_the_cycle_ends_at_its_limit_whatever_it_is_doing`<br>`tests/unit/test_refresh.py::test_a_cycle_whose_engine_is_gone_ends_itself`<br>`tests/unit/test_refresh.py::test_the_cycle_runs_inside_its_fetch_budget`<br>`tests/unit/test_fetch_bounds.py::test_no_fetch_starts_once_the_cycle_budget_is_spent`<br>`tests/unit/test_fetch_bounds.py::test_an_open_fetch_is_cut_at_the_end_of_the_cycle_budget` |
| INV-43 | The serving process loads no refresh, build, fetcher, source client, source parser (ingest, accessibility), `httpx` or `pyarrow`. Nothing the refresh loads imports the serving adapter. | D-154 cl. 1 and first amendment; D-116 cl. 2; W-125 (fixed in `145539d`); REQ-REF-007; M16 row 7; M17 row 27 | `tests/unit/test_nightly_refresh.py::test_the_serving_process_never_loads_the_refresh_the_build_or_the_fetchers`<br>`tests/unit/test_arena_slices.py::test_neither_the_server_nor_the_slice_module_loads_pyarrow`<br>`tests/unit/test_refresh.py::test_nothing_the_refresh_loads_imports_the_serving_adapter`<br>`tests/unit/test_refresh.py::test_the_refresh_never_imports_the_serving_adapter` |

### Downloads and parsing

| INV | Invariant | Source | Negative test(s) |
|---|---|---|---|
| INV-44 | The Arena parquet file is parsed in a child under a 512 MiB memory ceiling and a time limit. The ceiling fails closed, and a reader whose parent is gone stops itself. | D-165 cl. 1, 4; M17 row 1 | `tests/unit/test_arena_slices.py::test_the_watchdog_fails_closed`<br>`tests/unit/test_arena_slices.py::test_a_file_that_would_exhaust_memory_is_stopped_at_the_ceiling`<br>`tests/unit/test_arena_slices.py::test_a_reader_that_cannot_measure_itself_says_so`<br>`tests/unit/test_arena_slices.py::test_a_reader_that_hangs_is_stopped`<br>`tests/unit/test_arena_slices.py::test_a_reader_whose_parent_is_gone_stops_itself` |
| INV-3 | Every remote fetch is https to a host its client declares, on every redirect hop, with a bounded number of hops. A suffix entry matches a domain, not a substring. | M1, D-101 (INV-8 merged here); #25, #29; M17 row 6 | `tests/unit/test_fetch_bounds.py::test_a_first_url_that_is_not_https_is_refused`<br>`tests/unit/test_fetch_bounds.py::test_every_remote_client_declares_where_it_may_go`<br>`tests/unit/test_fetch_bounds.py::test_a_redirect_to_another_host_is_refused`<br>`tests/unit/test_fetch_bounds.py::test_a_redirect_down_to_plain_http_is_refused`<br>`tests/unit/test_fetch_bounds.py::test_a_suffix_entry_is_a_domain_not_a_substring`<br>`tests/unit/test_fetch_bounds.py::test_a_look_alike_of_the_sources_own_host_is_refused`<br>`tests/unit/test_fetch_bounds.py::test_more_redirects_than_the_bound_is_a_source_error` |
| INV-45 | One deadline bounds a whole fetch, retries and redirects included. | #29; M17 row 7 | `tests/unit/test_fetch_bounds.py::test_the_deadline_bounds_the_whole_fetch`<br>`tests/unit/test_fetch_bounds.py::test_a_read_failing_after_the_deadline_is_reported_as_the_deadline`<br>`tests/unit/test_fetch_bounds.py::test_without_a_deadline_of_its_own_a_fetch_takes_four_timeouts_at_most` |
| INV-46 | A downloaded body is bounded while it is read, before any parser sees it. The Epoch bundle download is capped, follows no redirect and has a deadline. | "The download bounds" (#89); D-158; M16 row 13 | `tests/unit/test_yaml_guard.py::test_the_remote_fetch_bounds_the_body_before_the_parser_sees_it`<br>`tests/unit/test_yaml_guard.py::test_every_remote_client_reads_through_the_bounded_fetcher`<br>`tests/unit/test_arena_slices.py::test_a_download_over_the_cap_is_cut_off`<br>`tests/unit/test_epoch_bundle_fetch.py::test_the_bundle_download_is_bounded_small_follows_no_redirect_and_has_a_deadline` |
| INV-9 | A paginated source stops at its page cap and its row bound. Running out is a `SourceError`, never a silent cut. | M2 | `tests/unit/test_arena_client.py::test_page_cap_exhaustion_fails_loudly_without_falling_back`<br>`tests/unit/test_arena_client.py::test_the_total_merged_rows_are_bounded_not_only_the_page_count` |
| INV-1 | Payloads are parsed as data. YAML goes only through the size- and expansion-bounded safe loader. `src/` and `scripts/` hold no `eval`, `exec`, `pickle` or shell call. | M1; D-104 (fetched content is data) | `tests/unit/test_yaml_guard.py::test_every_yaml_entry_point_goes_through_the_guard`<br>`tests/unit/test_yaml_guard.py::test_the_guard_runs_before_the_parser_not_after`<br>`tests/unit/test_yaml_guard.py::test_the_expansion_attack_is_refused_before_it_is_parsed`<br>`make lint` (ruff `S` over `src` and `scripts`) |
| INV-2 | SQL is parameterised. The one interpolated identifier is allowlisted. | M1 | `tests/unit/test_schema.py::test_reset_source_rejects_unknown_table`<br>`make lint` (ruff `S608`) |
| INV-47 | No Epoch archive member lands outside the scratch directory. A member that names a path outside, resolves outside, or is a symbolic link refuses the whole bundle. | D-158 cl. 2; M16 rows 9, 10 | `tests/unit/test_epoch_bundle_fetch.py::test_a_member_that_names_a_path_outside_is_refused`<br>`tests/unit/test_epoch_bundle_fetch.py::test_a_member_whose_resolved_path_escapes_is_refused_even_when_its_name_is_clean`<br>`tests/unit/test_epoch_bundle_fetch.py::test_a_symlink_member_is_refused` |
| INV-48 | An Epoch archive is refused when it expands past its limit (counted while writing), has too many members, or is not a zip. | D-158 cl. 2; M16 rows 11, 12 | `tests/unit/test_epoch_bundle_fetch.py::test_a_bundle_that_expands_past_the_limit_is_refused_by_what_it_writes`<br>`tests/unit/test_epoch_bundle_fetch.py::test_too_many_members_are_refused`<br>`tests/unit/test_epoch_bundle_fetch.py::test_a_body_that_is_not_a_zip_is_refused` |
| INV-49 | A fetch leaves no scratch behind, even on an interrupt, and the sweep removes only this artifact's day-old scratch. | D-158 cl. 1; M16 rows 15, 16 | `tests/unit/test_epoch_bundle_fetch.py::test_an_interrupt_during_the_fetch_propagates_and_leaves_no_scratch`<br>`tests/unit/test_epoch_bundle_fetch.py::test_scratch_a_killed_cycle_left_is_swept_by_the_next` |
| INV-50 | A failure to fetch, unpack or parse a source is a failed source, which carries. It never crashes the cycle or the build. | D-158 cl. 3; D-165 cl. 2; D-156; M16 row 14 | `tests/unit/test_epoch_bundle_fetch.py::test_any_error_a_fetcher_raises_is_a_failed_source`<br>`tests/unit/test_epoch_bundle_fetch.py::test_an_unreadable_archive_never_stops_the_cycle`<br>`tests/unit/test_parser_envelopes.py::test_a_hostile_envelope_raises_source_error_and_nothing_else`<br>`tests/unit/test_build_slices.py::test_a_hostile_file_fails_its_slices_and_never_the_build`<br>`tests/unit/test_arena_slices.py::test_a_reader_that_fails_is_a_source_error` |
| INV-22 | A file read from an operator-supplied directory is contained. A path or a link that resolves outside the directory is refused. | M5 | `tests/unit/test_epoch_board.py::test_a_symlink_escaping_the_bundle_is_refused`<br>`tests/unit/test_epoch_board.py::test_a_declared_file_that_climbs_out_of_the_bundle_is_refused`<br>`tests/unit/test_epoch_ingest.py::test_bundle_client_refuses_a_symlink_that_escapes_the_bundle`<br>`tests/unit/test_access.py::test_a_metadata_file_that_resolves_outside_the_bundle_is_refused` |
| INV-51 | A parquet text value over 256 characters is refused. A file that declares more rows or bytes than its bound is refused before it is read. | D-165 cl. 3; M17 row 4 | `tests/unit/test_arena_slices.py::test_a_value_longer_than_any_real_one_is_refused`<br>`tests/unit/test_arena_slices.py::test_the_reader_answers_rows_or_an_error_in_process`<br>`tests/unit/test_arena_slices.py::test_a_file_declaring_more_rows_than_the_bound_is_refused_before_it_is_read`<br>`tests/unit/test_arena_slices.py::test_a_file_declaring_more_uncompressed_bytes_than_the_bound_is_refused` |

### What a refresh may publish (guards against a hostile or broken upstream)

| INV | Invariant | Source | Negative test(s) |
|---|---|---|---|
| INV-52 | A candidate is refused if it blinds a surface, loses a quarter of a surface's models, fills a surface with models never served, or collapses the median price. This holds on an expiry night too. | D-128; D-132; W-049; M16 rows 18, 19 | `tests/unit/test_refresh.py::test_a_candidate_that_blinds_a_surface_is_refused`<br>`tests/unit/test_refresh.py::test_a_candidate_losing_more_than_a_quarter_of_a_surface_is_refused`<br>`tests/unit/test_refresh.py::test_a_loss_of_exactly_a_quarter_is_refused`<br>`tests/unit/test_refresh.py::test_a_surface_filling_with_models_nobody_has_seen_is_refused`<br>`tests/unit/test_refresh.py::test_a_median_price_collapse_is_refused`<br>`tests/unit/test_refresh_carry.py::test_an_expiry_night_does_not_admit_a_roster_never_served`<br>`tests/unit/test_refresh_carry.py::test_an_expiry_night_does_not_admit_a_price_jump_either` |
| INV-53 | The surface roster guards compare model ids, so a re-spelled display name moves no guard. | D-173 cl. 2 (#39) | `tests/unit/test_refresh.py::test_a_candidate_that_only_re_spells_names_moves_no_guard` |
| INV-54 | Every board, a surface's own and every declared one, is refused when it loses a quarter of its names or more than a quarter are new. Each floor and each board is in the fingerprint. | D-159 (owner ruling and its mirror); D-164 cl. 1-2; M17 rows 8, 9 | `tests/unit/test_floor_served.py::test_a_board_flooded_with_rows_it_has_never_seen_is_refused`<br>`tests/unit/test_floor_served.py::test_a_board_that_loses_a_quarter_of_its_names_is_refused`<br>`tests/unit/test_floor_served.py::test_every_surfaces_floor_is_hashed_to_its_published_precision`<br>`tests/unit/test_refresh_boards.py::test_a_board_whose_names_are_a_quarter_new_is_refused`<br>`tests/unit/test_refresh_boards.py::test_a_board_that_loses_a_quarter_of_its_names_is_refused`<br>`tests/unit/test_refresh_boards.py::test_the_fingerprint_moves_with_a_board_and_only_with_it` |
| INV-55 | A night that loses a quarter of the accessibility values is refused. | D-173 cl. 3 (#42) | `tests/unit/test_refresh.py::test_accessibility_values_falling_by_a_quarter_refuse_the_night` |
| INV-56 | The refresh refuses a candidate past a bound the engine serves under, a first artifact included, with the engine's own bound values. | D-173 cl. 4 (#57) | `tests/unit/test_refresh.py::test_a_candidate_past_a_serving_bound_is_refused`<br>`tests/unit/test_refresh.py::test_a_candidate_past_the_standings_bound_is_refused`<br>`tests/unit/test_refresh.py::test_a_first_artifact_past_a_bound_is_refused_too`<br>`tests/unit/test_nightly_refresh.py::test_the_child_checks_the_bounds_the_engine_serves_under` |
| INV-57 | On an expiry night the baseline drops every table an expired source fed, and an expiry excuses only that source. | #41, #47; D-156; M17 row 10 | `tests/unit/test_refresh_carry.py::test_the_expiry_baseline_drops_an_expired_attributes_values`<br>`tests/unit/test_refresh_carry.py::test_the_expiry_baseline_drops_the_sources_prices_as_well_as_its_scores`<br>`tests/unit/test_refresh_carry.py::test_the_expiry_baseline_drops_every_expired_source_at_once`<br>`tests/unit/test_refresh_carry.py::test_an_expiry_does_not_excuse_the_fresh_source_beside_it` |

### Upstream text and model identity

| INV | Invariant | Source | Negative test(s) |
|---|---|---|---|
| INV-5 | A stored row is bounded where every client stores it. A run date is a calendar date or nothing. A score is present and finite. A price is positive. Carried rows meet the same rules. | M17 MINOR-2; M1; #92 (N2, N3); M17 row 13 | `tests/unit/test_stored_scores_are_bounded.py::test_a_stored_date_is_a_calendar_date_or_nothing`<br>`tests/unit/test_stored_scores_are_bounded.py::test_a_non_finite_score_refuses_the_source`<br>`tests/unit/test_stored_scores_are_bounded.py::test_the_arena_parsers_date_is_bounded_where_it_is_stored`<br>`tests/unit/test_stored_scores_are_bounded.py::test_the_swebench_parsers_date_and_infinity_are_bounded_where_they_are_stored`<br>`tests/unit/test_stored_scores_are_bounded.py::test_a_missing_score_is_refused_as_a_source_error_not_a_type_error`<br>`tests/unit/test_carry_forward.py::test_carried_rows_meet_the_rules_every_client_row_meets`<br>`tests/unit/test_carry_forward.py::test_a_carried_date_is_validated_not_cut_and_no_infinity_is_carried`<br>`tests/unit/test_epoch_board.py::test_a_non_finite_score_is_skipped_and_counted`<br>`tests/unit/test_schema.py::test_pricing_rejects_zero_prices` |
| INV-58 | A derived model's display name is only a spelling of the model: the name's last route segment, at most 64 characters of a closed alphabet, read as the same model. Otherwise it is the id. | D-157 second amendment (M16 MAJOR-1); M17 row 14 | `tests/unit/test_registry_derived.py::test_a_derived_models_display_name_is_never_upstream_free_text`<br>`tests/unit/test_registry_derived.py::test_a_spelling_the_grammar_accepts_is_still_bounded_for_display` |
| INV-59 | A derived model never takes a curated id, never merges two products, and never comes from a fine-tune, a moving alias or a `-latest` name. | D-157 cl. 1, 3 and first amendment; D-166; D-173 cl. 8; M16 row 20; M17 row 11 | `tests/unit/test_registry_derived.py::test_a_curated_id_is_never_taken_by_a_derived_one`<br>`tests/unit/test_registry_derived.py::test_a_different_product_is_never_derived`<br>`tests/unit/test_registry_derived.py::test_a_fine_tune_is_never_derived`<br>`tests/unit/test_moving_aliases.py::test_a_moving_alias_derives_no_model`<br>`tests/unit/test_moving_aliases.py::test_reconcile_registers_no_model_from_an_alias_and_counts_it_dropped`<br>`tests/unit/test_moving_aliases.py::test_a_latest_token_followed_by_a_word_derives_no_model` |
| INV-60 | Upstream names that reach `/health` or a caller are bounded in number, length and characters. | D-157 cl. 4; M16 MINOR-1, row 22 | `tests/unit/test_registry_disclosure.py::test_an_unmatched_name_is_bounded_before_it_reaches_health`<br>`tests/unit/test_registry_disclosure.py::test_health_counts_the_derived_models_and_names_the_top_unmatched`<br>`tests/unit/test_stage40_minors.py::test_a_hostile_harness_string_is_bounded_before_it_reaches_a_caller` |
| INV-61 | An accessibility value is one of a fixed vocabulary. Names that disagree get no value. | D-167 (accessibility); D-175 (#78); M17 row 12 | `tests/unit/test_access.py::test_a_value_outside_the_vocabulary_is_refused_and_counted`<br>`tests/unit/test_access.py::test_names_link_to_the_models_their_scores_link_to_and_a_disagreement_gives_no_value`<br>`tests/unit/test_access.py::test_one_name_listed_twice_with_two_values_is_a_disagreement_not_the_last_row` |

### The phone: what may leave it

| INV | Invariant | Source | Negative test(s) |
|---|---|---|---|
| INV-62 | Only `EngineClient.swift` reaches the network, and only `FrontDoor.swift` and `StandingsStore.swift` touch the file system. Nothing shares, hands off, logs, opens a URL or writes shared storage. The compiler's resolved declarations are checked in all four build configurations, after the gate refuses its own fixture. | D-126; D-160 cl. 1; D-167 cl. 4; W-122; #51; M16 row 23 | `make client-decls`<br>`tests/unit/test_client_decl_gate.py::test_the_network_and_the_file_system_are_refused_outside_their_files`<br>`tests/unit/test_client_decl_gate.py::test_the_gate_refuses_its_compiled_fixture`<br>`tests/unit/test_client_decl_gate.py::test_make_client_decls_fails_when_its_self_test_does`<br>`tests/unit/test_router_hints.py::test_the_gap_register_stays_on_the_device` (runs the text gate's egress check)<br>Partial: gap G-3 |
| INV-63 | A URL decoded from text (`decode` or `decodeIfPresent`) counts as the network everywhere but `EngineClient.swift`. | #58 (D-126) | `tests/unit/test_client_decl_gate.py::test_a_url_decoded_outside_the_engine_client_is_the_network`<br>`tests/unit/test_client_decl_gate.py::test_a_url_decoded_if_present_is_the_network_too`<br>Partial: gap G-3 |
| INV-64 | The engine is asked only for the budget and a surface id that the router chose or the reader tapped. Nothing typed reaches a request. | D-126; D-160 cl. 1 as amended (D-168 note 9); REQ-RTR-004; M17 row 20 | `tests/unit/test_router_hints.py::test_nothing_typed_by_the_reader_reaches_the_engine`<br>`ios/EngineTests/EngineClientTests.swift::testNothingTheReaderTypedIsEverSent`<br>`ios/EngineTests/EngineClientTests.swift::testTheSurfaceAndTheBudgetAreBothSentAndNothingElseIs` |
| INV-65 | The boards request carries no parameter and no header of its own. | D-167 cl. 1; D-160 cl. 1 | `ios/EngineTests/EngineClientTests.swift::testTheBoardsRequestCarriesNothing`<br>`ios/EngineTests/EngineClientTests.swift::testTheBoardsRequestSetsNoHeaderOfItsOwn` |
| INV-66 | Nothing derived from the question (its text, its refinements, the reader's removals) reaches the boards request or the standings file. | D-168 cl. 9; D-160 cl. 1 as amended; REQ-GAP-001; **#85**; M17 MINOR-3, rows 22, 23 | **none**: gap G-1 (#85) |
| INV-67 | The typed question is kept only in the gap register: a file on this device, protected while locked, excluded from backup, bounded in bytes. | REQ-GAP-001; D-126; #58 | `tests/unit/test_router_hints.py::test_the_gap_register_stays_on_the_device`<br>`ios/EngineTests/FrontDoorTests.swift::testTheRegisterIsOnlyEverAFileOnThisDevice`<br>`ios/EngineTests/FrontDoorTests.swift::testThePhonesStoreIsProtectedWhileLocked`<br>`ios/EngineTests/FrontDoorTests.swift::testASavedRegisterIsExcludedFromBackupOnDisk`<br>`ios/EngineTests/FrontDoorTests.swift::testAnEntryIsBoundedInBytesNotOnlyCharacters`<br>`ios/EngineTests/FrontDoorTests.swift::testASaveToAnythingButAFileTriesNoWrite`<br>Partial: gap G-1 (the standings file) |
| INV-68 | Only a model search is kept in the register. A held reading (not a search, or unsure) sends no request and keeps nothing until the reader taps. | D-169 cl. 4, 5 as amended at M18-W3 | `ios/EngineTests/ReadingTests.swift::testOnlyASearchIsKeptInTheGapRegister`<br>`tests/unit/test_ios_client_contract.py::test_the_front_door_is_wired_to_the_logic_it_depends_on` |
| INV-69 | The on-device model's answer is a closed set, mapped only by `ModelOutputBoundary`. A surface the engine did not serve, an undeclared refinement, or a verdict outside its two values is dropped. Only the wording tier builds alternatives. | D-126; D-160 cl. 4; D-168 cl. 2, note 6; D-169 as amended; W5 S1; M17 row 21 | `ios/EngineTests/RouterBoundaryTests.swift::testAnIdTheEngineDidNotServeIsRefused`<br>`ios/EngineTests/RefinementBoundaryTests.swift::testAValueTheTableDoesNotDeclareIsDropped`<br>`ios/EngineTests/RefinementBoundaryTests.swift::testTheModelsSchemaOffersExactlyTheDeclaredChoicesAndNothingElse`<br>`ios/EngineTests/ReadingTests.swift::testTheBoundaryMapsTheModelsVerdict`<br>`tests/unit/test_router_hints.py::test_the_router_never_produces_anything_but_a_category_id`<br>`tests/unit/test_router_hints.py::test_only_the_model_output_boundary_builds_an_outcome_with_refinements`<br>`tests/unit/test_router_hints.py::test_only_the_wording_tier_builds_an_outcome_with_alternatives` |
| INV-70 | `select` makes a surface the request's `task` only when the engine lists it. | W5 security S1 (defence in depth); M17 I-8, row 24 | `tests/unit/test_ios_client_contract.py::test_the_front_door_is_wired_to_the_logic_it_depends_on` |

### The phone: what it reads, keeps and runs

| INV | Invariant | Source | Negative test(s) |
|---|---|---|---|
| INV-71 | Every response is read only up to its route's byte ceiling, and the read stops there while the body streams. A declared length past the ceiling is refused before the body. | #56; D-167 (4 MiB for boards) | `ios/EngineTests/EngineClientTests.swift::testTheReadStopsAtTheCeilingWhileTheResponseStreams`<br>`ios/EngineTests/EngineClientTests.swift::testADeclaredLengthOverTheCeilingIsRefusedBeforeTheBody`<br>`ios/EngineTests/EngineClientTests.swift::testAnOversizedAnswerIsRefusedOnTheRoutesThatHadNoCeiling`<br>`ios/EngineTests/EngineClientTests.swift::testAnOversizedRefusalIsCappedToo`<br>`tests/unit/test_ios_client_contract.py::test_every_response_is_read_through_its_routes_ceiling` |
| INV-72 | The app follows a redirect only on its configured engine host. | `SameHostOnly`; D-171 cl. 4 | `ios/EngineTests/EngineClientTests.swift::testARedirectToAnotherHostIsRefused`<br>`ios/EngineTests/EngineClientTests.swift::testAHostThatMERELYENDSWithTheEngineHostIsRefused`<br>`ios/EngineTests/EngineClientTests.swift::testARedirectWithNoHostAtAllIsRefused`<br>`tests/unit/test_ios_client_contract.py::test_the_client_refuses_a_redirect_that_leaves_its_configured_host` |
| INV-73 | The app's engine address is set per build, and is loopback unless an http(s) URL with a host is given. The only transport-security exception is local networking. The simulator build is pinned to loopback. | D-171 cl. 4, note 5 | `ios/EngineTests/EngineClientTests.swift::testAnythingElseFallsBackToLoopback`<br>`tests/unit/test_engine_address.py::test_the_default_engine_is_loopback_and_the_owners_address_stays_on_his_mac`<br>`tests/unit/test_engine_address.py::test_the_partial_plist_carries_the_address_and_only_the_local_network_exception`<br>`tests/unit/test_engine_service.py::test_the_app_script_builds_for_the_simulators_loopback_whatever_the_owners_override` |
| INV-74 | The standings store reads and writes only a file on the device, keeps only the fields the app decodes, and refuses a payload over 4 MiB. | D-167 amendment (W4 security S1, S2) | `ios/EngineTests/StandingsStoreTests.swift::testAStorePointedAnywhereButAFileReadsNothing`<br>`ios/EngineTests/StandingsStoreTests.swift::testOnlyTheFieldsTheAppDecodesAreStored`<br>`ios/EngineTests/StandingsStoreTests.swift::testAPayloadOverTheCeilingIsNeverAccepted` |
| INV-75 | A Release build reads neither its launch arguments nor its launch environment. A scripted routing answer passes the same boundary as the model's, and the Engine compiles the same on Debug. | D-175 cl. 3 and "as built" | `make client-decls`<br>`tests/unit/test_client_decl_gate.py::test_a_release_build_carries_no_ui_test_hook`<br>`tests/unit/test_client_decl_gate.py::test_main_refuses_a_release_dump_that_carries_a_ui_test_hook`<br>`ios/EngineTests/RouterBoundaryTests.swift::testAScriptedSurfaceTheEngineDoesNotServeIsRefused`<br>`tests/unit/test_ios_platform_drift.py::test_the_engine_sources_are_not_conditionally_compiled_on_debug_or_os` |
| INV-76 | The phone changes no number the engine sent, and orders nothing itself, except in the files an ADR names. | D-104; D-138; D-160 cl. 2; D-167 cl. 4 | `tests/unit/test_ios_client_contract.py::test_the_client_performs_no_arithmetic_on_a_number_the_engine_sent`<br>`tests/unit/test_ios_client_contract.py::test_score_arithmetic_happens_only_where_an_adr_permits_it`<br>`tests/unit/test_ios_client_contract.py::test_position_arithmetic_happens_only_where_an_adr_permits_it`<br>`tests/unit/test_ios_client_contract.py::test_the_client_applies_no_ordering_of_its_own`<br>Partial: gap G-2 |
| INV-77 | The engine has no model in its scoring path: no model makes or changes a score, price or rank. No module imports a model package, statically or by name, and no lock holds one. | D-104 | `tests/unit/test_security_surface.py::test_the_engine_imports_no_model_and_declares_none`<br>`tests/unit/test_security_surface.py::test_the_model_check_fails_on_a_planted_import` |

### Tests, supply chain and process

| INV | Invariant | Source | Negative test(s) |
|---|---|---|---|
| INV-6 | No test reaches the network. Every Swift test runs behind a tripwire, and no Python test downloads a slice file. | M1; #59; permission matrix §3 | `ios/EngineTests/OfflineTestCase.swift::testARequestAStubDeclinesIsCaughtToo`<br>`ios/EngineTests/OfflineTestCase.swift::testARequestNoStubAnswersIsCaughtWithoutLeavingTheMachine`<br>`ios/EngineTests/OfflineTestCase.swift::testEverySessionConfigurationAsksTheTripwireFirst`<br>`tests/unit/test_swift_tests_offline.py::test_every_swift_test_class_derives_from_the_offline_base`<br>`tests/unit/test_swift_tests_offline.py::test_no_swift_source_builds_a_background_session`<br>`tests/unit/test_arena_slices.py::test_no_test_downloads_a_slice_file`<br>`tests/unit/test_build_slices.py::test_an_unmarked_test_builds_with_no_slices_so_it_never_reaches_the_network`<br>`tests/unit/test_no_network.py::test_a_planted_real_request_fails_the_test`<br>`tests/unit/test_no_network.py::test_this_machine_is_still_reachable` |
| INV-78 | The text pins read code, not comments or strings, and fail closed on a comment that never closes. | #98 | `tests/unit/test_router_hints.py::test_the_comment_stripper_handles_nesting_and_comment_markers_in_comments`<br>`tests/unit/test_router_hints.py::test_the_comment_stripper_reads_raw_strings_and_interpolation`<br>`tests/unit/test_router_hints.py::test_the_comment_stripper_fails_closed_on_a_comment_that_never_closes`<br>Partial: gap G-3 |
| INV-79 | No secret is committed. | Baseline §1; M16 row 25; M17 row 29 | `make secrets` |
| INV-80 | Declared dependencies have no known advisory, exist on PyPI and are not brand new. | Baseline (dependency hygiene); permission matrix | `make deps`<br>`make slopsquat`<br>`tests/unit/test_dependency_gate.py::test_the_gate_sees_every_declared_dependency` |
| INV-81 | Every install (the working tree, the engine's release, the Docker image) takes a hash-checked lock that is current with `pyproject.toml`, and the locked build backend, and resolves or fetches nothing else. The serving lock carries no `pyarrow`. | D-177; #35, #26; M17 closure I-6 | `tests/unit/test_dependency_locks.py::test_every_lock_is_current_with_pyproject`<br>`tests/unit/test_dependency_locks.py::test_a_changed_dependency_makes_a_lock_stale`<br>`tests/unit/test_dependency_locks.py::test_every_package_is_pinned_with_its_hashes`<br>`tests/unit/test_dependency_locks.py::test_every_install_reads_its_lock_and_resolves_nothing_else`<br>`tests/unit/test_dependency_locks.py::test_the_install_check_reads_every_spelling`<br>`tests/unit/test_dependency_locks.py::test_only_the_refresh_locks_carry_pyarrow` |
| INV-14 | Every GitHub Action is pinned to a commit SHA. | M3 | `make conformance` (`conformance/test-action-pins.py`) |
| INV-82 | An agent cannot run a destructive git or `rm` command, or push the protected branch. | M16 row 24; permission matrix §5 | `make conformance` (`conformance/test-hook-claims.py` runs the guards) |
| INV-83 | A wave that touches input parsing (`src/app/clients`) is HIGH. | #83 | `tests/unit/test_wave_check_m18_rules.py::test_a_wave_touching_input_parsing_must_be_high`<br>`tests/unit/test_wave_check_m18_rules.py::test_the_input_parsing_rule_has_no_way_around_it` |
| INV-10 | The CI workflows are read-only (`contents: read`) with no secret in a run body. The issue agent's write scope is by design. | M2, M3 | `tests/unit/test_security_surface.py::test_every_workflow_reads_only_but_the_issue_agent`<br>`tests/unit/test_security_surface.py::test_the_workflow_check_fails_on_a_planted_writer_and_a_secret_in_a_run` |
| INV-11 | Nothing turns TLS verification off, tests included: no `verify=False` or unverified context in Python, no trust-any-server credential in Swift. | M2 | `tests/unit/test_security_surface.py::test_nothing_turns_tls_verification_off`<br>`tests/unit/test_security_surface.py::test_the_tls_check_fails_on_a_planted_verify_false` |

**Count.** 71 rows. One has no test yet (INV-66, gap G-1). Five more hold only in part, and each
names its gap.

## Gaps

Each gap is an invariant that a test does not yet hold, or holds only in part. Each one has an issue.

| Gap | Rows | What is not held | Issue |
|---|---|---|---|
| G-1 | INV-66, INV-67 | The two privacy sinks hold by spelling, not by data flow. A relay through a static on `EngineClient` can send a refinement on `/v1/boards`, and one line in `ContentView.swift` can save the typed question through `StandingsStore`. Both M17 mutants (P2, P3) still pass every gate | #85 |
| G-2 | INV-76 | The arithmetic and ordering tripwires match names, so an aliased value or a same-named receiver passes | #60 |
| G-3 | INV-62, INV-63, INV-78 | The phone gates have known holes: `URL(_:strategy:)`, `NSDataDetector` and a generic decode wrapper make a URL from text and pass; code under `#if false` passes the text pins, and a dropped declaration passes the declaration gate | #107, #110 |

**Closed by M18-W6.** Four gaps the drafting found were closed in the same wave, each with a test:
the `select` guard (INV-70, M17's I-8), CI least privilege (INV-10), TLS never turned off (INV-11),
and no model in the engine (INV-77). W-125, W-126 and W-130 (INV-43, INV-42) were fixed in the same
wave, and M17's survivors on the read-only rule (INV-23) and the launcher (INV-27 to INV-29) by
earlier M18 waves.

**Closed by M18-W7.** G-4 (#121, the register's save), G-5 (#122, the Python suite's network guard)
and G-6 (#123, the launcher's bound refusal), each with its test in its row.

**Related, not a gap.** #94: the Docker image binds 0.0.0.0 with no Host list, so INV-25 refuses
every outside request. That fails closed; it matters only for a hosted engine.

## Retired ids

These numbers were given by the M1 to M5 reviews and are not rows above. They are not reused.

| INV | What it was | Why it is not a row |
|---|---|---|
| INV-7 | CLI exit codes | A product rule, held by its REQ rows |
| INV-8 | Only the three documented endpoints are read, with no scraping (D-101) | Merged into INV-3: every fetch goes to a host its client declares |
| INV-12 | Curated data fails loud and is replaced atomically | A product rule; the atomic publish is INV-4 |
| INV-13 | Staleness fails toward disclosure | A product rule |
| INV-15 | Roster scope | A product rule |
| INV-16 | Link provenance | A product rule |
| INV-17 | Health fails toward disclosure | A product rule |
| INV-18 | Rounding happens once | A product rule |
| INV-19 | Roster evidence ages in the output | Proposed at M4, never ratified |
| INV-20 | Effort is printed | A product rule |
| INV-21 | A payload cites every source | A licensing rule, with the licence table (#88); held by `test_board_standings.py::test_an_unattributed_source_fails_rather_than_publishing` |
| INV-24 | Undated evidence is disclosed | A product rule |

Rows the closure tables listed that are now superseded:
- M16 row 21 (the D-157 display): fixed by D-157's second amendment, INV-58.
- M17 row 26 ("substring presence only"): replaced by M18-W1's tests that run the launcher (INV-27 to
  INV-29).
- D-160 clause 1 as first written: amended by D-168 note 9. The surface leaves as `task` (INV-64);
  the text, the refinements and the removals do not (INV-66).
- D-171 clause 3's firewall as a control: withdrawn by its note 7; `--no-lan` is the one control
  (INV-28).
- D-159 clause 3's first half: withdrawn by the M17-W1 correction; its second half is INV-52.

## Mutation samples

Each sample removes one invariant with a one-line edit in place, runs the row's tests, and restores
the file by hash. Killed means a cited test failed. The M16 and M17 samples are in their closure
reviews (§3 of `docs/reviews/m17-closure-security-review.md`).

**M18-W6, the author (2026-10-04, at `d894ab5` to `f984977`):**

| # | Row | The edit | Result |
|---|---|---|---|
| 1 | INV-26 | the Host check's `not in allowed` made `False` (`main.py`) | killed: `test_a_host_not_on_the_list_is_refused` |
| 2 | INV-25 | the network-address test made `return False` (`main.py`) | killed: `test_without_a_list_a_request_arriving_on_a_network_address_is_refused` |
| 3 | INV-27 | the launcher's preflight branch made `if false` (`engine_service.sh`) | killed: `test_the_launchers_preflight_refuses_a_bind_beyond_loopback_without_hosts` |
| 4 | INV-28 | `--host 0.0.0.0` added to the launcher's uvicorn line | killed: `test_the_launcher_binds_exactly_one_host_and_reads_it_from_the_bind_variable` |
| 5 | INV-29 | the wrapper's `chmod 700` made `777` (`install_engine_service.sh`) | killed: `test_the_installed_wrapper_is_the_owners_alone` |
| 6 | INV-23 | `/v1/boards` opens with `sqlite3.connect` instead of `open_readonly` | killed: `test_readonly_uri.py` |
| 7 | INV-47 | the archive's symlink check made `if False` (`epoch_bundle.py`) | killed: `test_a_symlink_member_is_refused` |
| 8 | INV-40 | the reader gets the whole environment (`arena_slices.py`) | killed: `test_the_reader_gets_no_secret_from_the_environment` |
| 9 | INV-5 | a stored date is cut, not parsed (`ingest.py`) | killed: `test_a_stored_date_is_a_calendar_date_or_nothing` |
| 10 | INV-58 | the display bound `{0,63}` made `{0,4999}` (`registry.py`) | killed: `test_a_spelling_the_grammar_accepts_is_still_bounded_for_display` |
| 11 | INV-70 | the `select` guard removed (`ContentView.swift`) | killed: `test_the_front_door_is_wired_to_the_logic_it_depends_on` |

**M18-W6, the independent code review** (`docs/reviews/m18-wave-6-review.md`): 20 mutants, 19
killed. The survivor was INV-38's group half (`S_IWOTH` alone); a test now holds it
(`test_a_group_writable_artifact_directory_stops_the_cycle_too`).

