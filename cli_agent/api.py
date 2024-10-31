from flask import Flask, jsonify, request
import asyncio
from agent import execute

app = Flask(__name__)


async def handle_message(message):
    res = execute(message)
    return res


@app.route('/agent', methods=['POST'])
async def agent():
    # Get the request JSON
    data = request.get_json()

    if 'msg' not in data:
        return (jsonify({"error": "No 'msg' field provided"}), 400)

    message = data['msg']

    response_message = await handle_message(message)

    return jsonify({'msg': response_message})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
