Execute the following commands equentially in order to import data into MongoDB and PostgreSQL:

```bash
uv run -m initializer.pois --uri mongodb://root:fudanse@localhost:27017
uv run -m initializer.hotels --uri mongodb://root:fudanse@localhost:27017
uv run -m initializer.room_types --uri mongodb://root:fudanse@localhost:27017
uv run -m initializer.attractions --uri mongodb://root:fudanse@localhost:27017
uv run -m initializer.spus --uri mongodb://root:fudanse@localhost:27017
uv run -m initializer.inventories --dsn postgresql://postgres:fudanse@localhost:5432/inventory_db
```