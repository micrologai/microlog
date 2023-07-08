#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from collections import defaultdict
import json
import random
import time


def simulateIO():
    time.sleep(0.1)


class Order():
    def __init__(self, count: int, book: any):
        self.count = count
        self.book = book
        simulateIO()
        print(f"New Order: {count} {book}")

    def getBook(self):
        print(f"Order: getBook => {self.book}")
        return self.book

    def getCount(self):
        print(f"Order: getCount => {self.count}")
        return self.count

    def __str__(self):
        return f"[Order: {self.count} copies of {self.book}]"


class Book():
    def __init__(self, object: any):
        for key in object:
            setattr(self, key, object[key])

    def __str__(self):
        return f"[Book: '{self.title}' by '{self.author}']"


class ShoppingCart():
    def __init__(self):
        self.orders = []

    def addOrder(self, order: Order):
        print(f"ShoppingCart: Add order {order.getCount()} of {order.getBook()}")
        self.orders.append(order)

    def checkout(self):
        pass

class BookStore():
    def __init__(self):
        self.books = [ Book(book) for book in json.loads(open("examples/books.json").read()) ]
        self.shoppingCarts = defaultdict(ShoppingCart)

    def getSession(self):
        print("BookStore: get session")
        return f"session-{time.time()}"

    def getBooks(self):
        print("BookStore: get books")
        return self.books

    def addToShoppingCart(self, session, count, book):
        order = Order(count, book)
        cart = self.shoppingCarts[session]
        cart.addOrder(order)
        print("BookStore: add order", order)

    def checkout(self, session):
        print("BookStore: checkout")
        self.shoppingCarts[session].checkout()
        del self.shoppingCarts[session]


def main():
    print("Main: simulate a bookstore")
    for n in range(1, 11):
        store = BookStore()
        session = store.getSession()
        books = store.getBooks()
        book = random.choice(books)
        store.addToShoppingCart(session, n, book)
        store.checkout(session)
        time.sleep(0.3)

main()
