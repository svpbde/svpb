.. meta::
   :scope: entwickler

************************
Entwickler-Dokumentation
************************

Struktur
========
Die Applikation besteht aus drei Teilen - *arbeitsplan*, *boote* und *mitglieder*.
*arbeitsplan* enthält nebem dem Arbeitsplan auch die Definition der Mitglieder-*models* (Datenbanktabellen).
*boote* enthält Funktionalität zum Reservieren von Booten und greift auf die models aus *arbeitsplan* zurück.
*mitglieder* enthält eine Weboberfläche für den Vorstand zur Verwaltung der Mitglieder - ohne eigene models.


Klassendiagramm
---------------

Eine Übersicht über die models gibt das Klassendiagramm in Abbildung :ref:`diagram-models`.
Das Klassendiagramm kann mittels `python manage.py graph_models -a -g -o klassendiagramm.png` bzw. `.pdf` gebaut werden,
wie in der `graph_models Dokumentation <https://django-extensions.readthedocs.io/en/latest/graph_models.html>`_ beschrieben.

.. _diagram-models:

.. figure:: figures/klassendiagramm.*

    Klassendiagramm der models


ToDos
=====

Generierte Dokumentation
========================

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


