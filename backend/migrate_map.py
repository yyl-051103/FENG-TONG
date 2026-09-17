from sqlalchemy import text
from app.database import SessionLocal

db = SessionLocal()
try:
    cols = db.execute(text("SHOW COLUMNS FROM news")).fetchall()
    col_names = [c[0] for c in cols]
    print("Existing:", col_names)

    migrations = [
        ("latitude", "DOUBLE", "纬度"),
        ("longitude", "DOUBLE", "经度"),
        ("location", "VARCHAR(255)", "地址描述"),
    ]
    for col, col_type, comment in migrations:
        if col not in col_names:
            sql = f"ALTER TABLE news ADD COLUMN {col} {col_type} NULL COMMENT '{comment}'"
            db.execute(text(sql))
            print(f"Added {col}")

    db.commit()
    print("Done")
except Exception as e:
    db.rollback()
    print(f"Error: {e}")
finally:
    db.close()
