import sqlalchemy
from database import metadata

profiles = sqlalchemy.Table(
    "profiles",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String, nullable=False, unique=True),
    sqlalchemy.Column("gender", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("gender_probability", sqlalchemy.Float, nullable=False),
    sqlalchemy.Column("sample_size", sqlalchemy.Integer, nullable=False),
    sqlalchemy.Column("age", sqlalchemy.Integer, nullable=False),
    sqlalchemy.Column("age_group", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("country_id", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("country_probability", sqlalchemy.Float, nullable=False),
    sqlalchemy.Column("created_at", sqlalchemy.String, nullable=False),
)
