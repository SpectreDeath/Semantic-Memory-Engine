# Russ Stylometric Forensics Context

**Saved:** 2026-06-15T19:54:15-04:00  
**Workspace:** `D:\GitHub\projects\SME`

## Project Context

- SME project: Lawnmower Man v3.0.1, Python 3.13 intended, current runtime warning shows Python 3.14 in use.
- Goal: build a stylometric profile for Russell Vought across multiple communication registers.
- Primary corpus root: `D:\STylometric profiling\Russ Vought`
- SME corpus root: `data/corpus/vought_baseline/`

## Corpus Categories

- `pure_prose/`
  - Active processed prose baseline.
  - Contains cleaned/processed markdown files with `wng_processed_` prefix plus `00_wng_author_page_Russell_Vought.md`.
  - Used for ScribeEngine and PyStyl baseline metrics.
- `raw_pure_prose/`
  - Raw source markdown copies for traceability.
  - Must not be scanned by active Scribe/PyStyl baseline loops.
- `social_x/`
  - X/Twitter profile and post snapshots.
  - Not mixed into `pure_prose` because short-form social text would skew editorial stylometry.
- `official_directives/`
  - OMB/budget directive PDFs.
- `official_directives_text/`
  - Extracted text from directive PDFs.
- `congressional_testimony/`
  - Congressional testimony/statement PDFs.
- `congressional_testimony_text/`
  - Extracted text from testimony PDFs.
  - `Final.Testimony of Russell T Vought[1].pdf` remains scanned/OCR-only and extracts as 1 character.
- `project_2025/`
  - `2025_MandateForLeadership_FULL.pdf`
- `project_2025_text/`
  - Extracted full Mandate text: `2025_MandateForLeadership_FULL.txt`

## Key Scripts

- `scripts/ingest_wng_vought.py`
  - Crawls WORLD author/archive URLs when accessible.
  - Detects AWS WAF challenges.
  - Writes clean markdown and manifest entries.
- `scripts/process_local_wng.py`
  - Processes local markdown files from `data/raw_cache/wng_prose/`.
  - Writes processed files into `data/corpus/vought_baseline/pure_prose/`.
  - Updates `wng_vought_manifest.json`.
  - Strips browser markdown scaffolding and avoids WAF garbage ingestion.
- `scripts/run_rolling_delta_analysis.py`
  - Runs `RollingDelta.analyze_rolling_delta()` over Project 2025 text.
  - Uses `window_size=1500`, `step=500`.
  - Loads candidates from:
    - `data/corpus/vought_baseline/pure_prose/`
    - `data/corpus/vought_baseline/official_directives_text/`
  - Appends register tags:
    - `_prose`
    - `_bureaucratic`
  - Saves complete output to:
    - `data/corpus/vought_baseline/project_2025_rolling_delta_results.json`

## Current Baseline Metrics

`pure_prose` processed baseline:

```text
file_count: 18
total_words: 16242
weighted_avg_sentence_length: 23.09
weighted_type_token_ratio: 0.455
```

`social_x` profile:

```text
file_count: 3
total_words: 577
weighted_avg_sentence_length: 12.44
weighted_type_token_ratio: 0.544
```

`official_directives` extracted text:

```text
file_count: 4
total_words: 17821
weighted_avg_sentence_length: 32.21
weighted_type_token_ratio: 0.192
```

`congressional_testimony` extracted text:

```text
file_count: 2
total_words: 601
weighted_avg_sentence_length: 23.31
weighted_type_token_ratio: 0.489
```

## Rolling Delta Results

Target:

```text
data/corpus/vought_baseline/project_2025_text/2025_MandateForLeadership_FULL.txt
```

Full rolling delta output:

```text
data/corpus/vought_baseline/project_2025_rolling_delta_results.json
```

Summary output:

```text
data/corpus/vought_baseline/project_2025_rolling_delta_summary.json
```

Chapter fingerprint summary:

```text
data/corpus/vought_baseline/project_2025_chapter_fingerprint_summary.json
```

Rolling Delta config:

```text
window_size: 1500
step: 500
threshold: 0.25
candidates: 22
windows analyzed: 733
low-distance hits: 666
hit rate: 90.86%
```

Chapter 2 control:

```text
Chapter 2: Executive Office of the President of the United States
author: Russ Vought
pages: 43–68
token range: 24230–35955
window indices: 49–71
window_count: 23
hit_count: 19
hit_rate: 82.61%
min_distance: 0.1588739429441642
dominant_candidate: Fiscal_Year_2026_Discretionary_Budget_Request_bureaucratic
```

Interpretation:

- Confirmed Vought Chapter 2 matches the bureaucratic/official-directive register more than the `pure_prose` register.
- Many non-Vought chapters also show high bureaucratic-register hit rates.
- Current `0.25` threshold is useful for detecting bureaucratic-register continuity but is too permissive for unique authorship claims.
- Strongest `pure_prose` matches are concentrated in early windows 18–29, closest to `wng_processed_Renewing_American_Purpose_prose`.

## Important Warnings

- Do not scan `raw_pure_prose/` as active baseline.
- Do not mix `social_x/` into `pure_prose`.
- Do not treat high bureaucratic-register matches as proof of Vought authorship without stricter controls.
- The current rolling delta baseline is dominated by `Fiscal_Year_2026_Discretionary_Budget_Request_bureaucratic`.
- Need stricter thresholds, candidate pruning, or chapter-specific controls before making ghostwriting/redrafting claims.

## Follow-Up Isolation Pass

**Saved:** 2026-06-15T20:15:00-04:00

### Interpretation Update

- The 90.86% all-register hit rate is now treated as evidence of broad bureaucratic-register alignment, not direct Vought authorship across the whole document.
- The confirmed Vought control chapter still anchors to `Fiscal_Year_2026_Discretionary_Budget_Request_bureaucratic`.
- High bureaucratic hit rates in non-Vought chapters should be interpreted as shared federal-policy/budget-register structure unless a stricter contrastive or prose-only pass also flags the same region.

### New Artifacts

- `data/corpus/vought_baseline/project_2025_anomalous_run_map.json`
  - Maps anomalous sustained low-distance runs to chapter/token boundaries and start snippets.
- `data/corpus/vought_baseline/project_2025_pure_prose_only_rolling_delta_results.json`
  - Pure-prose-only pass with strict threshold `0.10`.
- `data/corpus/vought_baseline/project_2025_pure_prose_only_threshold_013_results.json`
  - Pure-prose-only pass with threshold `0.13` to inspect the `Renewing_American_Purpose` lead.
- `data/corpus/vought_baseline/project_2025_contrastive_delta_results.json`
  - Contrastive pass comparing closest prose distance against closest bureaucratic distance.
- `data/corpus/vought_baseline/project_2025_followup_isolation_summary.json`
  - Compact summary of run map, pure-prose-only hits, and contrastive hits.

### Anomalous Run Mapping

Run 1, windows 71–200, tokens 35,500–101,500:

```text
Overlaps Chapter 2 tail: Russ Vought, Executive Office of the President
Overlaps Chapter 3: Donald Devine, Dennis Dean Kirk, and Paul Dans, Central Personnel Agencies
Overlaps Chapter 4: Christopher Miller, Department of Defense
Overlaps Chapter 5: Ken Cuccinelli, Department of Homeland Security
Overlaps Chapter 6: Kiron K. Skinner, Department of State
Overlaps Chapter 7: Dustin J. Carmack, Intelligence Community
```

Run 2, windows 276–339, tokens 138,000–171,000:

```text
Overlaps Chapter 10 tail: Daren Bakst, Department of Agriculture
Overlaps Chapter 11: Lindsey M. Burke, Department of Education
Overlaps Chapter 12: Bernard L. McNamee, Department of Energy and Related Commissions
```

Run 3, windows 490–604, tokens 245,000–303,500:

```text
Overlaps Chapter 17 tail: Gene Hamilton, Department of Justice
Overlaps Chapter 18: Jonathan Berry, Department of Labor and Related Agencies
Overlaps Chapter 19: Diana Furchtgott-Roth, Department of Transportation
Overlaps Chapter 20: Brooks D. Tucker, Department of Veterans Affairs
Overlaps Chapter 21: Thomas F. Gilman, Department of Commerce
Overlaps Chapter 22: William L. Walton, Stephen Moore, and David R. Burton, Department of the Treasury
Overlaps Chapter 23: Veronique de Rugy / Jennifer Hazelton, Export–Import Bank
```

### Pure-Prose Isolation Result

Strict pure-prose-only threshold `0.10`:

```text
hit_count: 0
```

Exploratory pure-prose-only threshold `0.13`:

```text
hit_count: 9
window_count: 733
hit_rate: 1.23%
dominant candidate: wng_processed_Renewing_American_Purpose_prose
windows: 18, 20, 21, 24, 25, 26, 27, 28, 29
start tokens: 9000, 10000, 10500, 12000, 12500, 13000, 13500, 14000, 14500
minimum distance: 0.11234351047749622 at window 21 / token 10500
```

Important correction: windows 18–29 are before the Chapter 1 token start in the current chapter map (`Chapter 1 start_token: 15834`), so they likely sit in introductory/front-matter material rather than inside Chapter 1 proper.

### Contrastive Delta Result

Contrastive score definition:

```text
closest_prose_distance - closest_bureaucratic_distance
```

Interpretation:

```text
Negative score means prose profile is closer than bureaucratic profile.
Threshold: < -0.05
```

Result:

```text
hit_count: 14
window_count: 733
hit_rate: 1.91%
```

Contrastive prose-closer clusters:

```text
windows 20–29, start tokens 10000–14500
dominant prose candidate: wng_processed_Renewing_American_Purpose_prose
contrastive score range: about -0.056 to -0.089
```

Additional isolated contrastive hits:

```text
window 470, start token 235000, Chapter 17 tail: Department of Justice
windows 658–660, start tokens 329000–330000, Chapter 26: Trade
```

### Script Update

`scripts/run_rolling_delta_analysis.py` now supports:

```text
--candidate-mode all|prose|bureaucratic
--contrastive-output <path>
--contrastive-threshold <float>
```

Example commands used:

```powershell
python scripts\run_rolling_delta_analysis.py --candidate-mode prose --threshold 0.10 --output data\corpus\vought_baseline\project_2025_pure_prose_only_rolling_delta_results.json

python scripts\run_rolling_delta_analysis.py --candidate-mode prose --threshold 0.13 --output data\corpus\vought_baseline\project_2025_pure_prose_only_threshold_013_results.json

python scripts\run_rolling_delta_analysis.py --candidate-mode all --threshold 0.25 --contrastive-output data\corpus\vought_baseline\project_2025_contrastive_delta_results.json --output data\corpus\vought_baseline\project_2025_rolling_delta_results.json
```

### Revised Forensic Position

- Strongest evidence for a distinctive Vought-like prose signal is the early front-matter cluster around windows 18–29 and contrastive windows 20–29.
- The massive sustained bureaucratic clusters are better treated as register-level evidence of Mandate-wide policy/budget engineering.
- Windows 470 and 658–660 are secondary prose-closer candidates but need manual inspection before being treated as authorship claims.
- Do not claim Vought ghostwriting from bureaucratic-register dominance alone.

## Review Fixes Applied

**Saved:** 2026-06-16T06:48:00-04:00

- `scripts/ingest_wng_vought.py`
  - Removed unused `timezone` import.
  - Changed default crawler output from active `pure_prose/` to staging `data/raw_cache/wng_prose/`.
  - Kept the crawl manifest pointed at `data/corpus/vought_baseline/pure_prose/wng_vought_manifest.json`.
  - Fixed manifest writes to use the configured `self.manifest_path` instead of the module-level default path.
- `scripts/run_rolling_delta_analysis.py`
  - Added `--candidate-mode all|prose|bureaucratic`.
  - Added `--contrastive-output` and `--contrastive-threshold`.
  - Added `--include-full-series`; default output is compact.
  - Fixed `end_token_estimate` to use the configured `window_size`.
  - Fixed contrastive output metadata so its embedded `output_path` points to the contrastive artifact.
- `.gitignore`
  - Added `data/corpus/` and `data/raw_cache/` to prevent accidental commit of large/copyrighted corpus artifacts.
- `pyproject.toml`
  - Added undeclared runtime dependencies:
    - `beautifulsoup4>=4.12.0`
    - `markdownify>=0.13.0`

Verification run after fixes:

```powershell
python -m py_compile scripts\ingest_wng_vought.py scripts\process_local_wng.py scripts\run_rolling_delta_analysis.py
ruff check scripts\ingest_wng_vought.py scripts\process_local_wng.py scripts\run_rolling_delta_analysis.py
```

Regenerated compact artifacts:

```text
data/corpus/vought_baseline/project_2025_rolling_delta_results.json
data/corpus/vought_baseline/project_2025_contrastive_delta_results.json
data/corpus/vought_baseline/project_2025_pure_prose_only_threshold_013_results.json
```

## Suspect Windows 18-29 Extraction

**Saved:** 2026-06-16T10:19:14-04:00

- New script:
  - `scripts/extract_suspect_windows.py`
- Target file:
  - `data/corpus/vought_baseline/project_2025_text/2025_MandateForLeadership_FULL.txt`
- Target range:
  - Windows 18–29 from the rolling delta sweep.
  - Configured as word-token `9000` inclusive through `16000` exclusive.
  - Rolling context: `window_size=1500`, `step=500`.
- Extracted artifact:
  - `data/corpus/vought_baseline/project_2025_text/suspect_windows_18_29_extracted.txt`

Detected headers in the extracted block:

```text
RETURN SELF-GOVERNANCE TO THE AMERICAN PEOPLE.
BORDERS, AND BOUNTY AGAINST GLOBAL THREATS.
BEST EFFORT
ENDNOTES
Section One
TAKING THE REINS
OF GOVERNMENT
WHITE HOUSE OFFICE
```

Interpretation:

- The suspect windows sit before `Section One / Taking the Reins of Government` and include the tail of the opening `Conservative Promise` section.
- The block crosses from endnotes/front-matter material into `Section One` and then lands at the start of `Chapter 1: White House Office`.
- The `Renewing_American_Purpose` pure-prose signal in windows 18–29 is therefore likely tied to this front-matter/section-opening material rather than a later agency chapter.

Validation:

```powershell
python scripts\extract_suspect_windows.py
python -m py_compile scripts\extract_suspect_windows.py
ruff check scripts\extract_suspect_windows.py
```

## Casework Data Ignore Policy

**Saved:** 2026-06-16T10:19:14-04:00

Root ignore policy:

```text
data/corpus/**
!data/corpus/
!data/corpus/.gitignore
data/raw_cache/**
!data/raw_cache/
!data/raw_cache/.gitignore
```

Nested ignore files added:

```text
data/corpus/.gitignore
data/raw_cache/.gitignore
```

Nested ignore contents:

```gitignore
*
!*/
!.gitignore
```

Purpose:

- Keep generated casework artifacts, PDFs, extracted text, JSON outputs, and raw source copies out of the working tree by default.
- Allow the nested `.gitignore` files themselves to remain trackable so future repos or checkout states preserve the ignore policy.
- Prevent accidental staging/commit of large or copyrighted corpus material.

Verification:

```text
git check-ignore -v data/corpus/vought_baseline/project_2025_rolling_delta_results.json
# data/corpus/.gitignore:1:*

git check-ignore -v data/corpus/.gitignore data/raw_cache/.gitignore
# data/corpus/.gitignore:3:!.gitignore
# data/raw_cache/.gitignore:3:!.gitignore
```

## Prompt Template for Suspect Window Extraction

**Saved:** 2026-06-16T12:12:05-04:00

The following prompt template was captured for future Kilo Code runs targeting the same early-window contrastive anomaly:

```text
Act as a Python engineer working inside my Semantic Memory Engine (SME) framework.

I need a diagnostic utility script that targets a specific anomalous text range we discovered during our rolling delta sweep.

Context:
1. Target File: `data/corpus/vought_baseline/project_2025_text/2025_MandateForLeadership_FULL.txt`
2. Target Range: Windows 18–29. At our configured window_size=1500 and step=500, this corresponds roughly to Word-Tokens 9,000 through 16,000.
3. Relevant Artifact to reference: `data/corpus/vought_baseline/project_2025_pure_prose_only_threshold_013_results.json`

Requirements:
- Create a script named `scripts/extract_suspect_windows.py`.
- The script must load the full `2025_MandateForLeadership_FULL.txt` file and slice the exact word-token range from token 9,000 to token 16,000.
- It must scan this slice to identify and extract any major Section Headers or Chapter Titles contained within it so we know exactly where this text sits in the book's layout.
- Print the isolated text block and headers cleanly to the console with a clear visual delimiter.
- Save the extracted text block as a separate forensic artifact to `data/corpus/vought_baseline/project_2025_text/suspect_windows_18_29_extracted.txt`.

Ensure the script handles file reading safely using utf-8 encoding and prints a clear success message once the artifact is written.
```

Validation routine attached to the template:

```powershell
ruff check scripts\extract_suspect_windows.py
python scripts\extract_suspect_windows.py
```

Current status:

- The script already exists at `scripts/extract_suspect_windows.py`.
- The artifact already exists at `data/corpus/vought_baseline/project_2025_text/suspect_windows_18_29_extracted.txt`.
- The extracted block has been mapped to the early front-matter / section-opening area around `Section One`, `Taking the Reins of Government`, and `White House Office`.

## Rapid Interpretive Checks on Extracted Artifact

**Saved:** 2026-06-16T13:32:00-04:00

### Structural Header Audit

Artifact inspected:

```text
data/corpus/vought_baseline/project_2025_text/suspect_windows_18_29_extracted.txt
```

Headers and structural markers found in the extracted token slice:

```text
Mandate for Leadership: The Conservative Promise
PROMISE #2: DISMANTLE THE ADMINISTRATIVE STATE AND
RETURN SELF-GOVERNANCE TO THE AMERICAN PEOPLE.
2025 Presidential Transition Project
PROMISE #3: DEFEND OUR NATION’S SOVEREIGNTY,
BORDERS, AND BOUNTY AGAINST GLOBAL THREATS.
The Conservative Promise lays out how to use many of these tools including:
ENDNOTES
Section One
TAKING THE REINS
OF GOVERNMENT
WHITE HOUSE OFFICE
```

Structural interpretation:

- The extracted range begins inside the opening `Conservative Promise` essay.
- It includes `PROMISE #2: Dismantle the Administrative State and Return Self-Governance to the American People.`
- It includes `PROMISE #3: Defend Our Nation’s Sovereignty, Borders, and Bounty Against Global Threats.`
- It includes `ENDNOTES` for that front-matter essay.
- It then crosses into `Section One: Taking the Reins of Government`.
- The tail lands at `WHITE HOUSE OFFICE`, the start of Chapter 1.
- This confirms the early prose-closer signal is not in a later agency chapter; it is in the book’s front-matter / section-opening material immediately before Chapter 1.

### Micro-Habit Verification

Quick counts on `suspect_windows_18_29_extracted.txt`:

```text
chars=44956
words=6757
exclamation_points=1
question_marks=0
commas=408
commas_per_1000_words=60.38
semicolons=20
colons=32
nonblank_lines=648
```

Interpretation:

- Exclamation points are effectively absent.
- Question marks are absent.
- Comma density is high at `60.38` commas per 1,000 words.
- The text contains long chained clauses and parenthetical-style comma sequencing.
- Ideological vocabulary is consistent with the known Vought/WORLD Opinions register: administrative accountability, constitutional authority, institutional capture, federal bureaucracy, executive restoration, and structural overhaul.
- This supports the hypothesis that the extracted front-matter block is where the document breaks away from generic bureaucratese and moves closer to the Vought `pure_prose` signature.

### Contrastive Plot Across Remaining Authorship Pools

Command run:

```powershell
python scripts\run_rolling_delta_analysis.py --target data\corpus\vought_baseline\project_2025_text\suspect_windows_18_29_extracted.txt --output C:\Users\spectre\AppData\Local\Temp\kilo\suspect_windows_18_29_extracted_rolling_delta_results.json --contrastive-output C:\Users\spectre\AppData\Local\Temp\kilo\suspect_windows_18_29_extracted_contrastive_delta_results.json --threshold 0.25 --contrastive-threshold -0.05 --include-full-series
```

Result:

- Target artifact word count reported by rolling script: `7000`.
- Windows analyzed: `12`.
- Every local extracted window was closest to:

```text
wng_processed_Renewing_American_Purpose_prose
```

- All 12 extracted windows fell below the `0.25` rolling delta threshold.
- Contrastive hit rate: `10 / 12 = 83.33%`.
- Contrastive threshold: `< -0.05`.
- Closest bureaucratic candidate in every contrastive hit:

```text
Fiscal_Year_2026_Discretionary_Budget_Request_bureaucratic
```

- Strongest local contrastive hit:

```text
window_index=3
start_token=1500
end_token_estimate=3000
closest_prose_candidate=wng_processed_Renewing_American_Purpose_prose
closest_prose_distance=0.11234351047749622
closest_bureaucratic_candidate=Fiscal_Year_2026_Discretionary_Budget_Request_bureaucratic
closest_bureaucratic_distance=0.20141941710574585
contrastive_score=-0.08907590662824963
```

Interpretation:

- The extracted artifact is not merely bureaucratic-register adjacent.
- It is consistently closer to the WORLD Opinions `pure_prose` pool than to the OMB/budget bureaucratic pool.
- The strongest match is still `Renewing_American_Purpose`, matching the earlier global rolling delta result.
- The contrastive result strengthens the earlier conclusion: windows 18–29 isolate a real prose-style departure from the dominant bureaucratic baseline.
- This remains a stylometric signal, not a standalone authorship proof.

## Contrastive Validation Layers Implementation

**Saved:** 2026-06-16T16:05:00-04:00

Implemented a stronger validation path for the Windows 18–29 contrastive finding.

Files changed/added:

```text
src/scribe/engine.py
scripts/run_rolling_delta_analysis.py
scripts/validate_contrastive_layers.py
data/corpus/control_authors/
```

### Layer 1: Cross-author control testing

- Added `data/corpus/control_authors/` as the intended staging location for signed public prose from control authors such as Lindsey M. Burke, Christopher Miller, and Ken Cuccinelli.
- `scripts/run_rolling_delta_analysis.py` now includes `CONTROL_AUTHORS_DIR`.
- When `--candidate-mode all` is used, the rolling loop automatically ingests any author subdirectories under:

```text
data/corpus/control_authors/<author_name>/*.md|*.txt
```

- Control authors are emitted as candidate keys like:

```text
control_lindsey_m_burke_prose
control_christopher_miller_prose
control_ken_cuccinelli_prose
```

- These control candidates are included in the rolling comparison but are not treated as prose-vs-bureaucratic contrastive candidates unless their keys end in `_prose` or `_bureaucratic`.

Validation logic:

```text
If Windows 18–29 remain closest to Vought pure prose after control authors are added,
false-positive risk is reduced because the model is no longer merely choosing the
nearest broad Heritage/conservative-policy register.
```

Current run status:

```text
warnings: No control-author files found under data\corpus\control_authors
candidate_count: 22
control_author_candidates: []
```

Interpretation:

- The control-author layer is structurally ready.
- The current validation run did not include control authors because no signed control-author prose has been staged yet.
- To complete this layer, add signed public prose under `data/corpus/control_authors/<author_name>/` and rerun:

```powershell
python scripts\validate_contrastive_layers.py
```

### Layer 2: Micro-stylometric feature injection

Added `ScribeEngine.extract_micro_features()` in:

```text
src/scribe/engine.py
```

Features now extracted:

```text
word_count
sentence_count
avg_sentence_length
avg_clause_chain_length
comma_per_1000_words
sentence_end_per_1000_words
comma_to_sentence_end_ratio
semicolon_per_1000_words
colon_per_1000_words
em_dash_per_1000_words
parenthetical_per_1000_words
passive_voice_ratio
active_voice_ratio
coordinated_statutory_phrase_per_1000_words
long_chained_construction_per_1000_words
```

Validation script:

```text
scripts/validate_contrastive_layers.py
```

Artifact:

```text
data/corpus/vought_baseline/validation_layers/validation_micro_features_summary.json
```

Current micro-feature result for Windows 18–29:

```text
suspect_window_indices: 18-29
adjacent_window_indices: 13-17 and 30-34
top delta features:
- word_count delta: -39.33333333333326
- sentence_end_per_1000_words delta: +4.389509318167711
- sentence_count delta: -3.299999999999997
- parenthetical_per_1000_words delta: -3.2174289190910037
- em_dash_per_1000_words delta: +2.053990302599015
- semicolon_per_1000_words delta: +1.9236172259039854
- comma_per_1000_words delta: +1.792007128585837
```

Interpretation:

- The suspect range shows a measurable structural shift relative to adjacent windows.
- The strongest signal is not a single function-word feature; it is a cluster of punctuation, sentence-boundary, and clause-chain features.
- This supports the authorial-intrusion hypothesis more than a pure function-word model would, but it still needs control-author comparison to rule out shared editorial style.

### Layer 3: High-frequency modifier keyness

Implemented a modifier-keyness pass in:

```text
scripts/validate_contrastive_layers.py
```

Method:

```text
extract_modifiers()
log_likelihood_ratio()
compute_modifier_keyness()
```

Artifact:

```text
data/corpus/vought_baseline/validation_layers/validation_modifier_keyness.json
```

Current top-ranked modifiers for Vought `Renewing_American_Purpose_prose` vs background corpora:

```text
constitutional   vought_per_1000_words=4.4543429844097995   background_per_1000_words=0.3061286965040103   llr=24.491957220004917
efficient        vought_per_1000_words=1.78173719376392     background_per_1000_words=0.0                    llr=16.912450399966485
dignified        vought_per_1000_words=1.3363028953229399   background_per_1000_words=0.0                    llr=12.683161608167772
original         vought_per_1000_words=1.3363028953229399   background_per_1000_words=0.0                    llr=12.683161608167772
left             vought_per_1000_words=0.89086859688196     background_per_1000_words=0.0                    llr=8.454657205457279
civil            vought_per_1000_words=1.3363028953229399   background_per_1000_words=0.06122573930080205    llr=8.44174582050778
independent      vought_per_1000_words=1.78173719376392     background_per_1000_words=0.18367721790240618    llr=8.123254338872485
```

Suspect-window modifier presence:

```text
window 18: civil, constitutional, difficult, independent, original
window 19: constitutional, courageous, difficult, independent, left
window 20: constitutional, courageous, difficult, independent, left
window 21: constant, constitutional, courageous, left
window 22: constant, constitutional
window 23: constant, constitutional
window 24: constitutional
window 25: bad, constitutional, new
window 26: bad, civil, constitutional, new
window 27: bad, civil, constitutional, new
window 28: civil, constitutional, donald, independent, new
window 29: constitutional, donald, independent, new
```

Interpretation:

- `constitutional` is the strongest modifier-keyness signal in the current background comparison.
- The suspect windows repeatedly contain top-ranked Vought modifiers, especially `constitutional`, `civil`, `independent`, and `original`.
- This aligns with the ideological/rhetorical frame of Vought’s `Renewing_American_Purpose_prose`.
- The keyness pass remains probabilistic because the current background excludes signed control-author prose.

### Layer 4: Macroscopic trend plotting

Implemented full-document rolling plot generation in:

```text
scripts/validate_contrastive_layers.py
```

Plot artifact:

```text
data/corpus/vought_baseline/validation_layers/vought_prose_vs_bureaucratic_full_document.png
```

Default plotted candidates:

```text
Vought prose:      wng_processed_Renewing_American_Purpose_prose
Vought bureaucratic: Fiscal_Year_2026_Discretionary_Budget_Request_bureaucratic
```

Smoothing:

```text
SMA 10
```

Validation command:

```powershell
python scripts\validate_contrastive_layers.py
```

Supporting validation commands already run:

```powershell
python -m py_compile src\scribe\engine.py scripts\run_rolling_delta_analysis.py scripts\validate_contrastive_layers.py
ruff check src\scribe\engine.py scripts\run_rolling_delta_analysis.py scripts\validate_contrastive_layers.py
python scripts\validate_contrastive_layers.py
```

Current validation outputs:

```text
data/corpus/vought_baseline/validation_layers/validation_summary.json
data/corpus/vought_baseline/validation_layers/validation_micro_features_summary.json
data/corpus/vought_baseline/validation_layers/validation_modifier_keyness.json
data/corpus/vought_baseline/validation_layers/validation_rolling_delta_results.json
data/corpus/vought_baseline/validation_layers/vought_prose_vs_bureaucratic_full_document.png
```

Interpretation guidance encoded in `validation_summary.json`:

Strengthens Vought hypothesis:

```text
- Windows 18-29 remain closest to Vought pure prose after control authors are added.
- Micro-feature deltas show a coherent structural shift, not just shared policy vocabulary.
- Modifier keyness shows Vought-aligned rhetorical choices inside Windows 18-29.
- Full-document plot shows local returns toward Vought prose rather than a document-wide genre effect.
```

Weakens Vought hypothesis:

```text
- A control author beats Vought prose once public prose controls are included.
- Windows 18-29 do not differ materially from adjacent windows on micro-features.
- Key modifiers are common across institutional chapters and not concentrated in the suspect range.
```

Suggests genre detection:

```text
- Vought prose and Vought bureaucratic profiles track together across the whole document.
- Control authors and institutional corpora cluster near Vought prose on the same conservative-policy register.
- Modifier keyness is dominated by generic conservative-policy terms rather than author-specific structural habits.
```

Current caveat:

```text
The control-author corpus is now populated for Lindsey M. Burke, Christopher C. Miller, and Ken Cuccinelli.
The validation run completed with no warnings and candidate_count=25.
One Federalist Cuccinelli source remained robots-blocked and was not staged.
```

## Control Author Corpus Completed

**Saved:** 2026-06-16T16:41:16-04:00

### Control Corpus Files

Staged signed public prose under:

```text
data/corpus/control_authors/
data/raw_cache/control_raw/
data/metadata/control_author_sources.csv
data/metadata/control_author_sources.json
```

Final staged files:

```text
data/corpus/control_authors/lindsey_m_burke/control_burke_prose_01.md
data/corpus/control_authors/lindsey_m_burke/control_burke_prose_02.md
data/corpus/control_authors/christopher_c_miller/control_miller_prose_01.md
data/corpus/control_authors/christopher_c_miller/control_miller_prose_02.md
data/corpus/control_authors/ken_cuccinelli/control_cuccinelli_prose_01.md
```

Approximate staged word counts:

```text
control_burke_prose_01.md: 876 words
control_burke_prose_02.md: 846 words
control_miller_prose_01.md: 2114 words
control_miller_prose_02.md: 5041 words
control_cuccinelli_prose_01.md: 927 words
```

Control candidates loaded by validation:

```text
control_lindsey_m_burke_prose
control_christopher_c_miller_prose
control_ken_cuccinelli_prose
```

### Source Decisions

Robots-allowed sources staged:

```text
Lindsey M. Burke — Fox News — Universal school choice is needed – Your address shouldn’t limit your child’s future
https://www.foxnews.com/opinion/lindsey-burke-universal-school-choice-is-needed-separate-housing-from-education

Lindsey M. Burke — Fox News — Coronavirus school closings should prompt states to pay parents to educate kids in other ways
https://www.foxnews.com/opinion/lindsey-burke-coronavirus-disruption-in-k-12-a-short-term-necessity-or-lasting-shift

Christopher C. Miller — Task & Purpose — US Army Special Forces Need To Go 'Back To Basics' For Great Power Competition
https://taskandpurpose.com/news/army-special-forces-back-to-basics-oped/

Christopher C. Miller — DocumentCloud / U.S. House Committee on Oversight and Reform — Statement for Committee on Oversight and Reform
https://s3.documentcloud.org/documents/20705853/christopher-c-miller-statement-5122021.pdf

Ken Cuccinelli — The Hill — DeSantis is right: Rhetoric won’t stop cartels at our borders, only force
https://digital-dev.thehill.com/opinion/immigration/4202741-desantis-is-right-rhetoric-wont-stop-cartels-at-our-borders-only-force/
```

Robots-blocked or skipped sources:

```text
Lindsey M. Burke Heritage URLs: robots.txt disallowed Heritage source URLs.
Ken Cuccinelli Federalist URL: robots.txt disallowed this URL.
```

### Ingestion Script Fixes

`scripts/ingest_control_authors.py` now:

- Uses Fox News and The Hill robots-allowed sources for Burke/Cuccinelli instead of robots-blocked Heritage/Federalist/Washington Examiner URLs.
- Extracts Task & Purpose `ArticleBody` from JSON-LD when normal HTML-to-markdown conversion is short or fragile.
- Handles BeautifulSoup tags whose `attrs` value is `None`.
- Records word counts for existing staged outputs instead of writing `word_count=0` for `skipped_existing`.

Validation commands run:

```powershell
python -m py_compile scripts\ingest_control_authors.py
ruff check scripts\ingest_control_authors.py
python scripts\ingest_control_authors.py
```

### Validation Run With Controls

Command run:

```powershell
python scripts\validate_contrastive_layers.py
```

Validation summary:

```text
warnings: []
candidate_count: 25
control_author_candidates:
- control_christopher_c_miller_prose
- control_ken_cuccinelli_prose
- control_lindsey_m_burke_prose
```

Artifacts regenerated:

```text
data/corpus/vought_baseline/validation_layers/validation_summary.json
data/corpus/vought_baseline/validation_layers/validation_micro_features_summary.json
data/corpus/vought_baseline/validation_layers/validation_modifier_keyness.json
data/corpus/vought_baseline/validation_layers/validation_rolling_delta_results.json
data/corpus/vought_baseline/validation_layers/vought_prose_vs_bureaucratic_full_document.png
```

### Rolling Delta Result With Controls

Top suspect-window 18-29 mean distances after controls were added:

```text
wng_processed_Renewing_American_Purpose_prose:
  suspect_mean=0.128011
  adjacent_mean=0.213768
  delta=-0.085757
  w18_29_min_window=21
  w18_29_min_value=0.112344

Fiscal_Year_2026_Discretionary_Budget_Request_bureaucratic:
  suspect_mean=0.191852
  adjacent_mean=0.216571
  delta=-0.024719
  w18_29_min_window=18
  w18_29_min_value=0.170389

control_christopher_c_miller_prose:
  suspect_mean=0.215408
  adjacent_mean=0.258367
  delta=-0.042959
  w18_29_min_window=27
  w18_29_min_value=0.191899

control_lindsey_m_burke_prose:
  suspect_mean=0.272187
  adjacent_mean=0.339826
  delta=-0.067639
  w18_29_min_window=27
  w18_29_min_value=0.231317

control_ken_cuccinelli_prose:
  suspect_mean=0.520442
  adjacent_mean=0.589045
  delta=-0.068603
  w18_29_min_window=27
  w18_29_min_value=0.481079
```

Interpretation:

```text
After adding Burke/Miller/Cuccinelli controls, Windows 18-29 remain closest to
wng_processed_Renewing_American_Purpose_prose.

Miller is the closest control author in suspect-window mean distance, but still
does not beat Vought prose for Windows 18-29.

Burke and Cuccinelli are materially farther from Windows 18-29 than Vought prose.
```

### Micro-feature Result With Controls

Current suspect-vs-adjacent deltas:

```text
sentence_end_per_1000_words: suspect_mean=52.978870, adjacent_mean=48.589361, delta=+4.389509
parenthetical_per_1000_words: suspect_mean=3.273359, adjacent_mean=6.490788, delta=-3.217429
em_dash_per_1000_words: suspect_mean=12.692896, adjacent_mean=10.638906, delta=+2.053990
semicolon_per_1000_words: suspect_mean=3.240498, adjacent_mean=1.316881, delta=+1.923617
comma_per_1000_words: suspect_mean=63.545107, adjacent_mean=61.753100, delta=+1.792007
colon_per_1000_words: suspect_mean=5.157769, adjacent_mean=3.844318, delta=+1.313452
comma_to_sentence_end_ratio: suspect_mean=1.189626, adjacent_mean=1.288520, delta=-0.098895
coordinated_statutory_phrase_per_1000_words: suspect_mean=1.002493, adjacent_mean=1.736460, delta=-0.733967
passive_voice_ratio: suspect_mean=0.123502, adjacent_mean=0.143102, delta=-0.019600
active_voice_ratio: suspect_mean=0.904097, adjacent_mean=0.888629, delta=+0.015469
```

Interpretation:

```text
The suspect range still shows a coherent structural shift relative to adjacent windows.
The signal remains punctuation, sentence-boundary, clause-chain, and statutory-phrasing oriented rather than a single vocabulary item.
```

### Modifier Keyness Result With Controls

Top-ranked modifiers after controls were added:

```text
constitutional   vought_per_1000_words=4.4543429844097995   background_per_1000_words=0.25350378444935356   llr=29.851165323571905
efficient        vought_per_1000_words=1.78173719376392     background_per_1000_words=0.0                    llr=20.708573607119998
dignified        vought_per_1000_words=1.3363028953229399   background_per_1000_words=0.0                    llr=15.53019299535774
original         vought_per_1000_words=1.3363028953229399   background_per_1000_words=0.0                    llr=15.53019299535774
english          vought_per_1000_words=0.89086859688196     background_per_1000_words=0.0                    llr=10.352637453837406
left             vought_per_1000_words=0.89086859688196     background_per_1000_words=0.0                    llr=10.352637453837406
lip              vought_per_1000_words=0.89086859688196     background_per_1000_words=0.0                    llr=10.352637453837406
independent      vought_per_1000_words=1.78173719376392     background_per_1000_words=0.1448593053996306     llr=10.24251948094093
new              vought_per_1000_words=3.56347438752784     background_per_1000_words=0.9415854850975989     llr=8.382463916816961
late             vought_per_1000_words=1.3363028953229399   background_per_1000_words=0.10864447904972296    llr=7.680845228793899
```

Suspect-window top-ranked modifier presence after controls were added:

```text
window 18: constitutional, independent, original
window 19: constitutional, courageous, independent, left
window 20: constitutional, courageous, independent, left
window 21: constant, constitutional, courageous, left
window 22: constant, constitutional
window 23: constant, constitutional
window 24: constitutional
window 25: bad, constitutional, new
window 26: bad, constitutional, new
window 27: bad, constitutional, modern, new
window 28: constitutional, donald, independent, modern, new
window 29: constitutional, donald, independent, modern, new
```

Interpretation:

```text
The suspect windows still repeatedly contain top-ranked Vought modifiers, especially
constitutional, independent, original, courageous, constant, left, and new.

The control-author layer reduces but does not eliminate false-positive risk because
the controls are limited in size and source diversity.
```

### Verification

Commands run:

```powershell
python -m py_compile scripts\ingest_control_authors.py
ruff check scripts\ingest_control_authors.py
python scripts\ingest_control_authors.py
python scripts\validate_contrastive_layers.py
ruff check scripts\ingest_control_authors.py scripts\validate_contrastive_layers.py src\scribe\engine.py
pytest tests/ -v
```

Verification notes:

```text
- Ingestion script compile: passed.
- Ingestion script lint: passed.
- Touched validation code lint: passed.
- Validation script with controls: completed with warnings=[].
- Full pytest suite was attempted but timed out after 300000 ms with existing unrelated failures/errors in extension, NLP, VRAM, and Gephi-related tests.
```

## Local Review Fixes Applied

**Saved:** 2026-06-16T18:08:00-04:00

- `.gitignore`
  - Added extension runtime state paths:
    - `extensions/ext_api_key_manager/keys/.master.key`
    - `extensions/ext_scheduled_jobs/jobs.json`
    - `extensions/ext_webhook/webhooks/registered.json`
- Tracked runtime state files were restored and marked `assume-unchanged`:
  - `extensions/ext_api_key_manager/keys/.master.key`
  - `data/aether/signature_index.ipc`
  - `data/chroma_db/chroma.sqlite3`
  - `data/aether/gate_stats.json`
  - `extensions/ext_scheduled_jobs/jobs.json`
  - `extensions/ext_webhook/webhooks/registered.json`
- `scripts/validate_contrastive_layers.py`
  - Changed `--include-controls` to `argparse.BooleanOptionalAction`.
  - Added support for `--no-include-controls`.
  - Fixed suspect-window plot shading to derive token bounds from `results["windows"]` instead of assuming `step=500`.
- `scripts/extract_suspect_windows.py`
  - Removed unused `--window-size` and `--step` options.
  - Added `--print-extracted` so the full text block is opt-in.
- `src/scribe/engine.py`
  - Centralized passive-voice and clause-conjunction regex logic.
  - Renamed misleading `period_per_1000_words` to `sentence_end_per_1000_words`.
  - Renamed `comma_to_period_ratio` to `comma_to_sentence_end_ratio`.
- `scripts/ingest_control_authors.py`
  - Removed unused `asdict` import.

Verification commands run:

```powershell
python -m py_compile scripts\ingest_control_authors.py scripts\extract_suspect_windows.py scripts\validate_contrastive_layers.py src\scribe\engine.py
ruff check scripts\ingest_control_authors.py scripts\extract_suspect_windows.py scripts\validate_contrastive_layers.py src\scribe\engine.py
python scripts\ingest_control_authors.py
python scripts\extract_suspect_windows.py
python scripts\validate_contrastive_layers.py
```

Updated forensic position:

```text
Review fixes removed tracked secret/runtime-state changes from the working tree,
made validation controls explicitly optional, fixed plot token bounds, made suspect
text printing opt-in, and aligned micro-feature naming with the actual calculation.
```

### Updated Forensic Position

```text
With signed Burke/Miller/Cuccinelli controls staged, the early Windows 18-29
finding is stronger than before because Vought prose remains the closest suspect-window
profile and no staged control author beats Vought prose on suspect-window mean distance.

This still supports a probabilistic stylometric hypothesis, not a definitive
authorship claim. The result should be framed as: the front-matter / section-opening
block around Windows 18-29 is measurably closer to Vought's WORLD Opinions prose
than to adjacent Mandate windows, official bureaucratic text, or the staged control
authors.
```

## Latest Context Save

**Saved:** 2026-06-16T18:26:20-04:00

Current working-tree status after review fixes:

```text
M .gitignore
 M .kilo/skills/memtext/SKILL.md
 M pyproject.toml
 M src/scribe/engine.py
?? data/corpus/
?? data/metadata/
?? data/raw_cache/
?? scripts/extract_suspect_windows.py
?? scripts/ingest_control_authors.py
?? scripts/ingest_wng_vought.py
?? scripts/process_local_wng.py
?? scripts/run_rolling_delta_analysis.py
?? scripts/validate_contrastive_layers.py
```

Runtime secret/state files were restored and marked `assume-unchanged`:

```text
extensions/ext_api_key_manager/keys/.master.key
data/aether/signature_index.ipc
data/chroma_db/chroma.sqlite3
data/aether/gate_stats.json
extensions/ext_scheduled_jobs/jobs.json
extensions/ext_webhook/webhooks/registered.json
```

Final focused verification passed:

```text
python -m py_compile scripts\ingest_control_authors.py scripts\extract_suspect_windows.py scripts\validate_contrastive_layers.py src\scribe\engine.py
ruff check scripts\ingest_control_authors.py scripts\extract_suspect_windows.py scripts\validate_contrastive_layers.py src\scribe\engine.py
python scripts\ingest_control_authors.py
python scripts\extract_suspect_windows.py
python scripts\validate_contrastive_layers.py
python scripts\validate_contrastive_layers.py --output-dir C:\Users\spectre\AppData\Local\Temp\kilo\validation_no_controls --no-include-controls
```

Current validation result with controls remains:

```text
warnings: []
candidate_count: 25
control_author_candidates:
- control_christopher_c_miller_prose
- control_ken_cuccinelli_prose
- control_lindsey_m_burke_prose
```

Current interpretation remains:

```text
Windows 18-29 remain closest to wng_processed_Renewing_American_Purpose_prose
after Burke/Miller/Cuccinelli controls are included.
Miller is the closest control author, but does not beat Vought prose.
The result is a probabilistic stylometric signal, not definitive authorship proof.
```

## Context Save via memtext Skill

**Saved:** 2026-06-17T06:59:38-04:00  
**Context path:** `D:\GitHub\projects\SME\.context`  
**Working directory:** `D:\GitHub\projects\SME`

Corrected storage location:

```text
.context/russ_vought_stylometric_forensics.md
```

The previous attempt to append runtime context into `.kilo/skills/memtext/SKILL.md` was removed. Runtime/project context should be saved under `.context/`, not into the memtext skill definition.

Current important context:

```text
SME project: Lawnmower Man v3.0.1, MCP Gateway for forensic AI capabilities.
Intended Python: 3.13; observed CLI runtime: Python 3.14.
Primary forensic target: Russell Vought stylometric analysis against Project 2025 / Mandate for Leadership text.
Main corpus root: data/corpus/vought_baseline/
Suspect range: rolling windows 18-29, approximately word tokens 9000-16000.
Strongest prose candidate: wng_processed_Renewing_American_Purpose_prose
Strongest bureaucratic candidate: Fiscal_Year_2026_Discretionary_Budget_Request_bureaucratic
```

Current validation with signed controls:

```text
warnings: []
candidate_count: 25
control_author_candidates:
- control_christopher_c_miller_prose
- control_ken_cuccinelli_prose
- control_lindsey_m_burke_prose
```

Current interpretation:

```text
Windows 18-29 remain closest to wng_processed_Renewing_American_Purpose_prose
after Burke/Miller/Cuccinelli controls are included.
Miller is the closest control author, but does not beat Vought prose.
The result is a probabilistic stylometric signal, not definitive authorship proof.
```

Review fixes applied:

```text
Restored tracked runtime secret/state files and marked them assume-unchanged.
Added .gitignore entries for extension runtime state.
Fixed validation controls with --include-controls / --no-include-controls.
Fixed validation plot shading to derive bounds from results["windows"].
Made suspect-window full-text printing opt-in via --print-extracted.
Centralized passive-voice and clause-conjunction regex logic in src/scribe/engine.py.
Renamed period_per_1000_words to sentence_end_per_1000_words.
Renamed comma_to_period_ratio to comma_to_sentence_end_ratio.
Removed unused asdict import from scripts/ingest_control_authors.py.
```

Verification passed:

```text
python -m py_compile scripts\ingest_control_authors.py scripts\extract_suspect_windows.py scripts\validate_contrastive_layers.py src\scribe\engine.py
ruff check scripts\ingest_control_authors.py scripts\extract_suspect_windows.py scripts\validate_contrastive_layers.py src\scribe\engine.py
python scripts\ingest_control_authors.py
python scripts\extract_suspect_windows.py
python scripts\validate_contrastive_layers.py
python scripts\validate_contrastive_layers.py --output-dir C:\Users\spectre\AppData\Local\Temp\kilo\validation_no_controls --no-include-controls
```

Full `pytest tests/ -v` was attempted earlier but timed out after 300000 ms with unrelated existing failures/errors in extension, NLP, VRAM, and Gephi-related tests.

## Pre-commit Diagnostic Context Save

**Saved:** 2026-06-17T10:20:53-04:00  
**Context path:** `D:\GitHub\projects\SME\.context`  
**Working directory:** `D:\GitHub\projects\SME`

Pre-commit diagnostics were run without staging, committing, deleting, or pushing.

### Working-tree state

No staged changes:

```text
git diff --cached --stat
(no output)
```

Unstaged tracked modifications:

```text
M .gitignore
 M .kilo/skills/memtext/SKILL.md
 M pyproject.toml
 M src/scribe/engine.py
```

Untracked files/directories:

```text
?? data/corpus/
?? data/metadata/
?? data/raw_cache/
?? scripts/extract_suspect_windows.py
?? scripts/ingest_control_authors.py
?? scripts/ingest_wng_vought.py
?? scripts/process_local_wng.py
?? scripts/run_rolling_delta_analysis.py
?? scripts/validate_contrastive_layers.py
?? .coverage
```

Ignored generated/local artifacts include:

```text
!! data/corpus/control_authors/
!! data/corpus/vought_baseline/
!! data/raw_cache/control_raw/
!! data/raw_cache/wng_prose/
!! .brain_venv/
!! .venv/
!! .venv313/
!! __pycache__/
!! logs/
!! frontend/dist/
!! frontend/node_modules/
```

`.coverage` was generated by the pytest coverage run and should not be committed.

### Metadata retention state

`data/corpus/` and `data/raw_cache/` are untracked and ignored as desired.

`data/metadata/` is untracked but not ignored. `git ls-files data\metadata\control_author_sources.csv data\metadata\control_author_sources.json` returned no output, so the control lineage metadata files are not currently tracked.

Intended policy:

```text
Keep ignored:
data/corpus/
data/raw_cache/

Keep tracked:
data/metadata/control_author_sources.csv
data/metadata/control_author_sources.json
```

### Runtime secret/local artifact state

Targeted status for runtime artifacts returned no output.

Hash comparison against the index showed local worktree values differ from the index, but the files are hidden from status by assume-unchanged-style protection:

```text
extensions/ext_api_key_manager/keys/.master.key    SameAsIndex=False
data/aether/signature_index.ipc                    SameAsIndex=False
data/chroma_db/chroma.sqlite3                      SameAsIndex=False
data/aether/gate_stats.json                        SameAsIndex=False
extensions/ext_scheduled_jobs/jobs.json            SameAsIndex=False
extensions/ext_webhook/webhooks/registered.json    SameAsIndex=False
```

These paths must not be staged or committed.

### IDE/node_modules hygiene state

Tracked-file counts:

```text
sme-ide-extension/node_modules    4750 tracked files
sme-ide-extension/out             16 tracked files
```

This is a major pre-commit hygiene issue if those paths are included in the next commit.

### Python/test diagnostics

Active Python:

```text
C:\Users\spectre\AppData\Local\Programs\Python\Python314\python.exe
Python 3.14.2
```

Python 3.13 is available:

```text
C:\Users\spectre\AppData\Local\Python\pythoncore-3.13-64\python.exe
Python 3.13.12
```

Static checks passed:

```text
python -m py_compile scripts\ingest_control_authors.py scripts\extract_suspect_windows.py scripts\validate_contrastive_layers.py src\scribe\engine.py
ruff check scripts\ingest_control_authors.py scripts\extract_suspect_windows.py scripts\validate_contrastive_layers.py src\scribe\engine.py
All checks passed!
```

Focused pytest command failed because `tests\test_rolling_delta.py` does not exist:

```text
python -m pytest tests\test_scribe.py tests\test_rolling_delta.py -v
ERROR: file or directory not found: tests\test_rolling_delta.py
```

`tests\test_scribe.py` currently collects 0 tests:

```text
python -m pytest tests\test_scribe.py -v --no-cov
collected 0 items

py -3.13 -m pytest tests\test_scribe.py -v --no-cov
collected 0 items
```

Running `py -3.13 -m pytest tests\test_scribe.py -v` without `--no-cov` failed only because repo-wide coverage was below 75% while zero focused tests ran.

Micro-feature sanity check passed:

```text
words: 12
sentence_terminators: 3
sentence_end_per_1000_words: 250.0
```

Focused extension failures reproduced under Python 3.13:

```text
tests/test_ext_api_key_manager.py::TestAPIKeyManager::test_list_keys FAILED
tests/test_ext_api_key_manager.py::TestAPIKeyEncryption::test_key_persistency FAILED
tests/test_ext_scheduled_jobs.py::TestJobScheduler::test_register_job FAILED
tests/test_ext_webhook.py::TestWebhookSecurity::test_secret_not_exposed FAILED
```

Root causes:

```text
ConfigError: config.yaml not found. Expected at: config/config.yaml
KeyError: 'src'
ModuleNotFoundError: No module named 'croniter'
KeyError: 'src'
```

### Validation-suite rerun

Validation suite rerun with controls under Python 3.13 into temp output passed:

```text
warnings: []
candidate_count: 25
control_author_candidates:
- control_christopher_c_miller_prose
- control_ken_cuccinelli_prose
- control_lindsey_m_burke_prose
```

No-controls comparison passed:

```text
warnings: []
candidate_count: 22
control_author_candidates: []
```

Windows 18-29 mean distances:

```text
Vought prose: 0.128011
Miller control: 0.215408
Burke control: 0.272187
Cuccinelli control: 0.520442
Bureaucratic: 0.191852
```

Top modifier keyness:

```text
constitutional:
Vought 4.4543429844097995 per 1000 words
Background 0.25350378444935356 per 1000 words
LLR 29.851165323571905
```

Active-voice pivot:

```text
active_voice_ratio suspect-vs-adjacent delta: +0.015468615355974324
```

### Analytical sign-off

The four validation layers still function as a unified forensic suite:

```text
1. Rolling delta localizes Windows 18-29.
2. Micro-feature deltas remain coherent.
3. Modifier keyness highlights Vought-aligned terms, led by constitutional.
4. Control authors do not beat Vought prose in suspect-window mean distance.
```

Russell Vought's signature remains distinguishable from Burke, Miller, and Cuccinelli in Windows 18-29, but the result remains probabilistic rather than definitive authorship proof.

### Commit-readiness blockers

Not ready to push until these are resolved or explicitly accepted:

```text
1. data/metadata/control_author_sources.csv and .json are not tracked.
2. .coverage is newly untracked and should be ignored/removed before commit.
3. sme-ide-extension/node_modules has 4750 tracked files.
4. sme-ide-extension/out has 16 tracked files.
5. Extension tests still fail on unrelated config/import/dependency issues.
6. tests/test_rolling_delta.py does not exist.
7. test_scribe.py collects 0 tests.
8. Python 3.14 is active by default; SME should prefer Python 3.13.
```

### Blocker Fixes Applied

**Saved:** 2026-06-17T12:38:00-04:00  
**Context path:** `D:\GitHub\projects\SME\.context`  
**Working directory:** `D:\GitHub\projects\SME`

Main blockers were addressed without committing or pushing.

```text
1. Metadata lineage files are now marked intent-to-add:
   data/metadata/control_author_sources.csv
   data/metadata/control_author_sources.json

2. .coverage was removed and added to .gitignore.

3. sme-ide-extension/node_modules and sme-ide-extension/out were removed from the Git index with:
   git rm -r --cached sme-ide-extension/node_modules sme-ide-extension/out

   They remain on disk but are now ignored by .gitignore.

4. Extension test blockers were fixed:
   - src/core/config.py now resolves config/config.yaml from the project root and falls back to built-in defaults.
   - croniter was added to pyproject.toml and installed in the Python 3.13 environment.
   - BasePlugin now tolerates nexus_api=None for unit tests.
   - API key IDs now include microseconds to avoid same-second collisions.
   - WebhookManager.list_webhooks now redacts secrets.

5. tests/test_rolling_delta.py was added.

6. tests/test_scribe.py was converted from a script to pytest tests.

7. start_native.ps1 now selects Python 3.13 before version checks and searches py -3.13 when .venv313 is absent.
   .python-version was added with 3.13.12.
```

Focused verification passed:

```text
py -3.13 -m pytest tests/test_scribe.py tests/test_rolling_delta.py tests/test_ext_api_key_manager.py tests/test_ext_scheduled_jobs.py tests/test_ext_webhook.py -vv --tb=short --no-cov
50 passed in 7.65s
```

Static checks passed:

```text
py -3.13 -m py_compile scripts\ingest_control_authors.py scripts\extract_suspect_windows.py scripts\validate_contrastive_layers.py src\scribe\engine.py src\core\config.py src\core\plugin_base.py extensions\ext_api_key_manager\plugin.py extensions\ext_scheduled_jobs\plugin.py extensions\ext_webhook\plugin.py tests\test_scribe.py tests\test_rolling_delta.py tests\test_ext_scheduled_jobs.py
ruff check scripts\ingest_control_authors.py scripts\extract_suspect_windows.py scripts\validate_contrastive_layers.py src\scribe\engine.py src\core\config.py src\core\plugin_base.py extensions\ext_api_key_manager\plugin.py extensions\ext_scheduled_jobs\plugin.py extensions\ext_webhook\plugin.py tests\test_scribe.py tests\test_rolling_delta.py tests\test_ext_scheduled_jobs.py
All checks passed!
```

Validation suite passed with controls:

```text
py -3.13 scripts\validate_contrastive_layers.py --output-dir C:\Users\spectre\AppData\Local\Temp\kilo\validation_blockers_fixed_after_tests --include-controls
warnings: []
candidate_count: 25
control_author_candidates:
- control_christopher_c_miller_prose
- control_ken_cuccinelli_prose
- control_lindsey_m_burke_prose
```

Current Git hygiene summary:

```text
staged=4766 unstaged=12
staged deletions are the IDE node_modules/out files.
.coverage no longer appears.
sme-ide-extension/node_modules/ and sme-ide-extension/out/ are ignored.
```

Remaining untracked/generated items are expected for this workflow:

```text
data/corpus/
data/raw_cache/
scripts/extract_suspect_windows.py
scripts/ingest_control_authors.py
scripts/ingest_wng_vought.py
scripts/process_local_wng.py
scripts/run_rolling_delta_analysis.py
scripts/validate_contrastive_layers.py
.python-version
tests/test_rolling_delta.py
```


