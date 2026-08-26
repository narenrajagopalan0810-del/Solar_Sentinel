"""
SonarSentinel — Step 6: Geotagging Engine (geotag.py)
=====================================================
Build Order Reference : SonarSentinel_Backend_Build_Order.txt  →  Step 6
Depends on           : Step 5 (Acoustic Noise Filter)

WHAT THIS FILE DOES
-------------------
1. Generates a simulated navigation sidecar (latitude, longitude, heading,
   and altitude) for any ingested sonar frame.
2. Implements WGS84 sonar swath georeferencing geometry:
   - Converts pixel offsets to metric nadir offsets.
   - Calculates slant range and Pythagorean ground range using altitude.
   - Rotates along-track/cross-track metric offsets using heading (yaw) matrix.
   - Projects offsets to WGS84 coordinates.
3. Attaches geotagging details to detections.
"""

import math
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("sonarsentinel.step6.geotag")

EARTH_RADIUS_METERS = 6378137.0  # WGS84 Equatorial Radius


class NavigationSidecar(BaseModel):
    """Simulated telemetry data associated with a sonar image."""
    vessel_lat: float = Field(..., description="Vessel latitude on WGS84 grid")
    vessel_lon: float = Field(..., description="Vessel longitude on WGS84 grid")
    heading: float = Field(..., description="Vessel True Heading in degrees [0-360]")
    altitude: float = Field(..., description="Towfish altitude above seabed in meters")
    swath_width_m: float = Field(..., description="Total sonar swath width in meters")
    survey_speed_knots: float = Field(default=4.0, description="Vessel speed in knots")
    mission_name: str = Field(default="MoES-Autonomous-Transect")


class GeotagDetails(BaseModel):
    """Detailed georeferencing metrics for a single detection."""
    latitude: float = Field(..., description="Calculated target latitude")
    longitude: float = Field(..., description="Calculated target longitude")
    cross_track_m: float = Field(..., description="Metric offset from vessel nadir (positive = starboard)")
    along_track_m: float = Field(..., description="Metric offset along vessel track (positive = forward)")
    slant_range_m: float = Field(..., description="Direct line-of-sight range in meters")
    ground_range_m: float = Field(..., description="Pythagorean seabed distance in meters")
    georef_method: str = Field(default="WGS84_Swath_Trigonometric_Projection")


def generate_simulated_navigation_sidecar(filename: Optional[str] = None) -> NavigationSidecar:
    """
    Simulates a navigation sidecar telemetry package.
    Matches filename keywords to realistic presets, or defaults to a plausible
    marine survey line if unrecognised.
    """
    fn_lower = (filename or "").lower()

    if "ghost" in fn_lower or "net" in fn_lower or "chennai" in fn_lower:
        return NavigationSidecar(
            vessel_lat=13.0827,
            vessel_lon=80.2707,
            heading=85.0,
            altitude=18.0,
            swath_width_m=100.0,
            survey_speed_knots=3.8,
            mission_name="MoES-Chennai-GhostNet-Audit"
        )
    elif "wreck" in fn_lower or "boat" in fn_lower or "palk" in fn_lower:
        return NavigationSidecar(
            vessel_lat=9.2876,
            vessel_lon=79.3129,
            heading=135.0,
            altitude=14.0,
            swath_width_m=120.0,
            survey_speed_knots=4.2,
            mission_name="PalkStrait-Debris-Audit"
        )
    elif "pipe" in fn_lower or "mumbai" in fn_lower:
        return NavigationSidecar(
            vessel_lat=18.9220,
            vessel_lon=72.8347,
            heading=210.0,
            altitude=22.0,
            swath_width_m=150.0,
            survey_speed_knots=4.0,
            mission_name="MumbaiHigh-Pipeline-Survey"
        )
    elif "cylinder" in fn_lower or "canister" in fn_lower or "vizag" in fn_lower:
        return NavigationSidecar(
            vessel_lat=17.6868,
            vessel_lon=83.2185,
            heading=45.0,
            altitude=16.0,
            swath_width_m=90.0,
            survey_speed_knots=3.5,
            mission_name="VizagPort-Security-Sweep"
        )

    # General fallback
    return NavigationSidecar(
        vessel_lat=13.0827,
        vessel_lon=80.2707,
        heading=90.0,
        altitude=15.0,
        swath_width_m=100.0,
        survey_speed_knots=4.0,
        mission_name="MoES-General-SSS-Survey"
    )


def project_pixel_to_wgs84(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    image_width: int,
    image_height: int,
    nav: NavigationSidecar
) -> GeotagDetails:
    """
    Performs slant-to-ground range georeferencing.

    Mathematical Projection:
      1. Target center in pixel coordinates: (cx, cy)
      2. Nadir line is at `image_width / 2.0`
      3. Metric scale = `swath_width_m / image_width`
      4. Cross-track offset from Nadir: `cross_track_m = (cx - nadir_px) * scale_x`
      5. Along-track offset from Center: `along_track_m = -(cy - center_py) * scale_y`
      6. Direct Slant Range: `slant_range_m = sqrt(cross_track_m^2 + altitude^2)`
      7. Ground Range: `ground_range_m = abs(cross_track_m)`
      8. True North/East offsets (rotational transformation using heading yaw ψ):
           - delta_north = along_track * cos(ψ) - cross_track * sin(ψ)
           - delta_east  = along_track * sin(ψ) + cross_track * cos(ψ)
      9. WGS84 Spherical Forward Geodesic:
           - lat = lat_v + (delta_north / R) * (180 / π)
           - lon = lon_v + (delta_east / (R * cos(lat_v))) * (180 / π)
    """
    # 1. Target center in pixel space
    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0

    nadir_px = image_width / 2.0
    along_mid_px = image_height / 2.0

    # Scale factors
    swath_m = nav.swath_width_m if nav.swath_width_m > 0 else 100.0
    scale_x = swath_m / max(image_width, 1)
    scale_y = scale_x  # Isometric assumption

    # 2. Metric offsets from towfish
    cross_track_m = (cx - nadir_px) * scale_x
    along_track_m = -(cy - along_mid_px) * scale_y

    # 3. Slant range vs Ground range
    altitude = max(nav.altitude, 1.0)
    slant_range_m = math.sqrt(cross_track_m**2 + altitude**2)
    ground_range_m = abs(cross_track_m)

    # 4. Rotation Matrix (heading True North adjustment)
    heading_rad = math.radians(nav.heading % 360.0)
    delta_north = along_track_m * math.cos(heading_rad) - cross_track_m * math.sin(heading_rad)
    delta_east  = along_track_m * math.sin(heading_rad) + cross_track_m * math.cos(heading_rad)

    # 5. Geodesic coordinates
    lat_rad = math.radians(nav.vessel_lat)
    
    delta_lat_deg = (delta_north / EARTH_RADIUS_METERS) * (180.0 / math.pi)
    
    # Correct for longitude convergence near poles
    cos_lat = math.cos(lat_rad)
    if abs(cos_lat) < 1e-6:
        cos_lat = 1e-6
        
    delta_lon_deg = (delta_east / (EARTH_RADIUS_METERS * cos_lat)) * (180.0 / math.pi)

    target_lat = nav.vessel_lat + delta_lat_deg
    target_lon = nav.vessel_lon + delta_lon_deg

    return GeotagDetails(
        latitude=round(target_lat, 6),
        longitude=round(target_lon, 6),
        cross_track_m=round(cross_track_m, 2),
        along_track_m=round(along_track_m, 2),
        slant_range_m=round(slant_range_m, 2),
        ground_range_m=round(ground_range_m, 2)
    )


def georeference_detections(
    detections: List[Dict[str, Any]],
    image_width: int,
    image_height: int,
    nav: NavigationSidecar
) -> List[Dict[str, Any]]:
    """
    Enriches detection dictionaries with WGS84 geodesic projection details.
    """
    geotagged_detections = []
    
    for det in detections:
        d = dict(det)
        bbox = d["bbox"]
        
        # Georeference
        geotag_details = project_pixel_to_wgs84(
            x1=bbox["x1"],
            y1=bbox["y1"],
            x2=bbox["x2"],
            y2=bbox["y2"],
            image_width=image_width,
            image_height=image_height,
            nav=nav
        )
        
        d["latitude"] = geotag_details.latitude
        d["longitude"] = geotag_details.longitude
        d["geotag_details"] = geotag_details.model_dump()
        
        geotagged_detections.append(d)
        
    return geotagged_detections
