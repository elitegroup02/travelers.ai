"""Extended seed database with additional cities and POIs for demo purposes."""

import asyncio
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from travelers_api.core.database import async_session_maker
from travelers_api.models.city import City
from travelers_api.models.poi import POI


EXTENDED_CITIES = [
    {
        "name": "Rome",
        "country": "Italy",
        "country_code": "IT",
        "coordinates": (41.9028, 12.4964),
        "timezone": "Europe/Rome",
        "wikidata_id": "Q220",
    },
    {
        "name": "Tokyo",
        "country": "Japan",
        "country_code": "JP",
        "coordinates": (35.6762, 139.6503),
        "timezone": "Asia/Tokyo",
        "wikidata_id": "Q1490",
    },
    {
        "name": "New York",
        "country": "United States",
        "country_code": "US",
        "coordinates": (40.7128, -74.0060),
        "timezone": "America/New_York",
        "wikidata_id": "Q60",
    },
    {
        "name": "London",
        "country": "United Kingdom",
        "country_code": "GB",
        "coordinates": (51.5074, -0.1278),
        "timezone": "Europe/London",
        "wikidata_id": "Q84",
    },
    {
        "name": "Cairo",
        "country": "Egypt",
        "country_code": "EG",
        "coordinates": (30.0444, 31.2357),
        "timezone": "Africa/Cairo",
        "wikidata_id": "Q85",
    },
    {
        "name": "Sydney",
        "country": "Australia",
        "country_code": "AU",
        "coordinates": (-33.8688, 151.2093),
        "timezone": "Australia/Sydney",
        "wikidata_id": "Q1355",
    },
    {
        "name": "Marrakech",
        "country": "Morocco",
        "country_code": "MA",
        "coordinates": (31.6295, -7.9811),
        "timezone": "Africa/Casablanca",
        "wikidata_id": "Q101625",
    },
]

EXTENDED_POIS = {
    "Rome": [
        {
            "name": "Colosseum",
            "wikidata_id": "Q10285",
            "coordinates": (41.8902, 12.4922),
            "year_built": 80,
            "architectural_style": "Roman",
            "heritage_status": "UNESCO World Heritage Site",
            "poi_type": "monument",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/Colosseo_2020.jpg/800px-Colosseo_2020.jpg",
            "summary": "The largest ancient amphitheater ever built, the Colosseum once held 50,000 spectators for gladiatorial contests and public spectacles. Construction began under Emperor Vespasian in 72 AD and was completed by his son Titus in 80 AD. The hypogeum beneath the arena floor, now visible, housed wild animals and gladiators before their dramatic entrances through trapdoors.",
            "summary_es": "El anfiteatro antiguo mas grande jamas construido, el Coliseo albergaba 50,000 espectadores para combates de gladiadores y espectaculos publicos. La construccion comenzo bajo el Emperador Vespasiano en el 72 d.C. y fue completada por su hijo Tito en el 80 d.C. El hipogeo bajo el piso de la arena, ahora visible, albergaba animales salvajes y gladiadores antes de sus dramaticas entradas.",
            "estimated_visit_duration": 120,
        },
        {
            "name": "Vatican Museums",
            "wikidata_id": "Q182955",
            "coordinates": (41.9065, 12.4536),
            "year_built": 1506,
            "poi_type": "museum",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/VaticanMuseumStaircase.jpg/800px-VaticanMuseumStaircase.jpg",
            "summary": "Home to one of the world's greatest art collections amassed by popes over centuries, including Michelangelo's Sistine Chapel ceiling. The spiral staircase designed by Giuseppe Momo in 1932 has become an architectural icon. Book the early morning entry to experience the Sistine Chapel with fewer crowds before the general public arrives.",
            "summary_es": "Hogar de una de las mejores colecciones de arte del mundo acumuladas por los papas durante siglos, incluyendo el techo de la Capilla Sixtina de Miguel Angel. La escalera de caracol disenada por Giuseppe Momo en 1932 se ha convertido en un icono arquitectonico. Reserva la entrada de la manana temprano para experimentar la Capilla Sixtina con menos multitudes.",
            "estimated_visit_duration": 180,
        },
        {
            "name": "Trevi Fountain",
            "wikidata_id": "Q185925",
            "coordinates": (41.9009, 12.4833),
            "year_built": 1762,
            "architect": "Nicola Salvi",
            "architectural_style": "Baroque",
            "poi_type": "monument",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/35/Trevi_Fountain%2C_Rome%2C_Italy_2_-_May_2007.jpg/800px-Trevi_Fountain.jpg",
            "summary": "The largest Baroque fountain in Rome, Trevi collects an estimated 3,000 euros in coins daily, donated to Caritas for charity. The tradition of throwing coins over your shoulder dates to the 1954 film 'Three Coins in the Fountain.' Visit at dawn to avoid crowds and see the recently restored white travertine stone gleaming.",
            "summary_es": "La fuente barroca mas grande de Roma, Trevi recoge aproximadamente 3,000 euros en monedas diariamente, donadas a Caritas para caridad. La tradicion de lanzar monedas sobre el hombro data de la pelicula de 1954 'Tres monedas en la fuente.' Visita al amanecer para evitar multitudes y ver la piedra travertino blanca recientemente restaurada.",
            "estimated_visit_duration": 30,
        },
        {
            "name": "Pantheon",
            "wikidata_id": "Q842858",
            "coordinates": (41.8986, 12.4769),
            "year_built": 126,
            "architect": "Apollodorus of Damascus",
            "architectural_style": "Roman",
            "poi_type": "church",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/06/Rome-Pantheon-Interieur1.jpg/800px-Rome-Pantheon-Interieur1.jpg",
            "summary": "The best-preserved ancient Roman building, with a dome that remained the world's largest for 1,300 years. The oculus at the dome's center is open to the sky, with rain falling through onto the slightly convex floor that channels water to drains. Raphael is buried here, and his epitaph reads 'Here lies Raphael, by whom Nature herself feared to be outdone.'",
            "summary_es": "El edificio romano antiguo mejor conservado, con una cupula que fue la mas grande del mundo durante 1,300 anos. El oculo en el centro de la cupula esta abierto al cielo, con la lluvia cayendo sobre el piso ligeramente convexo que canaliza el agua hacia los desagues. Rafael esta enterrado aqui, y su epitafio dice 'Aqui yace Rafael, por quien la Naturaleza misma temio ser superada.'",
            "estimated_visit_duration": 45,
        },
        {
            "name": "Roman Forum",
            "wikidata_id": "Q192782",
            "coordinates": (41.8925, 12.4853),
            "year_built": -500,
            "year_built_circa": True,
            "architectural_style": "Roman",
            "heritage_status": "UNESCO World Heritage Site",
            "poi_type": "monument",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Forum_Romanum_Rom.jpg/800px-Forum_Romanum_Rom.jpg",
            "summary": "Once the center of Roman public life, this sprawling complex of ruins includes temples, basilicas, and triumphal arches where Julius Caesar's body was cremated. The Via Sacra, the main street, was walked by triumphal processions and everyday Romans alike. Combine with Palatine Hill for a half-day exploration of ancient Rome's heart.",
            "summary_es": "Una vez el centro de la vida publica romana, este extenso complejo de ruinas incluye templos, basilicas y arcos triunfales donde el cuerpo de Julio Cesar fue incinerado. La Via Sacra, la calle principal, fue transitada tanto por procesiones triunfales como por romanos comunes. Combina con el Monte Palatino para una exploracion de medio dia del corazon de la antigua Roma.",
            "estimated_visit_duration": 120,
        },
    ],
    "Tokyo": [
        {
            "name": "Senso-ji Temple",
            "wikidata_id": "Q615086",
            "coordinates": (35.7148, 139.7967),
            "year_built": 645,
            "architectural_style": "Japanese Buddhist",
            "poi_type": "church",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/Cloudy_senso-ji.jpg/800px-Cloudy_senso-ji.jpg",
            "summary": "Tokyo's oldest temple, founded in 645 AD after two fishermen discovered a statue of Kannon, the goddess of mercy. The iconic Kaminarimon (Thunder Gate) with its giant red lantern has become one of Tokyo's most photographed landmarks. Walk through the Nakamise shopping street for traditional snacks and souvenirs before reaching the main hall.",
            "summary_es": "El templo mas antiguo de Tokio, fundado en 645 d.C. despues de que dos pescadores descubrieron una estatua de Kannon, la diosa de la misericordia. El iconico Kaminarimon (Puerta del Trueno) con su gigante farol rojo se ha convertido en uno de los lugares mas fotografiados de Tokio. Camina por la calle comercial Nakamise para probar bocadillos tradicionales y recuerdos.",
            "estimated_visit_duration": 60,
        },
        {
            "name": "Tokyo Tower",
            "wikidata_id": "Q180277",
            "coordinates": (35.6586, 139.7454),
            "year_built": 1958,
            "architect": "Tachu Naito",
            "architectural_style": "Lattice tower",
            "poi_type": "monument",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/Tokyo_Tower_at_night_%28portrait_view%29.jpg/800px-Tokyo_Tower_at_night.jpg",
            "summary": "Inspired by the Eiffel Tower but standing 13 meters taller, Tokyo Tower was built as a symbol of Japan's post-war rebirth. The orange and white paint scheme requires 28,000 liters of paint and takes a full year to repaint. Visit at night when the tower illuminates in different colors depending on the season.",
            "summary_es": "Inspirada en la Torre Eiffel pero 13 metros mas alta, la Torre de Tokio fue construida como simbolo del renacimiento de Japon despues de la guerra. El esquema de pintura naranja y blanco requiere 28,000 litros de pintura y toma un ano completo repintar. Visita por la noche cuando la torre se ilumina en diferentes colores segun la temporada.",
            "estimated_visit_duration": 90,
        },
        {
            "name": "Meiji Shrine",
            "wikidata_id": "Q182339",
            "coordinates": (35.6764, 139.6993),
            "year_built": 1920,
            "architectural_style": "Shinto",
            "poi_type": "church",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/MeijiShrineTorii1.jpg/800px-MeijiShrineTorii1.jpg",
            "summary": "Dedicated to Emperor Meiji and Empress Shoken, this Shinto shrine sits in a 170-acre forest of 100,000 trees donated from across Japan. The original shrine was destroyed in WWII bombings but rebuilt in 1958. Pass through the massive torii gate made from 1,700-year-old cypress from Taiwan, the largest wooden torii in Japan.",
            "summary_es": "Dedicado al Emperador Meiji y la Emperatriz Shoken, este santuario sintoista se encuentra en un bosque de 70 hectareas con 100,000 arboles donados de todo Japon. El santuario original fue destruido en los bombardeos de la Segunda Guerra Mundial pero reconstruido en 1958. Pasa por la enorme puerta torii hecha de cipres de 1,700 anos de Taiwan, el torii de madera mas grande de Japon.",
            "estimated_visit_duration": 60,
        },
        {
            "name": "Shibuya Crossing",
            "wikidata_id": "Q5893193",
            "coordinates": (35.6595, 139.7004),
            "poi_type": "monument",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Shibuya_Crossing%2C_Tokyo%2C_Japan_%2810%29.jpg/800px-Shibuya_Crossing.jpg",
            "summary": "The world's busiest pedestrian crossing, where up to 3,000 people cross simultaneously during peak times. The scramble intersection allows pedestrians to cross in all directions, including diagonally. Best viewed from the Starbucks overlooking the crossing or the Shibuya Sky observation deck for a bird's-eye view.",
            "summary_es": "El cruce peatonal mas concurrido del mundo, donde hasta 3,000 personas cruzan simultaneamente en horas pico. El cruce en scramble permite a los peatones cruzar en todas direcciones, incluyendo diagonalmente. Mejor visto desde el Starbucks con vista al cruce o la plataforma de observacion Shibuya Sky para una vista panoramica.",
            "estimated_visit_duration": 30,
        },
        {
            "name": "teamLab Borderless",
            "wikidata_id": "Q56343055",
            "coordinates": (35.6265, 139.7839),
            "year_built": 2018,
            "poi_type": "museum",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/TeamLab_Borderless.jpg/800px-TeamLab_Borderless.jpg",
            "summary": "A groundbreaking digital art museum where 60+ interactive installations flow into each other without boundaries. The artwork responds to your presence and movement, creating a unique experience each visit. Wear comfortable shoes as you'll walk through a maze-like space with uneven floors and dark passages.",
            "summary_es": "Un museo de arte digital innovador donde mas de 60 instalaciones interactivas fluyen entre si sin fronteras. Las obras de arte responden a tu presencia y movimiento, creando una experiencia unica en cada visita. Usa zapatos comodos ya que caminaras por un espacio laberintico con pisos irregulares y pasillos oscuros.",
            "estimated_visit_duration": 150,
        },
    ],
    "New York": [
        {
            "name": "Statue of Liberty",
            "wikidata_id": "Q9202",
            "coordinates": (40.6892, -74.0445),
            "year_built": 1886,
            "architect": "Frederic Auguste Bartholdi",
            "architectural_style": "Neoclassical",
            "heritage_status": "UNESCO World Heritage Site",
            "poi_type": "monument",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a1/Statue_of_Liberty_7.jpg/800px-Statue_of_Liberty_7.jpg",
            "summary": "A gift from France in 1886, Lady Liberty's copper skin has oxidized to its iconic green patina over time. The seven rays on her crown represent the seven continents and oceans. Book crown access months in advance for a climb up 354 steps to witness the intricate iron framework designed by Gustave Eiffel.",
            "summary_es": "Un regalo de Francia en 1886, la piel de cobre de la Dama de la Libertad se ha oxidado hasta su iconica patina verde con el tiempo. Los siete rayos de su corona representan los siete continentes y oceanos. Reserva el acceso a la corona con meses de anticipacion para subir 354 escalones y ver la intrincada estructura de hierro disenada por Gustave Eiffel.",
            "estimated_visit_duration": 180,
        },
        {
            "name": "Central Park",
            "wikidata_id": "Q160409",
            "coordinates": (40.7829, -73.9654),
            "year_built": 1858,
            "architect": "Frederick Law Olmsted",
            "architectural_style": "English landscape garden",
            "poi_type": "park",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Central_Park_-_The_Pond_%2848377220007%29.jpg/800px-Central_Park.jpg",
            "summary": "An 843-acre oasis in Manhattan that receives over 42 million visitors annually, more than any other urban park in the US. The park was designed before the surrounding city was built, with every rock, lake, and vista carefully planned. Rent a rowboat on The Lake for classic views of the skyline and Bow Bridge.",
            "summary_es": "Un oasis de 341 hectareas en Manhattan que recibe mas de 42 millones de visitantes anualmente, mas que cualquier otro parque urbano en EE.UU. El parque fue disenado antes de que se construyera la ciudad circundante, con cada roca, lago y vista cuidadosamente planeados. Alquila un bote de remos en The Lake para vistas clasicas del horizonte y Bow Bridge.",
            "estimated_visit_duration": 180,
        },
        {
            "name": "Metropolitan Museum of Art",
            "wikidata_id": "Q160236",
            "coordinates": (40.7794, -73.9632),
            "year_built": 1880,
            "architectural_style": "Beaux-Arts",
            "poi_type": "museum",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Metropolitan_Museum_of_Art_%28The_Met%29_-_Central_Park%2C_NYC.jpg/800px-Metropolitan_Museum.jpg",
            "summary": "America's largest art museum housing over 2 million works spanning 5,000 years of culture. The Egyptian Temple of Dendur, gifted by Egypt in 1965, sits in a glass-walled gallery overlooking Central Park. Admission is pay-what-you-wish for NY residents, but a suggested donation for others.",
            "summary_es": "El museo de arte mas grande de America alberga mas de 2 millones de obras que abarcan 5,000 anos de cultura. El Templo Egipcio de Dendur, regalado por Egipto en 1965, se encuentra en una galeria con paredes de vidrio con vista a Central Park. La entrada es lo que desees pagar para residentes de NY, con una donacion sugerida para otros.",
            "estimated_visit_duration": 240,
        },
        {
            "name": "Empire State Building",
            "wikidata_id": "Q9188",
            "coordinates": (40.7484, -73.9857),
            "year_built": 1931,
            "architect": "Shreve, Lamb & Harmon",
            "architectural_style": "Art Deco",
            "poi_type": "building",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Empire_State_Building_%28aerial_view%29.jpg/800px-Empire_State_Building.jpg",
            "summary": "Built in just 410 days during the Great Depression, this 102-story Art Deco icon was the world's tallest building for 40 years. The tower lights change colors for holidays and special events, a tradition since 1976. Visit the 86th floor outdoor observatory at night for unobstructed 360-degree views of the glittering city.",
            "summary_es": "Construido en solo 410 dias durante la Gran Depresion, este icono Art Deco de 102 pisos fue el edificio mas alto del mundo durante 40 anos. Las luces de la torre cambian de color para feriados y eventos especiales, una tradicion desde 1976. Visita el observatorio al aire libre del piso 86 por la noche para vistas de 360 grados de la ciudad brillante.",
            "estimated_visit_duration": 90,
        },
        {
            "name": "Brooklyn Bridge",
            "wikidata_id": "Q129557",
            "coordinates": (40.7061, -73.9969),
            "year_built": 1883,
            "architect": "John Augustus Roebling",
            "architectural_style": "Gothic Revival",
            "poi_type": "monument",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/00/Brooklyn_Bridge_Manhattan.jpg/800px-Brooklyn_Bridge_Manhattan.jpg",
            "summary": "The first steel-wire suspension bridge, it took 14 years to build and claimed the lives of 27 workers. Walk the elevated pedestrian path for stunning views of both the Manhattan and Brooklyn skylines. Start from Brooklyn for the best view of Manhattan, ideally at sunset when the city lights begin to glow.",
            "summary_es": "El primer puente colgante de cables de acero, tomo 14 anos en construirse y cobro la vida de 27 trabajadores. Camina por el sendero peatonal elevado para vistas impresionantes de los horizontes de Manhattan y Brooklyn. Comienza desde Brooklyn para la mejor vista de Manhattan, idealmente al atardecer cuando las luces de la ciudad comienzan a brillar.",
            "estimated_visit_duration": 60,
        },
    ],
    "London": [
        {
            "name": "Tower of London",
            "wikidata_id": "Q62378",
            "coordinates": (51.5081, -0.0759),
            "year_built": 1078,
            "architectural_style": "Norman",
            "heritage_status": "UNESCO World Heritage Site",
            "poi_type": "monument",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/Tower_of_London_from_the_Shard.jpg/800px-Tower_of_London.jpg",
            "summary": "A 1,000-year-old fortress that has served as royal palace, prison, and execution site. The Crown Jewels collection includes the 530-carat Cullinan I diamond in the Sovereign's Sceptre. Join a Yeoman Warder (Beefeater) tour for tales of intrigue, including the mysterious disappearance of the Princes in the Tower.",
            "summary_es": "Una fortaleza de 1,000 anos que ha servido como palacio real, prision y lugar de ejecucion. La coleccion de las Joyas de la Corona incluye el diamante Cullinan I de 530 quilates en el Cetro del Soberano. Unete a un tour de los Yeoman Warder (Beefeaters) para historias de intriga, incluyendo la misteriosa desaparicion de los Principes en la Torre.",
            "estimated_visit_duration": 180,
        },
        {
            "name": "British Museum",
            "wikidata_id": "Q6373",
            "coordinates": (51.5194, -0.1270),
            "year_built": 1759,
            "architectural_style": "Greek Revival",
            "poi_type": "museum",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/86/British_Museum_from_NE_2.JPG/800px-British_Museum.jpg",
            "summary": "Home to 8 million works tracing human history from its beginnings, including the Rosetta Stone and Parthenon sculptures. The Great Court, covered by a spectacular glass roof, is Europe's largest covered public square. Entry is free, making it possible to visit repeatedly to explore different galleries at your own pace.",
            "summary_es": "Hogar de 8 millones de obras que trazan la historia humana desde sus comienzos, incluyendo la Piedra Rosetta y las esculturas del Partenon. El Gran Patio, cubierto por un espectacular techo de cristal, es la plaza publica cubierta mas grande de Europa. La entrada es gratuita, permitiendo visitas repetidas para explorar diferentes galerias a tu propio ritmo.",
            "estimated_visit_duration": 180,
        },
        {
            "name": "Westminster Abbey",
            "wikidata_id": "Q5933",
            "coordinates": (51.4994, -0.1273),
            "year_built": 1090,
            "architectural_style": "Gothic",
            "heritage_status": "UNESCO World Heritage Site",
            "poi_type": "church",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Westminster_Abbey_West_Door.jpg/800px-Westminster_Abbey_West_Door.jpg",
            "summary": "The coronation church for English monarchs since 1066, where 17 monarchs are buried including Elizabeth I and Mary Queen of Scots. Poets' Corner commemorates literary giants from Chaucer to Dickens. Attend Evensong (free) to hear the world-famous choir in the stunning Gothic setting without paying admission.",
            "summary_es": "La iglesia de coronacion de los monarcas ingleses desde 1066, donde estan enterrados 17 monarcas incluyendo Isabel I y Maria Reina de Escocia. El Rincon de los Poetas conmemora gigantes literarios desde Chaucer hasta Dickens. Asiste a Evensong (gratis) para escuchar el famoso coro mundial en el impresionante escenario gotico sin pagar entrada.",
            "estimated_visit_duration": 120,
        },
        {
            "name": "Buckingham Palace",
            "wikidata_id": "Q42182",
            "coordinates": (51.5014, -0.1419),
            "year_built": 1703,
            "architectural_style": "Neoclassical",
            "poi_type": "government",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b4/Buckingham_Palace_from_gardens%2C_London%2C_UK_-_Diliff.jpg/800px-Buckingham_Palace.jpg",
            "summary": "The official London residence of the British monarch since Queen Victoria in 1837, with 775 rooms including 52 bedrooms. The Changing of the Guard ceremony occurs at 11am on certain days, lasting about 45 minutes. The State Rooms open to visitors in summer when the Royal Family is at Balmoral.",
            "summary_es": "La residencia oficial en Londres del monarca britanico desde la Reina Victoria en 1837, con 775 habitaciones incluyendo 52 dormitorios. La ceremonia del Cambio de Guardia ocurre a las 11am ciertos dias, durando aproximadamente 45 minutos. Las Salas de Estado se abren a visitantes en verano cuando la Familia Real esta en Balmoral.",
            "estimated_visit_duration": 150,
        },
        {
            "name": "Tower Bridge",
            "wikidata_id": "Q182925",
            "coordinates": (51.5055, -0.0754),
            "year_built": 1894,
            "architect": "Horace Jones",
            "architectural_style": "Victorian Gothic",
            "poi_type": "monument",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/Tower_Bridge_from_Shad_Thames.jpg/800px-Tower_Bridge.jpg",
            "summary": "Often confused with London Bridge, this Victorian marvel still raises its bascules about 800 times per year for tall ships. Walk across the glass floor walkways 42 meters above the Thames for a thrilling perspective. Check the lift times online to witness the iconic bridge opening, which takes about 5 minutes.",
            "summary_es": "A menudo confundido con London Bridge, esta maravilla victoriana aun levanta sus basculas unas 800 veces al ano para barcos altos. Camina por los pasillos con piso de cristal a 42 metros sobre el Tamesis para una perspectiva emocionante. Consulta los horarios de apertura en linea para presenciar la apertura del iconico puente, que toma unos 5 minutos.",
            "estimated_visit_duration": 60,
        },
    ],
    "Cairo": [
        {
            "name": "Pyramids of Giza",
            "wikidata_id": "Q37200",
            "coordinates": (29.9792, 31.1342),
            "year_built": -2560,
            "year_built_circa": True,
            "architectural_style": "Ancient Egyptian",
            "heritage_status": "UNESCO World Heritage Site",
            "poi_type": "monument",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/Kheops-Pyramid.jpg/800px-Kheops-Pyramid.jpg",
            "summary": "The only surviving wonder of the ancient world, the Great Pyramid stood as Earth's tallest structure for over 3,800 years. Each limestone block weighs an average of 2.5 tons, with over 2.3 million blocks used. Arrive at 8am for the smallest crowds and best light for photos, and consider a camel ride for desert views.",
            "summary_es": "La unica maravilla sobreviviente del mundo antiguo, la Gran Piramide fue la estructura mas alta de la Tierra durante mas de 3,800 anos. Cada bloque de piedra caliza pesa un promedio de 2.5 toneladas, con mas de 2.3 millones de bloques utilizados. Llega a las 8am para menos multitudes y mejor luz para fotos, y considera un paseo en camello para vistas del desierto.",
            "estimated_visit_duration": 180,
        },
        {
            "name": "Egyptian Museum",
            "wikidata_id": "Q188739",
            "coordinates": (30.0478, 31.2336),
            "year_built": 1902,
            "architectural_style": "Neoclassical",
            "poi_type": "museum",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/Egyptian_Museum_-_Cairo_1.jpg/800px-Egyptian_Museum.jpg",
            "summary": "Houses the world's largest collection of pharaonic antiquities, including Tutankhamun's golden death mask weighing 11 kilograms of solid gold. Over 120,000 items are displayed across two floors, though many more are in storage. The Royal Mummy Room (separate ticket) contains the preserved remains of ancient pharaohs.",
            "summary_es": "Alberga la coleccion mas grande del mundo de antiguedades faraonicas, incluyendo la mascara mortuoria de oro de Tutankamon que pesa 11 kilogramos de oro solido. Mas de 120,000 articulos se exhiben en dos pisos, aunque muchos mas estan en almacenamiento. La Sala de Momias Reales (boleto separado) contiene los restos preservados de faraones antiguos.",
            "estimated_visit_duration": 180,
        },
        {
            "name": "Khan el-Khalili",
            "wikidata_id": "Q631808",
            "coordinates": (30.0477, 31.2619),
            "year_built": 1382,
            "poi_type": "building",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/99/Cairo_-_Khan_el-Khalili_-_shops.jpg/800px-Khan_el-Khalili.jpg",
            "summary": "One of the Middle East's oldest and largest bazaars, trading continuously since the 14th century. Navigate the labyrinthine alleys to find copper artisans, spice merchants, and antique dealers. Stop at El Fishawy cafe, open 24 hours since 1773, where Nobel laureate Naguib Mahfouz found inspiration for his novels.",
            "summary_es": "Uno de los bazares mas antiguos y grandes del Medio Oriente, comerciando continuamente desde el siglo XIV. Navega por los callejones laberinticos para encontrar artesanos del cobre, comerciantes de especias y anticuarios. Detente en el cafe El Fishawy, abierto 24 horas desde 1773, donde el premio Nobel Naguib Mahfouz encontro inspiracion para sus novelas.",
            "estimated_visit_duration": 120,
        },
        {
            "name": "Great Sphinx of Giza",
            "wikidata_id": "Q37221",
            "coordinates": (29.9753, 31.1376),
            "year_built": -2500,
            "year_built_circa": True,
            "architectural_style": "Ancient Egyptian",
            "heritage_status": "UNESCO World Heritage Site",
            "poi_type": "monument",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/Great_Sphinx_of_Giza_-_20080716a.jpg/800px-Great_Sphinx.jpg",
            "summary": "The oldest known monumental sculpture, this limestone figure with a lion's body and human head stands 20 meters tall. The missing nose was already gone by the 15th century, possibly removed by iconoclasts. The Sound and Light Show after dark illuminates the Sphinx and pyramids with a dramatic historical narrative.",
            "summary_es": "La escultura monumental mas antigua conocida, esta figura de piedra caliza con cuerpo de leon y cabeza humana mide 20 metros de altura. La nariz faltante ya habia desaparecido para el siglo XV, posiblemente removida por iconoclastas. El Espectaculo de Sonido y Luz despues del anochecer ilumina la Esfinge y las piramides con una narrativa historica dramatica.",
            "estimated_visit_duration": 60,
        },
        {
            "name": "Al-Azhar Mosque",
            "wikidata_id": "Q169075",
            "coordinates": (30.0458, 31.2627),
            "year_built": 972,
            "architectural_style": "Islamic",
            "heritage_status": "UNESCO World Heritage Site",
            "poi_type": "church",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Al_Azhar_Mosque_Cairo.jpg/800px-Al_Azhar_Mosque.jpg",
            "summary": "Founded in 970 AD, Al-Azhar houses the world's second-oldest continuously operating university. The stunning marble courtyard and multiple minarets represent 1,000 years of Islamic architectural evolution. Non-Muslims are welcome to visit outside prayer times, but modest dress and head coverings are required.",
            "summary_es": "Fundada en 970 d.C., Al-Azhar alberga la segunda universidad en funcionamiento continuo mas antigua del mundo. El impresionante patio de marmol y multiples minaretes representan 1,000 anos de evolucion arquitectonica islamica. Los no musulmanes son bienvenidos a visitar fuera de los horarios de oracion, pero se requiere vestimenta modesta y cubrirse la cabeza.",
            "estimated_visit_duration": 60,
        },
    ],
    "Sydney": [
        {
            "name": "Sydney Opera House",
            "wikidata_id": "Q45178",
            "coordinates": (-33.8568, 151.2153),
            "year_built": 1973,
            "architect": "Jorn Utzon",
            "architectural_style": "Expressionist",
            "heritage_status": "UNESCO World Heritage Site",
            "poi_type": "theater",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/40/Sydney_Opera_House_Sails.jpg/800px-Sydney_Opera_House.jpg",
            "summary": "Danish architect Jorn Utzon's masterpiece took 16 years to build, 10 years over schedule, and cost 14 times the original budget. The roof's 1 million Swedish tiles are self-cleaning and have never been replaced since 1973. Catch a performance, or take a backstage tour to see the concert hall's massive pipe organ.",
            "summary_es": "La obra maestra del arquitecto danes Jorn Utzon tomo 16 anos en construirse, 10 anos mas de lo programado, y costo 14 veces el presupuesto original. Los 1 millon de azulejos suecos del techo son autolimpiables y nunca han sido reemplazados desde 1973. Asiste a una presentacion, o toma un tour tras bambalinas para ver el enorme organo de tubos del salon de conciertos.",
            "estimated_visit_duration": 120,
        },
        {
            "name": "Sydney Harbour Bridge",
            "wikidata_id": "Q1140119",
            "coordinates": (-33.8523, 151.2108),
            "year_built": 1932,
            "architect": "John Bradfield",
            "architectural_style": "Steel arch bridge",
            "poi_type": "monument",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Sydney_Harbour_Bridge_from_Circular_Quay.jpg/800px-Sydney_Harbour_Bridge.jpg",
            "summary": "Nicknamed 'The Coathanger' for its distinctive shape, this steel arch bridge took 8 years to build during the Great Depression. The BridgeClimb experience takes you 134 meters above the harbor for panoramic views of the city and ocean. The southeast pylon contains a museum about the bridge's construction.",
            "summary_es": "Apodado 'La Percha' por su forma distintiva, este puente de arco de acero tomo 8 anos en construirse durante la Gran Depresion. La experiencia BridgeClimb te lleva 134 metros sobre el puerto para vistas panoramicas de la ciudad y el oceano. El pilon sureste contiene un museo sobre la construccion del puente.",
            "estimated_visit_duration": 180,
        },
        {
            "name": "Bondi Beach",
            "wikidata_id": "Q813867",
            "coordinates": (-33.8908, 151.2743),
            "poi_type": "park",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Bondi_Beach_Sydney_Australia.jpg/800px-Bondi_Beach.jpg",
            "summary": "Australia's most famous beach hosts world-class surf breaks and a vibrant cafe culture along the foreshore. The Bondi to Coogee coastal walk (6km) offers stunning cliff views and natural ocean pools. Learn to surf with one of the many schools, or watch the Bondi Rescue lifeguards in action during summer.",
            "summary_es": "La playa mas famosa de Australia ofrece olas de surf de clase mundial y una vibrante cultura de cafes a lo largo del paseo maritimo. El sendero costero de Bondi a Coogee (6km) ofrece impresionantes vistas de acantilados y piscinas naturales de oceano. Aprende a surfear con una de las muchas escuelas, o mira a los salvavidas de Bondi Rescue en accion durante el verano.",
            "estimated_visit_duration": 180,
        },
        {
            "name": "Taronga Zoo",
            "wikidata_id": "Q3518199",
            "coordinates": (-33.8436, 151.2413),
            "year_built": 1916,
            "poi_type": "park",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Taronga_Zoo_entrance.jpg/800px-Taronga_Zoo.jpg",
            "summary": "Set on 28 hectares overlooking Sydney Harbour, this zoo houses over 4,000 animals from 350 species. The ferry ride from Circular Quay offers postcard views of the Opera House and Harbour Bridge. The Roar & Snore overnight safari experience lets you sleep in luxury tents among the animals.",
            "summary_es": "Ubicado en 28 hectareas con vista al puerto de Sydney, este zoologico alberga mas de 4,000 animales de 350 especies. El viaje en ferry desde Circular Quay ofrece vistas de postal de la Opera House y el Harbour Bridge. La experiencia de safari nocturno Roar & Snore te permite dormir en tiendas de lujo entre los animales.",
            "estimated_visit_duration": 240,
        },
        {
            "name": "Royal Botanic Garden",
            "wikidata_id": "Q1073831",
            "coordinates": (-33.8642, 151.2166),
            "year_built": 1816,
            "poi_type": "park",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/37/Royal_Botanic_Gardens_Sydney.jpg/800px-Royal_Botanic_Gardens.jpg",
            "summary": "Australia's oldest scientific institution spans 30 hectares along the harbor, with over 8,900 plant species. The garden occupies the site where Australia's first European farm was established in 1788. Free guided walks depart daily, or relax on the lawns with spectacular views of the Opera House.",
            "summary_es": "La institucion cientifica mas antigua de Australia abarca 30 hectareas a lo largo del puerto, con mas de 8,900 especies de plantas. El jardin ocupa el sitio donde se establecio la primera granja europea de Australia en 1788. Los paseos guiados gratuitos salen diariamente, o relajate en el cesped con vistas espectaculares de la Opera House.",
            "estimated_visit_duration": 120,
        },
    ],
    "Marrakech": [
        {
            "name": "Jemaa el-Fnaa",
            "wikidata_id": "Q853816",
            "coordinates": (31.6258, -7.9891),
            "heritage_status": "UNESCO Intangible Cultural Heritage",
            "poi_type": "monument",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/Jemaa_el_Fnaa.jpg/800px-Jemaa_el_Fnaa.jpg",
            "summary": "The heart of Marrakech transforms hourly: morning markets give way to snake charmers and henna artists, then evening food stalls and musicians. UNESCO designated it a Masterpiece of Oral and Intangible Heritage in 2008. Navigate the chaos from a rooftop cafe terrace for the best vantage point as night falls.",
            "summary_es": "El corazon de Marrakech se transforma cada hora: los mercados de la manana dan paso a encantadores de serpientes y artistas de henna, luego puestos de comida nocturnos y musicos. UNESCO lo designo Obra Maestra del Patrimonio Oral e Inmaterial en 2008. Navega el caos desde una terraza de cafe en la azotea para el mejor punto de vista al caer la noche.",
            "estimated_visit_duration": 180,
        },
        {
            "name": "Bahia Palace",
            "wikidata_id": "Q810158",
            "coordinates": (31.6214, -7.9833),
            "year_built": 1900,
            "architectural_style": "Moorish",
            "poi_type": "building",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/Bahia_Palace_Marrakech.jpg/800px-Bahia_Palace.jpg",
            "summary": "Built over 14 years for Grand Vizier Si Moussa, this palace showcases the finest Moroccan craftsmanship in its 8 hectares. The name means 'brilliance,' and intricate zellige tilework, carved cedar, and painted ceilings justify it. No furniture remains, but the architecture itself tells the story of 19th-century Moroccan aristocracy.",
            "summary_es": "Construido durante 14 anos para el Gran Visir Si Moussa, este palacio muestra la mejor artesania marroqui en sus 8 hectareas. El nombre significa 'brillantez,' y el intrincado trabajo de azulejos zellige, cedro tallado y techos pintados lo justifican. No queda mobiliario, pero la arquitectura misma cuenta la historia de la aristocracia marroqui del siglo XIX.",
            "estimated_visit_duration": 90,
        },
        {
            "name": "Majorelle Garden",
            "wikidata_id": "Q1077893",
            "coordinates": (31.6416, -8.0031),
            "year_built": 1931,
            "architect": "Jacques Majorelle",
            "poi_type": "park",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/62/Majorelle_Garden%2C_Marrakech_%282%29.jpg/800px-Majorelle_Garden.jpg",
            "summary": "Created by French painter Jacques Majorelle over 40 years, this garden was later owned by Yves Saint Laurent and Pierre Berge. The distinctive cobalt blue, now called Majorelle Blue, adorns buildings throughout the 2.5-acre oasis. YSL's ashes were scattered here, and a memorial dedicated to him stands in the garden.",
            "summary_es": "Creado por el pintor frances Jacques Majorelle durante 40 anos, este jardin fue posteriormente propiedad de Yves Saint Laurent y Pierre Berge. El distintivo azul cobalto, ahora llamado Azul Majorelle, adorna edificios en todo el oasis de 1 hectarea. Las cenizas de YSL fueron esparcidas aqui, y un memorial dedicado a el se encuentra en el jardin.",
            "estimated_visit_duration": 90,
        },
        {
            "name": "Koutoubia Mosque",
            "wikidata_id": "Q606721",
            "coordinates": (31.6237, -7.9937),
            "year_built": 1199,
            "architectural_style": "Almohad",
            "poi_type": "church",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Minaret_of_Koutoubia_Mosque.jpg/800px-Koutoubia_Mosque.jpg",
            "summary": "The largest mosque in Marrakech, its 77-meter minaret served as the model for the Giralda in Seville and Hassan Tower in Rabat. Non-Muslims cannot enter, but the surrounding gardens offer perfect views of the tower, especially at sunset. The muezzin's call to prayer echoes across the medina five times daily.",
            "summary_es": "La mezquita mas grande de Marrakech, su minarete de 77 metros sirvio como modelo para la Giralda en Sevilla y la Torre Hassan en Rabat. Los no musulmanes no pueden entrar, pero los jardines circundantes ofrecen vistas perfectas de la torre, especialmente al atardecer. El llamado a la oracion del muecin resuena por la medina cinco veces al dia.",
            "estimated_visit_duration": 30,
        },
        {
            "name": "Saadian Tombs",
            "wikidata_id": "Q1814282",
            "coordinates": (31.6179, -7.9886),
            "year_built": 1578,
            "architectural_style": "Saadian",
            "poi_type": "monument",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Saadian_tombs_%281%29.jpg/800px-Saadian_tombs.jpg",
            "summary": "Hidden for centuries and only rediscovered in 1917, these tombs house 66 members of the Saadian dynasty. The Hall of Twelve Columns contains the tomb of Sultan Ahmad al-Mansur, with stunning Italian Carrara marble columns. Arrive early to avoid queues in the intimate spaces of this hidden gem.",
            "summary_es": "Ocultas durante siglos y solo redescubiertas en 1917, estas tumbas albergan 66 miembros de la dinastia Saadiana. La Sala de las Doce Columnas contiene la tumba del Sultan Ahmad al-Mansur, con impresionantes columnas de marmol italiano de Carrara. Llega temprano para evitar colas en los espacios intimos de esta joya escondida.",
            "estimated_visit_duration": 45,
        },
    ],
}


async def seed_extended_data():
    """Seed the database with extended city and POI data."""
    async with async_session_maker() as session:
        # Check which cities already exist
        result = await session.execute(select(City.name))
        existing_cities = {row[0] for row in result.fetchall()}

        cities_added = 0
        pois_added = 0

        city_map = {}

        print("Seeding extended cities...")
        for city_data in EXTENDED_CITIES:
            if city_data["name"] in existing_cities:
                # Fetch existing city for POI linking
                result = await session.execute(
                    select(City).where(City.name == city_data["name"])
                )
                city_map[city_data["name"]] = result.scalar_one()
                print(f"  Skipping existing city: {city_data['name']}")
                continue

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
            cities_added += 1
            print(f"  Added city: {city_data['name']}")

        await session.flush()

        print("Seeding extended POIs...")
        for city_name, pois in EXTENDED_POIS.items():
            city = city_map.get(city_name)
            if not city:
                print(f"  Warning: City {city_name} not found, skipping POIs")
                continue

            # Check existing POIs for this city
            result = await session.execute(
                select(POI.name).where(POI.city_id == city.id)
            )
            existing_pois = {row[0] for row in result.fetchall()}

            for poi_data in pois:
                if poi_data["name"] in existing_pois:
                    print(f"  Skipping existing POI: {poi_data['name']} ({city_name})")
                    continue

                lat, lng = poi_data["coordinates"]
                point_wkt = f"SRID=4326;POINT({lng} {lat})"

                poi = POI(
                    id=uuid4(),
                    city_id=city.id,
                    name=poi_data["name"],
                    wikidata_id=poi_data.get("wikidata_id"),
                    coordinates=point_wkt,
                    year_built=poi_data.get("year_built"),
                    year_built_circa=poi_data.get("year_built_circa", False),
                    architect=poi_data.get("architect"),
                    architectural_style=poi_data.get("architectural_style"),
                    heritage_status=poi_data.get("heritage_status"),
                    poi_type=poi_data["poi_type"],
                    image_url=poi_data.get("image_url"),
                    summary=poi_data.get("summary"),
                    summary_es=poi_data.get("summary_es"),
                    estimated_visit_duration=poi_data.get(
                        "estimated_visit_duration", 60
                    ),
                    data_source="seed_extended",
                )
                session.add(poi)
                pois_added += 1
                print(f"  Added POI: {poi_data['name']} ({city_name})")

        await session.commit()
        print(f"\nSeeding complete! Added {cities_added} cities and {pois_added} POIs.")


if __name__ == "__main__":
    asyncio.run(seed_extended_data())
