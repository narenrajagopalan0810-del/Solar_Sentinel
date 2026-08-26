import cv2
import numpy as np

def preprocess_image(
    image: np.ndarray,
    clahe_clip_limit: float = 2.5,
    clahe_grid_size: tuple = (8, 8),
    bilateral_d: int = 7,
    bilateral_sigma_color: float = 50.0,
    bilateral_sigma_space: float = 50.0
) -> np.ndarray:
    """
    Standardized Sonar Image Preprocessing Pipeline:
    1. Grayscale Conversion (preserves luminance)
    2. Bilateral Filtering: Removes speckle noise while preserving sharp boundaries
    3. CLAHE: Amplifies contrast in low-backscatter/shadowed regions
    4. Min-Max Normalization: Rescales values to [0, 255] range
    
    Returns:
        np.ndarray: Preprocessed BGR image (3 channels) ready for YOLO/ONNX inference
    """
    # 1. Grayscale Handling
    if len(image.shape) == 3:
        if image.shape[2] == 4:  # RGBA
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # 2. Despeckling via Bilateral Filter
    despeckled = cv2.bilateralFilter(
        gray,
        d=bilateral_d,
        sigmaColor=bilateral_sigma_color,
        sigmaSpace=bilateral_sigma_space
    )

    # 3. CLAHE Contrast Enhancement
    clahe = cv2.createCLAHE(clipLimit=clahe_clip_limit, tileGridSize=clahe_grid_size)
    enhanced = clahe.apply(despeckled)

    # 4. Normalization
    normalized = cv2.normalize(enhanced, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)

    # 5. Convert back to 3-channel BGR for consistency in deep learning architectures
    processed_bgr = cv2.cvtColor(normalized, cv2.COLOR_GRAY2BGR)

    return processed_bgr
