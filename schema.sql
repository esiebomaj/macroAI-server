-- =============================================
-- Macro Tracker — Supabase Schema (v2)
-- Uses Supabase Auth — no custom users table
-- Run this in your Supabase SQL editor
-- =============================================

-- Goals per user
create table if not exists goals (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade not null,
  cal integer not null default 2000,
  pro numeric not null default 160,
  carb numeric not null default 180,
  fat numeric not null default 71,
  weight numeric,
  goal_weight numeric,
  updated_at timestamptz default now(),
  unique(user_id)
);

-- Food library per user
create table if not exists food_library (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade not null,
  name text not null,
  cal numeric not null,
  pro numeric not null default 0,
  carb numeric not null default 0,
  fat numeric not null default 0,
  unit text not null default 'per serving',
  created_at timestamptz default now()
);

-- Daily food log
create table if not exists food_log (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade not null,
  name text not null,
  meal text not null check (meal in ('Breakfast', 'Lunch', 'Dinner', 'Snack')),
  cal numeric not null,
  pro numeric not null default 0,
  carb numeric not null default 0,
  fat numeric not null default 0,
  qty numeric not null default 1,
  log_date date not null default current_date,
  created_at timestamptz default now()
);

-- Indexes for fast lookups
create index if not exists idx_food_log_user_date on food_log(user_id, log_date);
create index if not exists idx_food_library_user on food_library(user_id);
create index if not exists idx_goals_user on goals(user_id);

-- =============================================
-- Row Level Security
-- Users can only read/write their own data
-- =============================================

alter table goals enable row level security;
alter table food_library enable row level security;
alter table food_log enable row level security;

-- Goals policies
create policy "Users can view own goals" on goals
  for select using (auth.uid() = user_id);

create policy "Users can insert own goals" on goals
  for insert with check (auth.uid() = user_id);

create policy "Users can update own goals" on goals
  for update using (auth.uid() = user_id);

-- Food library policies
create policy "Users can view own library" on food_library
  for select using (auth.uid() = user_id);

create policy "Users can insert into own library" on food_library
  for insert with check (auth.uid() = user_id);

create policy "Users can update own library" on food_library
  for update using (auth.uid() = user_id);

create policy "Users can delete from own library" on food_library
  for delete using (auth.uid() = user_id);

-- Food log policies
create policy "Users can view own log" on food_log
  for select using (auth.uid() = user_id);

create policy "Users can insert into own log" on food_log
  for insert with check (auth.uid() = user_id);

create policy "Users can delete from own log" on food_log
  for delete using (auth.uid() = user_id);
