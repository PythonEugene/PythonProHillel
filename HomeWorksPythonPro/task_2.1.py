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


products_list = []
with open('products.txt', 'r') as file:
    for line in file:
        data = line.strip().split(',')
        name = data[0]
        category = data[1]
        price = float(data[2])
        quantity = int(data[3])
        new_product = Product(name, category, price, quantity)
        products_list.append(new_product)
print("___Test Products List___")
for p in products_list:
    print(f"Product: {p.name} Category: {p.category} Price: {p.price} Quantity: {p.quantity}")


customers_list = []
with open('customers.txt', 'r') as file:
    for line in file:
        data = line.strip().split(',')
        name = data[0]
        mail_address = data[1]
        new_customer = Customer(name, mail_address)
        customers_list.append(new_customer)
print("___Test Customers List___")
for c in customers_list:
    print(f"Customer: {c.name} Mail Address: {c.mail_address}")

order1 = Order()
order1.add_goods([products_list[0], products_list[1]])
customers_list[0].add_order(order1)
print("___Test Order1___")
print(f"Customer {customers_list[0].name} bought goods: {[f'{p.name} ({p.category})' for p in order1.goods_list]}")
print(f"Total order #1: {order1.total_amount} UAH")


order2 = Order()
order2.add_goods([products_list[2], products_list[3]])
customers_list[2].add_order(order2)
print("___Test Order2___")
print(f"Customer {customers_list[2].name} bought goods: {[f'{p.name} ({p.category})' for p in order2.goods_list]}")
print(f"Total order #2: {order2.total_amount} UAH")


