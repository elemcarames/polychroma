# PolyChroma 🎨

**Manual RGB polygon sampling tool for image color analysis.**

Built for researchers, food scientists, and anyone who needs to extract 
color histograms from specific regions of interest in images — without 
writing a single line of code.

---

## 🔬 Why PolyChroma?

During my PhD research on food authentication using NIR and hyperspectral 
imaging, I repeatedly needed to manually sample color histograms from 
specific regions of food images — and feed those features into ML models.

There was no simple, open-source tool for this. So I built one.

PolyChroma lets you draw polygons directly on images, extract color 
parameters from the selected regions, and export the results in a 
analysis-ready format.

---

## ✨ Features

- **Polygon sampling** — draw multiple polygons per image with 
  left click / right click
- **Multi-class support** — assign different class labels to polygons 
  within the same image
- **Color parameters** — extract R, G, B, yR, yG, yB, HSV, and 
  Luminosity histograms
- **Average colorgramme** — automatic averaging per class across 
  all polygons
- **Live visualization** — colorgramme charts update in real time 
  as you draw
- **Flexible export** — save results as `.xlsx`, `.csv`, or `.json`
- **Zoom control** — adjust image display size for precise sampling

---

## 🖥️ Interface

| Sidebar | Sampling |
|---|---|
| Navigation between modules | Draw polygons on images |
| Import folder of images | Live colorgramme visualization |
| Configure parameters | Save and export results |

---

## 🚀 Getting Started

### Requirements

- Python 3.8+
- pip

### Installation

```bash
git clone https://github.com/elemcarames/polychroma.git
cd polychroma
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
streamlit run app.py
```

### Usage

1. **Import Images** — point to a folder with `.jpg`, `.png`, or `.tiff` files
2. **Configuration** — select color parameters and sampling mode
3. **Export Settings** — choose output folder, format, and file name
4. **Sampling** — draw polygons and visualize colorgrammes in real time
5. **Export** — save all results to file

---

## 📦 Dependencies

streamlit
streamlit-drawable-canvas-fix
Pillow
numpy
pandas
matplotlib
scikit-image
openpyxl

---

## 🧪 Use Cases

- Food authenticity research — extract color features for ML classification
- Agricultural quality control — sample color from fruit/vegetable images
- Computer vision annotation — manual region-based color analysis
- Any image dataset where color distribution per region matters

---

## 📁 Project Structure

polychroma/
│
├── app.py                      # Main entry point
├── assets/                     # Logo and icons
├── views/                      # UI modules
│   ├── import_images.py
│   ├── configuration.py
│   ├── export_settings.py
│   └── sampling.py
├── utils/                      # Core logic
│   ├── color_extraction.py     # RGB/HSV/L extraction
│   └── export.py               # xlsx/csv/json export
└── .streamlit/
└── config.toml             # Theme configuration

---

## 👩‍🔬 About

Built by [Elem Carames](https://github.com/elemcarames) — Data Scientist 
and PhD in Food Science, with 10+ years of experience applying ML to 
spectroscopy and image analysis.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=flat&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/elem-carames)