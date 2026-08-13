from car_store_db import CarSaleDatabase

DATABASE_URL = "postgresql://postgres:13011993@localhost:5432/car_store_db"

db = CarSaleDatabase(DATABASE_URL)

toyota_id = db.add_brand("Toyota")
bmw_id = db.add_brand("BMW")
ford_id = db.add_brand("Ford")
vw_id = db.add_brand("VW")
opel_id = db.add_brand("Opel")
tesla_id = db.add_brand("Tesla")
mercedes_id = db.add_brand("Mercedes")
mazda_id = db.add_brand("Mazda")

car1id = db.add_car(toyota_id, "Camry", 2020, 50000.00, 49000, "JTDKAM78123456789" )
car2id = db.add_car(bmw_id, "X5", 2021, 150000.00, 56000, "WBAX5508123456789")
