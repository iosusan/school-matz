CERTIFICADO DE DOMINIO
En el primer arrange, se pregunta el dominio bajo el que se mostrará la aplicación
el certificado https se generará para el dominio indicado,tanto en el arranque estándar
como en el arranque por docker


USUARIOS Y ROLES
1. añadir un usuario  superadministrador inicial, que en el primer arranque pregunte username y password
y quede configurado como ROOT del sistema:
- en ejecución sin docker, será un paso más en los scripts de setup que tendrá que ejecutar
el usuario a mano, scripts/prepare_root.sh
que pedirá de forma interactiva nombre de usuario y contraseña. La contraseña se guardará hasheada de forma segura
- en ejecución con docker, en la primera ejecución del container pedirá de forma interactiva
el nomre de usuario y contraseña del superadministrador, y se configurarán dentro del contenedor.
LA contraseña se guardará hasheada de forma segura.

2. añadir soporte para roles de usuarios en la aplicación:
- admins, podrán entrar a la pestaña de administración, y crear/modificar/eliminar  usuarios
- el superadministrador inicial también puede entrar a la pestaña de administración y podrá
crear/modificar/eliminar admins y usuarios
- usuarios, podran retirar y devolver material, pero no entrar a la pestaña




-----------
lee el fichero MEJORAS.md y elabora un plan para implementarlo

quiero que analices qué opciones hay para dar soporte multi tenant a la aplicación
- serían en distintos stacks docker disjuntos, no en el mismo
- no compartirían infraestructura ni base de datos
- el enrutamiento sería por dominios distintos
-
