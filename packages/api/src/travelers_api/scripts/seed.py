"""Seed database with test cities and POIs"""

import asyncio
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from travelers_api.core.database import async_session_maker
from travelers_api.models.city import City
from travelers_api.models.poi import POI


SEED_CITIES = [
    {
        "name": "Barcelona",
        "country": "Spain",
        "country_code": "ES",
        "coordinates": (41.3851, 2.1734),
        "timezone": "Europe/Madrid",
        "wikidata_id": "Q1492",
    },
    {
        "name": "Buenos Aires",
        "country": "Argentina",
        "country_code": "AR",
        "coordinates": (-34.6037, -58.3816),
        "timezone": "America/Argentina/Buenos_Aires",
        "wikidata_id": "Q1486",
    },
    {
        "name": "Paris",
        "country": "France",
        "country_code": "FR",
        "coordinates": (48.8566, 2.3522),
        "timezone": "Europe/Paris",
        "wikidata_id": "Q90",
    },
]

SEED_POIS = {
    "Barcelona": [
        {
            "name": "La Sagrada Familia",
            "wikidata_id": "Q48958",
            "coordinates": (41.4036, 2.1744),
            "year_built": 1882,
            "architect": "Antoni Gaudí",
            "architectural_style": "Modernisme",
            "heritage_status": "UNESCO World Heritage Site",
            "poi_type": "church",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/01/Sagrada_Familia_01.jpg/800px-Sagrada_Familia_01.jpg",
            "summary": "Construction began in 1882 under architect Francisco de Paula del Villar, with Gaudí taking over a year later and transforming it into his life's work. Look up at the façade to spot intricate naturalistic sculptures representing the Nativity—each figure was cast from real people. Arrive early on a sunny morning to see light streaming through the stained glass, painting the interior in shifting blues and golds.",
            "summary_es": "La construcción comenzó en 1882 bajo el arquitecto Francisco de Paula del Villar, y Gaudí tomó el mando un año después, convirtiéndola en la obra de su vida. Mira hacia arriba en la fachada para ver esculturas naturalistas intrincadas que representan la Natividad—cada figura fue moldeada de personas reales. Llega temprano en una mañana soleada para ver la luz filtrarse a través de los vitrales, pintando el interior en tonos cambiantes de azul y oro.",
            "wikipedia_extract": "The Basílica i Temple Expiatori de la Sagrada Família, shortened as the Sagrada Família, is an unfinished church in the Eixample district of Barcelona, Catalonia, Spain.",
            "estimated_visit_duration": 90,
        },
        {
            "name": "Park Güell",
            "wikidata_id": "Q182589",
            "coordinates": (41.4145, 2.1527),
            "year_built": 1914,
            "architect": "Antoni Gaudí",
            "architectural_style": "Modernisme",
            "poi_type": "park",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/Park_G%C3%BCell_03.jpg/800px-Park_G%C3%BCell_03.jpg",
            "summary": "Originally conceived as a luxury housing development in 1900, the project failed commercially and became a public park in 1926. The colorful salamander fountain at the entrance—nicknamed 'El Drac' (The Dragon)—has become Barcelona's unofficial mascot. Visit before 9am to access the monumental zone for free, or stay for sunset when the ceramic mosaics catch the golden light.",
            "summary_es": "Concebido originalmente como un desarrollo de viviendas de lujo en 1900, el proyecto fracasó comercialmente y se convirtió en parque público en 1926. La colorida fuente de salamandra a la entrada—apodada 'El Drac' (El Dragón)—se ha convertido en la mascota no oficial de Barcelona. Visita antes de las 9am para acceder a la zona monumental gratis, o quédate para el atardecer cuando los mosaicos cerámicos captan la luz dorada.",
            "estimated_visit_duration": 120,
        },
        {
            "name": "Casa Batlló",
            "wikidata_id": "Q194458",
            "coordinates": (41.3916, 2.1649),
            "year_built": 1906,
            "architect": "Antoni Gaudí",
            "architectural_style": "Modernisme",
            "heritage_status": "UNESCO World Heritage Site",
            "poi_type": "building",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Casa_Batll%C3%B3.jpg/800px-Casa_Batll%C3%B3.jpg",
            "summary": "Gaudí transformed this 1877 apartment building between 1904-1906, reportedly inspired by the legend of Saint George slaying the dragon. The undulating facade represents the sea, with balconies resembling carnival masks and a rooftop spine-like chimney suggesting a dragon's back. The interior tour includes augmented reality experiences that reveal Gaudí's original vision.",
            "summary_es": "Gaudí transformó este edificio de apartamentos de 1877 entre 1904-1906, supuestamente inspirado por la leyenda de San Jorge matando al dragón. La fachada ondulante representa el mar, con balcones que parecen máscaras de carnaval y una chimenea en forma de espina dorsal en el tejado que sugiere el lomo de un dragón. El tour interior incluye experiencias de realidad aumentada que revelan la visión original de Gaudí.",
            "estimated_visit_duration": 60,
        },
    ],
    "Buenos Aires": [
        {
            "name": "Teatro Colón",
            "wikidata_id": "Q1137062",
            "coordinates": (-34.6009, -58.3833),
            "year_built": 1908,
            "architect": "Vittorio Meano",
            "architectural_style": "Eclecticism",
            "poi_type": "theater",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/94/Buenos_Aires_-_Teatro_Col%C3%B3n_-_Vista_exterior.jpg/800px-Buenos_Aires_-_Teatro_Col%C3%B3n_-_Vista_exterior.jpg",
            "summary": "Three architects worked on this opera house over 20 years, with the final architect dying just months before its 1908 opening. Acoustics experts consistently rank it among the world's five best concert halls, thanks to its horseshoe shape and golden dome. Arrive early for guided tours to peek into the costume workshop, where 35,000 pieces are stored across seven floors.",
            "summary_es": "Tres arquitectos trabajaron en esta ópera durante 20 años, y el último arquitecto murió meses antes de su inauguración en 1908. Los expertos en acústica lo clasifican consistentemente entre las cinco mejores salas de conciertos del mundo, gracias a su forma de herradura y cúpula dorada. Llega temprano para los tours guiados y echa un vistazo al taller de vestuario, donde se almacenan 35.000 piezas en siete pisos.",
            "estimated_visit_duration": 75,
        },
        {
            "name": "Casa Rosada",
            "wikidata_id": "Q466802",
            "coordinates": (-34.6083, -58.3701),
            "year_built": 1898,
            "architectural_style": "Italianate",
            "poi_type": "government",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/75/Casa_Rosada_desde_Plaza_de_Mayo.jpg/800px-Casa_Rosada_desde_Plaza_de_Mayo.jpg",
            "summary": "The distinctive pink color may have originated from mixing white lime with ox blood as a preservative, though this origin story is debated. Eva Perón delivered her famous speeches from the second-floor balcony, now accessible during weekend tours. Free guided tours on weekends reveal presidential offices and a museum with artifacts from every administration since 1862.",
            "summary_es": "El distintivo color rosa puede haber originado de mezclar cal blanca con sangre de buey como conservante, aunque este origen es debatido. Eva Perón pronunció sus famosos discursos desde el balcón del segundo piso, ahora accesible durante los tours de fin de semana. Los tours guiados gratuitos los fines de semana revelan oficinas presidenciales y un museo con artefactos de cada administración desde 1862.",
            "estimated_visit_duration": 60,
        },
    ],
    "Paris": [
        {
            "name": "Eiffel Tower",
            "wikidata_id": "Q243",
            "coordinates": (48.8584, 2.2945),
            "year_built": 1889,
            "architect": "Gustave Eiffel",
            "architectural_style": "Iron lattice",
            "poi_type": "monument",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Tour_Eiffel_Wikimedia_Commons_%28cropped%29.jpg/800px-Tour_Eiffel_Wikimedia_Commons_%28cropped%29.jpg",
            "summary": "Built as a temporary exhibit for the 1889 World's Fair, it was nearly demolished in 1909 but saved by its value as a radio transmission tower. The iron lattice shrinks by up to 6 inches in cold weather and expands toward the sun on hot days, causing the top to sway slightly. Book the stairs to the second floor for a more intimate experience than the crowded elevators.",
            "summary_es": "Construida como exhibición temporal para la Feria Mundial de 1889, casi fue demolida en 1909 pero se salvó por su valor como torre de transmisión de radio. El enrejado de hierro se encoge hasta 15 cm en clima frío y se expande hacia el sol en días calurosos, causando que la cima oscile ligeramente. Reserva las escaleras al segundo piso para una experiencia más íntima que los ascensores llenos.",
            "estimated_visit_duration": 120,
        },
        {
            "name": "Notre-Dame de Paris",
            "wikidata_id": "Q2981",
            "coordinates": (48.8530, 2.3499),
            "year_built": 1345,
            "architectural_style": "Gothic",
            "heritage_status": "UNESCO World Heritage Site",
            "poi_type": "church",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/Notre-Dame_de_Paris%2C_4_Oct_2012.jpg/800px-Notre-Dame_de_Paris%2C_4_Oct_2012.jpg",
            "summary": "Construction began in 1163 and took nearly 200 years to complete, with the flying buttresses added later to prevent the walls from collapsing outward. The three rose windows contain 13th-century glass that survived both revolutions and world wars. After the 2019 fire, restoration used medieval techniques, with timber from century-old oak trees replacing the burned spire.",
            "summary_es": "La construcción comenzó en 1163 y tomó casi 200 años en completarse, con los arbotantes añadidos después para evitar que las paredes colapsaran. Los tres rosetones contienen vidrio del siglo XIII que sobrevivió revoluciones y guerras mundiales. Después del incendio de 2019, la restauración usó técnicas medievales, con madera de robles centenarios reemplazando la aguja quemada.",
            "estimated_visit_duration": 90,
        },
    ],
}


async def seed_database():
    """Seed the database with test data"""
    async with async_session_maker() as session:
        # Check if already seeded
        from sqlalchemy import select
        result = await session.execute(select(City).limit(1))
        if result.scalar():
            print("Database already seeded, skipping...")
            return

        print("Seeding cities...")
        city_map = {}

        for city_data in SEED_CITIES:
            lat, lng = city_data["coordinates"]
            point_wkt = f"SRID=4326;POINT({lng} {lat})"

            city = City(
                id=uuid4(),
                name=city_data["name"],
                country=city_data["country"],
                country_code=city_data["country_code"],
                coordinates=point_wkt,
                timezone=city_data["timezone"],
                wikidata_id=city_data["wikidata_id"],
            )
            session.add(city)
            city_map[city_data["name"]] = city
            print(f"  Added city: {city_data['name']}")

        await session.flush()

        print("Seeding POIs...")
        for city_name, pois in SEED_POIS.items():
            city = city_map[city_name]
            for poi_data in pois:
                lat, lng = poi_data["coordinates"]
                point_wkt = f"SRID=4326;POINT({lng} {lat})"

                poi = POI(
                    id=uuid4(),
                    city_id=city.id,
                    name=poi_data["name"],
                    wikidata_id=poi_data["wikidata_id"],
                    coordinates=point_wkt,
                    year_built=poi_data.get("year_built"),
                    architect=poi_data.get("architect"),
                    architectural_style=poi_data.get("architectural_style"),
                    heritage_status=poi_data.get("heritage_status"),
                    poi_type=poi_data["poi_type"],
                    image_url=poi_data.get("image_url"),
                    summary=poi_data.get("summary"),
                    summary_es=poi_data.get("summary_es"),
                    wikipedia_extract=poi_data.get("wikipedia_extract"),
                    estimated_visit_duration=poi_data.get("estimated_visit_duration", 60),
                    data_source="seed",
                )
                session.add(poi)
                print(f"  Added POI: {poi_data['name']} ({city_name})")

        await session.commit()
        print("Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_database())
