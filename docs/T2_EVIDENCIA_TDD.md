# TDD real — ejercicio de la T2

Se detectó un comportamiento defectuoso en la búsqueda de empleos: cuando se
recibía un apoyo inexistente o inactivo, la consulta ignoraba el filtro y mostraba
todas las ofertas, lo que inducía a error sobre accesibilidad.

## RED (prueba primero)
- Commit de pruebas: [8df4929](https://github.com/1621-nicolas/talenvia/commit/8df492984a23251acbb3ac2f0e8cb63b90ef065f).
- Ejecución fallida [GitHub Actions RED](https://github.com/1621-nicolas/talenvia/actions/runs/39015561913): 34 pruebas; **2 fallos esperados**.
- Diagnóstico: para los filtros inexistente y desactivado se obtuvo un registro, frente a los 0 previstos.

## GREEN (código mínimo)
- Commit de corrección: [096cfe7](https://github.com/1621-nicolas/talenvia/commit/096cfe754bdd902f8e201becda0b33186fcee324).
- Ejecución exitosa [GitHub Actions GREEN](https://github.com/1621-nicolas/talenvia/actions/runs/39015651582): 34/34, **83 % cobertura** (sobre SQLite).
- La búsqueda devuelve cero registros si alguno de los apoyos solicitados no existe o no está activo. Si todos son válidos, aplica los filtros AND.

## Validación humana
Antes de la exposición, el equipo debe reproducir manualmente los tres casos
(válido/inválido/inactivo) en la web y adjuntar capturas. La prueba RED no es
un error dejado en producción: es una evidencia del comportamiento anterior.
