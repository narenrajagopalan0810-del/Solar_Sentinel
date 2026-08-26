def run(image):
    # TODO: load ONNX model and return real detections
    return [
        {
            "class": "ghost_net",
            "confidence": 0.84,
            "bbox": {"x": 120, "y": 340, "width": 142, "height": 89}
        }
    ]
