from flask import Flask, jsonify, request
from tasks import translate_task, summarize_task
from celery.result import AsyncResult

app = Flask(__name__)

@app.route("/")
def hello():
    return "<p>Hello World</p>"

@app.route("/api/ai")
def api():
    return jsonify({
        "success": True,
        "data": [{
            "id": "translate",
            "name": "文本翻译",
            "route": "/api/ai/<id>",
            "method": "POST",
            "req_body": {
                "text": "要翻译的文本",
                "target_lang": "翻译到的目标语言"
            },
            "desc": "自动判断text文本语言，将这段文本翻译成target_lang目标语言。",
            "resp_demo": {
                "text": "apple", 
                "source_lang": "英文",
                "target_lang": "中文",
                "is_same_lang": "否",
                "translated_text": "苹果"
            },
        },{
            "id": "summarize",
            "name": "文本总结",
            "route": "/api/ai/<id>",
            "method": "POST",
            "req_body": {
                "text": "要总结的文本",
            },
            "desc": "多维度总结text文本",
            "resp_demo": {
                "key_points": ["点1", "点2"],
                "emotional_tone": {"tone": "xx", "reason": "xx"},
                "summary": "xx",
                "action_items": ["项1", "项2"]
            }
        }]
    })

@app.route("/api/ai/<id>", methods=["POST"])
def execute_ai(id: str):
    data = request.get_json()
    if not data:
        return "Invalid JSON", 400
    if id == "translate":
        # print(data.get("text"), data.get("target_lang"))
        task = translate_task.delay(text=data.get("text"), target_lang=data.get("target_lang"))
    elif id == "summarize":
        task = summarize_task.delay(text=data.get("text"))
    else:
        return jsonify({
            "success": False,
            "message": "Ai not found"
        }), 404
    return jsonify({
        "success": True,
        "data": {
            "task_id": task.id
        }
    })
    
@app.route("/api/task", methods=["GET"])
def get_task_result():
    task_id = request.args.get("task_id")
    if not task_id:
        return "Invalid JSON", 400
    task = AsyncResult(task_id)
    return jsonify({
        "success": True,
        "data": {
            "task_id": task.id,
            "task_state": task.state,
            "task_result": task.result if task.ready() else None
        },
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)