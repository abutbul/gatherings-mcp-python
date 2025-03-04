"""
Services for the Gatherings application.

This module provides high-level services for managing gatherings and their members.
"""

from typing import Dict, List, Tuple, Optional, Any
from models import DatabaseManager, Gathering, Member


class GatheringService:
    """Service for managing gatherings and their members."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize the GatheringService with a DatabaseManager."""
        self.db_manager = db_manager
    
    def create_gathering(self, gathering_id: str, total_members: int) -> Gathering:
        """Creates a new gathering with the specified number of members."""
        gathering = self.db_manager.create_gathering(gathering_id, total_members)
        
        return gathering
    
    def get_gathering(self, gathering_id: str) -> Optional[Gathering]:
        """
        Get a gathering by ID.
        
        Args:
            gathering_id: The ID of the gathering
            
        Returns:
            The Gathering object, or None if not found
        """
        return self.db_manager.get_gathering(gathering_id)
    
    def add_expense(self, gathering_id: str, member_name: str, amount: float) -> Tuple[Gathering, Member]:
        """
        Add an expense for a member in a gathering.
        
        Args:
            gathering_id: The ID of the gathering
            member_name: The name of the member (can be auto-generated)
            amount: The expense amount (positive number)
            
        Returns:
            Tuple of (updated Gathering, Member who paid)
            
        Raises:
            ValueError: If the gathering is closed, the member doesn't exist, or the amount is invalid
        """
        return self.db_manager.add_expense(gathering_id, member_name, amount)
    
    def calculate_reimbursements(self, gathering_id: str) -> Dict[str, float]:
        """
        Calculate reimbursements for a gathering.
        
        Args:
            gathering_id: The ID of the gathering
            
        Returns:
            A dictionary mapping member names to reimbursement amounts
            (negative values mean the member gets reimbursed, positive values mean they owe money)
            
        Raises:
            ValueError: If the gathering doesn't exist
        """
        gathering = self.get_gathering(gathering_id)
        if not gathering:
            raise ValueError(f"Gathering '{gathering_id}' not found")
        
        # Calculate how much each member has paid and should pay
        expense_per_member = gathering.expense_per_member
        
        # Calculate reimbursements
        reimbursements = {}
        for member in gathering.members:
            # Amount to pay = total share - expenses + payments
            # If negative, member gets reimbursed; if positive, member owes money
            to_pay = expense_per_member - member.total_expenses + member.total_payments
            reimbursements[member.name] = to_pay
        
        return reimbursements
    
    def record_payment(self, gathering_id: str, member_name: str, amount: float) -> Tuple[Gathering, Member]:
        """
        Record a payment made by a member.
        
        Args:
            gathering_id: The ID of the gathering
            member_name: The name of the member
            amount: The payment amount (positive for payments, negative for reimbursements)
            
        Returns:
            Tuple of (updated Gathering, Member who paid/received)
            
        Raises:
            ValueError: If the gathering is closed, the member doesn't exist, or the payment is invalid
        """
        return self.db_manager.record_payment(gathering_id, member_name, amount)
    
    def rename_member(self, gathering_id: str, old_name: str, new_name: str) -> Member:
        """
        Rename a member in a gathering.
        
        Args:
            gathering_id: The ID of the gathering
            old_name: The current name of the member
            new_name: The new name for the member
            
        Returns:
            The updated Member object
            
        Raises:
            ValueError: If the gathering is closed, the member doesn't exist, or the new name is already taken
        """
        return self.db_manager.rename_member(gathering_id, old_name, new_name)
    
    def close_gathering(self, gathering_id: str) -> Gathering:
        """
        Close a gathering.
        
        Args:
            gathering_id: The ID of the gathering
            
        Returns:
            The updated Gathering object
            
        Raises:
            ValueError: If the gathering doesn't exist or is already closed
        """
        return self.db_manager.close_gathering(gathering_id)
    
    def delete_gathering(self, gathering_id: str, force: bool = False) -> None:
        """
        Delete a gathering and all related data.
        
        Args:
            gathering_id: The ID of the gathering
            force: If True, delete even if the gathering is closed
            
        Raises:
            ValueError: If the gathering doesn't exist or is closed and force is False
        """
        return self.db_manager.delete_gathering(gathering_id, force)
    
    def list_gatherings(self) -> List[Gathering]:
        """
        List all gatherings.
        
        Returns:
            A list of all Gathering objects
        """
        return self.db_manager.list_gatherings()
    
    def get_payment_summary(self, gathering_id: str) -> Dict[str, Any]:
        """
        Get a detailed payment summary for a gathering.
        
        Args:
            gathering_id: The ID of the gathering
            
        Returns:
            A dictionary with summary information:
            {
                'total_expenses': float,
                'expense_per_member': float,
                'members': {
                    'member1': {
                        'expenses': float,
                        'paid': float,
                        'balance': float,
                        'status': str
                    },
                    ...
                }
            }
            
        Raises:
            ValueError: If the gathering doesn't exist
        """
        gathering = self.get_gathering(gathering_id)
        if not gathering:
            raise ValueError(f"Gathering '{gathering_id}' not found")
        
        summary = {
            'total_expenses': gathering.total_expenses,
            'expense_per_member': gathering.expense_per_member,
            'members': {}
        }
        
        for member in gathering.members:
            summary['members'][member.name] = {
                'expenses': member.total_expenses,
                'paid': member.total_payments,
                'balance': member.balance,
                'status': member.status
            }
        
        return summary
    
    def add_member(self, gathering_id: str, member_name: str) -> Tuple[Gathering, Member]:
        """
        Add a new member to an existing gathering.
        
        Args:
            gathering_id: The ID of the gathering
            member_name: The name of the member to add
            
        Returns:
            Tuple of (updated Gathering, added Member)
            
        Raises:
            ValueError: If the gathering is closed, doesn't exist, or member already exists
        """
        member = self.db_manager.add_member(gathering_id, member_name)
        gathering = self.get_gathering(gathering_id)
        return gathering, member
    
    def remove_member(self, gathering_id: str, member_name: str) -> Gathering:
        """
        Remove a member from a gathering.
        
        Args:
            gathering_id: The ID of the gathering
            member_name: The name of the member to remove
            
        Returns:
            The updated Gathering object
            
        Raises:
            ValueError: If the gathering is closed, doesn't exist, the member doesn't exist,
                       or the member has expenses/payments
        """
        self.db_manager.remove_member(gathering_id, member_name)
        return self.get_gathering(gathering_id)
