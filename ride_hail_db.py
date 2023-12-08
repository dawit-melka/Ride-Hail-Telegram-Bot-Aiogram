import aiosqlite
import asyncio
# Define DB Functions
async def create_db():
    async with aiosqlite.connect('ride_hail.db') as conn:
        cur = await conn.cursor()
        await cur.execute('''CREATE TABLE IF NOT EXISTS Passenger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                last_name TEXT,
                phone TEXT,
                email TEXT,
                password TEXT)''')
        await cur.execute('''CREATE TABLE IF NOT EXISTS Driver (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                last_name TEXT,
                phone TEXT,
                email TEXT,
                password TEXT,
                car_type TEXT,
                plate_no TEXT)''')
        await conn.commit()
   
        
async def insert_passenger_data(id: str, first_name: str, last_name: str, phone: str, email: str, password: str):
    async with aiosqlite.connect('ride_hail.db') as conn:
        cur = await conn.cursor()
        await cur.execute('''INSERT INTO Passenger (id, first_name, last_name, phone, email, password) VALUES (?,?,?,?,?,?)''', (id, first_name, last_name, phone, email, password))
        await conn.commit()


async def insert_driver_data(id: str, first_name: str, last_name: str, phone: str, email: str, password: str, car_type: str, plate_no: str):
    async with aiosqlite.connect('ride_hail.db') as conn:
        cur = await conn.cursor()
        await cur.execute('''INSERT INTO Driver (id, first_name, last_name, phone, email, password, car_type, plate_no) VALUES (?,?,?,?,?,?,?,?)''', (id, first_name, last_name, phone, email, password, car_type, plate_no))
        await conn.commit()


async def get_passenger_data(email: str, password: str):
    async with aiosqlite.connect('ride_hail.db') as conn:
        cur = await conn.cursor()
        await cur.execute('''SELECT * FROM Passenger WHERE Email = ? AND Password = ?''', (email,password,))
        return await cur.fetchone()


async def get_driver_data(email: str, password: str):
    async with aiosqlite.connect('ride_hail.db') as conn:
        cur = await conn.cursor()
        await cur.execute('''SELECT * FROM Driver WHERE Email = ? AND Password = ?''', (email,password,))
        result =  await cur.fetchone()
        return result

async def update_user_data(role: str, user_id: int, field_name: str, field_value: str):
    async with aiosqlite.connect('ride_hail.db') as conn:
        cur = await conn.cursor()

        if role.lower() == 'passenger':
            await cur.execute(f'''UPDATE Passenger SET {field_name} = ? WHERE id = ?''', (field_value, user_id,))
            await cur.execute('''SELECT * FROM Passenger WHERE Id = ?''', (user_id,))
            result =  await cur.fetchone()
            await conn.commit()
            return result
        elif role.lower() == 'driver':
            await cur.execute(f'''UPDATE Driver SET {field_name} = ? WHERE id = ?''', (field_value, user_id,))
            await cur.execute('''SELECT * FROM Driver WHERE Id = ?''', (user_id,))
            result =  await cur.fetchone()
            await conn.commit()
            return result
        else:
            raise ValueError("Invalid role. Supported roles are 'passenger' and 'driver'.")

        
async def get_user_by_id(role: str, id: int):
    async with aiosqlite.connect('ride_hail.db') as conn:
        cur = await conn.cursor()
        await cur.execute(f'''SELECT * FROM {role} WHERE Id = ?''', (id,))
        result = await cur.fetchone()
        return result

async def get_all_drivers_id():
    async with aiosqlite.connect('ride_hail.db') as conn:
        cur = await conn.cursor()
        await cur.execute('''SELECT id FROM Driver''')
        result = await cur.fetchall()
        return result
    


asyncio.run(create_db())






      