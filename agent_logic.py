import os
import google.generativeai as genai
from database import DATABASE

def run_kobi_agent(user_message: str):
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        return "Gemini API key bulunamadı. Uygulama fallback modda çalışmalıdır."

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    system_prompt = f"""
    Sen bir KOBİ/Kooperatif operasyon asistanısın.
    Mevcut stok verilerin: {DATABASE}
    Kullanıcıya kısa, net ve profesyonel cevap ver.
    Kod içine API key yazma; key sadece .env dosyasından okunmalıdır.
    """

    response = model.generate_content(
        f"{system_prompt}\n\nKullanıcı Sorusu: {user_message}"
    )
    return response.text