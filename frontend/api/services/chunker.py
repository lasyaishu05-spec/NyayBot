def chunk_text(text, size=800):
    """Split text into chunks of roughly 'size' words each."""
    if not text or not text.strip():
        return [text or ""]

    words = text.split()
    chunks = []

    for i in range(0, len(words), size):
        chunk = " ".join(words[i:i + size])
        if chunk.strip():
            chunks.append(chunk)

    return chunks if chunks else [text]