# XAUUSD ICT Agent (πειραματικό)

Αυτόνομος trading agent για XAUUSD μέσω MetaTrader 5. Ο κώδικας της στρατηγικής
είναι **ο ίδιος** στο backtest και στο live: η `strategy/ict.py` είναι καθαρή
συνάρτηση των κλεισμένων κεριών και τη χρησιμοποιούν και τα δύο.

> ⚠️ Πειραματικό λογισμικό. Δεν υπάρχει καμία ένδειξη ότι η στρατηγική έχει edge
> μέχρι να περάσει τη Φάση 2 σε πραγματικά δεδομένα. Μην πας σε live πριν από αυτό.

## Δομή

```
config.yaml        όλες οι παράμετροι (με validation — τα όρια ρίσκου δεν χαλαρώνουν από το config)
main.py            CLI
core/              config, timezones/DST, μοντέλα δεδομένων
data/              Dukascopy downloader, MT5 export, loader/validation, resample H1/H4, synthetic
strategy/          indicators (ATR, swings), H1/H4 structural bias, ICT κανόνες
risk/              position sizing, ημερήσια/συνολικά όρια, kill switch
news/              news filter (ForexFactory feed + ιστορικό/χειροκίνητο CSV)
execution/         Broker interface, MT5 adapter (reconnect), live loop
backtest/          event-driven engine, μετρικές, report, walk-forward/OOS
notifier/          Telegram, logging, decision journal, ημερήσιο CSV
tests/             94 unit tests
```

## Εγκατάσταση (Windows, εκεί τρέχει το MT5)

```powershell
cd xauusd_agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # συμπλήρωσε MT5_* και TELEGRAM_*
python -m pytest            # όλα πρέπει να περάσουν
```

Στο MT5: Tools → Options → Expert Advisors → **Allow algorithmic trading**.
Ρύθμισε το `symbol.name` στο `config.yaml` αν ο broker λέει το χρυσό π.χ. `XAUUSD.m` ή `GOLD`.

## Φάσεις

| Φάση | Εντολή | Τι κάνει |
|---|---|---|
| Δεδομένα | `python main.py download` | Dukascopy M1 bid+ask → M5 με πραγματικό ιστορικό spread (2023-01 → 2026-09) |
| | `python main.py export-mt5` | (προαιρετικό) M5 από τον broker σου, για σύγκριση |
| 1. Backtest | `python main.py backtest` | Report: win rate, avg R, expectancy, PF, max DD, Sharpe, equity curve → `reports/` |
| 2. Walk-forward | `python main.py walkforward` | Holdout, rolling WF, sensitivity, τυχαίες είσοδοι, bootstrap → **ετυμηγορία** |
| 3. Paper | `python main.py run` | Demo λογαριασμός (default). Αρνείται να τρέξει αν ο λογαριασμός είναι real |
| 4. Live | `python main.py run --live` | Μόνο με real λογαριασμό **και** πληκτρολόγηση `LIVE <login>` στο τερματικό |

Άλλες εντολές: `python main.py news` (επερχόμενα blackouts), `python main.py reset-shutdown`
(μετά από max-DD shutdown), `python main.py synthetic` (τυχαία δεδομένα για smoke test — **χωρίς** edge εκ κατασκευής).

## Κανόνες στρατηγικής (`strategy/ict.py`)

1. **Ασιατικό range**: high/low M5 02:00–09:00 ώρα Ελλάδας.
2. Ένα επίπεδο είναι «άθικτο» μέχρι να το περάσει η τιμή. Μόνο το πρώτο πέρασμα **μέσα σε killzone** είναι sweep.
   Αν περαστεί εκτός killzone, «καταναλώνεται» και δεν δίνει setup.
3. **Killzones**: London 10:00–13:00 Athens, NY 08:30–11:00 New York (= 15:30–18:00 Athens εκτός από ~3 εβδομάδες/χρόνο με διαφορετικό DST — ρυθμίζεται).
4. **MSS**: μέσα σε 12 M5 κεριά από το sweep, κλείσιμο πέρα από το τελευταίο επιβεβαιωμένο αντίθετο swing, μέσα στο range,
   με displacement (μεγαλύτερο σώμα ≥ 1×ATR).
5. **Bias**: H1 market structure (κλείσιμο πέρα από swing) στην κατεύθυνση του trade, και το H4 να συμφωνεί.
6. **Entry**: limit στο μέσο του FVG του displacement, αλλιώς στο order block. Ισχύει 1 ώρα, ποτέ μετά το killzone.
7. **Stop** πίσω από το ακραίο του sweep (+buffer). **Target** η αντίθετη ασιατική πλευρά. Αν R:R < 2 → **απόρριψη** (το target δεν τεντώνεται).
8. Κλείσιμο όλων 16:45 New York (πριν το ημερήσιο break του χρυσού).

Κάθε βήμα γράφεται στο decision journal (`logs/decisions_*.jsonl`, `reports/*/decisions.csv`):
γιατί μπήκε ή γιατί **δεν** μπήκε (bias, displacement, R:R, news, spread, όρια, κ.λπ.).

## Risk (αδιαπραγμάτευτο — επιβάλλεται από τον validator του config)

- Ρίσκο 0,5–1% ανά trade. Lots = budget / (απώλεια ανά lot στο SL **μαζί με** slippage και commission), στρογγυλοποίηση πάντα προς τα κάτω.
  Αν ακόμα και το min lot ξεπερνά το budget → απόρριψη. Live: η απώλεια ανά lot υπολογίζεται από τον broker (`order_calc_profit`).
- Max 2 trades/ημέρα, max 1 ανοιχτή θέση (μαζί με τα pending).
- Daily loss 2% από το equity στην αρχή της ημέρας → κλείσιμο και παύση μέχρι την επόμενη μέρα. Το ρίσκο κάθε νέου trade περιορίζεται ώστε να μη μπορεί να ξεπεράσει το υπόλοιπο του ημερήσιου ορίου.
- Max DD 8% από το υψηλότερο equity → κλείνει τα πάντα + shutdown. Επιμένει μετά από restart. Ξεκλειδώνει μόνο με `reset-shutdown`.
- Spread filter (`risk.max_spread`).
- **Kill switch**: δημιούργησε ένα αρχείο `STOP` στον φάκελο ή στείλε `/stop` στο Telegram. Κλείνει θέσεις, ακυρώνει orders, σταματά.
  Το bot δέχεται εντολές μόνο από το δικό σου chat_id και αγνοεί εντολές που στάλθηκαν πριν ξεκινήσει.
- Η κατάσταση του risk γράφεται ατομικά στον δίσκο (`state/demo|live/`). Demo και live έχουν ξεχωριστή κατάσταση.

## News filter

Καμία νέα θέση 30' πριν έως 30' μετά από high-impact USD news. Τα pending ακυρώνονται μέσα στο παράθυρο.
- Live: ForexFactory weekly JSON (cache, refresh ανά 6 ώρες). Μπλοκάρει **όλα** τα high-impact USD.
- Fallback / backtest: `news/data/usd_high_impact.csv` (CPI, NFP, PCE, FOMC 2023–2026) + `news/data/manual_events.csv`.
- Αν καμία πηγή δεν καλύπτει την τρέχουσα στιγμή → **block** (fail-safe).

Το CSV έχει στήλη `status`: `confirmed` (επιβεβαιωμένο κατά την έρευνα), `recalled` (από γνώση, όχι διασταυρωμένο), `unverified`. Κάνε δειγματοληπτικό έλεγχο.

## Μοντέλο κόστους backtest (συντηρητικό)

Bid bars, ask = bid + πραγματικό spread Dukascopy (× multiplier, με ελάχιστο όριο). Commission 7$/lot round-turn, slippage 0,10$ στα stops.
Αν μέσα στο ίδιο κερί πιάνονται και το SL και το TP → SL. Στο κερί του fill μετράει μόνο το SL.
Gap πέρα από το stop → εκτέλεση στο open. Οι αριθμοί είναι στο `config.yaml → costs`.
Τα spreads του Dukascopy είναι ECN· ο broker σου μπορεί να είναι ακριβότερος. Δοκίμασε `spread_multiplier: 1.5`.

## Γνωστοί περιορισμοί (ειλικρινά)

- Ο MT5 adapter έχει ελεγχθεί μόνο με ψεύτικο MT5 module (τα tests τρέχουν σε Linux). **Η πρώτη εκτέλεση σε demo είναι μέρος της δοκιμής**: παρακολούθησέ την.
- Οι κανόνες είναι αυστηροί, οπότε τα trades αναμένονται λίγα (σε συνθετικά δεδομένα ~0,4 σήματα τον μήνα· σε πραγματικά θα φανεί στο backtest). Λίγα trades σημαίνει ότι συχνά δεν μπορεί να βγει στατιστικά σίγουρο συμπέρασμα. Το walk-forward τότε απαντά **INCONCLUSIVE**, και αυτό σημαίνει «δεν αποδείχθηκε edge», όχι «ίσως έχει».
- Το Dukascopy δεν είναι ο broker σου: διαφορές στις τιμές και στο ωράριο αλλάζουν ποια setups εμφανίζονται.
