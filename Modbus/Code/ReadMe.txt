Afin d'exécuter le code sur les différents modules ( raspberry, zolertia ),
plusieurs commandes sont essentielles à exécuter dans le terminal :


Raspbbery : Dans le répertoire Home :
python send.py // pour lancer le code python sur tous les modules raspberry.
python receice.py // pour lancer le code python sur le serveur et recevoir les données sur tous les Topics (sauf Final).
python receice-final.py // pour lancer le code python sur le serveur et recevoir les données sur le Topic 'Final'.


Zolertia : Dans le répertoire Contiki/examples/ipv6/rpl-udp/ :
Sudo make TARGET=zoul udp-client.upload // à lancer sur le Zolertia source et relais.
Sudo make TARGET=zoul udp-server.upload // à lancer sur le Zolertia destination.

N.B: 'login' peut s'ajouter à la fin des deux dernières commandes afin de visualiser les résultats.