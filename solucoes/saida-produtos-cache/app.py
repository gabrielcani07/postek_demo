import csv
import json
import os
import re
import socket
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "dados"
LOG_DIR = BASE_DIR / "logs"
WEB_DIR = BASE_DIR / "web"
POSTEK_DIR = BASE_DIR / "postek_app"
LAYOUT_PATH = POSTEK_DIR / "layout_textil.prn"

DEFAULT_SHEET_ID = "1zzlB_CjRyYvdNfOdZjh_5ifHF_bLw6QVgHRYK4Ro2iY"
INVENTORY_SOURCE = os.getenv(
    "INVENTORY_SOURCE",
    f"https://docs.google.com/spreadsheets/d/{DEFAULT_SHEET_ID}/edit?usp=sharing",
)
POSTEK_PRINTER_HOST = os.getenv("POSTEK_PRINTER_HOST", "")
POSTEK_PRINTER_PORT = int(os.getenv("POSTEK_PRINTER_PORT", "12346"))
PRINT_MODE = os.getenv("PRINT_MODE", "simulation").lower()
POSTEK_LABEL_HEIGHT_DOTS = os.getenv("POSTEK_LABEL_HEIGHT_DOTS", "")
POSTEK_LABEL_GAP_DOTS = os.getenv("POSTEK_LABEL_GAP_DOTS", "")
SAVE_PRINT_BATCH_FILES = os.getenv("SAVE_PRINT_BATCH_FILES", "0") == "1"


@dataclass
class Product:
    code: str
    description: str
    name: str = ""
    sku: str = ""
    price: str = ""
    category: str = ""
    size_color: str = ""
    unit_weight_g: str = ""
    composition: str = ""
    raw: dict[str, str] | None = None


class Inventory:
    def __init__(self) -> None:
        self.products: dict[str, Product] = {}
        self.last_loaded_at = ""
        self.last_error = ""

    def load(self) -> None:
        self.last_error = ""
        try:
            rows = load_csv_rows(INVENTORY_SOURCE)
            self.products = parse_products(rows)
            self.last_loaded_at = datetime.now().isoformat(timespec="seconds")
        except Exception as exc:
            self.last_error = str(exc)
            fallback = DATA_DIR / "produtos_exemplo.csv"
            if fallback.exists():
                rows = load_csv_rows(str(fallback))
                self.products = parse_products(rows)
                self.last_loaded_at = datetime.now().isoformat(timespec="seconds")

    def get(self, code: str) -> Product | None:
        return self.products.get(normalize_code(code))

    def status(self) -> dict[str, Any]:
        return {
            "source": INVENTORY_SOURCE,
            "products_count": len(self.products),
            "last_loaded_at": self.last_loaded_at,
            "last_error": self.last_error,
            "print_mode": PRINT_MODE,
            "printer_host": POSTEK_PRINTER_HOST,
            "printer_port": POSTEK_PRINTER_PORT,
        }


class ScanSession:
    def __init__(self) -> None:
        self.items: dict[str, int] = {}
        self.created_at = datetime.now().isoformat(timespec="seconds")

    def add(self, code: str) -> int:
        normalized = normalize_code(code)
        self.items[normalized] = self.items.get(normalized, 0) + 1
        return self.items[normalized]

    def remove_one(self, code: str) -> None:
        normalized = normalize_code(code)
        if normalized not in self.items:
            return
        self.items[normalized] -= 1
        if self.items[normalized] <= 0:
            del self.items[normalized]

    def clear(self) -> None:
        self.items.clear()
        self.created_at = datetime.now().isoformat(timespec="seconds")

    def summary(self, inventory: Inventory) -> list[dict[str, Any]]:
        result = []
        for code, quantity in sorted(self.items.items()):
            product = inventory.get(code)
            result.append(
                {
                    "code": code,
                    "quantity": quantity,
                    "found": product is not None,
                    "product": asdict(product) if product else None,
                }
            )
        return result


inventory = Inventory()
session = ScanSession()


def normalize_code(value: str) -> str:
    return "".join(str(value or "").strip().split())


def load_csv_rows(source: str) -> list[dict[str, str]]:
    source = normalize_inventory_source(source)
    if source.startswith("http://") or source.startswith("https://"):
        with urllib.request.urlopen(source, timeout=15) as response:
            content = response.read().decode("utf-8-sig")
    else:
        content = Path(source).read_text(encoding="utf-8-sig")
    return list(csv.DictReader(content.splitlines()))


def normalize_inventory_source(source: str) -> str:
    text = str(source or "").strip()
    parsed = urllib.parse.urlparse(text)
    if "docs.google.com" not in parsed.netloc or "/spreadsheets/d/" not in parsed.path:
        return text
    if parsed.path.endswith("/export") or "/gviz/tq" in parsed.path:
        return text

    sheet_id = parsed.path.split("/spreadsheets/d/", 1)[1].split("/", 1)[0]
    query = urllib.parse.parse_qs(parsed.query)
    gid = query.get("gid", ["0"])[0]
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid={gid}"


def first_value(row: dict[str, str], aliases: list[str]) -> str:
    normalized = {key.strip().lower(): value for key, value in row.items()}
    for alias in aliases:
        value = normalized.get(alias.lower())
        if value:
            return value.strip()
    return ""


def parse_products(rows: list[dict[str, str]]) -> dict[str, Product]:
    products: dict[str, Product] = {}
    for row in rows:
        code = normalize_code(
            first_value(row, ["codigo_barras", "codigo", "code", "barcode", "ean", "gtin", "sku"])
        )
        if not code:
            continue
        product = Product(
            code=code,
            sku=first_value(row, ["sku", "codigo_interno", "id"]),
            name=first_value(row, ["nome", "produto", "name"]),
            description=first_value(row, ["descricao", "descrição", "description", "produto", "nome"]),
            price=first_value(row, ["preco", "preço", "price", "valor"]),
            category=first_value(row, ["tipo", "categoria", "category", "linha"]),
            size_color=first_value(row, ["medidas", "tamanho_cor", "tamanho", "grade", "size", "cor"]),
            unit_weight_g=first_value(row, ["peso_unitario_g", "gramatura", "peso", "weight"]),
            composition=first_value(row, ["composicao", "composição", "composition", "tecido"]),
            raw={str(key): str(value) for key, value in row.items()},
        )
        if not product.price:
            product.price = first_value(row, ["preco_unitario"])
        products[code] = product
    if not products:
        raise ValueError("Nenhum produto encontrado. Confira as colunas da planilha.")
    return products


def build_print_lines(items: list[dict[str, Any]]) -> list[str]:
    lines = []
    for item in items:
        product = item["product"] or {}
        description = product.get("description") or product.get("name") or "Produto nao encontrado"
        for _ in range(int(item["quantity"])):
            payload = {
                "Input1": product.get("sku") or item["code"],
                "Input2": item["code"],
                "Input3": description,
                "Input4": product.get("size_color") or "-",
                "Input5": "1 un",
                "Input6": product.get("category") or "-",
                "Input7": format_money(product.get("price") or ""),
                "Input8": product.get("composition") or "-",
            }
            lines.append(json.dumps(payload, ensure_ascii=False))
    return lines


def format_money(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return "-"
    if text.startswith("R$"):
        return text
    return "R$ " + text.replace(".", ",")


def print_batch(items: list[dict[str, Any]]) -> dict[str, Any]:
    if any(not item["found"] for item in items):
        missing = [item["code"] for item in items if not item["found"]]
        return {"ok": False, "error": f"Produtos nao encontrados: {', '.join(missing)}"}

    lines = build_print_lines(items)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    printed_at = datetime.now().isoformat(timespec="seconds")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = None
    raw_log_path = None
    if SAVE_PRINT_BATCH_FILES:
        log_path = LOG_DIR / f"lote-{timestamp}.txt"
        log_path.write_text("\n".join(lines), encoding="utf-8")

    if PRINT_MODE == "tcp":
        if not POSTEK_PRINTER_HOST:
            return {"ok": False, "error": "POSTEK_PRINTER_HOST nao configurado."}
        payload = "\n".join(lines) + "\n"
        with socket.create_connection((POSTEK_PRINTER_HOST, POSTEK_PRINTER_PORT), timeout=10) as sock:
            sock.sendall(payload.encode("utf-8"))
    elif PRINT_MODE == "raw9100":
        if not POSTEK_PRINTER_HOST:
            return {"ok": False, "error": "POSTEK_PRINTER_HOST nao configurado."}
        payload = build_raw_print_payload(lines)
        if SAVE_PRINT_BATCH_FILES:
            raw_log_path = LOG_DIR / f"lote-{timestamp}.prn"
            raw_log_path.write_bytes(payload)
        with socket.create_connection((POSTEK_PRINTER_HOST, POSTEK_PRINTER_PORT), timeout=10) as sock:
            sock.sendall(payload)

    append_print_history(
        printed_at=printed_at,
        items=items,
        lines=lines,
        log_path=log_path,
        raw_log_path=raw_log_path,
    )
    return {
        "ok": True,
        "labels": len(lines),
        "log": str(LOG_DIR / "historico-impressoes.txt"),
        "mode": PRINT_MODE,
    }


def append_print_history(
    printed_at: str,
    items: list[dict[str, Any]],
    lines: list[str],
    log_path: Path | None,
    raw_log_path: Path | None,
) -> None:
    host_name = socket.gethostname()
    host_ip = get_local_ip()
    total_labels = sum(int(item["quantity"]) for item in items)
    event = {
        "printed_at": printed_at,
        "sent_from_host": host_name,
        "sent_from_ip": host_ip,
        "mode": PRINT_MODE,
        "printer_host": POSTEK_PRINTER_HOST,
        "printer_port": POSTEK_PRINTER_PORT,
        "labels": total_labels,
        "items": [
            {
                "code": item["code"],
                "quantity": item["quantity"],
                "sku": (item["product"] or {}).get("sku", ""),
                "description": (item["product"] or {}).get("description", ""),
            }
            for item in items
        ],
        "payload": [json.loads(line) for line in lines],
        "log_file": str(log_path) if log_path else "",
        "raw_log_file": str(raw_log_path) if raw_log_path else "",
    }

    history_jsonl = LOG_DIR / "historico-impressoes.jsonl"
    with history_jsonl.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event, ensure_ascii=False) + "\n")

    history_txt = LOG_DIR / "historico-impressoes.txt"
    with history_txt.open("a", encoding="utf-8") as file:
        file.write(f"[{printed_at}] host={host_name} ip={host_ip} modo={PRINT_MODE}\n")
        file.write(f"impressora={POSTEK_PRINTER_HOST}:{POSTEK_PRINTER_PORT} etiquetas={total_labels}\n")
        for item in event["items"]:
            file.write(
                f"- {item['code']} | qtd={item['quantity']} | sku={item['sku']} | {item['description']}\n"
            )
        if log_path:
            file.write(f"txt={log_path}\n")
        if raw_log_path:
            file.write(f"prn={raw_log_path}\n")
        file.write("\n")


def get_local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect((POSTEK_PRINTER_HOST or "8.8.8.8", POSTEK_PRINTER_PORT or 80))
            return sock.getsockname()[0]
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return ""


def build_raw_print_payload(lines: list[str]) -> bytes:
    layout = apply_raw_layout_settings(LAYOUT_PATH.read_bytes())
    commands = []
    for line in lines:
        values = json.loads(line)
        command = layout
        for index in range(1, 9):
            field = f"Input{index}"
            placeholder = f"#OX:{field}#".encode("ascii")
            value = raw_printer_value(values.get(field, "-"))
            command = command.replace(placeholder, value)
        commands.append(command)
    return b"".join(commands)


def apply_raw_layout_settings(layout: bytes) -> bytes:
    if not POSTEK_LABEL_HEIGHT_DOTS:
        return layout

    height = int(POSTEK_LABEL_HEIGHT_DOTS)
    gap = int(POSTEK_LABEL_GAP_DOTS or "25")
    return re.sub(rb"(?m)^Q\d+,\d+\s*$", f"Q{height},{gap}".encode("ascii"), layout)


def raw_printer_value(value: Any) -> bytes:
    text = str(value if value is not None else "-")
    text = text.replace("\r", " ").replace("\n", " ").replace('"', "'")
    return text.encode("latin-1", errors="replace")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = urllib.parse.urlparse(self.path).path
        if path == "/":
            self.send_file(WEB_DIR / "index.html", "text/html")
        elif path == "/app.css":
            self.send_file(WEB_DIR / "app.css", "text/css")
        elif path == "/app.js":
            self.send_file(WEB_DIR / "app.js", "application/javascript")
        elif path == "/api/status":
            self.send_json(inventory.status())
        elif path == "/api/session":
            self.send_json({"items": session.summary(inventory), "created_at": session.created_at})
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        path = urllib.parse.urlparse(self.path).path
        payload = self.read_json()
        if path == "/api/inventory/reload":
            inventory.load()
            self.send_json(inventory.status())
        elif path == "/api/scan":
            code = normalize_code(payload.get("code", ""))
            if not code:
                self.send_json({"ok": False, "error": "Codigo vazio."}, 400)
                return
            quantity = session.add(code)
            self.send_json({"ok": True, "code": code, "quantity": quantity, "items": session.summary(inventory)})
        elif path == "/api/remove":
            session.remove_one(payload.get("code", ""))
            self.send_json({"ok": True, "items": session.summary(inventory)})
        elif path == "/api/clear":
            session.clear()
            self.send_json({"ok": True, "items": []})
        elif path == "/api/print":
            items = session.summary(inventory)
            if not items:
                self.send_json({"ok": False, "error": "Nenhum item bipado."}, 400)
                return
            result = print_batch(items)
            if result["ok"]:
                session.clear()
                self.send_json(result)
            else:
                self.send_json(result, 400)
        else:
            self.send_error(404)

    def read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def send_json(self, data: dict[str, Any], status: int = 200) -> None:
        content = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_file(self, path: Path, content_type: str) -> None:
        content = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format: str, *args: Any) -> None:
        return


def main() -> None:
    inventory.load()
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8080"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Servidor iniciado em http://localhost:{port}")
    print(f"Produtos carregados: {len(inventory.products)}")
    if inventory.last_error:
        print(f"Aviso ao carregar planilha: {inventory.last_error}")
    server.serve_forever()


if __name__ == "__main__":
    main()
