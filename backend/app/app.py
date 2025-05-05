import logging
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import FastAPI

from .data_transformer import transform_ecocrop_data
from .database import async_session_maker, engine
from .logging import logger
from .models import Plant, Base
from .plant_router import get_plant_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Use the engine to create all tables before starting the session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema created successfully.")

    logger.info("Creating cleaned dataset")
    transform_ecocrop_data()
    logger.info("Finished creating cleaned dataset")

    logger.info("Loading Plants into DB")
    await load_data()
    logger.info("Finished Loading Plants into DB")

    yield
    logger.info("Shutting down API...")


app = FastAPI(lifespan=lifespan)

app.include_router(
    get_plant_router(),
    prefix="/plants",
    tags=["plants"]
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


async def load_data():
    async with async_session_maker() as session:
        # Load data from Excel file
        df = pd.read_excel('resources/Cleaned_EcoCrop_DB_Final.xlsx')

        # Replace NaN values: use empty strings for string columns and None for numeric columns
        for column in df.columns:
            if df[column].dtype == "object":
                df[column] = df[column].fillna("")  # Replace NaN with empty string for string columns
            else:
                df[column] = df[column].where(pd.notnull(df[column]), None)  # Replace NaN with None for numeric columns

        # Convert DataFrame to list of Plant objects
        plants = []
        for _, row in df.iterrows():
            # Check if the record already exists
            existing_plant = await session.get(Plant, row['EcoPortCode'])
            if existing_plant is None:
                plant = Plant(
                    EcoPortCode=row['EcoPortCode'],
                    ScientificName=row['ScientificName'],
                    AUTH=row['AUTH'],
                    FAMNAME=row['FAMNAME'],
                    SYNO=row['SYNO'],
                    COMNAME=row['COMNAME'],
                    LIFO=row['LIFO'],
                    HABI=row['HABI'],
                    LISPA=row['LISPA'],
                    PHYS=row['PHYS'],
                    CAT=row['CAT'],
                    PLAT=row['PLAT'],
                    TOPMN=row['TOPMN'],
                    TOPMX=row['TOPMX'],
                    TMIN=row['TMIN'],
                    TMAX=row['TMAX'],
                    ROPMN=row['ROPMN'],
                    ROPMX=row['ROPMX'],
                    RMIN=row['RMIN'],
                    RMAX=row['RMAX'],
                    KTMP=row['KTMP'],
                    GMIN=row['GMIN'],
                    GMAX=row['GMAX'],
                    LATOPMN=row.get('LATOPMN'),
                    LATOPMX=row.get('LATOPMX'),
                    LATMN=row.get('LATMN'),
                    LATMX=row.get('LATMX'),
                    ALTMX=row.get('ALTMX'),
                    LIOPMN=row.get('LIOPMN'),
                    LIOPMX=row.get('LIOPMX'),
                    LIMN=row.get('LIMN'),
                    LIMX=row.get('LIMX'),
                    DEP=row.get('DEP'),
                    DEPR=row.get('DEPR'),
                    TEXT=row.get('TEXT'),
                    TEXTR=row.get('TEXTR'),
                    FER=row.get('FER'),
                    FERR=row.get('FERR'),
                    TOX=row.get('TOX'),
                    TOXR=row.get('TOXR'),
                    SAL=row.get('SAL'),
                    SALR=row.get('SALR'),
                    DRA=row.get('DRA'),
                    DRAR=row.get('DRAR'),
                    KTMPR=row.get('KTMPR'),
                    PHOTO=row.get('PHOTO'),
                    CLIZ=row.get('CLIZ'),
                    ABITOL=row.get('ABITOL'),
                    ABISUS=row.get('ABISUS'),
                    INTRI=row.get('INTRI'),
                    PROSY=row.get('PROSY'),
                )
                plants.append(plant)

        if plants:
            session.add_all(plants)
            await session.commit()
