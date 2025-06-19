from myapp.utils.logger_config import get_logger
from typing import Optional, Any
from flask import Blueprint, request, jsonify, Response, make_response
import os
from werkzeug.utils import secure_filename
from myapp.utils.parsing_utils import process_uploaded_file
from myapp.utils.report_utils import create_and_email_report
from datetime import datetime

report_bp = Blueprint("report_bp", __name__)

UPLOAD_FOLDER = "uploads"
PDF_OUTPUT_FOLDER = "output/client_reports"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PDF_OUTPUT_FOLDER, exist_ok=True)


@report_bp.route("/upload", methods=["POST"])
def upload_file() -> Response:
    if "excel_file" not in request.files:
        return make_response(jsonify({"error": "No file part in the request"}), 400)
    file = request.files["excel_file"]
    filename: Optional[str] = file.filename
    if filename is None:
        raise ValueError("Missing file name")
    filename = secure_filename(filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    try:
        file.save(file_path)
    except Exception as e:
        return make_response(jsonify({"error": f"Failed to save file: {str(e)}"}), 500)

    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")
    if not start_date or not end_date:
        return make_response(jsonify({"error": "Missing start_date or end_date"}), 400)

    try:
        processed_data = process_uploaded_file(file_path, start_date, end_date)
    except FileNotFoundError:
        return make_response(jsonify({"error": "File not found or unreadable"}), 400)
    except ValueError as ve:
        return make_response(jsonify({"error": f"Invalid Excel file: {str(ve)}"}), 400)
    except Exception as e:
        return make_response(
            jsonify({"error": f"Failed to process Excel: {str(e)}"}), 500
        )

    results = []
    for data_dict in processed_data:
        client_name = data_dict.get("client_name", "client")
        client_email = data_dict.get(
            "client_email", "default@example.com"
        )  # Fallback email
        try:
            create_and_email_report(
                data_dict, client_email, start_date, end_date, filename
            )
            results.append({"client_name": client_name, "status": "success"})
        except Exception as e:
            results.append(
                {"client_name": client_name, "status": "failed", "error": str(e)}
            )

    return make_response(
        jsonify({"message": "Processing completed", "results": results}), 200
    )
