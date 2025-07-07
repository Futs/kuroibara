#!/usr/bin/env python3
import asyncio
import asyncpg

async def test_connection():
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='kuroibara',
            password='password',
            database='postgres'
        )
        print('✅ Connection successful!')
        
        # Try to create test database
        try:
            await conn.execute("CREATE DATABASE test_kuroibara;")
            print('✅ Test database created!')
        except Exception as e:
            if 'already exists' in str(e):
                print('✅ Test database already exists!')
            else:
                print(f'❌ Failed to create test database: {e}')
        
        await conn.close()
    except Exception as e:
        print(f'❌ Connection failed: {e}')

if __name__ == "__main__":
    asyncio.run(test_connection())
