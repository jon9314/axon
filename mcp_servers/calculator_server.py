"""Simple arithmetic calculator server."""

import ast
import math
from collections.abc import Callable, Mapping
from typing import Any

from fastapi import FastAPI, HTTPException

ALLOWED_FUNCTIONS: Mapping[str, Callable[..., Any]] = {
    name: getattr(math, name) for name in dir(math) if not name.startswith("_")
}


def _eval_node(node: ast.AST) -> float:
    """Recursively evaluate an AST node with math functions only."""
    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.Mod):
            return left % right
        if isinstance(node.op, ast.Pow):
            return left**right
        if isinstance(node.op, ast.FloorDiv):
            return left // right
        raise ValueError("unsupported operator")
    if isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand)
        if isinstance(node.op, ast.UAdd):
            return +operand
        if isinstance(node.op, ast.USub):
            return -operand
        raise ValueError("unsupported unary operator")
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("invalid function")
        func_name = node.func.id
        func = ALLOWED_FUNCTIONS.get(func_name)
        if func is None:
            raise ValueError(f"function {func_name} not allowed")
        args = [_eval_node(arg) for arg in node.args]
        return func(*args)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, int | float):
            return float(node.value)
        raise ValueError("non-numeric constant")
    if isinstance(node, ast.Name):
        value = ALLOWED_FUNCTIONS.get(node.id)
        if isinstance(value, int | float):
            return float(value)
        raise ValueError(f"name {node.id} not allowed")
    raise ValueError("unsupported expression")


def safe_eval(expr: str) -> float:
    """Safely evaluate an arithmetic expression using Python's AST."""
    tree = ast.parse(expr, mode="eval")
    return _eval_node(tree.body)


app = FastAPI()


@app.get("/evaluate")
def evaluate(expr: str):
    """Evaluate a mathematical expression safely."""
    try:
        result = safe_eval(expr)
    except Exception as err:  # noqa: BLE001 - surface error to client
        raise HTTPException(status_code=400, detail=str(err)) from err
    return {"result": result}


@app.get("/percent")
def percent(value: float, percent: float):
    return {"result": value * percent / 100.0}
