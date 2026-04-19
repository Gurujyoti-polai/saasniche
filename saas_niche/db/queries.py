"""Database queries notes."""

# Run this in the Supabase SQL editor before using the classifier if the column
# does not already exist:
#
# alter table raw_posts
# add column if not exists classified boolean default false;
#
# alter table raw_posts
# add column if not exists created_at timestamptz default now();
#
# create table if not exists scored_posts (
#   id          text primary key,
#   subreddit   text,
#   title       text,
#   body        text,
#   url         text,
#   upvotes     int,
#   category    text,
#   profession  text,
#   wtp_signal  text,
#   intensity   int,
#   score       float,
#   scored_at   timestamptz default now()
# );
#
# create table if not exists blueprints (
#   id               text primary key,
#   title            text,
#   category         text,
#   profession       text,
#   score            float,
#   target_audience  text,
#   problem_summary  text,
#   solution         text,
#   revenue_model    text,
#   pricing          text,
#   mvp_features     jsonb,
#   tech_complexity  text,
#   landing_copy     text,
#   generated_at     timestamptz default now()
# );
#
# alter table blueprints
#   add column if not exists market_size text,
#   add column if not exists competition text;


def run() -> None:
    """Placeholder queries entrypoint."""

    print("module not implemented yet")
