#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from collections import defaultdict
import json
import microlog
import random
import time
from typing import List



def simulateIO(s):
    if random.random() > 0.95:
        time.sleep(s)


@microlog.trace
class Order():
    def __init__(self, count: int, book: any):
        self.count = count
        self.book = book

    def getBook(self):
        return self.book

    def getCount(self):
        return self.count

    def __str__(self):
        return f"[Order: {self.count} copies of {self.book}]"


@microlog.trace
class Book():
    def __init__(self, object: any):
        for key in object:
            setattr(self, key, object[key])

    def __str__(self):
        return f"[Book: '{self.title}' by '{self.author}']"


@microlog.trace
class ShoppingCart():
    def __init__(self):
        self.orders = []

    def addOrder(self, order: Order):
        print(f"Add order {order.getCount()} of {order.getBook()}")
        self.orders.append(order)

    def checkout(self):
        pass

@microlog.trace
class BookStore():
    def __init__(self):
        self.books = [ Book(book) for book in json.loads(open("examples/books.json").read()) ]
        self.shoppingCarts = defaultdict(ShoppingCart)

    def getSession(self):
        return f"session-{time.time()}"

    def getBooks(self):
        return self.books

    def addToShoppingCart(self, session, count, book):
        order = Order(count, book)
        cart = self.shoppingCarts[session]
        cart.addOrder(order)
        print("add order", order)

    def checkout(self, session):
        self.shoppingCarts[session].checkout()
        del self.shoppingCarts[session]


def main():
    for n in range(1, 11):
        store = BookStore()
        session = store.getSession()
        books = store.getBooks()
        book = random.choice(books)
        store.addToShoppingCart(session, n, book)
        store.checkout(session)
        time.sleep(0.3)

main()