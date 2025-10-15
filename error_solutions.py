from typing import Optional


async def send_long_message(reply_func, text: str, chunk_size: int = 4096) -> None:

	if not text:
		return
	if len(text) <= chunk_size:
		await reply_func(text)
		return
	for i in range(0, len(text), chunk_size):
		await reply_func(text[i:i + chunk_size])


async def safe_reply(update, text: str, chunk_size: int = 4096) -> None:

	message = getattr(update, 'message', None)
	if message is None:
		return
	await send_long_message(message.reply_text, text, chunk_size)


