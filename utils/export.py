import pandas as pd
import numpy as np
import json
import io # Importar io para lidar com streams de bytes


def colorgramme_to_row(colorgramme):
    """Flatten a colorgramme dict into a flat dict of columns."""
    row = {}
    for param, data in colorgramme.items():
        hist = data["hist"]
        for i, val in enumerate(hist):
            row[f"{param}_{i}"] = val
    return row


def build_dataframe(all_results, sampling_mode):
    """
    all_results: list of dicts from session_state results_{idx}
    Each dict has: image, polygon, class, colorgramme, n_pixels
    sampling_mode: "one per polygon" or "one per image"
    """
    rows = []

    if "per polygon" in sampling_mode.lower() or "per polygon" in sampling_mode:
        # One row per polygon
        for res in all_results:
            row = {
                "image": res["image"],
                "polygon": res["polygon"],
                "class": res["class"],
                "n_pixels": res["n_pixels"]
            }
            row.update(colorgramme_to_row(res["colorgramme"]))
            rows.append(row)

    else:
        # One row per image — average colorgrammes per class per image
        from collections import defaultdict
        grouped = defaultdict(list)

        for res in all_results:
            key = (res["image"], res["class"])
            grouped[key].append(res["colorgramme"])

        for (image, class_name), cg_list in grouped.items():
            # Average all colorgrammes
            avg_cg = {}
            all_params = cg_list[0].keys()
            for param in all_params:
                hists = [cg[param]["hist"] for cg in cg_list if param in cg]
                edges = cg_list[0][param]["edges"]
                if hists:
                    avg_cg[param] = {
                        "hist": np.mean(hists, axis=0),
                        "edges": edges
                    }

            row = {
                "image": image,
                "class": class_name,
                "n_polygons": len(cg_list)
            }
            row.update(colorgramme_to_row(avg_cg))
            rows.append(row)

    return pd.DataFrame(rows)


# A função export_results original, mantida caso ainda seja usada
def export_results(all_results, sampling_mode, output_path, file_name, fmt):
    """
    Export results to file.
    Returns the full output path on success.
    """
    df = build_dataframe(all_results, sampling_mode)

    if df.empty:
        return None, "No data to export."

    full_path = os.path.join(output_path, f"{file_name}.{fmt}")

    if fmt == "xlsx":
        df.to_excel(full_path, index=False)
    elif fmt == "csv":
        df.to_csv(full_path, index=False)
    elif fmt == "json":
        df.to_json(full_path, orient="records", indent=2)

    return full_path, None


# NOVA FUNÇÃO para retornar os bytes do arquivo
def export_results_as_bytes(all_results, sampling_mode, file_name, fmt):
    """
    Export results and return as bytes for download.
    """
    df = build_dataframe(all_results, sampling_mode)

    if df.empty:
        return None

    output_buffer = io.BytesIO()

    if fmt == "xlsx":
        # Para xlsx, pandas precisa de um ExcelWriter
        with pd.ExcelWriter(output_buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
        output_buffer.seek(0) # Volta para o início do buffer
        return output_buffer.getvalue()
    elif fmt == "csv":
        # Para csv, to_csv pode escrever diretamente no buffer de string, depois codificamos
        df.to_csv(output_buffer, index=False)
        output_buffer.seek(0)
        return output_buffer.getvalue()
    elif fmt == "json":
        # Para json, to_json pode escrever diretamente no buffer de string, depois codificamos
        df.to_json(output_buffer, orient="records", indent=2)
        output_buffer.seek(0)
        return output_buffer.getvalue()

    return None
