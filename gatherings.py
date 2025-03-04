#!/usr/bin/env python3
"""
Gatherings - A command-line tool for managing friend gatherings and expense sharing.

This application helps track expenses and payments for social events, making it
easy to calculate reimbursements and settle balances between friends.
"""

import argparse
import sys
import os
import json
from models import DatabaseManager
from services import GatheringService

def setup_parser():
    """Set up the argument parser with all supported commands."""
    parser = argparse.ArgumentParser(description="Manage friend gatherings and expense sharing")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    subparsers = parser.add_subparsers(dest="command", help="Command to run", required=True)

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new gathering")
    create_parser.add_argument("gathering_id", help="Unique ID for the gathering (format: yyyy-mm-dd-type)")
    create_parser.add_argument("--members", "-m", type=int, required=True, help="Number of members in the gathering")

    # Add expense command
    expense_parser = subparsers.add_parser("add-expense", help="Add an expense for a member")
    expense_parser.add_argument("gathering_id", help="ID of the gathering")
    expense_parser.add_argument("member_name", help="Name of the member who paid")
    expense_parser.add_argument("amount", type=float, help="Amount paid by the member")

    # Calculate reimbursements command
    calculate_parser = subparsers.add_parser("calculate", help="Calculate reimbursements for a gathering")
    calculate_parser.add_argument("gathering_id", help="ID of the gathering")

    # Record payment command
    payment_parser = subparsers.add_parser("record-payment", help="Record a payment made by a member")
    payment_parser.add_argument("gathering_id", help="ID of the gathering")
    payment_parser.add_argument("member_name", help="Name of the member making the payment")
    payment_parser.add_argument("amount", type=float, help="Amount paid (negative for reimbursements)")

    # Rename member command
    rename_parser = subparsers.add_parser("rename-member", help="Rename an unnamed member")
    rename_parser.add_argument("gathering_id", help="ID of the gathering")
    rename_parser.add_argument("old_name", help="Current name of the member")
    rename_parser.add_argument("new_name", help="New name for the member")

    # Show gathering command
    show_parser = subparsers.add_parser("show", help="Show details of a gathering")
    show_parser.add_argument("gathering_id", help="ID of the gathering to display")

    # List gatherings command
    subparsers.add_parser("list", help="List all gatherings")

    # Close gathering command
    close_parser = subparsers.add_parser("close", help="Close a gathering")
    close_parser.add_argument("gathering_id", help="ID of the gathering to close")

    # Delete gathering command
    delete_parser = subparsers.add_parser("delete", help="Delete a gathering")
    delete_parser.add_argument("gathering_id", help="ID of the gathering to delete")
    delete_parser.add_argument("--force", "-f", action="store_true", help="Force deletion even if gathering is closed")

    # Add member command
    add_member_parser = subparsers.add_parser("add-member", help="Add a new member to a gathering")
    add_member_parser.add_argument("gathering_id", help="ID of the gathering")
    add_member_parser.add_argument("member_name", help="Name of the member to add")

    # Remove member command
    remove_member_parser = subparsers.add_parser("remove-member", help="Remove a member from a gathering")
    remove_member_parser.add_argument("gathering_id", help="ID of the gathering")
    remove_member_parser.add_argument("member_name", help="Name of the member to remove")

    return parser

def handle_create(service, args):
    """Handle the create command."""
    try:
        gathering = service.create_gathering(args.gathering_id, args.members)
        result = {
            "success": True,
            "gathering": {
                "id": gathering.id,
                "total_members": gathering.total_members,
                "status": gathering.status.value
            }
        }
        if args.json:
            print(json.dumps(result))
        else:
            print(f"Created gathering: {gathering.id}")
            print(f"Total members: {gathering.total_members}")
            print(f"Status: {gathering.status.value}")
        return True
    except ValueError as e:
        error = {"success": False, "error": str(e)}
        if args.json:
            print(json.dumps(error))
        else:
            print(f"Error: {e}")
        return False

def handle_add_expense(service, args):
    """Handle the add-expense command."""
    try:
        gathering, member = service.add_expense(args.gathering_id, args.member_name, args.amount)
        result = {
            "success": True,
            "expense": {
                "member": member.name,
                "amount": args.amount,
                "total_expenses": gathering.total_expenses
            }
        }
        if args.json:
            print(json.dumps(result))
        else:
            print(f"Added expense of ${args.amount:.2f} for {member.name}")
            print(f"Total expenses: ${gathering.total_expenses:.2f}")
        return True
    except ValueError as e:
        error = {"success": False, "error": str(e)}
        if args.json:
            print(json.dumps(error))
        else:
            print(f"Error: {e}")
        return False

def handle_calculate(service, args):
    """Handle the calculate command."""
    try:
        reimbursements = service.calculate_reimbursements(args.gathering_id)
        gathering = service.get_gathering(args.gathering_id)
        
        result = {
            "success": True,
            "calculation": {
                "total_expenses": gathering.total_expenses,
                "expense_per_member": gathering.expense_per_member,
                "reimbursements": {
                    name: {"amount": amount, "type": "gets_reimbursed" if amount < 0 else "needs_to_pay"}
                    for name, amount in reimbursements.items()
                }
            }
        }
        
        if args.json:
            print(json.dumps(result))
        else:
            print(f"Total expenses: ${gathering.total_expenses:.2f}")
            print(f"Expense per member: ${gathering.expense_per_member:.2f}")
            print("Reimbursements:")
            for name, amount in reimbursements.items():
                if amount < 0:
                    print(f"  {name} gets reimbursed ${abs(amount):.2f}")
                else:
                    print(f"  {name} needs to pay ${amount:.2f}")
        return True
    except ValueError as e:
        error = {"success": False, "error": str(e)}
        if args.json:
            print(json.dumps(error))
        else:
            print(f"Error: {e}")
        return False

def handle_record_payment(service, args):
    """Handle the record-payment command."""
    try:
        gathering, member = service.record_payment(args.gathering_id, args.member_name, args.amount)
        result = {
            "success": True,
            "payment": {
                "member": member.name,
                "amount": args.amount,
                "type": "reimbursement" if args.amount < 0 else "payment"
            }
        }
        if args.json:
            print(json.dumps(result))
        else:
            if args.amount < 0:
                print(f"Recorded reimbursement of ${abs(args.amount):.2f} to {member.name}")
            else:
                print(f"Recorded payment of ${args.amount:.2f} from {member.name}")
        return True
    except ValueError as e:
        error = {"success": False, "error": str(e)}
        if args.json:
            print(json.dumps(error))
        else:
            print(f"Error: {e}")
        return False

def handle_rename_member(service, args):
    """Handle the rename-member command."""
    try:
        member = service.rename_member(args.gathering_id, args.old_name, args.new_name)
        result = {
            "success": True,
            "member": {
                "old_name": args.old_name,
                "new_name": member.name
            }
        }
        if args.json:
            print(json.dumps(result))
        else:
            print(f"Renamed member from '{args.old_name}' to '{member.name}'")
        return True
    except ValueError as e:
        error = {"success": False, "error": str(e)}
        if args.json:
            print(json.dumps(error))
        else:
            print(f"Error: {e}")
        return False

def handle_show(service, args):
    """Handle the show command."""
    try:
        gathering = service.get_gathering(args.gathering_id)
        if gathering is None:
            error = {"success": False, "error": f"Gathering '{args.gathering_id}' not found"}
            if args.json:
                print(json.dumps(error))
            else:
                print(f"Gathering '{args.gathering_id}' not found")
            return False
        
        summary = service.get_payment_summary(args.gathering_id)
        result = {
            "success": True,
            "gathering": {
                "id": gathering.id,
                "status": gathering.status.value,
                "total_members": gathering.total_members,
                "total_expenses": summary["total_expenses"],
                "expense_per_member": summary["expense_per_member"],
                "members": summary["members"]
            }
        }
        
        if args.json:
            print(json.dumps(result))
        else:
            print(f"Gathering: {gathering.id}")
            print(f"Status: {gathering.status.value}")
            print(f"Total members: {gathering.total_members}")
            print(f"Total expenses: ${summary['total_expenses']:.2f}")
            print(f"Expense per member: ${summary['expense_per_member']:.2f}")
            
            print("\nMember details:")
            for name, data in summary["members"].items():
                print(f"  {name}:")
                print(f"    Expenses: ${data['expenses']:.2f}")
                print(f"    Paid: ${data['paid']:.2f}")
                print(f"    Balance: ${data['balance']:.2f}")
                print(f"    Status: {data['status']}")
        return True
    except ValueError as e:
        error = {"success": False, "error": str(e)}
        if args.json:
            print(json.dumps(error))
        else:
            print(f"Error: {e}")
        return False

def handle_list(service, args):
    """Handle the list command."""
    try:
        gatherings = service.list_gatherings()
        result = {
            "success": True,
            "gatherings": [
                {
                    "id": g.id,
                    "status": g.status.value
                }
                for g in gatherings
            ] if gatherings else []
        }
        
        if args.json:
            print(json.dumps(result))
        else:
            if not gatherings:
                print("No gatherings found")
            else:
                print(f"Found {len(gatherings)} gatherings:")
                for gathering in gatherings:
                    print(f"  {gathering.id} - Status: {gathering.status.value}")
        return True
    except ValueError as e:
        error = {"success": False, "error": str(e)}
        if args.json:
            print(json.dumps(error))
        else:
            print(f"Error: {e}")
        return False

def handle_close(service, args):
    """Handle the close command."""
    try:
        gathering = service.close_gathering(args.gathering_id)
        result = {
            "success": True,
            "gathering": {
                "id": gathering.id,
                "status": gathering.status.value
            }
        }
        if args.json:
            print(json.dumps(result))
        else:
            print(f"Closed gathering: {gathering.id}")
            print(f"Status: {gathering.status.value}")
        return True
    except ValueError as e:
        error = {"success": False, "error": str(e)}
        if args.json:
            print(json.dumps(error))
        else:
            print(f"Error: {e}")
        return False

def handle_delete(service, args):
    """Handle the delete command."""
    try:
        service.delete_gathering(args.gathering_id, args.force)
        result = {
            "success": True,
            "deleted": {
                "gathering_id": args.gathering_id,
                "forced": args.force
            }
        }
        if args.json:
            print(json.dumps(result))
        else:
            print(f"Deleted gathering: {args.gathering_id}")
        return True
    except ValueError as e:
        error = {"success": False, "error": str(e)}
        if args.json:
            print(json.dumps(error))
        else:
            print(f"Error: {e}")
        return False

def handle_add_member(service, args):
    """Handle the add-member command."""
    try:
        gathering, member = service.add_member(args.gathering_id, args.member_name)
        result = {
            "success": True,
            "member": {
                "name": member.name,
                "gathering_id": gathering.id,
                "total_members": gathering.total_members
            }
        }
        if args.json:
            print(json.dumps(result))
        else:
            print(f"Added member '{member.name}' to gathering '{gathering.id}'")
            print(f"Total members: {gathering.total_members}")
        return True
    except ValueError as e:
        error = {"success": False, "error": str(e)}
        if args.json:
            print(json.dumps(error))
        else:
            print(f"Error: {e}")
        return False

def handle_remove_member(service, args):
    """Handle the remove-member command."""
    try:
        gathering = service.remove_member(args.gathering_id, args.member_name)
        result = {
            "success": True,
            "removed": {
                "member_name": args.member_name,
                "gathering_id": gathering.id,
                "total_members": gathering.total_members
            }
        }
        if args.json:
            print(json.dumps(result))
        else:
            print(f"Removed member '{args.member_name}' from gathering '{gathering.id}'")
            print(f"Total members: {gathering.total_members}")
        return True
    except ValueError as e:
        error = {"success": False, "error": str(e)}
        if args.json:
            print(json.dumps(error))
        else:
            print(f"Error: {e}")
        return False

def main():
    """Main entry point for the Gatherings application."""
    parser = setup_parser()
    args = parser.parse_args()

    # Initialize the database manager and service
    db_path = os.environ.get("GATHERINGS_DB", "gatherings.db")
    db_manager = DatabaseManager(db_path)
    service = GatheringService(db_manager)
    
    # Route to the appropriate handler based on the command
    handlers = {
        "create": handle_create,
        "add-expense": handle_add_expense,
        "calculate": handle_calculate,
        "record-payment": handle_record_payment,
        "rename-member": handle_rename_member,
        "show": handle_show,
        "list": handle_list,
        "close": handle_close,
        "delete": handle_delete,
        "add-member": handle_add_member,
        "remove-member": handle_remove_member
    }
    
    handler = handlers.get(args.command)
    if handler:
        success = handler(service, args)
        sys.exit(0 if success else 1)
    else:
        print(f"Unknown command: {args.command}")
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
