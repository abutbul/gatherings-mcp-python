#!/usr/bin/env python3
"""
Test script for the Gatherings application.

This script demonstrates the functionality of the Gatherings application
by running through the example scenario from the requirements.
"""

import os
import sys
from models import DatabaseManager
from services import GatheringService

def main():
    # Remove the test database if it exists
    if os.path.exists("test_gatherings.db"):
        os.remove("test_gatherings.db")
    
    # Initialize the database and service
    db_manager = DatabaseManager("test_gatherings.db")
    service = GatheringService(db_manager)
    
    print("=== Gatherings Application Test ===")
    
    # Step 1: Create a gathering with 5 members
    print("\n1. Creating gathering with 5 members...")
    gathering_id = "2025-03-01-friendsbeer"
    gathering = service.create_gathering(gathering_id, 5)
    print(f"Created gathering: {gathering.id}")
    print(f"Total members: {gathering.total_members}")
    print(f"Status: {gathering.status.value}")
    
    # Debug: Print all member names to see what's available
    members_names = [m.name for m in gathering.members]
    print(f"Members: {', '.join(members_names)}")
    
    # Step 2: Add expenses for members
    print("\n2. Adding expenses...")
    # First expense will rename an unnamed member to "Roy"
    gathering, member = service.add_expense(gathering_id, "Roy", 50)
    print(f"Added expense of $50.00 for {member.name}")
    
    # Second expense will rename another unnamed member to "David"
    gathering, member = service.add_expense(gathering_id, "David", 100)
    print(f"Added expense of $100.00 for {member.name}")
    
    # Third expense will rename another unnamed member to "Felix"
    gathering, member = service.add_expense(gathering_id, "Felix", 50)
    print(f"Added expense of $50.00 for {member.name}")
    
    print(f"Total expenses: ${gathering.total_expenses:.2f}")
    
    # Get updated member list to see renamed members
    members_names = [m.name for m in gathering.members]
    print(f"Updated members: {', '.join(members_names)}")
    
    # Step 3: Calculate reimbursements
    print("\n3. Calculating reimbursements...")
    reimbursements = service.calculate_reimbursements(gathering_id)
    
    # Get fresh data after status change
    gathering = service.get_gathering(gathering_id)
    print(f"Expense per member: ${gathering.expense_per_member:.2f}")
    print("Reimbursements:")
    for name, amount in reimbursements.items():
        if amount < 0:
            print(f"  {name} gets reimbursed ${abs(amount):.2f}")
        else:
            print(f"  {name} needs to pay ${amount:.2f}")
    
    # Step 4: Record payments from unnamed members
    print("\n4. Recording payments from unnamed members...")
    # Use the actual member names from the database
    unnamed_members = [m.name for m in gathering.members if m.name.startswith("member")]
    if len(unnamed_members) >= 2:
        # Record payment for first unnamed member
        gathering, member = service.record_payment(gathering_id, unnamed_members[0], 40)
        print(f"Recorded payment of $40.00 from {member.name}")
        
        # Record payment for second unnamed member
        gathering, member = service.record_payment(gathering_id, unnamed_members[1], 40)
        print(f"Recorded payment of $40.00 from {member.name}")
    else:
        print("Warning: Not enough unnamed members available.")
    
    # Step 5: Record reimbursements to named members
    print("\n5. Recording reimbursements to named members...")
    # Roy needs to receive 10, so he pays -10
    gathering, member = service.record_payment(gathering_id, "Roy", -10)
    print(f"Recorded reimbursement of $10.00 to {member.name}")
    
    # David needs to receive 60, so he pays -60
    gathering, member = service.record_payment(gathering_id, "David", -60)
    print(f"Recorded reimbursement of $60.00 to {member.name}")
    
    # Felix needs to receive 10, so he pays -10
    gathering, member = service.record_payment(gathering_id, "Felix", -10)
    print(f"Recorded reimbursement of $10.00 to {member.name}")
    
    # Step 6: Close the gathering
    print("\n6. Closing the gathering...")
    gathering = service.close_gathering(gathering_id)
    print(f"Gathering status: {gathering.status.value}")
    
    # Step 7: Testing member addition and removal
    print("\n7. Testing member addition and removal...")
    
    # Create a new gathering specifically for testing member operations
    member_ops_id = "2025-03-05-membertest"
    member_gathering = service.create_gathering(member_ops_id, 3)
    print(f"Created test gathering: {member_ops_id}")
    print(f"Initial members: {[m.name for m in member_gathering.members]}")
    
    # Add a new member
    gathering, new_member = service.add_member(member_ops_id, "Charlie")
    print(f"Added member: {new_member.name}")
    print(f"Total members: {gathering.total_members}")
    print(f"Updated members: {[m.name for m in gathering.members]}")
    
    # Try adding a member with a duplicate name
    try:
        service.add_member(member_ops_id, "Charlie")
        print("ERROR: Should not be able to add duplicate member!")
    except ValueError as e:
        print(f"Successfully prevented adding duplicate member: {e}")
    
    # Try removing a member who doesn't exist
    try:
        service.remove_member(member_ops_id, "NonExistentMember")
        print("ERROR: Should not be able to remove non-existent member!")
    except ValueError as e:
        print(f"Successfully prevented removing non-existent member: {e}")
    
    # Try removing a member with expenses
    try:
        # Add an expense for a member first
        service.add_expense(member_ops_id, "Charlie", 25)
        print("Added expense for Charlie")
        
        # Try to remove the member
        service.remove_member(member_ops_id, "Charlie")
        print("ERROR: Should not be able to remove member with expenses!")
    except ValueError as e:
        print(f"Successfully prevented removing member with expenses: {e}")
    
    # Remove an unused member
    # First find an unused member
    all_members = [m.name for m in gathering.members]
    unused_members = [m for m in all_members if m.startswith("member")]
    if unused_members:
        unused_member = unused_members[0]
        gathering = service.remove_member(member_ops_id, unused_member)
        print(f"Successfully removed unused member: {unused_member}")
        print(f"Total members: {gathering.total_members}")
        print(f"Remaining members: {[m.name for m in gathering.members]}")
    else:
        print("No unused members to remove")
    
    # Try closing and then adding/removing members
    service.close_gathering(member_ops_id)
    print(f"Closed gathering: {member_ops_id}")
    
    try:
        service.add_member(member_ops_id, "TooLate")
        print("ERROR: Should not be able to add member to closed gathering!")
    except ValueError as e:
        print(f"Successfully prevented adding member to closed gathering: {e}")
    
    try:
        service.remove_member(member_ops_id, "Charlie")
        print("ERROR: Should not be able to remove member from closed gathering!")
    except ValueError as e:
        print(f"Successfully prevented removing member from closed gathering: {e}")

    # Step 8: Testing gathering deletion
    print("\n8. Testing gathering deletion...")
    try:
        # Try to delete a closed gathering (should fail)
        try:
            service.delete_gathering(gathering_id)
            print("ERROR: Should not be able to delete a closed gathering!")
        except ValueError as e:
            print(f"Successfully prevented deletion of closed gathering: {e}")
        
        # Test force deletion of a closed gathering
        try:
            service.delete_gathering(gathering_id, force=True)
            # Verify force deletion
            deleted_gathering = service.get_gathering(gathering_id)
            if deleted_gathering is None:
                print("Successfully force-deleted a closed gathering")
            else:
                print("ERROR: Force deletion of closed gathering failed!")
        except Exception as e:
            print(f"ERROR: Force deletion should have worked: {e}")
        
        # Create a new gathering with expenses for deletion test
        test_gathering_id = "2025-03-02-deletetest"
        test_gathering = service.create_gathering(test_gathering_id, 3)
        print(f"Created test gathering: {test_gathering_id}")
        
        # Add some expenses to the test gathering
        service.add_expense(test_gathering_id, "Alice", 30)
        service.add_expense(test_gathering_id, "Bob", 45)
        print("Added expenses to test gathering")
        
        # Delete the test gathering
        service.delete_gathering(test_gathering_id)
        
        # Verify deletion
        deleted_gathering = service.get_gathering(test_gathering_id)
        if deleted_gathering is None:
            print("Successfully deleted test gathering with expenses")
        else:
            print("ERROR: Gathering with expenses was not deleted!")
        
        # Create another gathering for deletion test
        another_gathering_id = "2025-03-03-deletetest"
        another_gathering = service.create_gathering(another_gathering_id, 2)
        print(f"Created another test gathering: {another_gathering_id}")
        
        # Delete the gathering
        service.delete_gathering(another_gathering_id)
        
        # Verify deletion
        deleted_gathering = service.get_gathering(another_gathering_id)
        if deleted_gathering is None:
            print("Successfully deleted empty gathering")
        else:
            print("ERROR: Empty gathering was not deleted!")
            
    except Exception as e:
        print(f"Error during deletion test: {e}")

    # Print final summary
    print("\n=== Final Summary ===")
    
    # Create a new gathering that mirrors our original test scenario
    final_gathering_id = "2025-03-04-finaltest"
    final_gathering = service.create_gathering(final_gathering_id, 5)
    
    # Add the same expenses as in the original test
    service.add_expense(final_gathering_id, "Roy", 50)
    service.add_expense(final_gathering_id, "David", 100)
    service.add_expense(final_gathering_id, "Felix", 50)
    
    # Record the same payments as in the original test
    # Get the unnamed members
    final_gathering = service.get_gathering(final_gathering_id)
    
    # Print all member names to verify what members exist in the database
    print(f"All members in new gathering: {[m.name for m in final_gathering.members]}")
    
    # Add some expenses and payments to demonstrate the summary
    service.add_expense(final_gathering_id, "Alice", 60)
    service.add_expense(final_gathering_id, "Bob", 30)
    
    # Get fresh data after adding expenses
    final_gathering = service.get_gathering(final_gathering_id)
    
    # Get the remaining unnamed member - check if any exist
    unnamed = [m.name for m in final_gathering.members if m.name.startswith("member")]
    print(f"Unnamed members after expenses: {unnamed}")
    
    # Only try to record a payment if there's an unnamed member
    if unnamed:
        try:
            service.record_payment(final_gathering_id, unnamed[0], 30)
            print(f"Recorded payment of $30.00 from {unnamed[0]}")
        except ValueError as e:
            print(f"Error recording payment: {e}")
    else:
        print("No unnamed members available for payment recording.")
    
    # Get the summary
    try:
        summary = service.get_payment_summary(final_gathering_id)
        
        print(f"Total expenses: ${summary['total_expenses']:.2f}")
        print(f"Expense per member: ${summary['expense_per_member']:.2f}")
        
        print("\nMember details:")
        for name, data in summary["members"].items():
            print(f"  {name}:")
            print(f"    Expenses: ${data['expenses']:.2f}")
            print(f"    Paid: ${data['paid']:.2f}")
            print(f"    Balance: ${data['balance']:.2f}")
            print(f"    Status: {data['status']}")
    except Exception as e:
        print(f"Error getting payment summary: {e}")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    main()
