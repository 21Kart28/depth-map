from anthropic import Anthropic

MODEL = "claude-haiku-5-5"

QUESTION = (
    "What is something you keep telling yourself you'll deal with later? "
    "What happens when you imagine dealing with it now?"
)

SYSTEM_PROMPT = (
    "Reflect the user's answer back to them in two or three sentences, "
    "using their own words where you can. Don't give advice."
)


def main():
    # reads ANTHROPIC_API_KEY from the environment
    client = Anthropic()

    print(QUESTION)
    response = input("> ")

    message = client.messages.create(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Question: {QUESTION}\n\nAnswer: {response}"}],
    )
    # thinking is on by default for this model, so the reply can start with a thinking block
    reply = next(block.text for block in message.content if block.type == "text")
    print()
    print(reply)


if __name__ == "__main__":
    main()
