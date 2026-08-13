import psycopg
from psycopg.rows import dict_row


class CarSaleDatabase:
    def __init__(self, db_url):
        self.db_url = db_url
        self._init_db()

    def _init_db(self):
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS brands (
                    id SERIAL PRIMARY KEY, 
                    name VARCHAR(50) NOT NULL UNIQUE
                    );
                """)

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS cars (
                        id SERIAL PRIMARY KEY,
                        brand_id INTEGER NOT NULL,
                        model VARCHAR(50) NOT NULL,
                        year INTEGER NOT NULL,
                        price NUMERIC(10, 2) NOT NULL,
                        mileage INTEGER NOT NULL,
                        VIN VARCHAR(20) UNIQUE NOT NULL,
                        status VARCHAR(50) DEFAULT 'available',
                        FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE RESTRICT
                    );
                """)

                cur.execute(""" 
                    CREATE TABLE IF NOT EXISTS sales (
                        id SERIAL PRIMARY KEY,
                        car_id INTEGER NOT NULL UNIQUE,
                        sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        final_price NUMERIC(10, 2) NOT NULL,
                        FOREIGN KEY (car_id) REFERENCES cars(id) ON DELETE CASCADE
                    );
                """)

    def add_brand(self, name: str)-> int:
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO brands (name) VALUES (%s) ON CONFLICT (name) DO UPDATE SET name=EXCLUDED.NAME RETURNING id;",
                    (name,)
                )
                return cur.fetchone()[0]

    def add_car(self, brand_id: int, model: str, year: int, price: float, mileage: int, vin:str):
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO cars (brand_id, model, year, price, mileage, VIN) 
                    VALUES (%s, %s, %s, %s, %s, %s) 
                    ON CONFLICT (vin) DO UPDATE SET 
                        price = EXCLUDED.price,
                        mileage = EXCLUDED.mileage
                    RETURNING id;
                    """,
                    (brand_id, model, year, price, mileage, vin)
                )
                return cur.fetchone()[0]

    def sell_car(self, car_id: int, final_price: float):
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO sales (car_id, final_price) VALUES (%s, %s);",
                    (car_id, final_price)
                )
                cur.execute(
                    "UPDATE cars SET status = 'sold' WHERE id = %s;",
                    (car_id,)
                )
                print(f"Car {car_id} has been sold successfully for the {final_price}!")

    def get_available_cars(self):
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    SELECT cars_id, brands.name as brand, cars.model, cars.year, cars.price, cars.mileage, cars.vin
                    FROM cars
                    JOIN brands ON cars.brand_id = brands.id
                    WHERE cars.status = 'available';
                """)
                return cur.fetchall()
                        
