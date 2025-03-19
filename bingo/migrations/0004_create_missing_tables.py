from django.db import migrations


class Migration(migrations.Migration):
    """
    Manual migration to create missing tables if they don't exist
    """
    dependencies = [
        ('bingo', '0003_initial_tables'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS bingo_event (
                id uuid NOT NULL PRIMARY KEY,
                name varchar(100) NOT NULL,
                prize numeric(10,2) NOT NULL,
                start timestamp with time zone NOT NULL,
                "end" timestamp with time zone NOT NULL,
                created_at timestamp with time zone NOT NULL,
                updated_at timestamp with time zone NOT NULL,
                is_active boolean NOT NULL
            );
            """,
            reverse_sql="DROP TABLE IF EXISTS bingo_event;"
        ),
        # Add missing BingoCard table
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS bingo_bingocard (
                id uuid NOT NULL PRIMARY KEY,
                numbers jsonb NOT NULL,
                is_winner boolean NOT NULL,
                hash varchar(64) NOT NULL UNIQUE,
                created_at timestamp with time zone NOT NULL,
                event_id uuid NOT NULL REFERENCES bingo_event(id) ON DELETE CASCADE,
                user_id integer NULL REFERENCES users_customuser(id) ON DELETE CASCADE
            );
            """,
            reverse_sql="DROP TABLE IF EXISTS bingo_bingocard;"
        ),
        # Add missing Number table
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS bingo_number (
                id uuid NOT NULL PRIMARY KEY,
                value integer NOT NULL,
                called_at timestamp with time zone NOT NULL,
                drawn boolean NOT NULL,
                event_id uuid NOT NULL REFERENCES bingo_event(id) ON DELETE CASCADE,
                UNIQUE(event_id, value)
            );
            """,
            reverse_sql="DROP TABLE IF EXISTS bingo_number;"
        ),
    ]
