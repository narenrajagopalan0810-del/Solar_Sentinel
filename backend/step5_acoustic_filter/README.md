# Step 5 — Acoustic Noise Filter

> **Build Order:** `SonarSentinel_Backend_Build_Order.txt` → Step 5  
> **Depends on:** Step 4 (POST `/detect` endpoint) and Step 3 (Preprocessing)

---

## What this step delivers

> *"In noise_filter.py, implement the highlight-to-shadow check: for each  
> detection, inspect the region trailing the bounding box in the sonar's look  
> direction for a dark shadow. No shadow -> downgrade confidence sharply.  
> Wire this into the /detect endpoint so it runs on every detection before  
> the response is returned."*

---

## Files in this folder

| File | Purpose |
|---|---|
| `noise_filter.py` | Shadow propagation checker, contrast calculator, and confidence downgrader |
| `test_noise_filter.py` | 4 unit tests covering port, starboard, no-shadow downgrade, and shadow retention |
| `README.md` | This file |

---

## Physical Logic: How Highlight-to-Shadow Check Works

Unlike optical cameras, Side-Scan Sonar (SSS) emits acoustic pressure waves at slant angles. Elevational obstacles cast an **acoustic shadow** (occlusion zone of near-zero energy) directly behind them along the propagation ray.

1. **Acoustic Nadir & Directionality Check**:
   * Nadir (vessel path line) splits the swath at the center (`image_width / 2`).
   * **Starboard Channel** (object center to the right of nadir): casts shadow to the right (+X).
   * **Port Channel** (object center to the left of nadir): casts shadow to the left (-X).
   * **Forward-Looking Sonar (FLS)**: casts shadow forward (top to bottom, +Y).

2. **Shadow ROI Extraction**:
   * Evaluates the trailing area (default `80px` length) along the look direction.
   * Compares the mean intensity of the shadow zone (`shadow_mean`) to the surrounding seafloor (`bg_mean`).

3. **Decision Criteria**:
   * A shadow is confirmed if:
     1. The shadow zone is significantly darker than the background: `shadow_mean < bg_mean * 0.85`.
     2. **OR** high contrast coupled with relative darkness: `(highlight_mean / shadow_mean) >= 1.25` AND `shadow_mean < bg_mean * 0.95`.
   * If neither condition is met, `shadow_detected` is marked `False` and a **confidence penalty factor (`0.30`)** is applied to filter out false-positives (speckle noise, ridges, anomalies without height).

---

## How to run unit tests

From the `backend/` directory with the virtual environment active:
```powershell
pytest step5_acoustic_filter/test_noise_filter.py -v
```

Expected output:
```
PASSED test_starboard_valid_shadow
PASSED test_port_valid_shadow
PASSED test_no_shadow_downgrade
PASSED test_with_shadow_retains_confidence
```
