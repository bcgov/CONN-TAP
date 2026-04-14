# spend_tracking.xlsx — Build Script

## Overview

`build_spend_sheet.py` generates `spend_tracking.xlsx` using the
[xlsxwriter](https://xlsxwriter.readthedocs.io/) library.  
It recreates the structure, formulas, colours, row groupings, and freeze panes
of the original **empty spend sheet.xlsx**, then leaves the data cells blank so
that values can be entered (or injected programmatically) separately.

```
python3 scripts/build_spend_sheet.py
# → scripts/spend_tracking.xlsx
```

Requires Python 3.9+ and `xlsxwriter`:

```
pip install xlsxwriter
```

---

## Column layout

| Columns | Description |
|---------|-------------|
| **A** | BGE entity name (Gov BC, BCLC, …) |
| **B** | Row label (Cellular, Data, Voice, etc.) |
| **C – N** | Monthly values — Jan 2024 → Dec 2024 |
| **O – Z** | Monthly values — Jan 2025 → Dec 2025 |
| **AA – AL** | Monthly values — Jan 2026 → Dec 2026 |
| **AM** | Visible group label (Gov & ECC, Health, …) |
| **AN – AS** | Hidden summary columns (annual totals, quarterly sums) |

**Data entry columns are C through AL (36 months).**  
Columns AM onward contain formulas and should not be edited.

---

## Sections and data expectations

The workbook is divided into six sections.  Each section is described below
with the exact rows that need to be filled in and the format expected.

---

### 1. TSMA  (rows 12 – 85)

**Owner:** TSMA contributor  
**Background colour:** light steel-blue

The TSMA section contains one block of rows per BGE entity.  
Each block has the following sub-rows (all within the same entity):

| Sub-row label | Meaning | Notes |
|---------------|---------|-------|
| Cellular | Cellular spend | Enter monthly $ |
| Data | Data spend | Enter monthly $ |
| Voice | Voice spend | Enter monthly $ |
| Voice - IVR | IVR-specific voice (Gov BC only) | Enter monthly $ |
| MMS | MMS spend | **FHA, PHSA, VCHA only** (see §6) |
| Out of Scope | Out-of-scope spend | Enter monthly $ |
| **Total** | Auto-calculated | **Do not edit** — formula sums rows above |

**Row map by BGE** (Excel rows, data columns C:AL):

| BGE | First row | Sub-rows | Last row (Total) |
|-----|-----------|----------|-----------------|
| Gov BC | 12 | Cellular, Data, Voice, Voice-IVR, Out of Scope, Total | 17 |
| BCLC | 18 | Cellular, Data, Voice, Out of Scope, Total | 22 |
| BC Hydro | 23 | Cellular, Data, Voice, Out of Scope, Total | 27 |
| WSBC | 28 | Cellular, Data, Voice, Out of Scope, Total | 32 |
| ECC | 33 | Cellular, Data, Voice, Out of Scope, Total | 37 |
| FHA | 38 | Cellular, **MMS**, Data, Voice, Out of Scope, Total | 43 |
| NHA | 44 | Cellular, Data, Voice, Out of Scope, Total | 48 |
| ICBC | 49 | Cellular, Data, Voice, Out of Scope, Total | 53 |
| PHSA | 54 | Cellular, **MMS**, Data, Voice, Out of Scope (MWLAN), Total | 59 |
| IHA | 60 | Cellular, Data, Voice, Out of Scope, Total | 64 |
| VIHA | 65 | Cellular, Data, Voice, Out of Scope, Total | 69 |
| FNHA | 70 | Cellular, Data, Voice, Out of Scope, Total | 74 |
| VCHA (+PHC) | 75 | Cellular, **MMS**, Data, Voice, Out of Scope (MWLAN), Total | 80 |
| School Districts | 81 | Cellular, Data, Voice, Out of Scope, Total | 85 |

Rows 5–9 (Cellular / Data / Voice / Out of Scope / Total) and row 10 (MMS) are
**summary rows** — they reference the aggregate rows 86–90 via formulas and
should **not** be edited.

---

### 2. TELUS NGTA  (rows 118 – 201)

**Owner:** TELUS NGTA contributor  
**Background colour:** light lavender

Each BGE has exactly **6 sub-rows**:

| Sub-row | Meaning | Notes |
|---------|---------|-------|
| Cellular Plans | Plan charges | Enter monthly $ |
| Cellular H/W | Hardware charges | Enter monthly $ |
| Data | Data charges | Enter monthly $ |
| Voice | Voice charges | Enter monthly $ |
| Other | Other charges | Enter monthly $ |
| **Total** | Auto-calculated | **Do not edit** |

**Row map by BGE** (each block is 6 rows, data columns C:AL):

| BGE | Cel Plans | Cel H/W | Data | Voice | Other | Total |
|-----|-----------|---------|------|-------|-------|-------|
| Gov BC | 118 | 119 | 120 | 121 | 122 | 123 |
| BCLC | 124 | 125 | 126 | 127 | 128 | 129 |
| BC Hydro | 130 | 131 | 132 | 133 | 134 | 135 |
| WSBC | 136 | 137 | 138 | 139 | 140 | 141 |
| ECC | 142 | 143 | 144 | 145 | 146 | 147 |
| FHA | 148 | 149 | 150 | 151 | 152 | 153 |
| NHA | 154 | 155 | 156 | 157 | 158 | 159 |
| ICBC | 160 | 161 | 162 | 163 | 164 | 165 |
| PHSA | 166 | 167 | 168 | 169 | 170 | 171 |
| IHA | 172 | 173 | 174 | 175 | 176 | 177 |
| VIHA | 178 | 179 | 180 | 181 | 182 | 183 |
| FNHA | 184 | 185 | 186 | 187 | 188 | 189 |
| VCHA (+PHC) | 190 | 191 | 192 | 193 | 194 | 195 |
| School Districts | 196 | 197 | 198 | 199 | 200 | 201 |

Rows 110–116 are **summary rows** — do not edit.  
Rows 202–206 are **aggregate totals** — do not edit.

---

### 3. Rogers NGTA  (rows 240 – 323)

**Owner:** Rogers NGTA contributor  
**Background colour:** light peach

Identical structure to TELUS NGTA (6 sub-rows per BGE).

**Row map by BGE** (each block is 6 rows, data columns C:AL):

| BGE | Cel Plans | Cel H/W | Data | Voice | Other | Total |
|-----|-----------|---------|------|-------|-------|-------|
| Gov BC | 240 | 241 | 242 | 243 | 244 | 245 |
| BCLC | 246 | 247 | 248 | 249 | 250 | 251 |
| BC Hydro | 252 | 253 | 254 | 255 | 256 | 257 |
| WSBC | 258 | 259 | 260 | 261 | 262 | 263 |
| ECC | 264 | 265 | 266 | 267 | 268 | 269 |
| FHA | 270 | 271 | 272 | 273 | 274 | 275 |
| NHA | 276 | 277 | 278 | 279 | 280 | 281 |
| ICBC | 282 | 283 | 284 | 285 | 286 | 287 |
| PHSA | 288 | 289 | 290 | 291 | 292 | 293 |
| IHA | 294 | 295 | 296 | 297 | 298 | 299 |
| VIHA | 300 | 301 | 302 | 303 | 304 | 305 |
| FNHA | 306 | 307 | 308 | 309 | 310 | 311 |
| VCHA (+PHC) | 312 | 313 | 314 | 315 | 316 | 317 |
| School Districts | 318 | 319 | 320 | 321 | 322 | 323 |

Rows 232–238 are **summary rows** — do not edit.  
Rows 324–328 are **aggregate totals** — do not edit.

---

### 4. Out of Scope  (rows 357 – 383)

**Owner:** Out of Scope contributor  
**Background colour:** white (no fill)

Three sub-categories, each with a set of organisation-level detail rows
followed by a **Total** row (auto-calculated — do not edit).

#### Managed Router  (rows 357 – 363, Total at 364)

| Row | Organisation |
|-----|-------------|
| 357 | CHILDRENS & WOMENS HEALTH CENTRE OF BC SOCIETY |
| 358 | FIRST NATIONS HEALTH AUTHORITY |
| 359 | GBC - MINISTRY OF CITIZENS SERVICES |
| 360 | GBC - SHARED SERVICES BC |
| 361 | GBC - MINISTRY OF EDUCATION & CHILD CARE |
| 362 | BRITISH COLUMBIA LIQUOR DISTRIBUTION BRANCH |
| 363 | GBC - LIQUOR DISTRIBUTION BRANCH |

#### Managed WLAN / Managed Wi-Fi  (rows 366 – 371, Total at 372)

| Row | Organisation |
|-----|-------------|
| 366 | VANCOUVER COASTAL HEALTH AUTHORITY O/A OLIVE DEVAUD RESIDENCE |
| 367 | VANCOUVER COASTAL HEALTH AUTHORITY O/A LIONS GATE HOSPITAL |
| 368 | VANCOUVER COASTAL HEALTH AUTHORITY HOWE SOUND HOME SUPPORT SERVICES |
| 369 | VANCOUVER COASTAL HEALTH AUTHORITY |
| 370 | PROVINCIAL HEALTH SERVICES AUTHORITY |
| 371 | GREATER VANCOUVER MENTAL HEALTH SERVICE |

#### Managed Security / Managed Firewall  (rows 374 – 383, Total at 384)

| Row | Organisation |
|-----|-------------|
| 374 | BRITISH COLUMBIA HYDRO & POWER AUTHORITY |
| 375 | WORKERS COMPENSATION BOARD OF BRITISH COLUMBIA |
| 376 | INSURANCE CORPORATION OF BRITISH COLUMBIA - ICBC |
| 377 | FRASER HEALTH AUTHORITY |
| 378 | GBC - MINISTRY OF EDUCATION & CHILD CARE |
| 379 | PROVINCIAL HEALTH SERVICES AUTHORITY |
| 380 | GBC - MINISTRY OF CITIZENS SERVICES |
| 381 | FIRST NATIONS HEALTH AUTHORITY |
| 382 | GBC - OFFICE OF THE CHIEF INFORMATION OFFICER |
| 383 | GBC - MINISTRY OF HEALTH |

All data cells are columns **C:AL** (monthly, Jan 2024 – Dec 2026).

---

### 5. TSMA Lite  (rows 387 – 394)

**Owner:** TSMA Lite contributor  
**Background colour:** white (no fill)

TSMA Lite uses **quarterly** data only.  Enter values in the quarter-end
columns listed below — leave all other month columns empty.

| Quarter-end column | Period |
|--------------------|--------|
| E (col 4) | Q1 2024 (Mar 2024) |
| H (col 7) | Q2 2024 (Jun 2024) |
| K (col 10) | Q3 2024 (Sep 2024) |
| N (col 13) | Q4 2024 (Dec 2024) |
| Q (col 16) | Q1 2025 (Mar 2025) |
| T (col 19) | Q2 2025 (Jun 2025) |
| W (col 22) | Q3 2025 (Sep 2025) |
| Z (col 25) | Q4 2025 (Dec 2025) |
| AC (col 28) | Q1 2026 (Mar 2026) |
| AF (col 31) | Q2 2026 (Jun 2026) |
| AI (col 34) | Q3 2026 (Sep 2026) |
| AL (col 37) | Q4 2026 (Dec 2026) |

**Input rows:**

| Row | Label |
|-----|-------|
| 387 | Voice - Total Charges |
| 388 | Data - Total Charges |
| 389 | \*Other Charges & Credits |
| 390 | Cellular User Equipment Cost |

Rows 391 (Total), 393 (Voice + Data + Other), and 394 (Cellular UE reference)
are **formula rows** — do not edit.

---

### 6. MMS  (within TSMA rows)

**Owner:** MMS contributor (or same as TSMA)

MMS rows are embedded inside the TSMA BGE blocks. Only three BGEs have an MMS
sub-row:

| BGE | MMS row |
|-----|---------|
| FHA | **39** |
| PHSA | **55** |
| VCHA (+PHC) | **76** |

Enter monthly values in columns **C:AL**.  
Row 10 (TSMA summary "MMS") and row 87 ("TOTAL MMS") are formula rows —
do not edit.

---

## Formula rows — do not edit

The following rows are fully formula-driven and must not be overwritten:

| Row(s) | Content |
|--------|---------|
| 1–10 | Year/quarter headers and TSMA summary |
| Every "Total" sub-row within each BGE | `=SUM(first_row:last_row-1)` per month |
| 86–90 | TSMA aggregate totals (TOTAL Cellular / MMS / Data / Voice / OoS) |
| 91 | TSMA + NGTAs combined row |
| 92–108 | Hidden TSMA sub-aggregates (Gov & ECC, Health, Crown Corps, School Districts) |
| 110–117 | TELUS NGTA headers and summary |
| 202–206 | TELUS NGTA aggregate totals |
| 207–231 | Hidden TELUS sub-aggregates |
| 232–239 | Rogers NGTA headers and summary |
| 324–328 | Rogers NGTA aggregate totals |
| 329–354 | Hidden Rogers sub-aggregates |
| 364, 372, 384 | Out of Scope category totals |
| 391, 393, 394 | TSMA Lite totals/references |

---

---

## Filling TELUS NGTA data from a CSV

The TELUS NGTA section can be populated automatically from a CSV file.  
Place the file at:

```
source/telus_ngta_spend.csv   (project root)
```

> `source/` is in `.gitignore` — files there are never committed.

### CSV format

| Column | Type | Notes |
|--------|------|-------|
| `provider` | string | Always `TELUS` — not used, present for consistency |
| `entity_key` | string | BGE identifier (see mapping below) |
| `month_start` | date | Any of `YYYY-MM-DD`, `YYYY-MM`, `YYYY/MM/DD`, `MM/DD/YYYY` |
| `cellular_plans` | number | Fills the Cellular Plans sub-row |
| `cellular_hardware` | number | Fills the Cellular H/W sub-row |
| `data_spend` | number | Fills the Data sub-row |
| `voice_spend` | number | Fills the Voice sub-row |
| `other_spend` | number | Fills the Other sub-row |
| `total_reported` | number | **Ignored** — Total is calculated by Excel formulas |

Commas inside numeric values are stripped automatically (e.g. `1,234.56` is accepted).

### entity_key mapping

| CSV entity_key | BGE in spreadsheet |
|----------------|--------------------|
| `GBC` | Gov BC |
| `BCLC` | BCLC |
| `BCH` | BC Hydro |
| `WSBC` | WSBC |
| `ECC` | ECC |
| `MOE` | ECC (alternate key — rows are merged into ECC) |
| `FHA` | FHA |
| `NHA` | NHA |
| `ICBC` | ICBC |
| `PHSA` | PHSA |
| `IHA` | IHA |
| `VIHA` | VIHA |
| `VCHA` | VCHA (+PHC) |
| `FNHA` | FNHA |
| `SD` | School Districts |

Unknown `entity_key` values and dates outside 2024–2026 are silently skipped.  
If the CSV file is absent the script still runs and leaves the TELUS section blank.

### Example row

```csv
provider,entity_key,month_start,cellular_hardware,cellular_plans,data_spend,voice_spend,other_spend,total_reported
TELUS,GBC,2024-01-01,100.00,2500.00,300.00,150.00,50.00,3100.00
TELUS,MOE,2024-02-01,50.00,950.00,125.00,82.00,12.00,1219.00
```

---

## Regenerating the file

After any structural change to the script, regenerate:

```bash
python3 scripts/build_spend_sheet.py
```

The output always overwrites `scripts/spend_tracking.xlsx`.  Any values
previously typed directly into the file will be lost — treat the generated
file as a **template** and only persist data through whatever process populates
it (manual entry, a separate injection script, etc.).
