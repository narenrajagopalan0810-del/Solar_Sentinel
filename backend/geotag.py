def attach_geotag(detections, base_lat=13.0827, base_lon=80.2707):
    # TODO: implement pixel offset to WGS84 projection
    for d in detections:
        d["location"] = {
            "lat": base_lat + d["bbox"]["x"] * 0.0001,
            "lon": base_lon + d["bbox"]["y"] * 0.0001
        }
    return detections
