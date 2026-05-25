import ast
import operator as op

from pyrogram.types import InlineQueryResultArticle, InputTextMessageContent

from utils.misc import modules_help
from utils.inline import inline_command


_ALLOWED_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}


def safe_eval(expr: str):
    def _eval(node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Разрешены только числа")

        if isinstance(node, ast.BinOp):
            operator = _ALLOWED_OPERATORS.get(type(node.op))
            if not operator:
                raise ValueError("Оператор запрещён")
            return operator(_eval(node.left), _eval(node.right))

        if isinstance(node, ast.UnaryOp):
            operator = _ALLOWED_OPERATORS.get(type(node.op))
            if not operator:
                raise ValueError("Оператор запрещён")
            return operator(_eval(node.operand))

        raise ValueError("Недопустимое выражение")

    expr = expr.replace(",", ".")
    tree = ast.parse(expr, mode="eval")
    return _eval(tree.body)


@inline_command("calc", "Мини-калькулятор")
async def inline_calc(app, query, args):
    expr = args.strip()

    if not expr:
        return [
            InlineQueryResultArticle(
                title="Калькулятор",
                description="Пример: calc 2 + 2 * 5",
                input_message_content=InputTextMessageContent(
                    "<b>Использование:</b> <code>calc 2 + 2 * 5</code>"
                ),
            )
        ]

    try:
        result = safe_eval(expr)

        if isinstance(result, float):
            result = round(result, 10)

        return [
            InlineQueryResultArticle(
                title=f"🧮 {expr} = {result}",
                description="Нажми, чтобы отправить результат",
                input_message_content=InputTextMessageContent(
                    f"<b>🧮 Калькулятор</b>\n\n"
                    f"<code>{expr}</code>\n"
                    f"<b>=</b> <code>{result}</code>"
                ),
            )
        ]

    except Exception as e:
        return [
            InlineQueryResultArticle(
                title="Ошибка вычисления",
                description=str(e),
                input_message_content=InputTextMessageContent(
                    f"<b>Ошибка:</b> <code>{e}</code>"
                ),
            )
        ]


modules_help["calc"] = {
    "calc [expression]": "мини-калькулятор в inline.",
}