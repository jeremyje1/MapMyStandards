#!/usr/bin/env python3
"""Apply webhook tables migration to Railway database."""

import asyncio
import asyncpg
import os
from pathlib import Path

async def create_webhook_tables():
    """Create webhook tables in the database."""
    # Get database URL from environment - Railway sets this automatically
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print('❌ DATABASE_URL not found in environment')
        return False
    
    # Read SQL file
    sql_file = Path(__file__).parent / 'create_webhook_tables.sql'
    if not sql_file.exists():
        print(f'❌ SQL file not found: {sql_file}')
        return False
    
    sql = sql_file.read_text()
    
    # Connect and execute
    try:
        conn = await asyncpg.connect(db_url)
        try:
            # Execute SQL
            await conn.execute(sql)
            print('✅ Webhook tables created successfully')
            
            # Check if tables exist
            tables = await conn.fetch('''
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename IN ('webhook_configs', 'webhook_deliveries')
                ORDER BY tablename
            ''')
            
            if tables:
                print('\n📊 Created tables:')
                for table in tables:
                    print(f'  - {table["tablename"]}')
                    
                    # Get column info
                    columns = await conn.fetch(f'''
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = '{table["tablename"]}'
                        AND table_schema = 'public'
                        ORDER BY ordinal_position
                        LIMIT 5
                    ''')
                    
                    print('    Columns:', ', '.join(f'{c["column_name"]} ({c["data_type"]})' for c in columns), '...')
            
            return True
            
        except Exception as e:
            if 'already exists' in str(e):
                print('✅ Webhook tables already exist')
                return True
            else:
                print(f'❌ Error creating tables: {e}')
                return False
        finally:
            await conn.close()
            
    except Exception as e:
        print(f'❌ Database connection error: {e}')
        return False


if __name__ == '__main__':
    success = asyncio.run(create_webhook_tables())
    exit(0 if success else 1)