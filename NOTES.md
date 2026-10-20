## 1. Retraso al iniciar llamadas grandes

El endpoint `GET /calls/{id}/context` cargaba las llamadas previas de
un contacto y después consultaba el resultado de cada una dentro de un
bucle. 
He usado `select_related` para cargar campaña y contacto junto a la
llamada, y `prefetch_related` para cargar los resultados históricos en
una consulta adicional. Así, el número de consultas permanece estable
aunque un contacto tenga más historial.

Añadí una prueba que crea historial y verifica el número de consultas.
`test_queries_historical_calls()`


## 2. Facturación duplicada
Vemos que se repite hasta 3 veces el intento de envío del POST cuando 
se detecta que no ha llegado respuesta de que se haya entregado el 
resultado de la llamada. El problema es que puede haber llegado el
resultado de la llamada pero se haya perdido la respuesta. Se reenvía
el POST y se añade una vez más la suma ya que no se comprueba si hay
resultado ya guardado o no.

Se genera un test para probar si esto es cierto:
`test_same_result_twice_is_only_billed_once`
En este test se prueban dos llamadas, y se comprueba l número de
llamadas registradas y el número de mintos facturados. 

Para arreglarlo se comprueba si el resultado ya estaba registrado o no.
En este caso, pasa el primer test.

### 2.1. Resultado distinto al guardado
Si llega un resultado distinto al que se ha guardado, de momento se
devuelve un código 409 como identificador del fallo. 