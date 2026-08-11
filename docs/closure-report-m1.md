# Closure Report — M1: Data Layer + Recommendation Engine (coding)

> Owner's A0.5 milestone-session review pack. Generated 2026-08-11 from committed artifacts
> (wave checklists, review files, test runs). Time-box: 60–90 min. **NOTE (mode variance):** no
> git history exists yet — the owner's repo (github.com/umutcanapaydin/Model_Ranking) was created
> at closure; "commit range" referents below are therefore FILE referents. All checkpoint commits
> are owed and collapse into the owner's initial commit(s) this session.

## 1. What shipped (from the signed plan — docs/plans/m1-plan.md §2)

| Acceptance criterion | Citing test | Gate run | Status |
|---|---|---|---|
| REQ-ING-001 LiteLLM pricing (≥500, no zero rows, provenance) | tests/unit/test_litellm_ingest.py::test_parse_skips_unpriced…, ::test_ingest_stores_rows_with_provenance; live: tests/integration/test_litellm_contract.py (2154 rows) | 71 passed + 3 live | ✅ |
| REQ-ING-002 SWE-bench Verified (harness with every score) | test_swebench_ingest.py::test_only_verified_board…, ::test_harness_is_retained…, ::test_run_date_and_cost… | same | ✅ |
| REQ-ING-003 Aider (+staleness flag) | test_aider_ingest.py::test_ingest_surfaces_health_in_report (+7) — live flag fired: "311 days old" | same | ✅ |
| REQ-ING-004 provenance + deterministic re-run, no scraping | rerun/rollback/NULL tests both ingest files; test_schema.py provenance ×3 | same | ✅ |
| REQ-CAN-001 alias→canonical, drops counted | test_registry.py::test_reconcile_maps_and_counts_drops (+dropped_names) | same | ✅ |
| REQ-CAN-002 variant-before-parent (spike-bug regression) | ::test_variant_never_leaks…, ::test_sibling_variants…, ::test_rule_order…, ::test_date_suffixed… | same | ✅ |
| REQ-CAN-003 median-not-min price | test_rank.py::test_median_not_min_beats_outlier, ::test_even_count_median… | same | ✅ |
| REQ-RANK-001 coding ranking (≥20 models live: 28 eligible) | ::test_ranking_takes_best_score…, ::test_model_without_price…, ::test_tied_best_scores… | same | ✅ |
| REQ-RANK-002 CSV+JSON identical + metadata | ::test_export_csv_and_json_identical_rows, ::test_export_empty… | same | ✅ |
| REQ-REC-001 three labeled deterministic picks | test_recommend.py::test_three_labeled_deterministic_picks; e2e test_cli_e2e.py (real entry, V4C-50) | same | ✅ |
| REQ-REC-002 hard budget filter (tested constants) | ::test_budget_filter_is_hard_constraint, ::test_budget_filters_nonempty_ranking_to_none, CLI exit-code tests | same | ✅ |
| REQ-REC-003 Pareto, never score÷price | ::test_pareto_non_dominance, ::test_frontier_excludes…, ::test_value_pick_rule… | same | ✅ |
| REQ-REC-004 confidence + close-call disclosure | ::test_confidence_grades…, ::test_close_call_is_disclosed | same | ✅ |

**Criteria diffs since plan signature:** NONE.

## 1a. Per-wave table

| Wave | Tier | Review depth | Findings o/c | Test Δ | Escalations | Checkpoint |
|---|---|---|---|---|---|---|
| W1 schema+LiteLLM | LOW | combined C-R+Tester | 9 MINOR / 9 | +23 | none | OWED → initial commit |
| W2 SWE-bench+Aider | LOW | combined | 5 MINOR / 5 | +18 | none | OWED |
| W3 registry+ranking | LOW | combined — **FAIL→fixed** | 2 BLOCKING + 4 MINOR / 6 | +15 | none | OWED |
| W4 recommender+CLI | LOW | combined — **CHANGES→fixed** | 1 BLOCKING + 3 MINOR / 4 | +18 | none | OWED |
| closure | — | Security-Reviewer | 0 BLOCKING, 2 MINOR / 2 | — | none | — |

## 1b. Decisions made on your behalf (assumption ledger)

- "W1 e başlayabiliriz" mesajın §13 imzası sayıldı (m1-plan.md:3) — teyit edildi sonraki mesajınla.
- A0.5 aktif mod kabul edildi (protokol default'u A0 iken) — D-103, statüsü PROPOSED; bu oturumda onayla/да düzelt.
- pyyaml bağımlılığı eklendi (plan W2 Aider YAML kapsamında; permission-matrix §2 "ASK" → checklist'e ledger'landı).
- Belirsiz alias'lar DÜŞÜRÜLÜR, tahmin edilmez (ör. `gpt-5-2026-08-01` hiçbir aileye yazılmaz) — REQ-CAN-001 muhafazakâr yorumu.
- Aider'ın 0.0 cost'u "rapor edilmemiş" sayılıp NULL'a çevrildi; swebench 0.0'ı olduğu gibi saklar (kaynak semantiği farkı, w2 checklist).
- Ruff'a Türkçe karakter istisnası eklendi (allowed-confusables, pyproject) — öneri metinleri Türkçe.

## 2. File record (git yok — dosya referansları)

- Net: ~2.600 satır (src+tests), 13 src modülü, 10 test dosyası, 74 test (71 unit + 3 canlı sözleşme).
- Coverage: %88 toplam (recommend.py %74 — CLI satırları subprocess'te koşuyor, coverage izleyemiyor; e2e testleri VAR).
- Değişen çekirdek dosyalar: schema/protocols/litellm/swebench/aider/fakes/ingest/registry/rank/recommend + testler + pyproject (+.gitignore *.db).

## 3. Trust telemetry

Mekanik telemetri (post-closure fix rate, churn, revert) **hesaplanamadı — git tarihi yok**; ilk
gerçek değerler M2 kapanışında. **Self-report (METR):** 4 dalganın 2'sinde taze-göz inceleme ciddi
hata yakaladı (W3 gerçek-alias sızıntısı, W4 yalan-açıklama) — kendi başıma bunları kaçırmıştım;
inceleme katmanı somut değer üretti. İlk CANLI koşu fixture'ların göremediği bir veri durumu yakaladı
(Aider mükerrer model), kontrol tasarlandığı gibi yüksek sesle durdu. Tripwire: yok.

## 4. Security & invariants

- Stage 4.0 Security review: **PASS**, 0 BLOCKING (docs/reviews/m1-security-review.md) — 10 maddelik
  baseline yürüyüşü + 8 güvenlik değişmezi, her biri negatif testiyle kayıtlı.
- MINOR'lar kapatıldı: kullanılmayan bağımlılıklar "planned" yorumuna çekildi; .gitignore'a `*.db` eklendi;
  CLI connect try-bloğuna alındı.
- ⛔-glob teması: YOK (auth/PII/ödeme/migration yüzeyi yok).

## 5. Ledgers (nothing silent)

- **Skipped ×4 dalga:** `make check` (venv) + gitleaks host-side'a ertelendi — **bu oturumda sen koşuyorsun** (aşağıda komutlar). Başka skip yok.
- **Seed adayları (onayına):** (1) "İlk canlı koşu dalganın İÇİNDE zorunlu adım — fixture hayal edilen veriyi modeller"; (2) "Starter'ın src/__init__.py kusuru upstream'e bildirilmeli (make typecheck kırılıyor)".
- **M2'ye taşınan riskler:** medyan her (alias,source) satırını eşit sayıyor (çok-kaynaklı fiyatta çarpıklaşır); Aider bayat — sıralamada kalsın mı kararı; kayıt tablosu canlı LiteLLM'e karşı driftlenir (dropped_names raporu kapanışlarda yürünecek — bu koşuda 1497 fiyat alias'ı düştü, çoğu embedding/eski model: örneklem incelendi).

## 6. Architecture delta — PROSE

Bu milestone sıfırdan bir veri motoru kurdu. Üç kaynak client'ı tek bir RawSource sözleşmesinin
arkasında yaşıyor; her biri ham metni indirir, saf fonksiyon parser'ı tipli satırlara çevirir, ingestion
katmanı tek transaction'da eski çalışma setini silip yenisini yazar — bu yüzden pipeline istediğin an,
hiçbir şey bozmadan yeniden koşulabilir; SQLite dosyası tamamen harcanabilirdir. İşin kalbi registry:
sıralı, ilk-eşleşme-kazanır alias kural tablosu; alt-varyant kuralları ebeveynden önce gelir ve
eşleşmeyen isim ASLA tahmin edilmez, sayılarak düşürülür — projenin IP'si bu tablonun bakımıdır.
Ranking katmanı model başına en iyi skoru harness'ıyla birlikte taşır ve fiyat referansı medyan alır;
öneri motoru önce bütçeyi keser, sonra Pareto sınırından üç etiketli cevap üretir ve emin olmadığında
bunu söyler. Kırılabilecek yerler: kaynak JSON/YAML şemaları değişirse parser'lar YÜKSEK SESLE durur
(sessiz bozulma yok, ama koşu durur); registry canlıdaki yeni model isimlerine karşı elle bakım ister —
dropped_names raporu bunun erken uyarısıdır. Gelecek bakımcının bilmesi gereken tek kritik kural:
skor daima model+harness çiftidir; harness'ı düşüren her sorgu yanlış sonuç üretir.

---
*Owner sign-off: ______ / tarih: ______*
