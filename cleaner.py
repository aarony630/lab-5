import re
import pandas as pd

REQUIRED_COLUMNS = {"Product Name", "ASIN", "Order ID"}

IT_KEYWORDS = {
    "cable", "monitor", "laptop", "keyboard", "mouse", "hub", "adapter",
    "router", "switch", "usb", "hdmi", "ethernet", "charger", "display",
    "webcam", "headset", "speaker", "microphone", "drive", "ssd", "ram",
}

MKSP_KEYWORDS = {
    "filament", "solder", "sensor", "resin", "cutter", "drill", "tape",
    "foam", "glue", "wire", "led", "arduino", "raspberry", "servo",
    "motor", "resistor", "capacitor", "breadboard", "nozzle",
}


def shorten_name(name: str, max_len: int = 40) -> str:
    if not isinstance(name, str):
        return ""
    name = re.split(r"[,\(\[]", name)[0].strip()
    name = re.sub(r"\s+", " ", name)
    return name[:max_len].strip()


def categorize_item(name: str) -> str:
    lower = name.lower()
    if any(kw in lower for kw in IT_KEYWORDS):
        return "IT"
    if any(kw in lower for kw in MKSP_KEYWORDS):
        return "MKSP"
    return "Unassigned"


def process_amazon_csv(df: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    result = pd.DataFrame()
    result["Original Name"] = df["Product Name"]
    result["Product Name"] = df["Product Name"].apply(shorten_name)
    result["Category"] = result["Product Name"].apply(categorize_item)
    result["Asset ID"] = [f"ASSET-{i + 1:04d}" for i in range(len(df))]
    result["Product Number"] = df["ASIN"].fillna(df.get("Order ID", ""))
    result["Import Date"] = pd.Timestamp.today().strftime("%Y-%m-%d")
    return result
