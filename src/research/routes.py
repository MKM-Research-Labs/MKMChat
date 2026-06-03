# Copyright (c) 2025-2026 MKM Research Labs. All rights reserved.
"""
Research API Routes
-------------------

Flask route factories for research query endpoints.
Supports both standard POST and streaming SSE endpoints.
"""

import json
import traceback
from http import HTTPStatus

from .handler import ResearchQueryHandler


def create_research_route(app_instance):
    """
    Create and return the Flask route handler for research queries (non-streaming).

    Args:
        app_instance: The DocumentQAApp instance

    Returns:
        Flask route handler function
    """
    from flask import request, jsonify

    handler = ResearchQueryHandler(app_instance)

    def research_query():
        """API endpoint for deep research queries (non-streaming)"""
        try:
            if not request.is_json:
                return jsonify({'error': 'Request must be JSON'}), HTTPStatus.BAD_REQUEST

            request_data = request.get_json()
            query = request_data.get('query')
            model = request_data.get('model')
            kb_keys = request_data.get('kb_keys')

            if not query:
                return jsonify({'error': 'Missing required field: query'}), HTTPStatus.BAD_REQUEST

            if not model:
                return jsonify({'error': 'Missing required field: model'}), HTTPStatus.BAD_REQUEST

            if model not in app_instance.AVAILABLE_MODELS:
                return jsonify({
                    'error': f'Invalid model. Valid models: {list(app_instance.AVAILABLE_MODELS.keys())}'
                }), HTTPStatus.BAD_REQUEST

            if kb_keys is not None:
                if not isinstance(kb_keys, list):
                    return jsonify({'error': 'kb_keys must be a list'}), HTTPStatus.BAD_REQUEST

                invalid_keys = [k for k in kb_keys if k not in app_instance.AVAILABLE_INDICES]
                if invalid_keys:
                    return jsonify({
                        'error': f'Invalid KB keys: {invalid_keys}'
                    }), HTTPStatus.BAD_REQUEST

            result = handler.execute_research_query(query, model, kb_keys)
            return jsonify(result.to_dict()), HTTPStatus.OK

        except Exception as e:
            print(f"Research query error: {str(e)}")
            print(traceback.format_exc())
            return jsonify({'error': f'Research query failed: {str(e)}'}), HTTPStatus.INTERNAL_SERVER_ERROR

    return research_query


def create_research_stream_route(app_instance):
    """
    Create and return the Flask route handler for streaming research queries.

    This uses Server-Sent Events (SSE) to stream progress updates to the client.

    Args:
        app_instance: The DocumentQAApp instance

    Returns:
        Flask route handler function
    """
    from flask import request, Response

    handler = ResearchQueryHandler(app_instance)

    def research_query_stream():
        """API endpoint for streaming research queries via SSE"""
        # Get parameters from query string (GET) or JSON body (POST)
        if request.method == 'GET':
            query = request.args.get('query')
            model = request.args.get('model')
            kb_keys_str = request.args.get('kb_keys')
            kb_keys = kb_keys_str.split(',') if kb_keys_str else None
        else:
            data = request.get_json() or {}
            query = data.get('query')
            model = data.get('model')
            kb_keys = data.get('kb_keys')

        # Validate
        if not query or not model:
            def error_gen():
                yield f"event: error\ndata: {json.dumps({'error': 'Missing query or model'})}\n\n"
            return Response(error_gen(), mimetype='text/event-stream')

        if model not in app_instance.AVAILABLE_MODELS:
            def error_gen():
                yield f"event: error\ndata: {json.dumps({'error': 'Invalid model'})}\n\n"
            return Response(error_gen(), mimetype='text/event-stream')

        # Stream the research query
        def generate():
            try:
                for event in handler.execute_research_query_streaming(query, model, kb_keys):
                    yield event
            except Exception as e:
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'  # Disable nginx buffering
            }
        )

    return research_query_stream
