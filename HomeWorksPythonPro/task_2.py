class  Product:
    def __init__(self, name, category,  price, quantity):
        self.name = name
        self.category = category
        self.price = price
        self.quantity = quantity


    def change_price(self, new_price):
        self.price = new_price


    def change_quantity(self, new_quantity):
        self.quantity = new_quantity


class Customer:
    def __init__(self, name, mail_address, order_list=None):
        self.name = name
        self.mail_address = mail_address
        self.order_list = []


    def add_order(self, order):
        self.order_list.append(order)

class Order:
    def __init__(self, total_order_amount=0, goods_list=None):
        self.total_order_amount = total_order_amount
        self.goods_list = []


    def add_goods(self, goods):
        self.goods_list.extend(goods)
        self.count_total_order_amount()


    def count_total_order_amount(self):
        self.total_amount = sum(product.price for product in self.goods_list)
        return self.total_order_amount


product1 = Product("Teddy Bear", "Soft toy", 1000, 100)
product2 = Product("Star Wars", "Lego", 2000, 100)
product3 = Product("Shark", "Soft toy", 500, 100)
product4 = Product("Disney", "Lego", 1500, 100)

print("___Test Product Class___")
print(f"Old price: {product1.price} UAH, quantity: {product1.quantity} pcs.")
product1.change_price(900)
product1.change_quantity(80)
print(f"New price: {product1.price} UAH, quantity: {product1.quantity} pcs.")

customer1 = Customer("Artem", "artem@mail.com")
customer2 = Customer("Anna", "anna@mail.com")
customer3 = Customer("Yulia", "yulia@mail.com")
customer4 = Customer("Nik", "nik@mail.com")

print("___Test make an order #1___")
order1 = Order()
order1.add_goods([product1, product3])
customer1.add_order(order1)
print(f"Customer {customer1.name} bought goods: {[f'{p.name} ({p.category})' for p in order1.goods_list]}")
print(f"Total order #1: {order1.total_amount} UAH")


print("___Test make an order #2___")
order2 = Order()
order2.add_goods([product4, product2])
customer2.add_order(order2)
print(f"Customer {customer2.name} bought goods: {[f'{p.name} ({p.category})' for p in order2.goods_list]}")
print(f"Total order #2: {order2.total_amount} UAH")
order2.add_goods([product3])
customer2.add_order(order2)
print(f"Customer {customer2.name} bought goods: {[f'{p.name} ({p.category})' for p in order2.goods_list]}")
print(f"Total order #2: {order2.total_amount} UAH")


print("___Check history___")
print(f" {customer1.name} has {len(customer1.order_list)} orders")
print(f" {customer2.name} has {len(customer2.order_list)} orders")



