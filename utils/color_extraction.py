import numpy as np
from PIL import Image
import colorsys
from skimage.draw import polygon as ski_polygon


def get_polygon_mask(points, img_h, img_w):
    """Create a boolean mask for a polygon defined by points."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    rr, cc = ski_polygon(ys, xs, shape=(img_h, img_w))
    mask = np.zeros((img_h, img_w), dtype=bool)
    mask[rr, cc] = True
    return mask


def extract_pixels(img_array, mask):
    """Extract pixels inside the mask."""
    pixels = img_array[mask]  # shape: (N, 3)
    return pixels


def compute_histogram(pixels, channel, bins=256):
    """Compute histogram for a single channel (0=R, 1=G, 2=B)."""
    values = pixels[:, channel]
    hist, bin_edges = np.histogram(values, bins=bins, range=(0, 255))
    return hist, bin_edges


def compute_y_channel(pixels, channel):
    """Compute normalized y channel (yR, yG, yB) from RGB pixels."""
    r = pixels[:, 0].astype(float)
    g = pixels[:, 1].astype(float)
    b = pixels[:, 2].astype(float)
    total = r + g + b + 1e-6  # avoid division by zero
    if channel == "yR":
        return r / total
    elif channel == "yG":
        return g / total
    elif channel == "yB":
        return b / total


def compute_hsv(pixels):
    """Compute mean HSV from RGB pixels."""
    hsv_values = []
    for pixel in pixels:
        r, g, b = pixel[0] / 255.0, pixel[1] / 255.0, pixel[2] / 255.0
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        hsv_values.append([h * 360, s * 100, v * 100])
    return np.array(hsv_values)


def compute_luminosity(pixels):
    """Compute luminosity L from RGB pixels (ITU-R BT.601)."""
    r = pixels[:, 0].astype(float)
    g = pixels[:, 1].astype(float)
    b = pixels[:, 2].astype(float)
    L = 0.299 * r + 0.587 * g + 0.114 * b
    return L


def extract_colorgramme(img_array, mask, config_params, bins=256):
    """
    Extract all selected parameters from pixels inside the mask.
    Returns a dict with parameter name -> histogram values.
    """
    pixels = extract_pixels(img_array, mask)

    if len(pixels) == 0:
        return {}

    result = {}

    if config_params.get("R"):
        hist, edges = compute_histogram(pixels, 0, bins)
        result["R"] = {"hist": hist, "edges": edges}

    if config_params.get("G"):
        hist, edges = compute_histogram(pixels, 1, bins)
        result["G"] = {"hist": hist, "edges": edges}

    if config_params.get("B"):
        hist, edges = compute_histogram(pixels, 2, bins)
        result["B"] = {"hist": hist, "edges": edges}

    if config_params.get("yR"):
        yr = compute_y_channel(pixels, "yR")
        hist, edges = np.histogram(yr, bins=bins, range=(0, 1))
        result["yR"] = {"hist": hist, "edges": edges}

    if config_params.get("yG"):
        yg = compute_y_channel(pixels, "yG")
        hist, edges = np.histogram(yg, bins=bins, range=(0, 1))
        result["yG"] = {"hist": hist, "edges": edges}

    if config_params.get("yB"):
        yb = compute_y_channel(pixels, "yB")
        hist, edges = np.histogram(yb, bins=bins, range=(0, 1))
        result["yB"] = {"hist": hist, "edges": edges}

    if config_params.get("HSV"):
        hsv = compute_hsv(pixels)
        hist_h, edges_h = np.histogram(hsv[:, 0], bins=bins, range=(0, 360))
        result["H"] = {"hist": hist_h, "edges": edges_h}
        hist_s, edges_s = np.histogram(hsv[:, 1], bins=bins, range=(0, 100))
        result["S"] = {"hist": hist_s, "edges": edges_s}
        hist_v, edges_v = np.histogram(hsv[:, 2], bins=bins, range=(0, 100))
        result["V"] = {"hist": hist_v, "edges": edges_v}

    if config_params.get("L"):
        L = compute_luminosity(pixels)
        hist, edges = np.histogram(L, bins=bins, range=(0, 255))
        result["L"] = {"hist": hist, "edges": edges}

    return result