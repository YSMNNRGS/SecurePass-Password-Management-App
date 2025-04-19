import tkinter as tk
from tkinter import messagebox
from cryptography.fernet import Fernet
import sqlite3
import os
import random
import string
from PIL import Image, ImageTk
from tkinter import simpledialog, messagebox

#-- the passkey for admin
ADMIN_PASSKEY = "Admin#2504"

# Generate/load encryption key
if not os.path.exists("key.key"):
    key = Fernet.generate_key()
    with open("key.key", "wb") as key_file:
        key_file.write(key)
else:
    with open("key.key", "rb") as key_file:
        key = key_file.read()

cipher = Fernet(key)

# SQL DBS for saving passwords
conn = sqlite3.connect("data.db")
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS passwords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    website TEXT NOT NULL,
    email TEXT NOT NULL,
    password BLOB NOT NULL
)
''')
conn.commit()
conn.close()

# Main window of the APP
window = tk.Tk()
window.title("Password Manager")
window.geometry("1280x720")
bg_path = os.path.join(os.path.dirname(__file__), "background.png")
try:
    bg_img = Image.open(bg_path)
    bg_img = bg_img.resize((1280, 720), Image.LANCZOS)
    bg_photo = ImageTk.PhotoImage(bg_img)
    bg_label = tk.Label(window, image=bg_photo)
    bg_label.image = bg_photo
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)
except Exception as e:
    print("Error loading background:", e)
    window.config(bg="#f0f2f5")

# Save password functionality
def save_password():
    website = website_entry.get()
    email = email_entry.get()
    password = password_entry.get()

    if not website or not email or not password:
        messagebox.showerror("Error", "Please fill all fields")
        return
    encrypted = cipher.encrypt(password.encode())
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO passwords (website, email, password) VALUES (?, ?, ?)",
                   (website, email, encrypted))
    conn.commit()
    conn.close()

    messagebox.showinfo("Saved", "Password saved successfully")
    website_entry.delete(0, tk.END)
    email_entry.delete(0, tk.END)
    password_entry.delete(0, tk.END)

def generate_password():
    characters = string.ascii_letters + string.digits + string.punctuation
    generated = ''.join(random.choice(characters) for _ in range(12))
    password_entry.delete(0, tk.END)
    password_entry.insert(0, generated)

# Admin access check
def verify_admin_access(success_callback):
    entered_key = simpledialog.askstring("Admin Access", "Enter Admin Passkey:", show="*")
    if entered_key == ADMIN_PASSKEY:
        success_callback()
    else:
        messagebox.showerror("Access Denied", "Incorrect passkey.")

# Show saved passwords
def show_passwords():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT website, email, password FROM passwords")
    records = cursor.fetchall()
    conn.close()

    result = ""
    for website, email, encrypted in records:
        decrypted = cipher.decrypt(encrypted).decode()
        result += f"Website: {website}\nEmail: {email}\nPassword: {decrypted}\n\n"

    # Create a custom window instead of a messagebox
    pw_window = tk.Toplevel(window)
    pw_window.title("Saved Passwords")
    pw_window.geometry("500x500")

    text_area = tk.Text(pw_window, wrap="word", font=("Times New Roman", 10))
    text_area.insert(tk.END, result)
    text_area.config(state="disabled")  # Make it read-only
    text_area.pack(expand=True, fill="both", padx=10, pady=10)


# Manage passwords
def manage_passwords():
    manage_window = tk.Toplevel(window)
    manage_window.title("Manage Passwords")
    manage_window.geometry("800x500")

    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, website, email, password FROM passwords")
    records = cursor.fetchall()
    conn.close()

    for i, (pid, website, email, encrypted_pass) in enumerate(records):
        decrypted_pass = cipher.decrypt(encrypted_pass).decode()

        tk.Label(manage_window, text=f"{website} | {email} | {decrypted_pass}", font=("Times New Roman", 11)).grid(row=i, column=0, sticky="w", padx=5, pady=3)

        def make_update_closure(p=pid, w=website, e=email, pword=decrypted_pass):
            return lambda: update_entry(p, w, e, pword)

        def make_delete_closure(p=pid):
            return lambda: delete_entry(p, manage_window)

        tk.Button(manage_window, text="Update", command=make_update_closure(), bg="#2196F3", fg="white").grid(row=i, column=1, padx=5)
        tk.Button(manage_window, text="Delete", command=make_delete_closure(), bg="#f44336", fg="white").grid(row=i, column=2, padx=5)

def delete_entry(entry_id, parent_window):
    confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this password?")
    if confirm:
        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM passwords WHERE id = ?", (entry_id,))
        conn.commit()
        conn.close()
        parent_window.destroy()
        verify_admin_access(manage_passwords)

def update_entry(entry_id, website, email, password):
    def save_updated():
        new_website = website_entry.get()
        new_email = email_entry.get()
        new_password = cipher.encrypt(password_entry.get().encode())

        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE passwords SET website=?, email=?, password=? WHERE id=?
        """, (new_website, new_email, new_password, entry_id))
        conn.commit()
        conn.close()

        update_win.destroy()
        verify_admin_access(manage_passwords)

    update_win = tk.Toplevel(window)
    update_win.title("Update Password")
    update_win.geometry("400x250")

    tk.Label(update_win, text="Website:").pack()
    website_entry = tk.Entry(update_win)
    website_entry.pack()
    website_entry.insert(0, website)

    tk.Label(update_win, text="Email:").pack()
    email_entry = tk.Entry(update_win)
    email_entry.pack()
    email_entry.insert(0, email)

    tk.Label(update_win, text="Password:").pack()
    password_entry = tk.Entry(update_win)
    password_entry.pack()
    password_entry.insert(0, password)

    tk.Button(update_win, text="Save", command=save_updated, bg="green", fg="white").pack(pady=10)

# GUI setup of the app
website_entry = tk.Entry(window, font=("Times New Roman", 14))
website_entry.place(x=450, y=200, width=400)
tk.Label(window, text="Website:", font=("Times New Roman", 14)).place(x=350, y=200)

email_entry = tk.Entry(window, font=("Times New Roman", 14))
email_entry.place(x=450, y=250, width=400)
tk.Label(window, text="Email:", font=("Times New Roman", 14)).place(x=350, y=250)

password_entry = tk.Entry(window, font=("Times New Roman", 14))
password_entry.place(x=450, y=300, width=400)
tk.Label(window, text="Password:", font=("Times New Roman", 14)).place(x=350, y=300)

# save password button
tk.Button(window, text="Save Password", command=save_password, font=("Times New Roman", 12), bg="#4CAF50", fg="white").place(x=450, y=360)
tk.Button(window, text="Generate Password", command=generate_password, font=("Times New Roman", 12), bg="#673AB7", fg="white").place(x=580, y=360)

# Passkey requirement for accessing
menubar = tk.Menu(window)
menubar.add_command(label="🔒 View Passwords", command=lambda: verify_admin_access(show_passwords))
menubar.add_command(label="🛠 Manage Passwords", command=lambda: verify_admin_access(manage_passwords))
window.config(menu=menubar)

window.mainloop()
