## 1. Retraso al iniciar llamadas grandes

El endpoint `GET /calls/{id}/context` cargaba las llamadas previas de
un contacto y después consultaba el resultado de cada una dentro de un
bucle. 
He usado `select_related` para cargar campaña y contacto junto a la
llamada, y `prefetch_related` para cargar los resultados históricos en
una consulta adicional. Así, el número de consultas permanece estable
aunque un contacto tenga más historial.

Añadí una prueba que crea historial y verifica el número de consultas.