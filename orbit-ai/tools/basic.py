def calculator(expression):
    try:
        return eval(expression, {"__builtins__": {}})
    except Exception as error:
        return f"Calculation error: {error}"


def text_analyzer(text):
    words = text.split()

    return {
        "characters": len(text),
        "words": len(words)
    }
