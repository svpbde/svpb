.. meta::
   :scope: entwickler

************************
Entwickler-Dokumentation
************************

Bauen dieser Dokumentation
==========================
Diese Dokumentation kann mit Hilfe von `Sphinx <https://www.sphinx-doc.org/en/master/>`_ über einen Aufruf von :code:`make allversions` im Ordner docs gebaut werden.
Dabei werden vier verschiedene pdf-Dokumente für die jeweiligen Zielgruppen gebaut.
Die Auswahl der Zielgruppen ist über eine Sphinx extension (siehe docs/extensions) realisiert, welche die Sphinx-Option "-t" auswertet.
Keine Angabe entspricht der Zielgruppe Mitglieder, ansonsten gibt es *teamleader*, *vorstand* und *entwickler*.
Außerdem kann die Dokumentation im html-Format gebaut werden: :code:`make html SPHINXOPTS='-t entwickler'`.

Struktur
========
Die Applikation besteht aus drei Teilen - *arbeitsplan*, *boote* und *mitglieder*.
*arbeitsplan* enthält nebem dem Arbeitsplan auch die Definition der Mitglieder-*models* (Datenbanktabellen).
*boote* enthält Funktionalität zum Reservieren von Booten und greift auf die models aus *arbeitsplan* zurück.
*mitglieder* enthält eine Weboberfläche für den Vorstand zur Verwaltung der Mitglieder - ohne eigene models.


Klassendiagramm
---------------

Eine Übersicht über die models gibt das Klassendiagramm in Abbildung :ref:`diagram-models`.
Das Klassendiagramm kann mittels :code:`python manage.py graph_models -a -g -o klassendiagramm.png` bzw. `.pdf` gebaut werden,
wie in der `graph_models Dokumentation <https://django-extensions.readthedocs.io/en/latest/graph_models.html>`_ beschrieben.

.. _diagram-models:

.. figure:: figures/klassendiagramm.*

    Klassendiagramm der models


Commands
========

Die commands können z.B. als cronjobs ausgeführt werden.

meldungConsistent
-----------------
.. automodule:: arbeitsplan.management.commands.meldungConsistent
    :members:

mitgliedExcel
-------------
.. automodule:: arbeitsplan.management.commands.mitgliedExcel
    :members:

reminderLeistungen
------------------
.. automodule:: arbeitsplan.management.commands.reminderLeistungen
    :members:

reservationEmails
-----------------
.. automodule:: arbeitsplan.management.commands.reservationEmails
    :members:

statistics
----------
.. automodule:: arbeitsplan.management.commands.statistics
    :members:

upcomingJob
-----------
.. automodule:: arbeitsplan.management.commands.upcomingJob
    :members:

yearendArbeitslast
------------------
.. automodule:: arbeitsplan.management.commands.yearendArbeitslast
    :members:


Arbeitsplan
===========

Models
------

.. automodule:: arbeitsplan.models
    :members:

Views
-----

.. automodule:: arbeitsplan.views
    :members:

Tables
------

.. automodule:: arbeitsplan.tables
    :members:

Forms
------

.. automodule:: arbeitsplan.forms
    :members:


Boote
=====

Models
------

.. automodule:: boote.models
    :members:

Views
-----

.. automodule:: boote.views
    :members:

Forms
------

.. automodule:: boote.forms
    :members:


Mitglieder
==========

Models
------

.. automodule:: mitglieder.models
    :members:

Views
-----

.. automodule:: mitglieder.views
    :members:

Tables
------

.. automodule:: mitglieder.tables
    :members:

Forms
------

.. automodule:: mitglieder.forms
    :members:
