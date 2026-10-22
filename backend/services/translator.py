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
    if language.lower() in ["english", "en"]:
        return text

    target_code = LANG_MAP.get(language, LANG_MAP.get(language.capitalize(), LANG_MAP.get(language.lower(), None)))
    if not target_code and len(language) == 2:
        target_code = language.lower()

    # If language not found in map or is English, return original
    if target_code is None or target_code == "en":
        return text

    # Try GoogleTranslator first
    try:
        if len(text) <= 4500:
            translated = GoogleTranslator(source="auto", target=target_code).translate(text)
            if translated:
                return translated
    except Exception as e:
        pass

    # Try GTX endpoint fallback
    try:
        import urllib.request
        import urllib.parse
        import json
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_code}&dt=t&q=" + urllib.parse.quote(text[:3000])
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data and data[0]:
                return "".join([part[0] for part in data[0] if part[0]])
    except Exception as e:
        print(f"Translation error for language '{language}' (code: {target_code}): {e}")

    return text