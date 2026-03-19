# Telegram VPS Bot v3

## Fitur baru
- Progress bar 1 pesan yang terus diupdate saat proses install / reboot / monitor berjalan.
- Tidak menumpuk banyak pesan progress.
- Input data VPS langsung dari Telegram.
- Multi VPS, switch VPS, delete VPS.

## Install
```bash
pip3 install -r requirements.txt
```

## Jalankan
Set environment:
```bash
export BOT_TOKEN="TOKEN_BOT_ANDA"
export ADMIN_IDS="123456789"
python3 bot.py
```

## Catatan progress bar
Progress bar ini adalah progress **estimasi visual** agar user tahu proses masih berjalan.
Saat command selesai, bar langsung berubah ke 100% dan output akhir ditampilkan di pesan yang sama.
