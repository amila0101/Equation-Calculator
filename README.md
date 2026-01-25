# Equation Calculator

[![Python](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128.0-brightgreen.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Equation Calculator** is a Python-based API built with **FastAPI** and **SymPy** that solves **algebra, calculus, and trigonometry equations**. It provides **step-by-step solutions** and returns **JSON responses**, making integration into web or mobile applications easy.

---

## Features
- Solve algebraic equations (e.g., `x^2 - 4 = 0`)
- Compute derivatives and integrals for calculus problems
- Support trigonometric equations
- Step-by-step solution generation
- Clean JSON API responses for easy integration

---

## Tech Stack
- Python 3.13+
- FastAPI
- SymPy
- Uvicorn (ASGI server)
- Pydantic (request validation)

---
## ✨ Key Features

- 📐 **Algebraic Solver:** Solve linear and non-linear equations (e.g., $x^2 - 4 = 0$).
- 📈 **Calculus Support:** Compute derivatives and integrals with precision.
- 📐 **Trigonometry:** Full support for trigonometric functions and identities.
- 📝 **Step-by-Step Logic:** Generates logical steps for each solution to aid learning.
- ⚡ **Developer Friendly:** Returns clean, structured JSON responses for seamless integration.

---

## 🛠 Tech Stack

| Technology | Purpose |
| :--- | :--- |
| **Python 3.13+** | Core Programming Language |
| **FastAPI** | High-performance Web Framework |
| **SymPy** | Symbolic Mathematics Library |
| **Uvicorn** | ASGI Server Implementation |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.13+ installed
- `pip` (Python Package Manager)

### Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/amila0101/Equation-Calculator.git](https://github.com/amila0101/Equation-Calculator.git)
   cd Equation-Calculator


2. **Set up a Virtual Environment:**

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux / MacOS
python3 -m venv venv
source venv/bin/activate

```


3. **Install Dependencies:**
```bash
pip install -r requirements.txt

```


4. **Run the Server:**
```bash
uvicorn app.main:app --reload

```



The API will be live at `http://127.0.0.1:8000`.

---

## 📖 API Usage & Documentation

### Interactive Docs

Once the server is running, you can access the interactive Swagger UI documentation at:
🔗 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Example Response

`POST /solve`

```json
{
  "success": true,
  "equation": "x**2 - 4",
  "variable": "x",
  "type": "algebra",
  "result": ["2", "-2"],
  "steps": [
    "Equation received: x**2 - 4",
    "Solving equation gives: 2, -2",
    "Steps generation complete"
  ]
}

```

---

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 👥 Connect with Us

**Amila Gamage**

* **GitHub:** [@amila0101](https://github.com/amila0101)
* **LinkedIn:** [Amila Buddhika](https://www.linkedin.com/in/amila-gamage/)
* **Twitter:** [@amila_gamage](https://twitter.com/amila_gamage)
---
* **GitHub:** [@Isugithub](https://github.com/Isugithub/)
* **LinkedIn:** [Isuri Liyanage](https://www.linkedin.com/in/isuri-liyanage-252b26233/)

---

*Project Link: [https://github.com/amila0101/Equation-Calculator*](https://www.google.com/search?q=https://github.com/amila0101/Equation-Calculator)



