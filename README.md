# LeAPI

This implements a REST style API to provide access to
[LEWAS](http://www.lewas.centers.vt.edu/) collected data. If you're
already familiar with
[REST APIs](http://www.restapitutorial.com/lessons/whatisrest.html)
and the LEWAS data and just want an endpoint reference, check out the
[swagger-generated docs](http://lewaspedia.enge.vt.edu:8080/leapi-doc/#!/leapi).

## Limitations/TODO

While planned, the current implementation doesn't fully incorporate
the [HATEOAS](https://spring.io/understanding/HATEOAS) principle. This
means people implementing programs that access the API need to pay
more attention to
[endpoint names](http://lewaspedia.enge.vt.edu:8080/leapi-doc/#!/leapi)
for different resources their program must access and be aware of
when/if endpoint names change. Hopefully HATEOAS will be implemented
in the near future allowing for more robust and maintainable client
code.
