# Step 6 — Geotagging Engine

> **Build Order:** `SonarSentinel_Backend_Build_Order.txt` → Step 6  
> **Depends on:** Step 5 (Acoustic Noise Filter)

---

## What this step delivers

> *"In geotag.py, generate a simulated navigation sidecar (lat/lon/heading/  
> altitude per image), then implement the slant-range-to-ground-range  
> projection to convert each detection's pixel offset into a real WGS84  
> lat/long. Attach this to each detection object in the response."*

---

## Files in this folder

| File | Purpose |
|---|---|
| `geotag.py` | Geotagging mathematics (swath-to-meters projection + heading yaw rotation + WGS84 coordinates) and simulated telemetry generator |
| `test_geotag.py` | 2 unit tests covering sidecar presets and projection logic for an Eastward vessel heading |
| `README.md` | This file |

---

## Mathematical Logic: Slant-to-Ground Range Georeferencing

Given a vessel coordinate $(\phi_v, \lambda_v)$, COMPASS heading $\psi$, altitude $h$, swath width $W$ (meters), and image dimensions $W_{px} \times H_{px}$:

1. **Local Metric Offset Calculation**:
   * Nadir Line is at `image_width / 2.0`.
   * Scale factor: $S_x = \frac{W}{W_{px}}$ (meters per pixel).
   * Cross-track offset ($x_c$ from nadir): $\Delta x = (x_c - \text{nadir}) \cdot S_x$ (positive = starboard).
   * Along-track offset ($y_c$ from center): $\Delta y = -(y_c - \text{center}) \cdot S_x$.

2. **Acoustic Ranges**:
   * Slant Range: $R_s = \sqrt{\Delta x^2 + h^2}$.
   * Ground Range (Pythagorean seabed distance): $R_g = |\Delta x|$.

3. **Vessel Yaw Rotation Matrix**:
   * Transform along-track and cross-track offsets to local North/East frame:
     $$\Delta \text{North} = \Delta y \cos\psi - \Delta x \sin\psi$$
     $$\Delta \text{East} = \Delta y \sin\psi + \Delta x \cos\psi$$

4. **WGS84 Forward Geodesic Projection**:
   * Project metric offsets to global coordinate system (using Earth radius $R_E = 6,378,137\text{ m}$ and correcting longitudinal convergence at latitude $\phi_v$):
     $$\phi_{\text{target}} = \phi_v + \left(\frac{\Delta \text{North}}{R_E}\right) \times \frac{180}{\pi}$$
     $$\lambda_{\text{target}} = \lambda_v + \left(\frac{\Delta \text{East}}{R_E \cos\phi_v}\right) \times \frac{180}{\pi}$$

---

## Simulated Navigation Sidecar Presets

Keywords in the uploaded filename are detected to assign high-fidelity mock telemetry:
* `ghost` / `net` / `chennai` → Chennai Coast (`lat: 13.0827`, `lon: 80.2707`, `heading: 85.0`, `altitude: 18.0`)
* `wreck` / `boat` / `palk` → Palk Strait (`lat: 9.2876`, `lon: 79.3129`, `heading: 135.0`, `altitude: 14.0`)
* `pipe` / `mumbai` → Mumbai Offshore (`lat: 18.9220`, `lon: 72.8347`, `heading: 210.0`, `altitude: 22.0`)
* `cylinder` / `canister` / `vizag` → Vizag Port (`lat: 17.6868`, `lon: 83.2185`, `heading: 45.0`, `altitude: 16.0`)
* Default fallback → General survey line (`heading: 90.0`, `altitude: 15.0`)

---

## How to run unit tests

From the `backend/` directory with the virtual environment active:
```powershell
pytest step6_geotagging/test_geotag.py -v
```

Expected output:
```
PASSED test_nav_sidecar_presets
PASSED test_eastward_heading_starboard_projection
```
