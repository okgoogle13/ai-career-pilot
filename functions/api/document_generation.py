"""
HTTP endpoint for document generation.
"""
import asyncio
import json
from typing import Dict, Any, Optional

from firebase_functions import https_fn
from werkzeug.datastructures import FileStorage

from ..ai.document_generator import generate_application

@https_fn.on_request(cors=True)
def generate_application_http(req: https_fn.Request) -> https_fn.Response:
    """HTTP endpoint for the generate_application flow."""

    if req.method == 'OPTIONS':
        # Handle preflight requests for CORS
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return https_fn.Response("", status=204, headers=headers)

    if req.method != 'POST':
        return https_fn.Response("Method not allowed", status=405)

    try:
        # Handle multipart form data
        request_data_str = req.form.get('requestData')
        if not request_data_str:
            return https_fn.Response(json.dumps({"error": "Missing requestData"}), status=400, headers={"Content-Type": "application/json"})

        request_data = json.loads(request_data_str)
        resume_file = req.files.get('resume')

        # Basic validation
        if not all(k in request_data for k in ["job_ad_url", "theme_id", "tone_of_voice"]):
            return https_fn.Response(
                json.dumps({"error": "Missing required fields"}),
                status=400,
                headers={"Content-Type": "application/json"}
            )

        # Run the async flow
        result = asyncio.run(generate_application(request_data, resume_file))

        return https_fn.Response(
            json.dumps(result),
            status=200,
            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"}
        )

    except Exception as e:
        # Log the error for better debugging
        # from google.cloud import logging
        # client = logging.Client()
        # logger = client.logger('http_errors')
        # logger.log_struct({'message': f"Error in generate_application_http: {str(e)}"}, severity='ERROR')

        return https_fn.Response(
            json.dumps({"error": "An unexpected error occurred."}),
            status=500,
            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"}
        )
