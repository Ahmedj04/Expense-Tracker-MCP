create extension if not exists "uuid-ossp";

create table expenses (
    id uuid primary key default uuid_generate_v4(),
    user_id text not null,
    title text not null,
    amount numeric not null,
    category text,
    notes text,
    expense_date date not null default current_date,
    created_at timestamptz default now()
);

create index if not exists idx_expenses_user_id
on expenses(user_id);

create index if not exists idx_expenses_expense_date
on expenses(expense_date);