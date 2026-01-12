import matplotlib.pyplot as plt
import numpy as np
from sympy import lambdify, symbols

def plot_equation(expr, variable="x", filename="graph.png"):
    var = symbols(variable)
    func = lambdify(var, expr, "numpy")
    x_vals = np.linspace(-10, 10, 400)
    y_vals = func(x_vals)
    
    plt.figure(figsize=(6,4))
    plt.plot(x_vals, y_vals, label=str(expr))
    plt.xlabel(variable)
    plt.ylabel("y")
    plt.title("Equation Graph")
    plt.grid(True)
    plt.legend()
    plt.savefig(filename)
    plt.close()
