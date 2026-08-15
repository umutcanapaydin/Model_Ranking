---
record_type: ratification
id: closure-report-m2
status: ratified
date: 2026-08-11
---
# Closure Report — M2: New Sources + Everyday-Assistant Category

> Owner's A0.5 milestone-session review pack. Generated 2026-08-11 from committed artifacts.
> Mode variance (owner-signed amendments, m2-plan:3-9): no per-wave checkpoint commits (git = this
> session, once); council-instead-of-owner for questions (none convened — see §5).

## 1. What shipped (signed plan m2-plan.md §2 — criteria diffs: NONE)

| Criterion | Citing test | Status |
|---|---|---|
| REQ-ING-005 OpenRouter pricing ($/token str→$/1M, skip-unpriced, provenance) | test_openrouter_ingest.py (8 tests incl. '-1'/''/'1e-3' edges); live: contract test (CI) | ✅ |
| REQ-ING-006 median of per-source medians (M1 risk fix) | test_rank.py::test_median_of_per_source_medians_beats_outlier_source | ✅ |
| REQ-ING-007 Arena → Elo rows (harness=arena-crowd, full-slice, dup keep-best) | test_arena_ingest.py (9) + test_arena_client.py (4, respx pagination); live ≥20: CI | ✅ |
| REQ-ING-008 CC-BY attribution in every export | test_categories.py::test_export_carries_attribution (+observed_at) | ✅ |
| REQ-CAT-001 categories as data | test_categories.py::test_categories_are_data_not_code | ✅ |
| REQ-CAT-002 assistant ranks on Arena Elo | ::test_assistant_ranking_orders_by_elo | ✅ |
| REQ-CAT-003 no cross-scale averaging (structural) | ::test_no_cross_scale_averaging_structural | ✅ |
| REQ-REC-005 --task assistant|coding, Elo wording, coding regression | test_recommend_assistant.py (7) + test_cli_e2e.py::test_cli_task_assistant… + full M1 suite green | ✅ |
| REQ-REC-006 stale primary evidence disclosed | ::test_stale_primary_source_is_disclosed (both branches) + suppression fault RED | ✅ |
| REQ-CI-001 unit gate on push + gated contract job | ci.yml (repo) + contract-tests.yml (NEW; dispatch+weekly cron, RUN_CONTRACT_TESTS=1) | ✅* |

*Live half runs in CI — trigger `contract-tests` from the Actions tab after this commit; its first
green run completes REQ-ING-005/007's live clauses (sandbox cannot reach HF/OpenRouter).

## 1a. Per-wave table

| Wave | Tier | Review | Findings o/c | Test Δ | Escalations |
|---|---|---|---|---|---|
| W1 OpenRouter + median fix | LOW | combined (pair-batch, own verdict) | 2 MINOR / 2 | +8 | none |
| W2 Arena | LOW | combined — PASS | 3 MINOR / 3 | +13 | none |
| W3 category layer | LOW | combined — PASS | 2 MINOR + 2 PROCESS / 4 | +6 | none |
| W4 recommender + CI | LOW | combined — PASS | 4 MINOR / 4 | +9 | none |
| closure | — | Security-Reviewer — PASS | 2 MINOR (replica artifacts) + 4 NOTE / 2 | — | none |
| W5 Epoch (stretch) | — | NOT STARTED — deferred as planned | — | — | — |

## 1b. Decisions made on your behalf (assumption ledger)

- Arena erişimi HF **datasets-server rows API** ile (dokümante endpoint; parquet bağımlılığı yok);
  şekil dataset card'dan doğrulandı (WebFetch, 2026-08-11) — "shape pinned at dispatch" sözü böyle tutuldu.
- Arena'da "full" kategori dilimi tercih, yoksa toleranslı fallback (test edildi) — kart 22 subset listeliyor.
- OpenRouter'da mükerrer id keep-FIRST (katalog sırası kanonik; skorlardaki keep-best'ten farklı — kodda gerekçeli).
- Asistan eşikleri: min 1300 Elo, değer penceresi 30 Elo, yakın-çağrı 5 Elo — İLK KALİBRASYON,
  canlı CI verisiyle M3'te gözden geçirilecek (özellikle 1300 tabanı keyfî).
- RankingRow/Pick alan adları genelleştirildi (plan §4 "frozen" notundan belgeli sapma — D-105;
  dış tüketici yoktu). JSON çıktısı değişti: `score`/`metric`/`secondary_score`.
- Review'lar çift-dalga BATCH koşuldu (W1+W2, W3+W4; ayrı hükümler) — token ekonomisi; her dalga
  kendi verdiktini aldı, ledger'landı.

## 2. File record (git = this session)

Net M2: ~1.260 satır ekleme (src+tests+CI); yeni modüller: openrouter.py, arena.py, categories.py,
contract-tests.yml; suite 74 → **109 test** (104 unit + 5 gated), coverage **90%**.

## 3. Trust telemetry

İlk gerçek git verisi bu commit'le başlar (M1 tek commit'ti; owner waiver ile M2 de tek commit).
Self-report (METR): 4/4 dalgada review bulgu üretti (13 uygulandı); en değerlisi W4'ün "üçüncü
kategori yanlış ölçek devralır" latent-debt yakalaması — üçüncü kategori daha YOKKEN yakalandı.
Tripwire: yok. Council: hiç toplanmadı (0 çağrı).

## 4. Security & invariants

Stage 4.0: **PASS** (docs/reviews/m2-security-review.md). M1'in 8 değişmezi tutuyor (endpoint
sayısı 3→5, ikisi de dokümante veri API'si); YENİ: INV-9 (sayfalama sessiz kırpma yapamaz,
negatif testli), INV-10 (CI least-privilege — yaptırımı SENİN K.10 diff incelemen), INV-11
(testler TLS kapatamaz). ⛔-glob teması: yok.

## 5. Ledgers (nothing silent)

- **Skipped:** canlı Arena/OpenRouter doğrulaması sandbox'ta İMKÂNSIZ → CI'a taşındı (plan §0,
  imzalı) — ilk CI koşusu senin tetiklemende. make-check-venv/gitleaks yine host/CI-side.
- **Council:** 0 toplantı — tek adaydı (Arena şekli), birincil kaynak (dataset card) çözdü.
- **Seed adayları:** (1) "Owner sorusu sanılan şeylerin çoğu birincil-kaynak sorusudur";
  (2) "Proxy kontrolün kör noktası docstring'inde yaşar" (stale-notice false-negative).
- **M3'e taşınan:** Elo eşik kalibrasyonu (canlı veriyle); ArenaClient url-param temizliği;
  actions SHA-pin (cron canlıya alınmadan); Epoch (W5 stretch, hiç başlanmadı); frontier-dışı
  yakın-çağrı ifşası (tasarım tercihi — istersen tartışırız).

## 6. Architecture delta — PROSE

Bu milestone motoru tek-kategorili bir araçtan çok-kategorili bir platforma çevirdi, ama bunu tek
bir dürüstlük kuralının etrafında yaptı: her kullanım alanı KENDİ ölçeğinde yarışır. Kategoriler
artık kod değil veri — categories.py'daki bir kayıt; birincil benchmark'ı, ölçek birimi ve üç
eşiği (taban/pencere/yakın-çağrı) kaydın içinde taşınır, bu yüzden üçüncü kategori eklemek SQL'e
veya motora dokunmaz ve yanlış ölçek devralamaz (bunu bir yapısal test de kilitler: aynı modelin
hem Elo'su hem SWE yüzdesi varken ikisi de ham kalmak zorundadır). Fiyat tarafında ikinci kaynak
geldi ve medyan iki aşamalı oldu — önce kaynak içi, sonra kaynaklar arası — böylece 50 ucuz alias
listeleyen bir kaynak tek adil fiyatlı kaynağı ezemez. Arena verisi resmî veri setinin dokümante
API'sinden sayfalanarak gelir; sayfalama sınıra çarparsa sessizce kırpmak yerine durur. Kırılma
noktaları: HF datasets-server şeması değişirse parser YÜKSEK SESLE durur (haftalık CI probu bunun
erken uyarısı); Elo eşikleri ilk kalibrasyon — canlı veri başka bir dağılım gösterirse M3'te
categories.py'daki üç sayı değişir, kod değişmez. Gelecek bakımcı için tek kritik yeni kural:
bir kategorinin skoru daima kendi birincil benchmark'ının ham değeridir — "birleşik puan" isteği
gelirse cevap D-105'tir, refleks değil.

---
*Owner sign-off: ______ / tarih: ______*
