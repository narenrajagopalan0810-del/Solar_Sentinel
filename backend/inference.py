from preprocess import preprocess_image

def run(image):
    # Apply identical preprocessing pipeline prior to inference
    preprocessed = preprocess_image(image)
    
    # TODO: feed preprocessed image into ONNX model and return real detections
    return [
        {
            "class": "ghost_net",
            "confidence": 0.84,
            "bbox": {"x": 120, "y": 340, "width": 142, "height": 89}
        }
    ]
