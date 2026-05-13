import os
from typing import Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

load_dotenv()

try:
    import google.generativeai as genai
except Exception:
    genai = None

app = FastAPI(title="KOBİ Dostu AI Operasyon Ajanı")

# Demo veritabanı: Hackathon demosu için gerçekçi KOBİ/kooperatif stok ve operasyon verisi.
DATABASE: Dict[str, Dict[str, Any]] = {
    "domates": {
        "stok": 45,
        "esik": 50,
        "birim": "kg",
        "tedarikci": "tarim@koop.com",
        "kategori": "Tarım",
        "gunluk_satis": 18,
    },
    "zeytinyagi": {
        "stok": 120,
        "esik": 30,
        "birim": "litre",
        "tedarikci": "ege@koop.com",
        "kategori": "Gıda",
        "gunluk_satis": 5,
    },
    "salca": {
        "stok": 15,
        "esik": 30,
        "birim": "kavanoz",
        "tedarikci": "fabrika@koop.com",
        "kategori": "Gıda",
        "gunluk_satis": 7,
    },
    "sabun": {
        "stok": 9,
        "esik": 20,
        "birim": "adet",
        "tedarikci": "dogal@atolye.com",
        "kategori": "El Sanatları",
        "gunluk_satis": 4,
    },
}

ORDERS = {
    "128": {
        "musteri": "Ayşe Yılmaz",
        "durum": "Kargoda",
        "kargo": "EgeKargo",
        "takip_no": "TRK1282026",
        "tahmini_teslim": "Yarın",
        "gecikme": True,
        "son_guncelleme": "Aktarma merkezinde yoğunluk nedeniyle gecikme işareti var.",
    },
    "129": {
        "musteri": "Mehmet Kaya",
        "durum": "Hazırlanıyor",
        "kargo": "Henüz kargoya verilmedi",
        "takip_no": "-",
        "tahmini_teslim": "Bugün kargoya verilmesi bekleniyor",
        "gecikme": False,
        "son_guncelleme": "Depoda paketleme aşamasında.",
    },
    "130": {
        "musteri": "Elif Demir",
        "durum": "Teslim Edildi",
        "kargo": "HızlıKargo",
        "takip_no": "TRK1302026",
        "tahmini_teslim": "Teslim edildi",
        "gecikme": False,
        "son_guncelleme": "Sipariş müşteriye teslim edildi.",
    },
}


class ChatRequest(BaseModel):
    message: str


def normalize(text: str) -> str:
    return (
        text.lower()
        .replace("ı", "i")
        .replace("ğ", "g")
        .replace("ü", "u")
        .replace("ş", "s")
        .replace("ö", "o")
        .replace("ç", "c")
    )


def find_product(message: str):
    text = normalize(message)
    for name in DATABASE:
        if normalize(name) in text:
            return name, DATABASE[name]
    return None, None


def find_order(message: str):
    for order_no in ORDERS:
        if order_no in message:
            return order_no, ORDERS[order_no]
    return None, None


def critical_products():
    return {
        name: data
        for name, data in DATABASE.items()
        if data["stok"] <= data["esik"]
    }


def fallback_agent(user_message: str) -> str:
    """Gemini API yoksa veya hata verirse demo yine çalışsın diye deterministik cevap üretir."""
    text = normalize(user_message)

    order_no, order = find_order(user_message)
    if order_no:
        delay_note = (
            " Bu siparişte gecikme riski var; müşteriye bilgilendirme mesajı gönderilmesi önerilir."
            if order["gecikme"]
            else ""
        )
        return (
            f"{order_no} numaralı sipariş {order['musteri']} adına kayıtlı. "
            f"Durum: {order['durum']}. Kargo: {order['kargo']}. "
            f"Takip no: {order['takip_no']}. Tahmini teslim: {order['tahmini_teslim']}. "
            f"Son güncelleme: {order['son_guncelleme']}.{delay_note}"
        )

    if any(word in text for word in ["kritik", "az", "stok", "envanter"]):
        product_name, product = find_product(user_message)
        if product_name:
            status = "kritik seviyede" if product["stok"] <= product["esik"] else "güvenli seviyede"
            answer = (
                f"{product_name.capitalize()} stoğu {product['stok']} {product['birim']}. "
                f"Kritik eşik {product['esik']} {product['birim']}; şu an {status}."
            )
            if product["stok"] <= product["esik"]:
                target_stock = product["gunluk_satis"] * 14
                suggested = max(0, int(target_stock - product["stok"]))
                answer += (
                    f" 14 günlük güvenli stok için yaklaşık {suggested} {product['birim']} "
                    f"sipariş önerilir. Tedarikçi: {product['tedarikci']}."
                )
            return answer

        critical = critical_products()
        if not critical:
            return "Şu anda kritik stok seviyesinde ürün görünmüyor."
        lines = []
        for name, data in critical.items():
            lines.append(f"• {name.capitalize()}: {data['stok']} {data['birim']} kaldı. Kritik eşik: {data['esik']} {data['birim']}.")
        return "Kritik stoktaki ürünler:\n" + "\n".join(lines)

    if any(word in text for word in ["gecik", "kargo", "teslimat"]):
        delayed = {no: o for no, o in ORDERS.items() if o["gecikme"]}
        if not delayed:
            return "Şu anda gecikme riski taşıyan kargo görünmüyor."
        lines = []
        for no, order in delayed.items():
            lines.append(f"• Sipariş {no}: {order['musteri']} - {order['son_guncelleme']}")
        return "Gecikme riski olan kargolar:\n" + "\n".join(lines)

    if any(word in text for word in ["ozet", "bugun", "günlük", "dashboard"]):
        crit_count = len(critical_products())
        delayed_count = len([o for o in ORDERS.values() if o["gecikme"]])
        return (
            f"Bugünkü operasyon özeti: {len(ORDERS)} sipariş takip ediliyor. "
            f"{crit_count} ürün kritik stok seviyesinde, {delayed_count} kargoda gecikme riski var. "
            "Öncelik: kritik stoklar için tedarik aksiyonu almak ve geciken sipariş müşterilerini bilgilendirmek."
        )

    return (
        "Ben KOBİ Dostu AI Operasyon Ajanı'yım. "
        "Sipariş durumu, stok seviyesi, kritik ürünler ve kargo gecikmeleri hakkında yardımcı olabilirim. "
        "Örnek: '128 numaralı sipariş nerede?' veya 'Hangi ürünlerde stok kritik?'"
    )


def gemini_agent(user_message: str) -> str | None:
    """API anahtarı .env dosyasından okunur. Kod içine asla key yazılmaz."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or genai is None:
        return None

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""
        Sen KOBİ ve kooperatifler için çalışan Türkçe bir operasyon asistanısın.
        Aşağıdaki demo verileri dışında bilgi uydurma.

        STOK VERİSİ:
        {DATABASE}

        SİPARİŞ VERİSİ:
        {ORDERS}

        Kullanıcı sorusu: {user_message}

        Kurallar:
        - Cevabı kısa, net ve profesyonel ver.
        - Kritik stok varsa tedarik aksiyonu öner.
        - Kargo gecikmesi varsa müşteriye bilgilendirme öner.
        - Veride yoksa 'Bu bilgi mevcut veri setinde bulunmuyor' de.
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception:
        return None


def run_agent(user_message: str) -> str:
    return gemini_agent(user_message) or fallback_agent(user_message)


@app.get("/api/health")
def health():
    return {"status": "ok", "gemini_enabled": bool(os.getenv("GEMINI_API_KEY", "").strip())}


@app.get("/api/dashboard")
def dashboard():
    return {
        "product_count": len(DATABASE),
        "order_count": len(ORDERS),
        "critical_stock_count": len(critical_products()),
        "delayed_order_count": len([o for o in ORDERS.values() if o["gecikme"]]),
        "critical_products": critical_products(),
        "orders": ORDERS,
    }


@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    return {"reply": run_agent(req.message)}


@app.get("/", response_class=HTMLResponse)
def get_ui():
    return """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>KOBİ Dostu AI</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-emerald-900 text-slate-900 p-4 md:p-8 font-sans">
        <main class="max-w-6xl mx-auto">
            <section class="text-white mb-6">
                <div class="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 border border-white/20 mb-4">
                    <span>🚀</span><span class="text-sm font-semibold">YZTA Hackathon MVP</span>
                </div>
                <h1 class="text-4xl md:text-6xl font-black tracking-tight">KOBİ Dostu AI Operasyon Ajanı</h1>
                <p class="mt-4 text-lg text-blue-100 max-w-3xl">
                    Sipariş, stok, kargo ve günlük operasyon süreçlerini yapay zeka destekli tek panelde yönetin.
                </p>
            </section>

            <section class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6" id="cards"></section>

            <section class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div class="lg:col-span-2 bg-white/95 backdrop-blur rounded-3xl shadow-2xl overflow-hidden border border-white/40">
                    <div class="p-5 border-b bg-slate-50 flex items-center justify-between">
                        <div>
                            <h2 class="text-xl font-black">🤖 AI Operasyon Asistanı</h2>
                            <p class="text-sm text-slate-500">Doğal dille sipariş, stok ve kargo sorgulayın.</p>
                        </div>
                        <span id="geminiBadge" class="text-xs font-bold px-3 py-1 rounded-full bg-slate-200 text-slate-700">Kontrol ediliyor</span>
                    </div>
                    <div id="chat" class="h-[430px] overflow-y-auto p-5 space-y-4 bg-slate-50">
                        <div class="text-left">
                            <span class="bg-white border p-4 rounded-2xl rounded-tl-none inline-block shadow-sm max-w-[85%]">
                                Hoş geldiniz! Örnek: <b>128 numaralı sipariş nerede?</b> veya <b>Hangi ürünlerde stok kritik?</b>
                            </span>
                        </div>
                    </div>
                    <div class="p-5 bg-white border-t">
                        <div class="flex flex-wrap gap-2 mb-3">
                            <button onclick="quick('Bugünkü operasyon özetini ver.')" class="px-3 py-2 rounded-full bg-blue-50 text-blue-700 text-sm font-bold">Günlük özet</button>
                            <button onclick="quick('128 numaralı sipariş nerede?')" class="px-3 py-2 rounded-full bg-blue-50 text-blue-700 text-sm font-bold">Sipariş 128</button>
                            <button onclick="quick('Hangi ürünlerde stok kritik?')" class="px-3 py-2 rounded-full bg-orange-50 text-orange-700 text-sm font-bold">Kritik stok</button>
                            <button onclick="quick('Geciken kargoları listele.')" class="px-3 py-2 rounded-full bg-red-50 text-red-700 text-sm font-bold">Geciken kargo</button>
                        </div>
                        <div class="flex gap-3">
                            <input id="input" class="flex-1 border-2 border-slate-100 p-4 rounded-2xl outline-none focus:border-blue-500 transition" placeholder="Mesajınızı yazın...">
                            <button onclick="send()" class="bg-blue-600 hover:bg-blue-700 text-white px-7 rounded-2xl font-black shadow-lg transition">Gönder</button>
                        </div>
                    </div>
                </div>

                <div class="bg-white/95 backdrop-blur rounded-3xl shadow-2xl border border-white/40 p-5">
                    <h2 class="text-xl font-black mb-4">📌 Canlı Operasyon Görünümü</h2>
                    <div id="sidePanel" class="space-y-3"></div>
                </div>
            </section>
        </main>

        <script>
            const chat = document.getElementById('chat');
            const input = document.getElementById('input');

            function addMessage(role, text) {
                const isUser = role === 'user';
                const div = document.createElement('div');
                div.className = isUser ? 'text-right' : 'text-left';
                div.innerHTML = `<span class="${isUser ? 'bg-blue-600 text-white rounded-tr-none' : 'bg-white border text-slate-800 rounded-tl-none'} p-4 rounded-2xl inline-block shadow-sm max-w-[85%] whitespace-pre-line">${text}</span>`;
                chat.appendChild(div);
                chat.scrollTop = chat.scrollHeight;
            }

            function quick(text) {
                input.value = text;
                send();
            }

            async function send() {
                const msg = input.value.trim();
                if (!msg) return;
                addMessage('user', msg);
                input.value = '';
                const loading = 'Yanıt hazırlanıyor...';
                addMessage('assistant', loading);
                const last = chat.lastChild;
                try {
                    const res = await fetch('/api/chat', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({message: msg})
                    });
                    const data = await res.json();
                    last.querySelector('span').textContent = data.reply;
                } catch (err) {
                    last.querySelector('span').textContent = 'Backend bağlantısında hata oluştu.';
                }
            }

            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') send();
            });

            async function loadDashboard() {
                const health = await fetch('/api/health').then(r => r.json());
                document.getElementById('geminiBadge').textContent = health.gemini_enabled ? 'Gemini aktif' : 'Fallback mod';
                document.getElementById('geminiBadge').className = health.gemini_enabled
                    ? 'text-xs font-bold px-3 py-1 rounded-full bg-emerald-100 text-emerald-700'
                    : 'text-xs font-bold px-3 py-1 rounded-full bg-amber-100 text-amber-700';

                const data = await fetch('/api/dashboard').then(r => r.json());
                const cards = document.getElementById('cards');
                cards.innerHTML = `
                    <div class="bg-white/95 rounded-3xl p-5 shadow-xl"><p class="text-slate-500 text-sm font-bold">Ürün Sayısı</p><h3 class="text-3xl font-black">${data.product_count}</h3></div>
                    <div class="bg-white/95 rounded-3xl p-5 shadow-xl"><p class="text-slate-500 text-sm font-bold">Sipariş Sayısı</p><h3 class="text-3xl font-black">${data.order_count}</h3></div>
                    <div class="bg-white/95 rounded-3xl p-5 shadow-xl"><p class="text-slate-500 text-sm font-bold">Kritik Stok</p><h3 class="text-3xl font-black text-orange-600">${data.critical_stock_count}</h3></div>
                    <div class="bg-white/95 rounded-3xl p-5 shadow-xl"><p class="text-slate-500 text-sm font-bold">Geciken Kargo</p><h3 class="text-3xl font-black text-red-600">${data.delayed_order_count}</h3></div>
                `;

                const side = document.getElementById('sidePanel');
                const critical = Object.entries(data.critical_products).map(([name, p]) =>
                    `<div class="p-4 rounded-2xl bg-orange-50 border border-orange-100"><b>⚠️ ${name}</b><br><span class="text-sm text-slate-600">${p.stok} ${p.birim} kaldı. Eşik: ${p.esik}</span></div>`
                ).join('');
                side.innerHTML = critical || '<div class="p-4 rounded-2xl bg-emerald-50 border border-emerald-100">✅ Kritik stok yok.</div>';
            }
            loadDashboard();
        </script>
    </body>
    </html>
    """
