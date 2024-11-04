import asyncio
from flask import Flask, request, jsonify
import agent

app = Flask(__name__)


async def execute(msg: str) -> str:
    """Execute the agent with the provided message and return the agent state."""
    app_state = await agent.execute(msg)
    return f"Agent status: {app_state}"


@app.route("/agent", methods=["POST"])
def agent_endpoint():
    """
    Endpoint to interact with the agent.
    Expects a JSON payload containing the 'msg' field.
    Returns the agent's response or an error 400 if 'msg' is missing.
    """
    data = request.get_json()
    if not data or "msg" not in data:
        return jsonify({"error": "Missing 'msg' field"}), 400

    msg = data["msg"]
    response_msg = asyncio.run(execute(msg))
    return jsonify({"msg": response_msg})


if __name__ == "__main__":
    # Run the API on 0.0.0.0:8000 for external access.
    app.run(host="0.0.0.0", port=8000)
