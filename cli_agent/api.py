from flask import Flask, request, jsonify
import asyncio

import agent

app = Flask(__name__)


async def execute(msg: str) -> str:
    app_state = await agent.execute(msg)
    return f"Agent status: {app_state}"


@app.route('/agent', methods=['POST'])
def agent_endpoint():
    data = request.get_json()
    if not data or 'msg' not in data:
        return (jsonify({"error": "Missing 'msg' field"}), 400)

    msg = data['msg']

    response_msg = asyncio.run(execute(msg))
    return jsonify({"msg": response_msg})


# Run the api on 0.0.0.0:8000
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)
