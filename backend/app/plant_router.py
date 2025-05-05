import math

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from .database import get_async_session
from .models import Plant, PlantModel, PlantSuitabilityResponse
from .suitability import get_weather_and_suitability


def _replace_nan_with_none(plant):
    """
    Replace NaN values with None for a Plant object.

    This function iterates over all attributes of a Plant object. If a float
    attribute is NaN, it replaces the value with None.

    :param plant: The Plant object to process.
    :return: The processed Plant object with NaN values replaced by None.
    """
    for field, value in plant.__dict__.items():
        if isinstance(value, float) and math.isnan(value):
            setattr(plant, field, None)
    return plant


def get_plant_router() -> APIRouter:
    router = APIRouter()

    @router.get("/", response_model=list[PlantModel])
    async def get_all_plants(session: AsyncSession = Depends(get_async_session)):
        """
            Retrieve all plants from the database.

            This endpoint retrieves all plant records from the database. If no plants are found,
            a 404 error is returned.

            ### Parameters:

            ### Responses:
            - **200 OK**: A list of all plant objects.
            - **404 Not Found**: If no plants are found in the database.

            ### Example Response:
            ```
            [
                {
                    "EcoPortCode": 123,
                    "ScientificName": "Rosa",
                    "TOPMN": 10.0,
                    "TOPMX": 25.0,
                    ...
                }
            ]
            ```
            """
        result = await session.execute(select(Plant))
        plants = result.scalars().all()
        if not plants:
            raise HTTPException(status_code=404, detail="No plants found")
        # Replace NaN values with None
        plants = [_replace_nan_with_none(plant) for plant in plants]
        return plants

    @router.get("/scientific_name/{scientific_name}", response_model=list[PlantModel])
    async def get_plant_by_scientific_name(scientific_name: str, db: AsyncSession = Depends(get_async_session)):
        """
        Retrieve plants by their scientific name.

        This endpoint retrieves plants that match the provided scientific name (case-insensitive).
        If no plant is found, a 404 error is returned.

        ### Parameters:
        - **scientific_name** (str): The scientific name of the plant to search for.

        ### Responses:
        - **200 OK**: A list of plant objects matching the scientific name.
        - **404 Not Found**: If no matching plant is found.

        ### Example Request:
        ```
        GET /scientific_name/Rosa
        ```

        ### Example Response:
        ```
        [
            {
                "EcoPortCode": 123,
                "ScientificName": "Rosa",
                "TOPMN": 10.0,
                "TOPMX": 25.0,
                ...
            }
        ]
        ```
        """
        scientific_name = scientific_name.strip()
        query = select(Plant).where(Plant.ScientificName.ilike(scientific_name))
        result = await db.execute(query)
        plants = result.scalars().all()
        if not plants:
            raise HTTPException(status_code=404, detail="Plant not found")
        # Replace NaN values with None
        plants = [_replace_nan_with_none(plant) for plant in plants]
        return plants

    @router.get("/common_name/{common_name}", response_model=list[PlantModel])
    async def get_plant_by_common_name(common_name: str, db: AsyncSession = Depends(get_async_session)):
        """
        Retrieve plants by their common name.

        This endpoint performs a case-insensitive search on the common name (COMNAME field).
        If no plant is found, a 404 error is returned.

        ### Parameters:
        - **common_name** (str): The common name to search for.

        ### Responses:
        - **200 OK**: A list of plant objects matching the common name.
        - **404 Not Found**: If no matching plant is found.

        ### Example Request:
        ```
        GET /common_name/Rose
        ```

        ### Example Response:
        ```
        [
            {
                "EcoPortCode": 123,
                "ScientificName": "Rosa",
                ...
            }
        ]
        ```
        """
        common_name = common_name.strip()
        query = select(Plant).where(Plant.COMNAME.ilike(f"%{common_name}%"))
        result = await db.execute(query)
        plants = result.scalars().all()
        if not plants:
            raise HTTPException(status_code=404, detail="No plants found")
        # Replace NaN values with None
        plants = [_replace_nan_with_none(plant) for plant in plants]
        return plants

    @router.get("/search/{query}", response_model=list[PlantModel])
    async def search_plants(query: str, db: AsyncSession = Depends(get_async_session)):
        """
        Search plants by a general query.

        This endpoint performs a case-insensitive search in the ScientificName and SYNO (synonyms) fields.
        If no plant is found, a 404 error is returned.

        ### Parameters:
        - **query** (str): The search query to match against the ScientificName and SYNO fields.

        ### Responses:
        - **200 OK**: A list of plant objects matching the search query.
        - **404 Not Found**: If no matching plant is found.

        ### Example Request:
        ```
        GET /search/Rosa
        ```

        ### Example Response:
        ```
        [
            {
                "EcoPortCode": 123,
                "ScientificName": "Rosa",
                ...
            }
        ]
        ```
        """
        query = query.strip()
        query_stmt = select(Plant).where(
            (Plant.ScientificName.ilike(f"%{query}%")) | (Plant.SYNO.ilike(f"%{query}%"))
        )
        result = await db.execute(query_stmt)
        plants = result.scalars().all()
        if not plants:
            raise HTTPException(status_code=404, detail="No plants found")
        # Replace NaN values with None
        plants = [_replace_nan_with_none(plant) for plant in plants]
        return plants

    @router.get("/suitability/{scientific_name}", response_model=PlantSuitabilityResponse)
    async def calculate_suitability_for_plant(
            scientific_name: str,
            location: str,
            session: AsyncSession = Depends(get_async_session)
    ):
        """
            Calculate the suitability of a plant for a specific location based on weather data.

            This endpoint retrieves plant information based on the scientific name provided,
            fetches historical weather data for the specified location, and calculates a
            suitability score. The suitability score is determined using predefined optimal
            climate ranges for the plant species, along with real-time weather conditions.

            ### Parameters:
            - **scientific_name** (str): The scientific name of the plant (case-insensitive).
            - **location** (str): The location for which the suitability score should be calculated.

            ### Responses:
            - **200 OK**: Returns a `PlantSuitabilityResponse` model with the calculated suitability score,
              weather data, and plant-specific climate requirements.
            - **404 Not Found**: If the plant with the given scientific name is not found.

            ### Example Request:
            ```
            GET /suitability/rosa?location=Berlin
            ```

            ### Example Response:
            ```
            {
                "scientific_name": "Rosa",
                "suitability_score": 75,
                "weather_data": {
                    "temperature": [16, 18, 19],
                    "precipitation": [10, 12, 8]
                },
                "optimal_conditions": {
                    "temperature": {"min": 15, "max": 25},
                    "precipitation": {"min": 5, "max": 20}
                }
            }
            ```

            ### Raises:
            - `HTTPException`: If the plant is not found (404) or if there are issues fetching weather data.
            """
        query = select(Plant).where(Plant.ScientificName.ilike(scientific_name.strip()))
        result = await session.execute(query)
        plant = result.scalars().first()

        if not plant:
            raise HTTPException(status_code=404, detail="Plant not found.")

        suitability_data = await get_weather_and_suitability(location, scientific_name, session)

        plant_response = PlantSuitabilityResponse(
            **suitability_data
        )

        return plant_response

    @router.put("/", response_model=PlantModel)
    async def update_plant(updated_plant: PlantModel,
                           session: AsyncSession = Depends(get_async_session)):
        """
                  Update the details of an existing plant.

                  This endpoint allows for the modification of an existing plant's information in the database.
                  It takes an updated plant model, searches for the plant by its scientific name, and updates
                  its details with the provided data. If the plant is not found, an error is returned.

                  ### Parameters:
                  - **updated_plant** (PlantModel): The updated plant data containing all fields to modify.

                  ### Responses:
                  - **200 OK**: Returns the updated plant record with all fields, including the unchanged ones.
                  - **404 Not Found**: If no plant with the given scientific name is found in the database.

                  ### Example Request:
                  ```
                  PUT /
                  {
                      "EcoPortCode": 123,
                      "ScientificName": "Rosa",
                      "TOPMN": 10.0,
                      "TOPMX": 25.0,
                      "TMIN": 5.0,
                      "TMAX": 35.0,
                      "ROPMN": 300.0,
                      "ROPMX": 1200.0,
                      "RMIN": 200.0,
                      "RMAX": 1500.0,
                      "KTMP": -5.0,
                      "GMIN": 90,
                      "GMAX": 365
                  }
                  ```

                  ### Example Response:
                  ```
                  {
                      "EcoPortCode": 123,
                      "ScientificName": "Rosa",
                      "AUTH": "L.",
                      "FAMNAME": "Rosaceae",
                      "TOPMN": 10.0,
                      "TOPMX": 25.0,
                      "TMIN": 5.0,
                      "TMAX": 35.0,
                      "ROPMN": 300.0,
                      "ROPMX": 1200.0,
                      "RMIN": 200.0,
                      "RMAX": 1500.0,
                      "KTMP": -5.0,
                      "GMIN": 90,
                      "GMAX": 365
                  }
                  ```

                  ### Raises:
                  - `HTTPException`: If the plant is not found (404).
                  """
        query = select(Plant).where(Plant.ScientificName.ilike(updated_plant.ScientificName))
        result = await session.execute(query)
        plant = result.scalars().first()

        if not plant:
            raise HTTPException(status_code=404, detail="Plant not found.")

        for key, value in updated_plant.dict().items():
            setattr(plant, key, value)

        await session.commit()
        await session.refresh(plant)
        return plant

    @router.post("/", response_model=PlantModel)
    async def create_plant(new_plant: PlantModel, session: AsyncSession = Depends(get_async_session)):
        """
        Create a new plant entry in the database.

        This endpoint allows for the creation of a new plant record.
        If a plant with the same scientific name already exists, a 400 error is returned.

        ### Parameters:
        - **new_plant** (PlantModel): The details of the plant to create.

        ### Responses:
        - **201 Created**: The created plant object.
        - **400 Bad Request**: If a plant with the same scientific name already exists.

        ### Example Request:
        ```
        POST /
        {
            "EcoPortCode": 123,
            "ScientificName": "Rosa",
            ...
        }
        ```

        ### Example Response:
        ```
        {
            "EcoPortCode": 123,
            "ScientificName": "Rosa",
            "TOPMN": 10.0,
            "TOPMX": 25.0,
            ...
        }
        ```
        """
        # Check if plant with same ScientificName already exists
        query = select(Plant).where(Plant.ScientificName.ilike(new_plant.ScientificName))
        result = await session.execute(query)
        existing_plant = result.scalars().first()

        if existing_plant:
            raise HTTPException(status_code=400, detail="Plant with this scientific name already exists.")

        # Create the new plant record
        plant = Plant(**new_plant.dict())
        session.add(plant)
        await session.commit()
        await session.refresh(plant)
        return plant

    @router.delete("/{eco_port_code}")
    async def delete_plant(eco_port_code: int, session: AsyncSession = Depends(get_async_session)):
        """
        Delete a plant by its EcoPortCode.

        This endpoint deletes a plant based on its unique EcoPortCode.
        If no plant is found with the provided EcoPortCode, a 404 error is returned.

        ### Parameters:
        - **eco_port_code** (int): The unique EcoPortCode of the plant to delete.

        ### Responses:
        - **204 No Content**: Successful deletion of the plant.
        - **404 Not Found**: If no matching plant is found.

        ### Example Request:
        ```
        DELETE /123
        ```

        ### Example Response:
        - 204 No Content
        """
        # Find the plant by EcoPortCode
        query = select(Plant).where(Plant.EcoPortCode == eco_port_code)
        result = await session.execute(query)
        plant = result.scalars().first()

        if not plant:
            raise HTTPException(status_code=404, detail="Plant not found.")

        await session.delete(plant)
        await session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return router
