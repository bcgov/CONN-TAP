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

### 2. TELUS NGTA  (rows 117 – 186)

**Owner:** TELUS NGTA contributor  
**Background colour:** light lavender

Each BGE has exactly **5 sub-rows**:

| Sub-row | Meaning | Notes |
|---------|---------|-------|
| Cellular Plans | Plan charges | Enter monthly $ |
| Cellular H/W | Hardware charges | Enter monthly $ |
| Data | Data charges | Enter monthly $ |
| Voice | Voice charges | Enter monthly $ |
| **Total** | Auto-calculated | **Do not edit** |

**Row map by BGE** (each block is 5 rows, data columns C:AL):

| BGE | Cellular Plans | Cellular H/W | Data | Voice | Total |
|-----|---------------|--------------|------|-------|-------|
| Gov BC | 117 | 118 | 119 | 120 | 121 |
| BCLC | 122 | 123 | 124 | 125 | 126 |
| BC Hydro | 127 | 128 | 129 | 130 | 131 |
| WSBC | 132 | 133 | 134 | 135 | 136 |
| ECC | 137 | 138 | 139 | 140 | 141 |
| FHA | 142 | 143 | 144 | 145 | 146 |
| NHA | 147 | 148 | 149 | 150 | 151 |
| ICBC | 152 | 153 | 154 | 155 | 156 |
| PHSA | 157 | 158 | 159 | 160 | 161 |
| IHA | 162 | 163 | 164 | 165 | 166 |
| VIHA | 167 | 168 | 169 | 170 | 171 |
| FNHA | 172 | 173 | 174 | 175 | 176 |
| VCHA (+PHC) | 177 | 178 | 179 | 180 | 181 |
| School Districts | 182 | 183 | 184 | 185 | 186 |

Rows 110–115 are **summary rows** — do not edit.  
Rows 187–190 are **aggregate totals** — do not edit.

---

### 3. Rogers NGTA  (rows 219 – 288)

**Owner:** Rogers NGTA contributor  
**Background colour:** light peach

Identical structure to TELUS NGTA (5 sub-rows per BGE).

**Row map by BGE** (each block is 5 rows, data columns C:AL):

| BGE | Cellular Plans | Cellular H/W | Data | Voice | Total |
|-----|---------------|--------------|------|-------|-------|
| Gov BC | 219 | 220 | 221 | 222 | 223 |
| BCLC | 224 | 225 | 226 | 227 | 228 |
| BC Hydro | 229 | 230 | 231 | 232 | 233 |
| WSBC | 234 | 235 | 236 | 237 | 238 |
| ECC | 239 | 240 | 241 | 242 | 243 |
| FHA | 244 | 245 | 246 | 247 | 248 |
| NHA | 249 | 250 | 251 | 252 | 253 |
| ICBC | 254 | 255 | 256 | 257 | 258 |
| PHSA | 259 | 260 | 261 | 262 | 263 |
| IHA | 264 | 265 | 266 | 267 | 268 |
| VIHA | 269 | 270 | 271 | 272 | 273 |
| FNHA | 274 | 275 | 276 | 277 | 278 |
| VCHA (+PHC) | 279 | 280 | 281 | 282 | 283 |
| School Districts | 284 | 285 | 286 | 287 | 288 |

Rows 212–217 are **summary rows** — do not edit.  
Rows 289–292 are **aggregate totals** — do not edit.

---

### 4. Out of Scope  (rows 317 – 343)

**Owner:** Out of Scope contributor  
**Background colour:** white (no fill)

Three sub-categories, each with a set of organisation-level detail rows
followed by a **Total** row (auto-calculated — do not edit).

#### Managed Router  (rows 317 – 323, Total at 324)

| Row | Organisation |
|-----|-------------|
| 317 | CHILDRENS & WOMENS HEALTH CENTRE OF BC SOCIETY |
| 318 | FIRST NATIONS HEALTH AUTHORITY |
| 319 | GBC - MINISTRY OF CITIZENS SERVICES |
| 320 | GBC - SHARED SERVICES BC |
| 321 | GBC - MINISTRY OF EDUCATION & CHILD CARE |
| 322 | BRITISH COLUMBIA LIQUOR DISTRIBUTION BRANCH |
| 323 | GBC - LIQUOR DISTRIBUTION BRANCH |

#### Managed WLAN / Managed Wi-Fi  (rows 326 – 331, Total at 332)

| Row | Organisation |
|-----|-------------|
| 326 | VANCOUVER COASTAL HEALTH AUTHORITY O/A OLIVE DEVAUD RESIDENCE |
| 327 | VANCOUVER COASTAL HEALTH AUTHORITY O/A LIONS GATE HOSPITAL |
| 328 | VANCOUVER COASTAL HEALTH AUTHORITY HOWE SOUND HOME SUPPORT SERVICES |
| 329 | VANCOUVER COASTAL HEALTH AUTHORITY |
| 330 | PROVINCIAL HEALTH SERVICES AUTHORITY |
| 331 | GREATER VANCOUVER MENTAL HEALTH SERVICE |

#### Managed Security / Managed Firewall  (rows 334 – 343, Total at 344)

| Row | Organisation |
|-----|-------------|
| 334 | BRITISH COLUMBIA HYDRO & POWER AUTHORITY |
| 335 | WORKERS COMPENSATION BOARD OF BRITISH COLUMBIA |
| 336 | INSURANCE CORPORATION OF BRITISH COLUMBIA - ICBC |
| 337 | FRASER HEALTH AUTHORITY |
| 338 | GBC - MINISTRY OF EDUCATION & CHILD CARE |
| 339 | PROVINCIAL HEALTH SERVICES AUTHORITY |
| 340 | GBC - MINISTRY OF CITIZENS SERVICES |
| 341 | FIRST NATIONS HEALTH AUTHORITY |
| 342 | GBC - OFFICE OF THE CHIEF INFORMATION OFFICER |
| 343 | GBC - MINISTRY OF HEALTH |

All data cells are columns **C:AL** (monthly, Jan 2024 – Dec 2026).

---

### 5. TSMA Lite  (rows 347 – 354)

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
| 347 | Voice - Total Charges |
| 348 | Data - Total Charges |
| 349 | \*Other Charges & Credits |
| 350 | Cellular User Equipment Cost |

Rows 351 (Total), 353 (Voice + Data + Other), and 354 (Cellular UE reference)
are **formula rows** — do not edit.

---

### 6. MMS  (within TSMA rows)

**Owner:** MMS contributor (or same as TSMA)

MMS rows are embedded inside the TSMA BGE blocks.  Only three BGEs have an MMS
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
| 110–116 | TELUS NGTA headers and summary |
| 187–190 | TELUS NGTA aggregate totals |
| 191–211 | Hidden TELUS sub-aggregates |
| 212–218 | Rogers NGTA headers and summary |
| 289–292 | Rogers NGTA aggregate totals |
| 293–313 | Hidden Rogers sub-aggregates |
| 324, 332, 344 | Out of Scope category totals |
| 351, 353, 354 | TSMA Lite totals/references |

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
