import asyncio
import csv
import sys
import time

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import create_async_engine

from src.core.config import get_settings
from src.models.nutrition import Food, FoodPortion

FOOD_BATCH_SIZE = 3500
PORTION_BATCH_SIZE = 7000
PROGRESS_EVERY = 20

FOOD_FLUSHES_PER_TX = 20
PORTION_FLUSHES_PER_TX = 20

settings = get_settings()
engine = create_async_engine(
    settings.database_url,
    echo=False,
    hide_parameters=True,
)


def get_csv_reader(file_path):
    with open(file_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        yield from reader


def to_int(value):
    v = (value or "").strip()
    if not v:
        return None
    try:
        return int(v)
    except ValueError:
        return None


def to_float(value, default=0.0):
    v = (value or "").strip()
    if not v:
        return default
    try:
        return float(v)
    except ValueError:
        return default


def format_seconds(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.2f}s"
    minutes, sec = divmod(seconds, 60)
    if minutes < 60:
        return f"{int(minutes)}m {sec:.1f}s"
    hours, minutes = divmod(minutes, 60)
    return f"{int(hours)}h {int(minutes)}m {sec:.0f}s"


async def clear_loader_tables(conn):
    print("Clearing existing loader data...")
    started = time.perf_counter()

    await conn.execute(text("TRUNCATE TABLE food_portion RESTART IDENTITY"))
    await conn.execute(text("DELETE FROM food"))

    print(f"[TIMER] Clear tables: {format_seconds(time.perf_counter() - started)}")


async def insert_food_batch(conn, batch):
    await conn.execute(insert(Food), batch)


async def load_usda_data(csv_path: str):
    total_started = time.perf_counter()

    async with engine.begin() as conn:
        await clear_loader_tables(conn)

    print("Pre-loading nutrient data...")
    nutrient_started = time.perf_counter()
    nutrient_lookup = {}
    target_ids = {"1008": "cal", "1003": "pro", "1004": "fat", "1005": "carb"}

    for row in get_csv_reader(f"{csv_path}/food_nutrient.csv"):
        n_id = (row.get("nutrient_id") or "").strip()
        if n_id not in target_ids:
            continue

        fdc_id = to_int(row.get("fdc_id"))
        if fdc_id is None:
            continue

        if fdc_id not in nutrient_lookup:
            nutrient_lookup[fdc_id] = {"cal": 0.0, "pro": 0.0, "fat": 0.0, "carb": 0.0}

        nutrient_lookup[fdc_id][target_ids[n_id]] = to_float(row.get("amount"), 0.0)

    nutrient_elapsed = time.perf_counter() - nutrient_started
    print(f"[TIMER] Nutrient preload: {format_seconds(nutrient_elapsed)}")

    print("Pre-loading brand data...")
    brand_started = time.perf_counter()
    brand_lookup = {}
    for row in get_csv_reader(f"{csv_path}/branded_food.csv"):
        fdc_id = to_int(row.get("fdc_id"))
        if fdc_id is None:
            continue
        brand_lookup[fdc_id] = (row.get("brand_owner") or "")[:255] or None

    brand_elapsed = time.perf_counter() - brand_started
    print(f"[TIMER] Brand preload: {format_seconds(brand_elapsed)}")

    print("Streaming foods to database...")
    foods_started = time.perf_counter()
    batch = []
    food_rows = 0
    food_flushes = 0
    food_skipped = 0

    async with engine.connect() as conn:
        tx = await conn.begin()
        food_flushes_in_tx = 0

        try:
            for row in get_csv_reader(f"{csv_path}/food.csv"):
                food_rows += 1

                fdc_id = to_int(row.get("fdc_id"))
                if fdc_id is None:
                    food_skipped += 1
                    continue

                nutrients = nutrient_lookup.get(
                    fdc_id, {"cal": 0.0, "pro": 0.0, "fat": 0.0, "carb": 0.0}
                )

                food_item = {
                    "fdc_id": fdc_id,
                    "name": (row.get("description") or "Unknown")[:255],
                    "brand_name": brand_lookup.get(fdc_id),
                    "data_type": row.get("data_type"),
                    "calories_per_100g": nutrients["cal"],
                    "protein_per_100g": nutrients["pro"],
                    "fat_per_100g": nutrients["fat"],
                    "carbs_per_100g": nutrients["carb"],
                    "is_verified": False,
                }
                batch.append(food_item)

                if len(batch) >= FOOD_BATCH_SIZE:
                    await insert_food_batch(conn, batch)
                    batch = []
                    food_flushes += 1
                    food_flushes_in_tx += 1

                    if PROGRESS_EVERY > 0 and food_flushes % PROGRESS_EVERY == 0:
                        elapsed = time.perf_counter() - foods_started
                        rate = food_rows / elapsed if elapsed > 0 else 0.0
                        print(
                            f"[PROGRESS] foods rows={food_rows}, flushes={food_flushes}, "
                            f"skipped={food_skipped}, elapsed={format_seconds(elapsed)}, rate={rate:.1f} rows/s"
                        )

                    if food_flushes_in_tx >= FOOD_FLUSHES_PER_TX:
                        await tx.commit()
                        tx = await conn.begin()
                        food_flushes_in_tx = 0

            if batch:
                await insert_food_batch(conn, batch)
                food_flushes += 1

            await tx.commit()
        except Exception:
            await tx.rollback()
            raise

    foods_elapsed = time.perf_counter() - foods_started
    foods_rate = food_rows / foods_elapsed if foods_elapsed > 0 else 0.0
    print(
        f"[TIMER] Foods load: {format_seconds(foods_elapsed)} "
        f"(rows={food_rows}, skipped={food_skipped}, flushes={food_flushes}, avg_rate={foods_rate:.1f} rows/s)"
    )

    print("Building food id map...")
    id_map_started = time.perf_counter()
    async with engine.connect() as conn:
        rows = await conn.execute(select(Food.id, Food.fdc_id))
        id_map = {fdc_id: internal_id for internal_id, fdc_id in rows if fdc_id is not None}
    id_map_elapsed = time.perf_counter() - id_map_started
    print(f"[TIMER] Food id map: {format_seconds(id_map_elapsed)} (size={len(id_map)})")

    print("Streaming portions...")
    portions_started = time.perf_counter()
    batch = []
    portion_rows = 0
    portion_flushes = 0
    portion_skipped = 0

    async with engine.connect() as conn:
        tx = await conn.begin()
        portion_flushes_in_tx = 0

        try:
            for row in get_csv_reader(f"{csv_path}/food_portion.csv"):
                fdc_id = to_int(row.get("fdc_id"))
                if fdc_id is None:
                    portion_skipped += 1
                    continue

                if fdc_id in id_map:
                    portion_rows += 1
                    portion = {
                        "food_id": id_map[fdc_id],
                        "amount": to_float(row.get("amount"), 1.0),
                        "measure_unit_name": (row.get("modifier") or "serving")[:100],
                        "gram_weight": to_float(row.get("gram_weight"), 0.0),
                    }
                    batch.append(portion)
                else:
                    portion_skipped += 1

                if len(batch) >= PORTION_BATCH_SIZE:
                    await conn.execute(insert(FoodPortion), batch)
                    batch = []
                    portion_flushes += 1
                    portion_flushes_in_tx += 1

                    if PROGRESS_EVERY > 0 and portion_flushes % PROGRESS_EVERY == 0:
                        elapsed = time.perf_counter() - portions_started
                        rate = portion_rows / elapsed if elapsed > 0 else 0.0
                        print(
                            f"[PROGRESS] portions rows={portion_rows}, flushes={portion_flushes}, "
                            f"skipped={portion_skipped}, elapsed={format_seconds(elapsed)}, rate={rate:.1f} rows/s"
                        )

                    if portion_flushes_in_tx >= PORTION_FLUSHES_PER_TX:
                        await tx.commit()
                        tx = await conn.begin()
                        portion_flushes_in_tx = 0

            if batch:
                await conn.execute(insert(FoodPortion), batch)
                portion_flushes += 1

            await tx.commit()
        except Exception:
            await tx.rollback()
            raise

    portions_elapsed = time.perf_counter() - portions_started
    portions_rate = portion_rows / portions_elapsed if portions_elapsed > 0 else 0.0
    print(
        f"[TIMER] Portions load: {format_seconds(portions_elapsed)} "
        f"(rows={portion_rows}, skipped={portion_skipped}, flushes={portion_flushes}, avg_rate={portions_rate:.1f} rows/s)"
    )

    total_elapsed = time.perf_counter() - total_started
    print(f"[TIMER] Total operation: {format_seconds(total_elapsed)}")

    await engine.dispose()
    print("Database was successfully populated.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m src.scripts.load_fdc_data <csv_path>")
        raise SystemExit(1)

    asyncio.run(load_usda_data(sys.argv[1]))