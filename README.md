# KOBİ Dostu AI Operasyon Ajanı

Google Yapay Zeka ve Teknoloji Akademisi Hackathon projesi için hazırlanmış çalışan MVP.

Bu ürün, KOBİ ve kooperatiflerin sipariş, stok, kargo ve müşteri iletişimi süreçlerini yapay zeka destekli bir operasyon asistanıyla tek panelden yönetmesini sağlar.

## Özellikler

- FastAPI backend
- Gemini destekli AI cevap üretimi
- API key yoksa çalışan fallback mod
- Modern HTML/Tailwind arayüz
- Stok sorgulama
- Kritik stok uyarısı
- Sipariş ve kargo durumu sorgulama
- Geciken kargo tespiti
- Günlük operasyon özeti

## Güvenlik Notu

API key kod içine yazılmamalıdır. Bu projede Gemini API key `.env` dosyasından okunur.

`.env` dosyası GitHub'a gönderilmemelidir.

## Kurulum

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

`.env` dosyasını açıp kendi Gemini API key'inizi ekleyin:

```env
GEMINI_API_KEY=buraya_yeni_key
```

Gemini key eklemeden de uygulama fallback modda çalışır.

## Çalıştırma

```bash
uvicorn main:app --reload
```

Tarayıcıda açın:

```text
http://127.0.0.1:8000
```

## Demo Soruları

```text
Bugünkü operasyon özetini ver.
128 numaralı sipariş nerede?
Hangi ürünlerde stok kritik?
Domates stoğu ne durumda?
Geciken kargoları listele.
```

## Değer Önerisi

KOBİ’lerin manuel operasyon yükünü azaltır; sipariş, stok ve kargo takibini hızlı ve izlenebilir hale getirir.
