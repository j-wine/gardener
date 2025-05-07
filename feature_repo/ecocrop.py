from datetime import timedelta

from feast import Entity, FileSource
from feast.data_format import ParquetFormat
from feast.types import ValueType
from feast import FeatureView, Field
from feast.types import Float32, Array, String

item = Entity(
    name="item_id",
    value_type=ValueType.INT64,
    description="Unique ID for EcoCrop RAG document chunk"
)
source = FileSource(
    path="data/ecocrop_rag_embeddings.parquet",
    file_format=ParquetFormat(),
    timestamp_field="event_timestamp",
)

ecocrop_embeddings_view = FeatureView(
    name="ecocrop_embeddings",
    entities=[item],
    ttl=timedelta(days=365),
    schema=[
        Field(name="vector", dtype=Array(Float32), vector_index=True, vector_search_metric="COSINE"),
        Field(name="rag_chunk_text", dtype=String),
        Field(name="scientific_name", dtype=String),
    ],
    source=source,
)