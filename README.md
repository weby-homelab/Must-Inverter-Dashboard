# MUST Power Desk v0.1.1

Локальний read-only веб-дашборд для MUST PV18-3224 VPM II / PV1800. Сервіс читає перевірені Modbus RTU holding registers через USB CH340, зберігає samples у SQLite та віддає live-оновлення через Server-Sent Events.

## Запуск

```bash
cd /root/weby/projects/Must-Inverter-Dashboard
cp .env.example .env
python3 -m unittest discover -s tests -v
python3 main.py
```

Відкрити `http://127.0.0.1:8090`.

Для локального запуску потрібен `pyserial`:

```bash
python3 -m pip install -r requirements.txt
```

На `yoga` пакет вже був доступний під час апаратної перевірки.

## Налаштування

Основні змінні знаходяться у `.env.example`. За замовчуванням:

- serial: `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0`;
- Modbus: slave `4`, `19200 8N1`, function `03`;
- poll: кожні 15 секунд;
- persistence: один sample на хвилину;
- configuration refresh: кожні 5 хвилин;
- retention: 730 днів;
- database: `data/inverter.sqlite3`.

Dashboard підтримує history resolutions `minute` (1 хв), `30m` (30 хв), `hour`, `day`, `week`, `month` і `raw`. Для добового графіка за замовчуванням використовується 30-хвилинна resolution; 1-хвилинна доступна через selector/API.

В інвертор не відправляються write-команди. Застосунок читає такі діапазони:

| Section | Start | Count | Призначення |
| --- | ---: | ---: | --- |
| identity | 20001 | 16 | модель та версії |
| charger status | 15201 | 21 | PV/charger стан |
| inverter status | 25201 | 79 | AC, power, temperatures |
| charger config | 10101 | 24 | параметри заряджання |
| inverter config | 20101 | 44 | параметри інвертора |

## API

- `GET /api/current` — останній snapshot та health.
- `GET /api/health` — стан poller, помилки та статистика SQLite.
- `GET /healthz` — readiness endpoint: `503`, якщо інвертор offline або sample застарів.
- `GET /api/history?range=24h&period=minute` — хвилинна history.
- `GET /api/history?range=24h&period=30m` — 30-хвилинна history.
- `GET /api/history?range=24h&period=hour` — history buckets.
- `GET /api/history?range=30d&period=day` — денна агрегація.
- `GET /api/history?range=1y&period=month` — місячна агрегація.
- `GET /api/history?range=24h&period=raw` — raw samples, до 20 000 останніх точок.
- `GET /api/export.csv?range=30d&period=day` — CSV export.
- `GET /api/events` — SSE live events.

## v0.1.1

- Додано resolutions `minute` і `30m`.
- Додано перемикач мови `UKR | ENG` із збереженням вибору в браузері.
- Розширено локалізацію current, history, diagnostics і configuration UI.

## systemd

Unit-файл: `deploy/must-inverter-dashboard.service`.

```bash
sudo setfacl -m u:weby:--x /root
sudo chown -R weby:weby data
sudo chmod 0750 data
sudo install -m 0644 deploy/must-inverter-dashboard.service /etc/systemd/system/must-inverter-dashboard.service
sudo systemctl daemon-reload
sudo systemctl enable --now must-inverter-dashboard.service
systemctl status must-inverter-dashboard.service
journalctl -u must-inverter-dashboard.service -f
```

Unit запускається від non-root `weby`; systemd додає лише групу `dialout` для serial device. Через те, що каталог проєкту знаходиться під `/root`, перед першим запуском треба надати `weby` лише право traversal до `/root` і write-доступ до `data`. Сервіс обмежений localhost, не має write API та має systemd filesystem hardening; перед remote exposure потрібна окрема auth/reverse-proxy політика.

## Перевірки

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q .
curl -fsS http://127.0.0.1:8090/api/health
```
