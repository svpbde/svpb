# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User


# Create your models here.

## class Mitgliedsstatus (models.Model):
##     status = models.CharField (max_length=30)
##     bemerkung = models.TextField(blank=True)

##     def __unicode__ (self):
##         return self.status 

##     class Meta:
##         verbose_name_plural ="Mitgliedsstatus"
    
## class Mitglied (models.Model):
##     user = models.OneToOneField (User)
##     status = models.ForeignKey (Mitgliedsstatus)

##     def __unicode__ (self):
##         return self.user.__unicode__()

class Aufgabengruppe (models.Model):
    gruppe = models.CharField (max_length=30)
    verantwortlich = models.ForeignKey (User) 
    bemerkung = models.TextField(blank=True)

    def __unicode__ (self):
        return self.gruppe

    class Meta:
        verbose_name_plural = "Aufgabengruppen"
    
class Aufgabe (models.Model):
    aufgabe = models.CharField (max_length=30)
    datum = models.DateField (blank=True, null=True)
    verantwortlich = models.ForeignKey (User)
    gruppe = models.ForeignKey (Aufgabengruppe)
    anzahl = models.IntegerField ()
    bemerkung = models.TextField(blank=True)

    def __unicode__ (self):
        return self.aufgabe

    class Meta:
        verbose_name_plural = "Aufgaben"

class Meldung (models.Model):
    erstellt = models.DateField (auto_now_add=True)
    veraendert = models.DateField (auto_now=True)
    melder = models.ForeignKey (User)
    aufgabe = models.ForeignKey (Aufgabe)

    def __unicode__ (self):
        return (self.melder.__unicode__() + " ; " +
                self.aufgabe.__unicode__() + " ; " +
                (self.veraendert.strftime("%d/%m/%y")
                 if self.veraendert else "--") 
                )

    class Meta:
        verbose_name_plural = "Meldungen"


class Zuteilung (models.Model):
    aufgabe = models.ForeignKey (Aufgabe)
    ausfuehrer = models.ForeignKey (User)
    automatisch = models.BooleanField (default=False)
    class Meta:
        verbose_name_plural = "Zuteilungen"

    def __unicode__ (self):
        return self.aufgabe.__unicode__() + ": " + self.ausfuehrer.__unicode__()
    
    

    
class Leistung (models.Model):
    melder = models.ForeignKey (User)
    aufgabe = models.ForeignKey (Aufgabe)
    erstellt = models.DateField (auto_now_add=True)
    veraendert = models.DateField (auto_now=True)
    wann = models.DateField (help_text="An welchem Tag haben Sie die Leistung erbracht?",
                             ) 
    zeit = models.DecimalField (max_digits=3,
                                decimal_places = 1,
                                help_text="Wieviel Zeit (in Stunden) haben Sie gearbeitet?", 
                                )
    auslagen = models.DecimalField (max_digits=6,
                                    decimal_places = 2,
                                    help_text = "Hatten Sie finanzielle Auslagen? Bitte Belege vorlegen!",
                                    default = 0, 
                                    ) 
    km = models.DecimalField (max_digits= 4,
                              decimal_places = 0,
                              help_text = "Hatten Sie Wegstrecken, für die Sie km-Vergütung erhalten?",
                              default = 0, 
                              )
    
    OFFEN =  'OF'
    ACK = 'AK'
    RUECKFRAGE = 'RU'
    NEG = 'NE'
    
    STATUS = (
        (OFFEN, 'Offen'), 
        (ACK, 'Akzeptiert'), 
        (RUECKFRAGE, 'Rückfrage'), 
        (NEG, 'Abgelehnt'), 
        )

    status = models.CharField (max_length=2,
                               choices = STATUS,
                               default = OFFEN) 
    
    bemerkung = models.TextField (blank=True)
    bemerkungVorstand = models.TextField (blank=True)
            
    class Meta:
        verbose_name_plural = "Leistungen"

    def __unicode__ (self):
        return (self.melder.__unicode__() + " ; " +
                self.aufgabe.__unicode__() + " ; " +
                (self.veraendert.strftime("%d/%m/%y")
                 if self.veraendert else "--") 
                )
        
