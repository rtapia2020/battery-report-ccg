
from flask import Flask, render_template, request, send_file
from bs4 import BeautifulSoup
from datetime import datetime
import os
import pdfkit

app = Flask(__name__, template_folder=".")
UPLOAD_FOLDER = "."
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def analizar_reporte(ruta_archivo):
    with open(ruta_archivo, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")

    info = {
        "design_capacity": "",
        "full_charge_capacity": "",
        "cycle_count": "",
        "computer_name": "",
        "system_product": "",
        "bios": "",
        "os_build": "",
        "platform_role": "",
        "connected_standby": "",
        "report_time": "",
        "battery_name": "",
        "battery_manufacturer": "",
        "battery_serial": "",
        "battery_chemistry": "",
        "battery_health": "",
        "recommendation": "",
        "estimated_life": "",
        "health_percent": 0
    }

    tables = soup.find_all("table")
    if len(tables) > 0:
        rows = tables[0].find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) == 2:
                label = cells[0].text.strip().lower()
                value = cells[1].text.strip()
                if "computer name" in label:
                    info["computer_name"] = value
                elif "system product name" in label:
                    info["system_product"] = value
                elif "bios" in label:
                    info["bios"] = value
                elif "os build" in label:
                    info["os_build"] = value
                elif "platform role" in label:
                    info["platform_role"] = value
                elif "connected standby" in label:
                    info["connected_standby"] = value
                elif "report time" in label:
                    info["report_time"] = value

    if len(tables) > 1:
        rows = tables[1].find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) == 2:
                label = cells[0].text.strip().lower()
                value = cells[1].text.strip()
                if "name" == label:
                    info["battery_name"] = value
                elif "manufacturer" == label:
                    info["battery_manufacturer"] = value
                elif "serial number" in label:
                    info["battery_serial"] = value
                elif "chemistry" in label:
                    info["battery_chemistry"] = value
                elif "design capacity" in label:
                    info["design_capacity"] = value.replace(",", "").replace(" mWh", "")
                elif "full charge capacity" in label:
                    info["full_charge_capacity"] = value.replace(",", "").replace(" mWh", "")
                elif "cycle count" in label:
                    info["cycle_count"] = value

    try:
        design = int(info["design_capacity"])
        full = int(info["full_charge_capacity"])
        info["health_percent"] = int((full / design) * 100)
    except:
        info["health_percent"] = 0

    health = info["health_percent"]
    if health >= 90:
        info["recommendation"] = "✅ La batería está en buen estado. No se recomienda cambio."
    elif health >= 70:
        info["recommendation"] = "⚠️ La batería ha perdido capacidad. Considerar reemplazo pronto."
    else:
        info["recommendation"] = "❌ La batería está degradada. Se recomienda cambio."

    try:
        ciclos_actuales = int(info["cycle_count"])
        vida_util_estimada = 500
        ciclos_restantes = vida_util_estimada - ciclos_actuales
        meses_restantes = max(1, round(ciclos_restantes / 30, 1))
        info["estimated_life"] = f"⏳ Se estima que la batería tendrá un rendimiento aceptable durante aproximadamente {meses_restantes} meses más."
    except:
        info["estimated_life"] = "⏳ No se pudo calcular una estimación de vida útil por falta de datos."

    return info

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["batteryfile"]
        export_pdf = "export_pdf" in request.form
        if file and file.filename.endswith(".html"):
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(filepath)
            data = analizar_reporte(filepath)

            if export_pdf:
                rendered = render_template("report.html", info=data, fecha=datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
                pdf_name = f"Reporte_Bateria-{data['computer_name']}-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
                pdf_path = os.path.join(app.config["UPLOAD_FOLDER"], pdf_name)
                pdfkit.from_string(rendered, pdf_path)
                return send_file(pdf_path, as_attachment=True)

            html_name = f"Reporte_Bateria-{data['computer_name']}-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.html"
            output_path = os.path.join(app.config["UPLOAD_FOLDER"], html_name)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(render_template("report.html", info=data, fecha=datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
            return render_template("report.html", info=data, fecha=datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

    return render_template("index.html")
