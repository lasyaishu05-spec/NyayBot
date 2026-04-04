from deep_translator import GoogleTranslator

# Map language names to Google Translate language codes
LANG_MAP = {
    "English": "en",
    "Hindi": "hi",
    "Telugu": "te",
    "Tamil": "ta",
    "Kannada": "kn",
    "Bengali": "bn",
    "Marathi": "mr",
    "Gujarati": "gu",
    "Malayalam": "ml",
    "Punjabi": "pa",
    "Urdu": "ur",
    "Odia": "or",
}


def translate_text(text, language):
    """Translate text into the target language using Google Translate (free)."""
    if not text or not text.strip():
        return text

    # If target is English, no translation needed
    if language.lower() == "english":
        return text

    target_code = LANG_MAP.get(language, None)

    # If language not found in map or is English, return original
    if target_code is None or target_code == "en":
        return text

    try:
        # deep-translator has a 5000 char limit per request, so chunk if needed
        if len(text) <= 4500:
            translated = GoogleTranslator(source="auto", target=target_code).translate(text)
            return translated or text
        else:
            # Split into smaller chunks for translation
            chunks = []
            sentences = text.split(". ")
            current_chunk = ""

            for sentence in sentences:
                if len(current_chunk) + len(sentence) + 2 < 4500:
                    current_chunk += sentence + ". "
                else:
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence + ". "

            if current_chunk.strip():
                chunks.append(current_chunk.strip())

            translated_chunks = []
            for chunk in chunks:
                translated = GoogleTranslator(source="auto", target=target_code).translate(chunk)
                if translated:
                    translated_chunks.append(translated)
                else:
                    translated_chunks.append(chunk)

            return " ".join(translated_chunks)

    except Exception as e:
        print(f"Translation error for language '{language}' (code: {target_code}): {e}")
        return text  # Return original text on failure, not an error message