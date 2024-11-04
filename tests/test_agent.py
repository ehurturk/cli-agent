import pytest
import os
from cli_agent.agent import execute

# Define a constant for the OutTests directory
OUTTESTS_DIR = "./OutTests"


@pytest.mark.asyncio
async def test_create_text_file():
    query = "create a text file named 'testfile.txt' containing 'This is a test' in the OutTests directory in this working directory"
    file_path = os.path.join(OUTTESTS_DIR, "testfile.txt")

    # Execute the agent's command
    res = await execute(query)

    # Verify if the file was created
    assert os.path.exists(file_path), "File 'testfile.txt' was not created."

    # Verify the file content
    with open(file_path, "r") as file:
        content = file.read()
    assert content == "This is a test\n", "File content does not match expected text."


@pytest.mark.asyncio
async def test_remove_file():
    query = "delete the file named 'testfile.txt' in the OutTests directory that is in this working directory"
    file_path = os.path.join(OUTTESTS_DIR, "testfile.txt")

    # Create a file to delete (since the previous test may have deleted it)
    with open(file_path, "w") as file:
        file.write("Temporary content.")

    # Execute the agent's command
    res = await execute(query)

    # Verify if the file was deleted
    assert not os.path.exists(file_path), "File 'testfile.txt' was not deleted."


@pytest.mark.asyncio
async def test_move_file():
    query = "move 'testfile.txt' in OutTests to a directory named 'backup' in the OutTests directory that is in this working directory."
    backup_dir = os.path.join(OUTTESTS_DIR, "backup")
    os.makedirs(backup_dir, exist_ok=True)  # Ensure backup directory exists
    file_path = os.path.join(OUTTESTS_DIR, "testfile.txt")

    # Create a file to move
    with open(file_path, "w") as file:
        file.write("Temporary content.")

    # Execute the agent's command
    res = await execute(query)

    # Verify if the file was moved to the backup directory
    moved_file_path = os.path.join(backup_dir, "testfile.txt")
    assert os.path.exists(
        moved_file_path
    ), "File 'testfile.txt' was not moved to 'backup' directory."
    assert not os.path.exists(
        file_path
    ), "Original file 'testfile.txt' still exists in the source directory."
