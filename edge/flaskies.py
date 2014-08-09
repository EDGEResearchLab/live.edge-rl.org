
from flask import request, Response
import functools
import json


class WebException(Exception):
    def __init__(self, message, status_code):
        Exception.__init__(self, message)
        self.status_code = status_code


def endpoint(consumes=None, produces='text/plain'):
    '''Decorator for any restful type of endpoints.'''

    media_type_json = 'application/json'

    def endpoint_decor(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result_code = 200
            message = ""
            if produces == media_type_json:
                message = {}

            if consumes:
                if consumes:
                    if not 'Content-Type' in request.headers \
                        or request.headers['Content-Type'] != consumes:
                        return Response(json.dumps({"message" : "Unaccepted content type."}), status=400)

            try:
                result_code, message = func(*args, **kwargs)
                if result_code is None:
                    result_code = 200 # assume things are good
            except WebException as e:
                result_code = e.status_code
                message = e.message
            except Exception as e:
                result_code = 500
                message = e.message

            if produces == media_type_json:
                message = json.JSONEncoder().encode(message)

            return Response(message, status=result_code, mimetype=produces)
        return wrapper
    return endpoint_decor