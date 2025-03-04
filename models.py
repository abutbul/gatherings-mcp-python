"""
Models for the Gatherings application using SQLAlchemy ORM.

This module defines the data models and database interactions for the Gatherings application.
"""

import enum
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any

from sqlalchemy import create_engine, Column, String, Integer, Float, ForeignKey, Enum, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session, scoped_session

Base = declarative_base()


class GatheringStatus(enum.Enum):
    """Status of a gathering."""
    OPEN = "open"
    CLOSED = "closed"


class Gathering(Base):
    """SQLAlchemy model for gatherings table."""
    __tablename__ = 'gatherings'
    
    id = Column(String, primary_key=True)
    total_members = Column(Integer, nullable=False)
    status = Column(Enum(GatheringStatus), nullable=False, default=GatheringStatus.OPEN)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    members = relationship("Member", back_populates="gathering", cascade="all, delete-orphan")
    
    @property
    def expense_per_member(self) -> float:
        """Calculate the expense per member."""
        if self.total_members == 0:
            return 0.0
        
        total_expenses = sum(sum(expense.amount for expense in member.expenses) for member in self.members)
        return total_expenses / self.total_members
    
    @property
    def total_expenses(self) -> float:
        """Calculate total expenses for the gathering."""
        return sum(sum(expense.amount for expense in member.expenses) for member in self.members)
    
    @property
    def total_payments(self) -> float:
        """Calculate total payments for the gathering."""
        return sum(sum(payment.amount for payment in member.payments) for member in self.members)


class Member(Base):
    """SQLAlchemy model for members table."""
    __tablename__ = 'members'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    gathering_id = Column(String, ForeignKey('gatherings.id'), nullable=False)
    
    # Relationships
    gathering = relationship("Gathering", back_populates="members")
    expenses = relationship("Expense", back_populates="member", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="member", cascade="all, delete-orphan")
    
    @property
    def total_expenses(self) -> float:
        """Calculate total expenses for this member."""
        return sum(expense.amount for expense in self.expenses)
    
    @property
    def total_payments(self) -> float:
        """Calculate total payments for this member."""
        return sum(payment.amount for payment in self.payments)
    
    @property
    def balance(self) -> float:
        """
        Calculate the member's balance.
        Positive balance means they are owed money (they paid more than their share).
        Negative balance means they owe money (they paid less than their share).
        """
        expense_per_member = self.gathering.expense_per_member
        # Balance = what they paid (expenses + payments) - what they should pay (share)
        # If positive, they paid more than their share and are owed money
        # If negative, they paid less than their share and owe money
        return self.total_expenses + self.total_payments - expense_per_member
    
    @property
    def status(self) -> str:
        """Get the member's payment status."""
        if abs(self.balance) < 0.01:  # Using a small epsilon to handle floating-point errors
            return "settled"
        elif self.balance > 0:
            return "is owed money"  # Changed from "paid"
        else:
            return "owes money"


class Expense(Base):
    """SQLAlchemy model for expenses table."""
    __tablename__ = 'expenses'
    
    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey('members.id'), nullable=False)
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    member = relationship("Member", back_populates="expenses")


class Payment(Base):
    """SQLAlchemy model for payments table."""
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey('members.id'), nullable=False)
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    member = relationship("Member", back_populates="payments")


class DatabaseManager:
    """Database manager using SQLAlchemy."""
    
    def __init__(self, db_path: str = "gatherings.db"):
        """Initialize the DatabaseManager with the specified database path."""
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}')
        
        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)
        
        # Create a session factory with expire_on_commit=False to avoid detached instance issues
        session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.Session = scoped_session(session_factory)
    
    def create_gathering(self, gathering_id: str, total_members: int) -> Gathering:
        """
        Create a new gathering.
        
        Args:
            gathering_id: A unique ID for the gathering (format: yyyy-mm-dd-type)
            total_members: The number of members in the gathering
            
        Returns:
            The created Gathering object
            
        Raises:
            ValueError: If the gathering ID is invalid or already exists
        """
        # Validate gathering_id format
        try:
            date_part = "-".join(gathering_id.split("-")[:3])
            datetime.strptime(date_part, "%Y-%m-%d")
        except (ValueError, IndexError):
            raise ValueError("Gathering ID must start with a valid date in format yyyy-mm-dd-type")
        
        session = self.Session()
        try:
            # Check if gathering already exists
            existing_gathering = session.query(Gathering).filter_by(id=gathering_id).first()
            if (existing_gathering):
                raise ValueError(f"Gathering with ID '{gathering_id}' already exists")
            
            # Create the gathering
            gathering = Gathering(
                id=gathering_id,
                total_members=total_members,
                status=GatheringStatus.OPEN
            )
            session.add(gathering)
            
            # Create unnamed members
            for i in range(1, total_members + 1):
                member_name = f"member{i:04d}"
                member = Member(name=member_name, gathering_id=gathering_id)
                session.add(member)
            
            session.commit()
            
            # Create a new session to fetch the complete gathering with all relationships
            return self.get_gathering(gathering_id)
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def add_member(self, gathering_id: str, member_name: str) -> Member:
        """
        Add a member to a gathering.
        
        Args:
            gathering_id: The ID of the gathering
            member_name: The name of the member
            
        Returns:
            The created Member object
            
        Raises:
            ValueError: If the gathering doesn't exist or is closed, or the member already exists
        """
        session = self.Session()
        try:
            # Get the gathering
            gathering = session.query(Gathering).filter_by(id=gathering_id).first()
            if not gathering:
                raise ValueError(f"Gathering '{gathering_id}' not found")
            
            # Check if gathering is open
            if gathering.status == GatheringStatus.CLOSED:
                raise ValueError(f"Cannot add member to closed gathering '{gathering_id}'")
            
            # Check if member already exists
            existing_member = session.query(Member).filter_by(gathering_id=gathering_id, name=member_name).first()
            if existing_member:
                raise ValueError(f"Member '{member_name}' already exists in gathering '{gathering_id}'")
            
            # Create the member
            member = Member(name=member_name, gathering_id=gathering_id)
            session.add(member)
            
            # Update the total members count
            gathering.total_members += 1
            
            session.commit()
            return member
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def remove_member(self, gathering_id: str, member_name: str) -> None:
        """
        Remove a member from a gathering.
        
        Args:
            gathering_id: The ID of the gathering
            member_name: The name of the member
            
        Raises:
            ValueError: If the gathering is closed, the member doesn't exist, 
                        or the member has expenses/payments
        """
        session = self.Session()
        try:
            # Get the gathering
            gathering = session.query(Gathering).filter_by(id=gathering_id).first()
            if not gathering:
                raise ValueError(f"Gathering '{gathering_id}' not found")
            
            # Check if gathering is open
            if gathering.status == GatheringStatus.CLOSED:
                raise ValueError(f"Cannot remove member from closed gathering '{gathering_id}'")
            
            # Get the member to remove
            member = session.query(Member).filter_by(gathering_id=gathering_id, name=member_name).first()
            if not member:
                raise ValueError(f"Member '{member_name}' not found in gathering '{gathering_id}'")
            
            # Check if member has expenses
            expenses_count = session.query(Expense).filter_by(member_id=member.id).count()
            if expenses_count > 0:
                raise ValueError(f"Cannot remove member '{member_name}' who has recorded expenses")
            
            # Check if member has payments
            payments_count = session.query(Payment).filter_by(member_id=member.id).count()
            if payments_count > 0:
                raise ValueError(f"Cannot remove member '{member_name}' who has recorded payments")
            
            # Delete the member
            session.delete(member)
            
            # Update the total members count
            gathering.total_members -= 1
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_gathering(self, gathering_id: str) -> Optional[Gathering]:
        """
        Get a gathering by ID.
        
        Args:
            gathering_id: The ID of the gathering
            
        Returns:
            The Gathering object, or None if not found
        """
        session = self.Session()
        try:
            # Get gathering with eager loading of all relationships to avoid detached session issues
            from sqlalchemy.orm import joinedload
            
            gathering = (
                session.query(Gathering)
                .options(
                    joinedload(Gathering.members)
                    .joinedload(Member.expenses),
                    joinedload(Gathering.members)
                    .joinedload(Member.payments)
                )
                .filter_by(id=gathering_id)
                .first()
            )
            
            if gathering:
                # Ensure all attributes are loaded before detaching
                _ = gathering.id
                _ = gathering.total_members
                _ = gathering.status
                _ = gathering.total_expenses
                _ = gathering.total_payments
                
                # Load all member attributes
                for member in gathering.members:
                    _ = member.id
                    _ = member.name
                    _ = member.total_expenses
                    _ = member.total_payments
                    _ = member.balance
                    _ = member.status
            
            return gathering
        finally:
            session.close()
    
    def add_expense(self, gathering_id: str, member_name: str, amount: float) -> Tuple[Gathering, Member]:
        """
        Add an expense for a member.
        
        Args:
            gathering_id: The ID of the gathering
            member_name: The name of the member
            amount: The expense amount (positive number)
            
        Returns:
            Tuple of (updated Gathering, Member who paid)
            
        Raises:
            ValueError: If the gathering is closed, the member doesn't exist, or the amount is invalid
        """
        if amount <= 0:
            raise ValueError("Expense amount must be positive")
        
        session = self.Session()
        try:
            # Get the gathering
            gathering = session.query(Gathering).filter_by(id=gathering_id).first()
            if not gathering:
                raise ValueError(f"Gathering '{gathering_id}' not found")
            
            # Check if gathering is open
            if gathering.status == GatheringStatus.CLOSED:
                raise ValueError(f"Cannot add expense to closed gathering '{gathering_id}'")
            
            # Get the member
            member = session.query(Member).filter_by(gathering_id=gathering_id, name=member_name).first()
            if not member:
                # If member name doesn't exist, check if we need to rename an existing member
                # Get available unnamed members
                unnamed_members = session.query(Member).filter(
                    Member.gathering_id == gathering_id,
                    Member.name.like("member%")
                ).all()
                
                if not unnamed_members:
                    raise ValueError(f"Member '{member_name}' not found in gathering '{gathering_id}'")
                
                # Use the first available unnamed member and rename it
                member = unnamed_members[0]
                member.name = member_name
            
            # Add the expense
            expense = Expense(member_id=member.id, amount=amount)
            session.add(expense)
            
            session.commit()
            
            # Get fresh copies of the gathering and member
            updated_gathering = self.get_gathering(gathering_id)
            
            # Find the member in the updated gathering
            updated_member = None
            for m in updated_gathering.members:
                if m.name == member_name:
                    updated_member = m
                    break
                    
            if not updated_member:
                raise ValueError(f"Cannot find member '{member_name}' after adding expense")
                
            return updated_gathering, updated_member
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
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
        session = self.Session()
        try:
            # Get the gathering
            gathering = session.query(Gathering).filter_by(id=gathering_id).first()
            if not gathering:
                raise ValueError(f"Gathering '{gathering_id}' not found")
            
            # Check if gathering is open
            if gathering.status == GatheringStatus.CLOSED:
                raise ValueError(f"Cannot record payment to closed gathering '{gathering_id}'")
            
            # Get the member
            member = session.query(Member).filter_by(gathering_id=gathering_id, name=member_name).first()
            if not member:
                raise ValueError(f"Member '{member_name}' not found in gathering '{gathering_id}'")
            
            # Add the payment
            payment = Payment(member_id=member.id, amount=amount)
            session.add(payment)
            
            session.commit()
            
            # Get fresh copies of the gathering and member
            updated_gathering = self.get_gathering(gathering_id)
            
            # Find the member in the updated gathering
            updated_member = None
            for m in updated_gathering.members:
                if m.name == member_name:
                    updated_member = m
                    break
                    
            if not updated_member:
                raise ValueError(f"Cannot find member '{member_name}' after recording payment")
                
            return updated_gathering, updated_member
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
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
        session = self.Session()
        try:
            # Get the gathering
            gathering = session.query(Gathering).filter_by(id=gathering_id).first()
            if not gathering:
                raise ValueError(f"Gathering '{gathering_id}' not found")
            
            # Check if gathering is open
            if gathering.status == GatheringStatus.CLOSED:
                raise ValueError(f"Cannot rename member in closed gathering '{gathering_id}'")
            
            # Get the member to rename
            member = session.query(Member).filter_by(gathering_id=gathering_id, name=old_name).first()
            if not member:
                raise ValueError(f"Member '{old_name}' not found in gathering '{gathering_id}'")
            
            # Check if new name already exists
            existing_member = session.query(Member).filter_by(gathering_id=gathering_id, name=new_name).first()
            if existing_member:
                raise ValueError(f"Member '{new_name}' already exists in gathering '{gathering_id}'")
            
            # Update the member name
            member.name = new_name
            
            session.commit()
            
            # Get a fresh copy of the gathering
            updated_gathering = self.get_gathering(gathering_id)
            
            # Find the member in the updated gathering
            for m in updated_gathering.members:
                if m.name == new_name:
                    return m
                    
            raise ValueError(f"Cannot find member '{new_name}' after renaming")
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
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
        session = self.Session()
        try:
            # Get the gathering
            gathering = session.query(Gathering).filter_by(id=gathering_id).first()
            if not gathering:
                raise ValueError(f"Gathering '{gathering_id}' not found")
            
            # Check if already closed
            if gathering.status == GatheringStatus.CLOSED:
                raise ValueError(f"Gathering '{gathering_id}' is already closed")
            
            # Close the gathering
            gathering.status = GatheringStatus.CLOSED
            
            session.commit()
            
            # Return a fresh copy of the gathering
            return self.get_gathering(gathering_id)
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def delete_gathering(self, gathering_id: str, force: bool = False) -> None:
        """
        Delete a gathering and all related data.
        
        Args:
            gathering_id: The ID of the gathering
            force: If True, delete even if the gathering is closed
            
        Raises:
            ValueError: If the gathering doesn't exist or is closed and force is False
        """
        session = self.Session()
        try:
            # Get the gathering
            gathering = session.query(Gathering).filter_by(id=gathering_id).first()
            if not gathering:
                raise ValueError(f"Gathering '{gathering_id}' not found")
            
            # Check if closed and not forced
            if gathering.status == GatheringStatus.CLOSED and not force:
                raise ValueError(f"Cannot delete closed gathering '{gathering_id}'. Use --force to override.")
            
            # Delete the gathering (cascading delete will handle members, expenses, and payments)
            session.delete(gathering)
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def list_gatherings(self) -> List[Gathering]:
        """
        List all gatherings.
        
        Returns:
            A list of all Gathering objects
        """
        session = self.Session()
        try:
            # Get all gatherings
            gatherings = session.query(Gathering).all()
            return gatherings
        finally:
            session.close()
