"""
SonarSentinel — Step 6: Geotagging Engine Tests
================================================
Tests WGS84 geodesic projections and simulated navigation sidecars.
Verifies that:
  - If a vessel is heading East (90 degrees), a starboard target (to the right of nadir)
    projects South (latitude decreases, longitude stays close to vessel).
  - Telemetry sidecars match filename keywords correctly.
  - Trigonometric slant-to-ground range projections resolve to realistic numbers.
"""

import pytest
import math
from step6_geotagging.geotag import (
    generate_simulated_navigation_sidecar,
    project_pixel_to_wgs84,
    NavigationSidecar
)


def test_nav_sidecar_presets():
    """Verifies that filename keywords map to the correct presets."""
    nav_ghost = generate_simulated_navigation_sidecar("mission_ghostnet_chennai.png")
    assert nav_ghost.vessel_lat == 13.0827
    assert nav_ghost.vessel_lon == 80.2707
    assert nav_ghost.altitude == 18.0

    nav_wreck = generate_simulated_navigation_sidecar("palk_strait_wreckage.png")
    assert nav_wreck.vessel_lat == 9.2876
    assert nav_wreck.vessel_lon == 79.3129
    assert nav_wreck.heading == 135.0

    nav_default = generate_simulated_navigation_sidecar("unknown.png")
    assert nav_default.heading == 90.0
    assert nav_default.vessel_lat == 13.0827


def test_eastward_heading_starboard_projection():
    """
    If the vessel is heading East (90 degrees True), the starboard side
    is directly South of the vessel path.
    - Latitude should decrease (South displacement).
    - Longitude should remain very close to vessel longitude (zero East/West offset).
    """
    nav = NavigationSidecar(
        vessel_lat=13.0827,
        vessel_lon=80.2707,
        heading=90.0,         # Heading East
        altitude=15.0,
        swath_width_m=100.0,
        survey_speed_knots=4.0
    )

    # Image: 800 wide, 400 high. Nadir is at x=400.
    # We place a target on starboard at x=600 (center of x1=580, x2=620).
    # Since cy=200, along_track_m is 0.
    w, h = 800, 400
    x1, x2 = 580, 620
    y1, y2 = 180, 220

    geotag = project_pixel_to_wgs84(x1, y1, x2, y2, w, h, nav)

    # 1. Target is on starboard, so cross_track_m must be positive
    assert geotag.cross_track_m > 0
    # 2. Target is directly starboard of an East-heading vessel, which is South.
    # Therefore, target latitude must be less than vessel latitude
    assert geotag.latitude < nav.vessel_lat
    # 3. No along-track offset, so longitude should remain exactly equal to vessel
    assert geotag.longitude == pytest.approx(nav.vessel_lon, abs=1e-5)
    # 4. Slant range check: sqrt(cross_track^2 + altitude^2)
    # scale_x = 100m / 800px = 0.125m/px.
    # cx = 600. nadir = 400. offset = 200px.
    # cross_track_m = 200 * 0.125 = 25m.
    # slant_range = sqrt(25^2 + 15^2) = sqrt(625 + 225) = sqrt(850) = 29.15m.
    assert geotag.cross_track_m == 25.0
    assert geotag.slant_range_m == pytest.approx(29.15, abs=0.1)
    assert geotag.ground_range_m == 25.0
