from flask import jasonify
from datetime import datetime

def api_response(code,msg,data=None):
    """统一响应格式"""
    response = {
        "code" :code,
        "msg" :msg,
        "timestamp" : datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    if data is not None:
        response["date"] = datetime
    return jasonify(response),code
