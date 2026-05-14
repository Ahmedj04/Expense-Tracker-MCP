from fastmcp import FastMCP
from fastmcp.server.lifespan import lifespan
from datetime import date
from typing import Optional
from uuid import UUID

from db import init_db, close_db, fetch, fetchrow, execute
from models import ExpenseCreate, ExpenseUpdate



@lifespan
async def app_lifespan(app):
    await init_db()
    try:
        yield("db ready")
    finally:
        await close_db()


mcp = FastMCP("Expense Tracker MCP", lifespan=app_lifespan)


@mcp.tool
async def add_expense(
    user_id: str,
    title: str,
    amount: float,
    category: Optional[str] = None,
    notes: Optional[str] = None,
    expense_date: Optional[date] = None,
):
    """
    Add a new expense for a user with optional category, notes, and expense date (YYYY-MM-DD).
    """

    query = """
    insert into expenses (
        user_id,
        title,
        amount,
        category,
        notes,
        expense_date
    )
    values ($1, $2, $3, $4, $5, $6)
    returning *
    """

    row = await fetchrow(
        query,
        user_id,
        title,
        amount,
        category,
        notes,
        expense_date or date.today(),
    )

    return {
        "message": "Expense added successfully",
        "expense": dict(row)
    }

@mcp.tool
async def list_expenses(
    user_id: str,
    limit: int = 20,
    category: Optional[str] = None,
):
    """
    Retrieve a user's expenses with optional category filtering and result limit.
    """

    if category:
        query = """
        select *
        from expenses
        where user_id = $1
        and category = $2
        order by expense_date desc
        limit $3
        """

        rows = await fetch(query, user_id, category, limit)

    else:
        query = """
        select *
        from expenses
        where user_id = $1
        order by expense_date desc
        limit $2
        """

        rows = await fetch(query, user_id, limit)

    return {
        "count": len(rows),
        "expenses": [dict(row) for row in rows]
    }

@mcp.tool
async def edit_expense(
    expense_id: str,
    user_id: str,
    title: Optional[str] = None,
    amount: Optional[float] = None,
    category: Optional[str] = None,
    notes: Optional[str] = None,
    expense_date: Optional[date] = None,
):
    """
    Update an existing expense by expense ID. Only provided fields will be changed.
    """

    existing = await fetchrow(
        """
        select *
        from expenses
        where id = $1
        and user_id = $2
        """,
        expense_id,
        user_id,
    )

    if not existing:
        return {
            "error": "Expense not found"
        }

    query = """
    update expenses
    set
        title = coalesce($1, title),
        amount = coalesce($2, amount),
        category = coalesce($3, category),
        notes = coalesce($4, notes),
        expense_date = coalesce($5, expense_date)
    where id = $6
    and user_id = $7
    returning *
    """

    updated = await fetchrow(
        query,
        title,
        amount,
        category,
        notes,
        expense_date,
        expense_id,
        user_id,
    )

    return {
        "message": "Expense updated successfully",
        "expense": dict(updated)
    }

@mcp.tool
async def delete_expense(
    expense_id: str,
    user_id: str,
):
    """
    Delete a user's expense using the expense ID.
    """

    result = await execute(
        """
        delete from expenses
        where id = $1
        and user_id = $2
        """,
        expense_id,
        user_id,
    )

    return {
        "message": "Expense deleted successfully",
        "result": result
    }

@mcp.tool
async def summarize_expenses(
    user_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    """
    Generate an expense summary with total spending and category breakdown for an optional date range.
    """

    query = """
    select
        category,
        sum(amount) as total
    from expenses
    where user_id = $1
    and ($2::date is null or expense_date >= $2)
    and ($3::date is null or expense_date <= $3)
    group by category
    order by total desc
    """

    rows = await fetch(
        query,
        user_id,
        start_date,
        end_date,
    )

    total_query = """
    select sum(amount) as grand_total
    from expenses
    where user_id = $1
    and ($2::date is null or expense_date >= $2)
    and ($3::date is null or expense_date <= $3)
    """

    total_row = await fetchrow(
        total_query,
        user_id,
        start_date,
        end_date,
    )

    return {
        "total_spent": float(total_row["grand_total"] or 0),
        "by_category": [
            {
                "category": row["category"],
                "total": float(row["total"])
            }
            for row in rows
        ]
    }


if __name__ == "__main__":
    # mcp.run()
    mcp.run(transport= 'http', host='0.0.0.0', port=8000)