"""
/*
 * #file:license-header.txt
 * Copyright 2025 Gatherings MCP Python Server Contributors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
"""
import os
import sys
import json
import subprocess
from typing import Dict, Any, List, Optional, Union, TypedDict

print(f"Python path: {sys.path}")
print(f"Python executable: {sys.executable}")
# Import MCP SDK
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP
mcp = FastMCP("Gatherings")

# Get Python script path from environment or use default
PYTHON_PATH = os.environ.get("GATHERINGS_SCRIPT", os.path.join(os.getcwd(), "gatherings.py"))

# Error handling
def error_handler(error):
    print(f"[MCP Error] {error}", file=sys.stderr)

mcp.onerror = error_handler

def run_command(cmd_args):
    """Execute a command and return the result"""
    try:
        command = ["python", PYTHON_PATH, "--json"] + cmd_args
        
        # Execute the command
        env = os.environ.copy()
        env["GATHERINGS_DB_PATH"] = os.environ.get("GATHERINGS_DB_PATH", "gatherings.db")
        
        process = subprocess.run(
            command,
            env=env,
            capture_output=True,
            text=True
        )
        
        if process.stderr:
            print(f"[Command Error] {process.stderr}", file=sys.stderr)
        
        try:
            result = json.loads(process.stdout)
            return result
        except json.JSONDecodeError:
            # If output is not valid JSON, return it as text
            return {
                "success": False,
                "error": "Invalid JSON response",
                "output": process.stdout
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Define create_gathering handler
@mcp.tool()
def create_gathering(gathering_id: str, members: int):
    """Create a new gathering"""
    return run_command(["create", gathering_id, "--members", str(int(members))])

# Define add_expense handler
@mcp.tool()
def add_expense(gathering_id: str, member_name: str, amount: float):
    """Add an expense for a member"""
    return run_command(["add-expense", gathering_id, member_name, str(amount)])

# Define calculate_reimbursements handler
@mcp.tool()
def calculate_reimbursements(gathering_id: str):
    """Calculate reimbursements for a gathering"""
    return run_command(["calculate", gathering_id])

# Define record_payment handler
@mcp.tool()
def record_payment(gathering_id: str, member_name: str, amount: float):
    """Record a payment made by a member"""
    return run_command(["record-payment", gathering_id, member_name, str(amount)])

# Define rename_member handler
@mcp.tool()
def rename_member(gathering_id: str, old_name: str, new_name: str):
    """Rename an unnamed member"""
    return run_command(["rename-member", gathering_id, old_name, new_name])

# Define show_gathering handler
@mcp.tool()
def show_gathering(gathering_id: str):
    """Show details of a gathering"""
    return run_command(["show", gathering_id])

# Define list_gatherings handler
@mcp.tool()
def list_gatherings():
    """List all gatherings"""
    return run_command(["list"])

# Define close_gathering handler
@mcp.tool()
def close_gathering(gathering_id: str):
    """Close a gathering"""
    return run_command(["close", gathering_id])

# Define delete_gathering handler
@mcp.tool()
def delete_gathering(gathering_id: str, force: bool = False):
    """Delete a gathering"""
    cmd = ["delete", gathering_id]
    if force:
        cmd.append("--force")
    return run_command(cmd)

# Define add_member handler
@mcp.tool()
def add_member(gathering_id: str, member_name: str):
    """Add a new member to a gathering"""
    return run_command(["add-member", gathering_id, member_name])

# Define remove_member handler
@mcp.tool()
def remove_member(gathering_id: str, member_name: str):
    """Remove a member from a gathering"""
    return run_command(["remove-member", gathering_id, member_name])

if __name__ == "__main__":
    print("Gatherings MCP server running on stdio", file=sys.stderr)
    
    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        print("\nShutting down server...", file=sys.stderr)
