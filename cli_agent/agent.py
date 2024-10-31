from typing import TypedDict, List
from dotenv import load_dotenv
import subprocess

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from langgraph.graph import StateGraph, END

load_dotenv()

llm = ChatOpenAI(model="gpt-4o")

prompt = ChatPromptTemplate.from_messages([
    ("system", """
Given a description of a problem, you will generate only the command line code needed to implement a solution. Follow these guidelines to ensure the output is flawless:

Instructions:
Focus on Functionality and Correctness:

Analyze the problem to understand the core requirements and the expected input-output behavior.
Ensure the code meets each requirement, handles all specified inputs, and produces accurate outputs.
Use Proper Structuring and Naming:

Organize the code logically.
Avoid unnecessary code or comments; write concise and purpose-driven code.
Handle Edge Cases:

Account for edge cases or potential issues in the input, such as invalid data types, boundary values, and unexpected input sizes or formats.
Output Only the command line code:

Your response must contain only the command line code needed to solve the problem. Do not include any markdown formatting, explanations, comments, or text.
The output should be ready to execute immediately and should not include any extra text, headers, or formatting.

IMPORTANT: Avoid External Commands.

IMPORTANT: Use only standard command line commands.
Requirements Summary:

IMPORTANT: use only standard default command line commands.

IMPORTANT: You are a command line tool agent, and you are not permitted to execute anything besides tasks that execute File I/O command line tools.


Write only code.
Use standard default command line commands aimed for File I/O.
USE FILE I/O COMMANDS!
The code should be clear, accurate, and handle edge cases.
Do not include markdown or additional formatting, just the command line code.

    
Your task: Now, given the problem: \n-----\n {problem} \n ----- \n Write the command line code solution."""),
    ("placeholder", "{messages}")])


class AgentState(TypedDict):
    messages: List[dict]  # Update to a list of dictionaries for messages
    query: str
    execution_status: str  # "success" or "fail"
    generated_code: str  # Change to `str` for storing code as a single string
    error_log: List[str]  # error log
    iterations: int  # retry count of checks. if it exceeds 5, human intervention will be provided


# Max tries
max_iterations = 5
# Reflect
flag = 'reflect'
# flag = "do not reflect"


def convert_code_block_to_plain_text(code_block):
    # Remove the triple backticks and strip any extra whitespace
    return code_block.strip("```").strip()[len("bash\n"):]


agent_chain = prompt | llm

# Nodes


def create_solution(state: AgentState):
    messages = state["messages"]
    iterations = state["iterations"]
    error = state["execution_status"]
    query = state["query"]

    if error == "fail":
        messages.append({
            "role": "user",
            "content": "The previous command did not work as expected. Analyze the error and try generating a revised command that addresses any issues. Ensure the command uses standard command-line syntax, handles edge cases, and meets all specified requirements. Provide only the corrected command."
        })

    # Get generated code from LLM
    code_solution = agent_chain.invoke({
        "problem": query,
        "messages": messages
    }).content

    # Format the generated code if it includes markdown backticks
    if "```" in code_solution:
        code_solution = convert_code_block_to_plain_text(code_solution)

    print(code_solution)

    # Append the assistant's response in the correct format
    messages.append({"role": "assistant", "content": code_solution})
    state["messages"] = messages
    state["iterations"] = iterations + 1
    state["generated_code"] = code_solution

    return state


def execute_solution(state: AgentState):
    """This function executes the solution provided"""
    messages = state["messages"]
    code_solution = state["generated_code"]

    try:
        subprocess.run(code_solution, check=True, shell=True)
    except Exception as e:
        print("-----EXECUTING CODE: FAILED-----")
        err_msg = f"Your solution has failed the code execution test: {e}"
        print(err_msg)

        # Append the error message in the correct format
        messages.append({"role": "user", "content": err_msg})
        state["messages"] = messages
        state["error_log"].append(err_msg)
        state["execution_status"] = "fail"
        return state

    print("---NO CODE TEST FAILURES---")
    state["execution_status"] = "success"
    return state


def reflect(state: AgentState):
    """
    Reflect on errors

    Args:
        state (AgentState): The current graph state

    Returns:
        AgentState: Updated state with reflection added to messages
    """
    print("---GENERATING CODE SOLUTION---")

    # State
    messages = state["messages"]

    # Prompt reflection and add reflection to messages
    reflections = agent_chain.invoke({
        "problem": state["query"],
        "messages": messages
    }).content

    messages.append({
        "role": "assistant",
        "content": f"Here are reflections on the error: {reflections}"
    })

    state["messages"] = messages
    return state


# Edges


def decide_to_finish(state: AgentState):
    """
    Determines whether to finish.

    Args:
        state (dict): The current graph state

    Returns:
        str: Next node to call
    """
    error = state["execution_status"]
    iterations = state["iterations"]

    if error == "success" or iterations == max_iterations:
        print("---DECISION: FINISH---")
        return "end"
    else:
        print("---DECISION: RE-TRY SOLUTION---")
        if flag == "reflect":
            return "reflect"
        else:
            return "recreate"


workflow = StateGraph(AgentState)

# Nodes
workflow.add_node("create_solution", create_solution)
workflow.add_node("execute_solution", execute_solution)
workflow.add_node("reflect", reflect)

# Edges
workflow.set_entry_point("create_solution")
workflow.add_edge("create_solution", "execute_solution")
workflow.add_conditional_edges("execute_solution", decide_to_finish,
                               {
                                   "end": END,
                                   "reflect": "reflect",
                                   "recreate": "create_solution",
                               }
                               )

workflow.add_edge("reflect", "create_solution")
app = workflow.compile()


def execute(query):
    # question = "in tel.txt, answer the question: how to teleport?"
    solution = app.invoke({
        "messages": [{"role": "user", "content": query}],
        "query": query,
        "iterations": 0,
        "error_log": [],
        "execution_status": "success"
    })
    return solution
