from llama_cpp import Llama

MODEL_PATH = "./models/model-q8_0.gguf"
DEFAULT_SYSTEM_PROMPT = "Ты — Сайга, русскоязычный автоматический ассистент. Ты разговариваешь с людьми и помогаешь им."

llm = Llama(model_path=MODEL_PATH, n_ctx=8192)

histories = {}


MAX_TOKENS_CTX = 8192


def trim_history(history: list) -> list:
    # всегда оставляем system-промпт
    system_prompt = history[0]
    rest = history[1:]

    while True:
        prompt = "".join(
            f"<|{msg['role']}|>\n{msg['content']}\n" for msg in [system_prompt] + rest
        )
        n_tokens = len(llm.tokenize(prompt.encode("utf-8")))
        if n_tokens <= MAX_TOKENS_CTX:
            break
        rest.pop(0)

    return [system_prompt] + rest


def model(user_input: str, chat_id: int) -> str:
    if chat_id not in histories:
        histories[chat_id] = [{"role": "system", "content": DEFAULT_SYSTEM_PROMPT}]

    histories[chat_id].append({"role": "user", "content": user_input})

    histories[chat_id] = trim_history(histories[chat_id])

    prompt = "".join(
        f"<|{msg['role']}|>\n{msg['content']}\n" for msg in histories[chat_id]
    )
    prompt += "<|assistant|>\n"

    n_input_tokens = len(llm.tokenize(prompt.encode("utf-8")))

    output = llm.create_completion(
        prompt=prompt,
        max_tokens=min(max(8, n_input_tokens * 2), 2048),
        stop=["<|user|>", "<|assistant|>", "<|system|>"],
        temperature=0.9,
        top_p=0.9,
        repeat_penalty=1.2,
    )

    answer = output["choices"][0]["text"].strip()
    answer = answer.split("<|assistant|>")[0].strip()

    histories[chat_id].append({"role": "assistant", "content": answer})
    histories[chat_id] = trim_history(histories[chat_id])

    return answer
