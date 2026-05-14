from pydantic import BaseModel
from typing import Optional
from datetime import date
from uuid import UUID


class ExpenseCreate(BaseModel):
    user_id: str
    title: str
    amount: float
    category: Optional[str] = None
    notes: Optional[str] = None
    expense_date: Optional[date] = None


class ExpenseUpdate(BaseModel):
    expense_id: UUID
    user_id: str
    title: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[str] = None
    notes: Optional[str] = None
    expense_date: Optional[date] = None