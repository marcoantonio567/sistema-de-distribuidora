# Distributor System

## 📌 About the Project

The **Distributor System** is an application developed to assist in the management of distributors, allowing control of products, customers, sales, inventory, and other commercial operations.

The project was developed focusing on:

* Organization of internal processes;

* Efficient inventory control;

* Sales and customer management;

* Ease of use;

* Scalability for future improvements.

---

# 🚀 Features

## 📦 Product Management

* Product registration;

* Price updates;

* Stock quantity control;

* Quick product lookup.

## 👥 Customer Management

* Customer registration;

* Information lookup;

* Purchase history.

## 🛒 Sales Control

* Sales registration;

* Order control;

* Automatic stock update. ## 📊 Reports

* Sales reports;

* Inventory reports;

* Basic financial control.

---

# 🛠️ Technologies Used

This project was developed using the following technologies:

* Python
* Django
* HTML5
* CSS3
* JavaScript
* SQLite3

---

# 📂 Project Structure

```bash
distributor-system/
│
├── core/
├── templates/
├── static/
├── database/
├── manage.py
├── requirements.txt
└── README.md
```

---

# ⚙️ How to Run the Project

## 1️⃣ Clone the repository

```bash
git clone https://github.com/marcoantonio567/sistema-de-distribuidora.git


## 2️⃣ Access the project folder

```bash
cd sistema-de-distribuidora

```

## 3️⃣ Create a virtual environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate

```

### Linux/Mac

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 4️⃣ Install the dependencies

```bash
pip install -r requirements.txt

```

---

## 5️⃣ Execute the migrations

```bash
python manage.py migrate
```

---

## 6️⃣ Start the server

```bash
python manage.py runserver
```

---

# 🌐 System Access

After starting the server, access:

```bash
http://127.0.0.1:8000/
```


## Dashboard

```md
![Dashboard](./assets/dashboard.png)

```

---

# 🔐 Administrator User

If using Django Admin:

```bash
python manage.py createsuperuser
```

Access:

```bash
http://127.0.0.1:8000/admin

```

---

# 📈 Future Improvements

* Integration with invoice issuance;

* Dashboard with graphs;

* Permissions system;

* Advanced financial control;

* REST API;

* Mobile responsiveness.

---

# 🤝 Contribution

Contributions are always welcome.

To contribute:

1. Fork the project;

2. Create a branch;

3. Commit your changes;

4. Submit a Pull Request.
