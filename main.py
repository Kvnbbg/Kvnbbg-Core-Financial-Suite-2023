import os
import sys
import time
import matplotlib.pyplot as plt
import numpy as np
from forex_python.converter import CurrencyRates, RatesNotAvailableError

#By Kvnbbg, Kevin Marville

import os
import sys
from forex_python.converter import CurrencyRates, RatesNotAvailableError

# Credits to the author: Kvnbbg, Kevin Marville
# Kvnbbg Core Financial Suite 2023

# Global Variables
users = {}
logged_in_user = None

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def obfuscate_string(input_string):
    """Obfuscate the input string by shifting each character by 3 positions."""
    return ''.join(chr(ord(char) + 3) for char in input_string)

def deobfuscate_string(obfuscated_string):
    """Deobfuscate the input string by shifting each character back by 3 positions."""
    return ''.join(chr(ord(char) - 3) for char in obfuscated_string)

def register_user():
    """Register a new user."""
    global users
    username = input("Enter desired username: ")
    if username in users:
        print("\nUsername already taken.")
        return
    password = input("Enter password: ")
    obfuscated_password = obfuscate_string(password)
    users[username] = {"password": obfuscated_password, "history": [], "portfolio": {}}
    print("\nRegistration successful!")

def login():
    """Login an existing user."""
    global logged_in_user
    username = input("Enter your username: ")
    if username not in users:
        print("\nUser does not exist.")
        return
    password = input("Enter password: ")
    if users[username]["password"] == obfuscate_string(password):
        logged_in_user = username
        print(f"\nWelcome back, {logged_in_user}!")
    else:
        print("\nIncorrect password.")

def logout():
    """Logout the current logged-in user."""
    global logged_in_user
    logged_in_user = None
    print("\nLogged out successfully.")

def get_currency_rates():
    """Convert currency in real-time."""
    c = CurrencyRates()
    try:
        amount = float(input("\nEnter the amount: "))
        print("\nAvailable currency codes:", ", ".join(c.get_rates('USD').keys()))
        from_currency = input("\nFrom Currency (e.g. USD): ").upper()
        to_currency = input("To Currency (e.g. EUR): ").upper()

        result = c.convert(from_currency, to_currency, amount)
        conversion = f"{amount} {from_currency} is equal to {result:.2f} {to_currency}"
        print("\n💸", conversion, "💸")
        if logged_in_user:
            users[logged_in_user]["history"].append(conversion)

    except RatesNotAvailableError:
        print("\n❌ Rates not available for the selected currencies.")
    except ValueError:
        print("\n❌ Invalid input. Please enter a valid number.")

def virtual_portfolio():
    """Manage the virtual cryptocurrency portfolio."""
    if not logged_in_user:
        print("\nPlease log in to manage your portfolio.")
        return

    while True:
        print("\n--- 📈 Virtual Cryptocurrency Portfolio 📈 ---")
        print("1. View Portfolio.")
        print("2. Buy Cryptocurrency.")
        print("3. Sell Cryptocurrency.")
        print("4. Back to Main Menu.")
        choice = input("\nChoose an option: ")

        if choice == '1':
            for crypto, amount in users[logged_in_user]["portfolio"].items():
                print(f"{crypto}: {amount}")
        elif choice == '2':
            crypto = input("\nEnter cryptocurrency code (e.g., BTC): ").upper()
            amount = float(input("Enter amount to buy: "))
            users[logged_in_user]["portfolio"][crypto] = users[logged_in_user]["portfolio"].get(crypto, 0) + amount
        elif choice == '3':
            crypto = input("\nEnter cryptocurrency code (e.g., BTC): ").upper()
            if crypto not in users[logged_in_user]["portfolio"]:
                print("\nYou don't have this cryptocurrency in your portfolio.")
                continue
            amount = float(input("Enter amount to sell: "))
            if amount > users[logged_in_user]["portfolio"][crypto]:
                print("\nYou don't have enough to sell.")
            else:
                users[logged_in_user]["portfolio"][crypto] -= amount
        elif choice == '4':
            break
        else:
            print("\n❌ Invalid choice.")

def main_menu():
    """Main menu of the application."""
    while True:
        clear_screen()
        if logged_in_user:
            print(f"\n🚀 Welcome, {logged_in_user}, to Kvnbbg Core Financial Suite 2023 🚀")
        else:
            print(f"\n🚀 Welcome to Kvnbbg Core Financial Suite 2023 🚀")
        print("\n--- 📜 Main Menu 📜 ---")
        print("1. Real-time currency conversion.")
        print("2. Manage virtual cryptocurrency portfolio.")
        print("3. User management.")
        print("4. Exit.")
        choice = input("\nChoose an option: ")

        if choice == '1':
            get_currency_rates()
        elif choice == '2':
            virtual_portfolio()
        elif choice == '3':
            user_mgmt = True
            while user_mgmt:
                print("\n--- 👥 User Management 👥 ---")
                print("1. Register.")
                print("2. Login.")
                print("3. Logout.")
                print("4. Back to Main Menu.")
                user_choice = input("\nChoose an option: ")

                if user_choice == '1':
                    register_user()
                elif user_choice == '2':
                    login()
                elif user_choice == '3':
                    logout()
                elif user_choice == '4':
                    user_mgmt = False
        elif choice == '4':
            if logged_in_user:
                print(f"\nThank you, {logged_in_user}, for using Kvnbbg Core Financial Suite! Goodbye! 🚀")
            else:
                print("\nThank you for using Kvnbbg Core Financial Suite! Goodbye! 🚀")
            sys.exit()
        else:
            print("\n❌ Invalid choice. Please select a valid option.")

main_menu()
