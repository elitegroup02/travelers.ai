export const es = {
  // App
  'app.name': 'travelers.ai',
  'app.tagline': 'Descubre las historias detrás de cada lugar',

  // Common
  'common.loading': 'Cargando...',
  'common.error': 'Ha ocurrido un error',
  'common.retry': 'Reintentar',
  'common.cancel': 'Cancelar',
  'common.save': 'Guardar',
  'common.delete': 'Eliminar',
  'common.edit': 'Editar',
  'common.share': 'Compartir',
  'common.export': 'Exportar',
  'common.search': 'Buscar',
  'common.back': 'Atrás',
  'common.next': 'Siguiente',
  'common.done': 'Hecho',
  'common.close': 'Cerrar',

  // Auth
  'auth.login': 'Iniciar Sesión',
  'auth.register': 'Registrarse',
  'auth.logout': 'Cerrar Sesión',
  'auth.email': 'Correo electrónico',
  'auth.password': 'Contraseña',
  'auth.confirmPassword': 'Confirmar contraseña',
  'auth.displayName': 'Nombre',
  'auth.forgotPassword': '¿Olvidaste tu contraseña?',
  'auth.noAccount': '¿No tienes cuenta?',
  'auth.hasAccount': '¿Ya tienes cuenta?',
  'auth.loginError': 'Correo o contraseña inválidos',
  'auth.registerError': 'No se pudo crear la cuenta',

  // Navigation
  'nav.home': 'Inicio',
  'nav.explore': 'Explorar',
  'nav.trips': 'Mis Viajes',
  'nav.settings': 'Ajustes',

  // Home
  'home.welcome': 'Bienvenido a travelers.ai',
  'home.welcomeMessage': 'Planifica tu próxima aventura cultural',
  'home.recentTrips': 'Viajes Recientes',
  'home.recentCities': 'Ciudades Recientes',
  'home.noTrips': 'Aún no hay viajes',
  'home.startPlanning': 'Comienza a planificar tu primer viaje',

  // City
  'city.search': 'Buscar Ciudades',
  'city.searchPlaceholder': 'Buscar una ciudad...',
  'city.noResults': 'No se encontraron ciudades',
  'city.pointsOfInterest': 'Puntos de Interés',
  'city.noPois': 'No se encontraron puntos de interés',
  'city.showOnMap': 'Ver en Mapa',
  'city.showList': 'Ver Lista',

  // POI
  'poi.yearBuilt': 'Construido',
  'poi.architect': 'Arquitecto',
  'poi.style': 'Estilo',
  'poi.heritage': 'Patrimonio',
  'poi.visitDuration': 'Duración de visita',
  'poi.minutes': 'min',
  'poi.addToTrip': 'Añadir al Viaje',
  'poi.removeFromTrip': 'Quitar del Viaje',
  'poi.viewOnWikipedia': 'Ver en Wikipedia',
  'poi.mustSee': 'Imprescindible',
  'poi.dataQuality': 'Calidad de datos',
  'poi.aboutThisPlace': 'Sobre este lugar',
  'poi.coordinates': 'Coordenadas',
  'poi.placesFound': 'lugares encontrados',
  'poi.noPOIs': 'No se encontraron lugares',

  // POI Types
  'poiType.cathedral': 'Catedral',
  'poiType.church': 'Iglesia',
  'poiType.museum': 'Museo',
  'poiType.palace': 'Palacio',
  'poiType.castle': 'Castillo',
  'poiType.monument': 'Monumento',
  'poiType.park': 'Parque',
  'poiType.plaza': 'Plaza',
  'poiType.bridge': 'Puente',
  'poiType.tower': 'Torre',
  'poiType.theater': 'Teatro',
  'poiType.library': 'Biblioteca',
  'poiType.university': 'Universidad',
  'poiType.building': 'Edificio',
  'poiType.government': 'Gobierno',
  'poiType.landmark': 'Monumento',
  'poiType.other': 'Otro',

  // Trip
  'trip.newTrip': 'Nuevo Viaje',
  'trip.editTrip': 'Editar Viaje',
  'trip.tripName': 'Nombre del Viaje',
  'trip.destination': 'Destino',
  'trip.startDate': 'Fecha de Inicio',
  'trip.endDate': 'Fecha de Fin',
  'trip.status.draft': 'Borrador',
  'trip.status.planned': 'Planificado',
  'trip.status.completed': 'Completado',
  'trip.noPois': 'Aún no hay lugares añadidos',
  'trip.addPlaces': 'Añade lugares para visitar',
  'trip.deleteConfirm': '¿Estás seguro de que quieres eliminar este viaje?',

  // Itinerary
  'itinerary.generate': 'Generar Itinerario',
  'itinerary.regenerate': 'Regenerar',
  'itinerary.day': 'Día',
  'itinerary.walkingTime': 'Tiempo caminando',
  'itinerary.totalTime': 'Tiempo total',
  'itinerary.arrival': 'Llegada',
  'itinerary.departure': 'Salida',
  'itinerary.noItinerary': 'Aún no se ha generado itinerario',

  // Export
  'export.asPdf': 'Exportar como PDF',
  'export.asCalendar': 'Añadir al Calendario',
  'export.asGoogleMaps': 'Abrir en Google Maps',
  'export.shareLink': 'Compartir Enlace',
  'export.copyLink': 'Copiar Enlace',
  'export.linkCopied': 'Enlace copiado al portapapeles',

  // Settings
  'settings.language': 'Idioma',
  'settings.languageEn': 'Inglés',
  'settings.languageEs': 'Español',
  'settings.account': 'Cuenta',
  'settings.about': 'Acerca de',
  'settings.version': 'Versión',
  'settings.privacy': 'Política de Privacidad',
  'settings.terms': 'Términos de Servicio',

  // Errors
  'error.network': 'Error de red. Por favor verifica tu conexión.',
  'error.server': 'Error del servidor. Por favor intenta más tarde.',
  'error.notFound': 'No encontrado',
  'error.unauthorized': 'Por favor inicia sesión para continuar',
  'error.forbidden': 'No tienes acceso a este recurso',

  // Sync
  'sync.syncing': 'Sincronizando...',
  'sync.synced': 'Todos los cambios sincronizados',
  'sync.offline': 'Sin conexión - los cambios se sincronizarán cuando vuelvas a estar en línea',
  'sync.error': 'Error de sincronización',
} as const;
