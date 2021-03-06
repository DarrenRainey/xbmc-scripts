# -*- coding: UTF8 -*-
# ATTENTION ! ! !
# ce script n'est nullement affilié au groupe allocine.fr
# il est fourni à titre d'exemple et n'est pas garanti de fonctionner ultérieurement.
# allocine.fr ne peut être tenu responsable de l'utilisation qui en serait faite.
# allocine.fr ne permet pas que l'on consulte des informations de leur site en dehors de leur site sans leur accord préalable.
# Le contenu textuel et multimedia (images / videos) appartient exclusivement à allocine.fr
import urllib,re
import sys
import os.path, os
import time

__doc__=u"""
La librairie supporte les 4 versions d'allocine selon le pays :
    - france     : allocine.fr
    - espagne    : screenrush.co.uk
    - angleterre : sensacine.com
    - allemagne  : allocine.de
Pour configurer un pays, utiliser la fonction :
    set_country( <code pays> )
        code_pays = FR ou ES ou EN ou DE
        retourne une exception si aucun pays n'est choisi ou si le code ne correspond à aucun pays

Sorties de la semaine et agenda
    instancier la classe 'agenda' avec en paramètre facultatif la période désirée
    Sans paramètre, la semaine en cours est utilisée

    get_movies()
        retourne une liste de blocs html pour chaque film
    get_movies_datas()
        retourne une liste de tuples contenant les informations récupérées des films
        le tuple est constitué des éléments : ID,Titre,Titre Original,URL de l'affiche,Genre,Duree

Fiche film : Movie(id)
    instancier la classe Movie pour gérer les informations d'un film repéré par son ID (paramètre obligatoire)

    title()
        retourne le titre du film
    
    date()
        retourne la date de sortie du film

    abstract()
        retourne le résumé du film
    
    casting()
        retourne les personnalités (acteurs/realisateurs/...) liées au film
        (ID, nom, fonction)

    pictureURL()
        retourne l'url de l'image associée au film

    ...
        plus de fonctions à venir
   
Fiche personnalité(id)
    instancier la classe Personality pour gérer les informations d'une personnalité (acteur, metteur en scène, ...) repéré par son ID (paramètre obligatoire)
  

"""
__author__  = u"Alexsolex®"
__email__   = u"alexsolex(AT)gmail.com"
__version__ = u"0.0.1"
#debut du travail le 22 septembre 2008

global COUNTRY
global ALLOCINE_ENCODING
global ALLOCINE_DOMAIN

AVAILABLE_COUNTRIES = ["FR", "EN", "ES", "DE"]

ALLOCINE_DOMAIN_dic = {"FR":"http://www.allocine.fr",
                       "EN":"http://www.screenrush.co.uk",
                       "ES":"http://www.sensacine.com",
                       "DE":"http://www.allocine.de"
                       }
ALLOCINE_ENCODING_dic = {"FR":"ISO-8859-1",
                         "EN":"ISO-8859-1",
                         "ES":"ISO-8859-1",
                         "DE":"ISO-8859-1"
                         }
VIDEO_STREAM_URL_dic = {"FR":"http://a69.g.akamai.net/n/69/32563/v1/mediaplayer.allocine.fr%s.flv",
                        "EN":"http://h.uk.mediaplayer.allocine.fr/uk/medias/nmedia%s.flv",
                        "ES":"http://h.es.mediaplayer.allocine.fr%s.flv",
                        "DE":"http://h.de.mediaplayer.allocine.fr%s.flv"
                        }
PHOTOS_MEDIA_URL = "http://a69.g.akamai.net/n/69/10688/v1/img5.allocine.fr/acmedia/rsz/434/x/x/x/medias"
THIS_WEEK_URL       = "/film/cettesemaine.html"
AGENDA_URL          = "/film/agenda.html"
MOVIE_URL           = "/film/fichefilm_gen_cfilm=%s.html"
CASTING_URL         = "/film/casting_gen_cfilm=%s.html"
SORTIES_URL         = "/film/agenda_gen_date=%s.html"
PHOTOS_FILM_URL     = "/film/galerievignette_gen_cfilm=%s.html"

PERSO_URL           = "/personne/fichepersonne_gen_cpersonne=%s.html"
PHOTOS_PERSON_URL   = "/personne/galerievignette_gen_cpersonne=%s.html"

XML_BA_INFOS        = "/video/xml/videos.asp?media=%s"

SEARCH_URL          = "/recherche/"


import cookielib
ROOTDIR = os.getcwd()
CACHEDIR = ROOTDIR#os.path.join(ROOTDIR,"cache")
COOKIEFILE = os.path.join(CACHEDIR,'cookies_allocine.lwp')
cj = cookielib.LWPCookieJar()

if os.path.isfile(COOKIEFILE):
    # si nous avons un fichier cookie déjà sauvegardé
    #  alors charger les cookies dans le Cookie Jar
    cj.load(COOKIEFILE)
    
        #---------------------#
        # FONCTIONS GENERALES #
        #---------------------#
def unescape(text):
    """
    credit : Fredrik Lundh
    found : http://effbot.org/zone/re-sub.htm#unescape-html"""
    import htmlentitydefs
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)

def Log(msg,cat="I"):
    """Used to write log messages"""
    if not msg:
        cat = "I"
        msg = "------marker------"
    logcats = {"W":"WARNING",
               "I":"Info",
               "E":"Error"
               }
    print "%s : %s"%(logcats[cat],msg)
    
        #---------------------------#
        # FONCTIONS TRAITEMENT HTML #
        #---------------------------#

def get_page(url,params={},savehtml=True,filename="defaut.html",debuglevel=0):
    """
    Download given url and return datas. Use GZIP compression if available
    <params> is a ditionnary for POST request
    when 'True', <savehtml> param indicate that <filename> should be used to write file on disk
    Set debuglevel to 1 to print http headers 
    """
    import gzip,StringIO,urllib2
    from urlparse import urlparse
    host=urlparse(url)[1]
    Log( u" >>> get_page(%s) ..."%url)
    h1=urllib2.HTTPHandler(debuglevel=debuglevel)
    h=urllib2.HTTPCookieProcessor(cj)
    if not params:
        request = urllib2.Request(url)
    else:
        request = urllib2.Request(url,urllib.urlencode(params))

    request.add_header('Host',host)#ALLOCINE_DOMAIN[7:])
    request.add_header('Referer', ALLOCINE_DOMAIN)
    request.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; fr; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
    request.add_header('Accept','text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
    request.add_header('Accept-Language','fr,fr-fr;q=0.8,en-us;q=0.5,en;q=0.3')
    request.add_header('Accept-Charset','ISO-8859-1,utf-8;q=0.7,*;q=0.7')
    request.add_header('Accept-Encoding','gzip,deflate')
    request.add_header('Keep-Alive','300')
    for index, cookie in enumerate(cj):
        #print index, '  :  ', cookie
        request.add_header('Cookie',cookie)
    request.add_header('Connection','keep-alive')
    request.add_header('Content-type','application/x-www-form-urlencoded')
    request.add_header('Content-length',len(urllib.urlencode(params)))
    request.add_header('Pragma','no-cache')
    request.add_header('Cache-Control','no-cache')
    request.add_header('Cookie','TestCookie=123')

    opener = urllib2.build_opener(h,h1)
    urllib2.install_opener(opener)
    try:
        connexion = opener.open(request)
    except Exception, msg:
        raise AllocineError, "The requested page for download did not succeed. Reason given : %s"%msg
    html = connexion.read(int(connexion.headers["Content-Length"]))
    if connexion.headers.has_key("Content-Encoding") and connexion.headers["Content-Encoding"]=="gzip":
        compressedstream = StringIO.StringIO(html)
        gzipper = gzip.GzipFile(fileobj=compressedstream)
        data = gzipper.read()
        Log( "\tGZIP (%s o) --> HTML (%s o)"%(str(len(html)),str(len(data))))
    else:
        data = html
    if connexion.headers.has_key("Content-Disposition"):
        Log( connexion.headers["Content-Disposition"].split("filename=")[1] )#: inline; filename=18992446_w434_h_q80.jpg

    try:
        open(os.path.join(CACHEDIR,filename),"wb").write(data)
    except Exception,msg:
        Log("Error while writing download file. \nException says : %s" % msg,"E")
    # save the cookies again
    cj.save(COOKIEFILE)
    Log(u" <<< Fin du téléchargement")
    return data

def infos_text(datas):
    """
    Return given <datas> without html markup
    Allocine picture starring system is replaced with a textual equivalent
    <h*> and <br /> are replaced with newline escape char \\n
    All other <...> markups are deleted and then datas are returned escaped (no '&...;' or such)
    """
    import re
    #remplacement des étoiles de notation
    datas = re.sub(r'<img src="[^"]+?empty\.gif" width="\d+" height="\d+" class="etoile_(\d{1})" border="0" />',r'\1/5',datas)
    #remplacement des sauts de ligne
    datas = re.sub(r"<(?:/h\d|br /)>", "\n", datas)
    #suppression de toutes les autres balises
    datas = re.sub(r"<.*?>", r"", datas)
    #retour du texte échappé (remplacement des caractères html)
    return unescape(datas.decode(ALLOCINE_ENCODING))

def get_pic(url,filename=""):
    """
    Download the picture in the <url> into the optional <filename>
    If the <filename> is not given, it will be an arbitrary temporary filename
    """
    ret = urllib.urlretrieve(url)
    print ret
    
        #---------------------------#
        # EXCEPTIONS PERSONNALISEES #
        #---------------------------#
        
class AllocineError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

        #--------------------#
        # FONCTIONS ALLOCINE #
        #--------------------#
def set_country(country=None):
    if (not (country in AVAILABLE_COUNTRIES)) or country == None:
        raise AllocineError,"<country> MUST be given and MUST BE one of the followings : \n" + " , ".join(AVAILABLE_COUNTRIES)
    else:
        global COUNTRY,ALLOCINE_ENCODING,ALLOCINE_DOMAIN,VIDEO_STREAM_URL
        COUNTRY = country
        ALLOCINE_ENCODING = ALLOCINE_ENCODING_dic[COUNTRY]
        ALLOCINE_DOMAIN   = ALLOCINE_DOMAIN_dic[COUNTRY]
        VIDEO_STREAM_URL  = VIDEO_STREAM_URL_dic[COUNTRY]
        return 

def get_video_url(mediaID,quality=None):
    """
    Search and return a video link for the given <mediaID>
    Will search in this order : HD, MD then LD (the best to the worst quality)
    Optional <quality> parameter enable to limit the search to 
    """
    Log("Getting video url for %s media"%mediaID)
    from types import StringType
    if not (type(mediaID) is StringType):
        raise AllocineError,"<mediaID> MUST be String type"
    if not quality:
        Log ("\tno quality given for video. HD quality used instead")
        quality="HD" #default max quality
    if not quality in ["HD","MD","LD"]:
        raise AllocineError,"<quality> MUST BE one of the followings : HD (or None), MD, LD"
    lq=["HD","MD","LD"]
    BA_path=""
    for q in lq[lq.index(quality):]:
        Log ("\ttrying %s quality"%q)
        if q=="HD":
            xml=get_page(ALLOCINE_DOMAIN + XML_BA_INFOS % mediaID + "&hd=1") #HD
        else:
            xml=get_page(ALLOCINE_DOMAIN + XML_BA_INFOS % mediaID) #LD et MD

        match = re.search(r'<video\s+title=".*?"\s+xt_title=".*?"\s+ld_path="(.*?)"\s+md_path="(.*?)"\s+hd_path="(.*?)".*?/>',xml)
        if match:
            if q=="LD" and match.group(1): BA_path = match.group(1)
            if q=="MD" and match.group(2): BA_path = match.group(2)
            if q=="HD" and match.group(3): BA_path = match.group(3)
            if BA_path:
                Log("\t%s quality successful for media"%q)
                break #si match non vide alors on quitte la boucle for
            else: Log ("\t%s quality not available !"%q)
        else:
            #raise AllocineError,"get_video_url did not match anything for the given mediaID. Make sure mediaID#%s on %s is valid."%(mediaID,ALLOCINE_DOMAIN)
            pass
    if not BA_path:
        raise AllocineError,"The media %s seems not contain videos from <%s> to worst quality(ies). Please try higher quality."%(mediaID,quality)
    else:
        return VIDEO_STREAM_URL % BA_path



class agenda:
    """
    gère la page des sorties pour une date donnée
    Sans période mentionnée, prend les sorties de la semaine
    """
    def __init__(self,periode=None):
        if not periode or periode == "now":
            self.HTML = get_page(ALLOCINE_DOMAIN + THIS_WEEK_URL)
        elif periode == "next":
            self.HTML = get_page(ALLOCINE_DOMAIN + AGENDA_URL)
        else:
            if re.match(r'\d\d/\d\d/\d\d\d\d',periode):
                self.HTML = get_page(ALLOCINE_DOMAIN + SORTIES_URL % periode)
            else:
                raise AllocineError,"<periode> parameter MUST be 'now' for the current week, 'next' for the next week, or a date 'DD/MM/YYYY' for the corresponding week"
        self.PERIODE = periode

    def __repr__(self):
        return "< AGENDA object for '%s' period >"%self.PERIODE

    def get_movies(self):
        """
        Retourne une liste de blocs HTML correspondant aux films
        """
        exp = re.compile(r'<a class="link1" href="(?:/film/)??fichefilm_gen_cfilm=\d+\.html">.*?(?:<hr />|</h5><br />)', re.DOTALL)
        movies = exp.findall(self.HTML)
        return movies

    def get_movies_datas(self):
        """
        Retourne une liste de tuples d'informations extraites des films
            (ID,Titre,TitreO,AfficheURL,Genre,Duree)
        """
        datas=[]
        for moviedatas in self.get_movies():
            # id, titre et titre original
            match = re.search(r'<h2><a class="link1" href="(?:/film/)??fichefilm_gen_cfilm=(\d+)\.html">(.*?)</a></h2>(?:&nbsp;<h4>(.*?)</h4>|)',moviedatas)
            if match:
                ID = match.group(1)
                Titre = match.group(2)
                TitreO = match.group(3)
            else:
                ID = Titre = TitreO = None
                
            #url de l'affiche
            match = re.search(r'<img src="(http://[./\w]+\.jpg)" border="0" alt=".+" class="affichette" />', moviedatas)
            if match:
                AfficheURL = match.group(1)
            else:
                AfficheURL = None
                
            #genre et durée
            match = re.search(r"<h5>(.*?)\((.*?)\)</h5>",moviedatas)
            if match:
                Genre = match.group(1)
                Duree = match.group(2)
            else:
                Genre = Duree = None
                
            #notes public
            match = re.search(r'<a href="(?:/film/)??critiquepublic_gen_cfilm=\d+\.html" class="link1">.*?</a> : <img src="[^"]+?empty\.gif" width="\d+" height="\d+" class="etoile_(\d{1})" border="0" />',moviedatas)
            if match:
                NotePublic = match.group(1)
            else:
                NotePublic = None
            #ajoute les données du film
            datas.append((ID,Titre,TitreO,AfficheURL,Genre,Duree,NotePublic))
            
        return datas

    def previous_week_date(self):
        """
        retourne une chaine représentant la période précédente à la période en cours
        """
        if not self.PERIODE or self.PERIODE == "now":
            #cette semaine, on retourne self.PERIODE car on ne revient pas en arrière
            #à voir si c'est vrai ou pas
            return self.PERIODE #renvoi None ou 'now'
        elif self.PERIODE == "next":
            #semaine prochaine : on retourne "now" pour prendre la semaine actuelle
            return "now"
        else:
            match = re.search(ur'<a href="/film/agenda_gen_date=([/\d]+?)\.html" class="link1">(?:Semaine préc\.|Previous week|Anterior|Zurück)</a>',self.HTML)
            #   aide sur l'expression régulière  :                                                      FR             EN         ES      DE
            if match:
                return match.group(1)
            else:
                raise AllocineError,"the 'previous week' match did not succeed. Regular expression may need changes !"
        
    def next_week_date(self):
        """
        retourne une chaine représentant la  période suivante à la période en cours
        """
        if not self.PERIODE or self.PERIODE == "now":
            #cette semaine, on retourne 'next' pour la semaine prochaine
            return 'next'
        else:
            #semaine prochaine OU tous les autres cas
            match = re.search(ur'<a href="/film/agenda_gen_date=([/\d]+?)\.html" class="link1">(?:Semaine (?:suiv\.|suivante)|Next week|Sigui?ente|Weiter)</a>',self.HTML)
            #   aide sur l'expression régulière                                                                   FR              EN       ES         DE
            if match:
                return match.group(1)
            else:
                raise AllocineError,"the 'next week' match did not succeed. Regular expression may need changes !"            

class Movies:
    """gère les instances de 'Movie(ID)'"""
    def __init__(self):
        self.Session = {}

    def new(self,IDmovie):
        if self.Session.has_key(IDmovie):
            return self.Session[IDmovie]
        else:
            f = Movie(IDmovie)
            self.Session[IDmovie]=f
            return f
            
class Movie:
    """
    procure toutes les méthodes nécessaires pour gérer un film selon son ID
    """
    def __init__(self,IDmovie):
        self.ID=IDmovie
        self.HTML = get_page(ALLOCINE_DOMAIN + MOVIE_URL%self.ID)
        print ALLOCINE_DOMAIN + MOVIE_URL%self.ID
        self.TITLE = ""
        self.DATE = ""
        self.DIRECTOR = tuple()
        self.NATIONALITY = ""
        self.INFOS = ""
        self.SYNOPSIS = ""
        self.HAS_VIDEOS = False
        self.HAS_CASTING = False
        self.PHOTOS = []
        self.HAS_PHOTOS = False
        self.CASTING = dict()
        self.PICurl = ""
        self.MEDIAS = []
        self.PARSEDflag = False

        #self.parser()
    
    def director(self):
        """
        """
        #  a internationnaliser !
        if not self.PARSEDflag:
            match = re.search(ur'<h4>Réalisé par <a class="link1" href="/personne/fichepersonne_gen_cpersonne=(\d+)\.html">(.*?)</a></h4>',self.HTML)
            if match: self.DIRECTOR = (match.group(1),match.group(2))# id,nom
            else: self.DIRECTOR = (None,None)
        return self.DIRECTOR

    def nationality(self):
        """
        """
        if not self.PARSEDflag:
            match = re.search(r'<h4>(?:Film|Nationality :|Land:|Película) (.*?)[\.]?&nbsp;</h4><h4>(?:Genre|Género)',self.HTML)
            if match: self.NATIONALITY = match.group(1)
            else: self.NATIONALITY = ""
        return self.NATIONALITY

    def infos(self):
        """
        """
        if not self.PARSEDflag:
            #la récupération suivante prend toutes les infos.
            #A voir si il faut filtrer les infos unitairement
            match = re.search(r'<div style=".*?"><h4>(Date de sortie :.*?)(?:<h5>|<div id=\'divRecos\' style=\'width:175px\'>)',self.HTML)
            if match: self.INFOS = infos_text(match.group(1))
            else: self.INFOS = "No infos found"
        return self.INFOS

    def title(self):
        """
        retourne le titre du film
        """
        if not self.PARSEDflag:
            match = re.search(r'<title>(.*?)</title>',self.HTML)
            if match: self.TITLE = match.group(1)
            else: self.TITLE = ""
        return self.TITLE

    def date(self):
        """
        retourne la date de sortie du film
        """
        if not self.PARSEDflag:
            match = re.search(r'<h4>[ \w]+? : <b>([\s\w\d].*?)</b>',self.HTML)
            if match: self.DATE = match.group(1)
            else: self.DATE = None        
        return self.DATE
    
    def synopsis(self):
        """
        retourne le résumé du film
        """
        if not self.PARSEDflag:
            match = re.search(ur'<td valign="top" style="padding:[\d ]+?"><div align="justify"><h4>(.*?)</h4>',self.HTML)
            if match: self.SYNOPSIS=infos_text(match.group(1))
            else: self.SYNOPSIS = ""
        return self.SYNOPSIS

    def has_videos(self):
        """
        """
        if not self.PARSEDflag:
            match = re.search(r'<a href="(/video/player_gen_cmedia=\d+&cfilm=\d+\.html)" class="link5">',self.HTML)
            if match:self.HAS_VIDEOS=match.group(1)
            else: self.HAS_VIDEOS=False
        return self.HAS_VIDEOS

    def has_casting(self):
        """
        """
        if not self.PARSEDflag:
            if self.HTML.count(CASTING_URL%self.ID): self.HAS_CASTING=True
            else: self.HAS_CASTING=False
        return self.HAS_CASTING
    
    def has_photos(self):
        """
        """
        if not self.PARSEDflag:
            if self.HTML.count(PHOTOS_FILM_URL%self.ID): self.HAS_PHOTOS=True
            else: self.HAS_PHOTOS=False
        return self.HAS_PHOTOS

    def pictureURL(self):
        """
        retourne l'url de l'image associée au film
        """
        if not self.PARSEDflag:
            match = re.search(r'<img src="(http://[a-z0-9/\.]+?\.jpg)" border="0" alt="" class="affichette" />',self.HTML)
            if match: self.PICurl=match.group(1)
            else: self.PICurl=None
        return self.PICurl

    def parser(self):
        """
        parse la page html du film et alimente les informations
        """
        match = re.search(r'<h4>[ \w]+? : <b>([\s\w\d].*?)</b>',self.HTML)
        if match: self.DATE = match.group(1)
        else: self.DATE = None
        
        match = re.search(ur'<h4>Réalisé par <a class="link1" href="/personne/fichepersonne_gen_cpersonne=(\d+)\.html">(.*?)</a></h4>',self.HTML)
        if match: self.DIRECTOR = (match.group(1),match.group(2))# id,nom
        else: self.DIRECTOR = (None,None)
        
        match = re.search(r'<h4>(?:Film|Nationality :|Land:|Película) (.*?)[\.]?&nbsp;</h4><h4>(?:Genre|Género)',self.HTML)
        if match: self.NATIONALITY = match.group(1)
        else: self.NATIONALITY = ""
        
        #la récupération suivante prend toutes les infos.
        #A voir si il faut filtrer les infos unitairement
        match = re.search(r'<div style=".*?"><h4>(Date de sortie :.*?)(?:<h5>|<div id=\'divRecos\' style=\'width:175px\'>)',self.HTML)
        if match: self.INFOS = infos_text(match.group(1))
        else: self.INFOS = "No infos found"
        
        match = re.search(r'<title>(.*?)</title>',self.HTML)
        if match: self.TITLE = match.group(1)
        else: self.TITLE = ""
        
        match = re.search(r'<h4>(?:Date de sortie |Theatrical release date |Fecha de estreno|Kinostart): <b>(\d+(?:\.)? \S+? \d{4}?)</b>',self.HTML)
        if match: self.DATE=match.group(1)
        else: self.DATE=""
        
        #l'expression suivante fonctionne dans regexbuddy mais pas dans python... pkoi ??
        match = re.search(ur'<td valign="top" style="padding:[\d ]+?"><div align="justify"><h4>(.*?)</h4>',self.HTML)
        if match: self.SYNOPSIS=infos_text(match.group(1))
        else: self.SYNOPSIS = ""
        
        #booleen qui permet de savoir si la fiche film propose des vidéos
        match = re.search(r'<a href="(/video/player_gen_cmedia=\d+&cfilm=\d+\.html)" class="link5">',self.HTML)
        if match:self.HAS_VIDEOS=match.group(1)
        else: self.HAS_VIDEOS=False
        
        if self.HTML.count(CASTING_URL%self.ID): self.HAS_CASTING=True
        else: self.HAS_CASTING=False
##        self.NOTES = tuple()
##        self.PICurl = ""

        #when all parsing are done, flag it as parsed
        self.PARSEDflag = True

    def get_photos(self):
        """
        Récupère la liste des photos
        [ ( picpath , title ) , ... ]
        """
        if not self.has_photos(): raise AllocineError,"No photos for the movie ID#%s"%self.ID
        if not self.PHOTOS:
            html=get_page(ALLOCINE_DOMAIN + PHOTOS_FILM_URL%self.ID)#,os.path.join(CACHEDIR,"galery%s.html"%self.ID))
            exp = re.compile(r'{"\w+?":\d+,"\w+":"([a-z0-9\d/]+\.jpg)","\w+":"(.*?)"}')
            # VIDEO_STREAM_URL + picpath
            self.PHOTOS = [(PHOTOS_MEDIA_URL+picpath,unescape(title.decode(ALLOCINE_ENCODING))) for picpath,title in exp.findall(html)]
        return self.PHOTOS

    def get_casting(self):
        """
        Récupère le casting si il n'a pas été récupéré, puis retourne le casting
        [ (fonction, metier, id, nom),(...) ...]
        """
        if not self.has_casting(): raise AllocineError,"No casting for the movie ID#%s"%self.ID
        else: #si le casting est vide
            html=get_page(ALLOCINE_DOMAIN + CASTING_URL%self.ID)#,os.path.join(CACHEDIR,"casting%s.html"%self.ID))
            match = re.search(ur"<h2.+?>Casting complet</h2>.*?<h3><b>Liens sponsorisés</b></h3>", html,re.DOTALL)#a faire fonctionner et à internationaliser
            if match:
                # match start: match.start()
                deb= match.start()
                fin= match.end()
                # match end (exclusive): match.end()
                # matched text: match.group()
            else:
                print "pas de match"
            casting = []
            exp = re.compile(ur'<h4.*?><b>(.*?)</b></h4><hr /></td></tr>(.*?)</tr>\s+</table>',re.DOTALL)
            fonctions = exp.findall(html[deb:fin])
            for fcttitre,fctdatas in fonctions:
                print fcttitre
                exp = re.compile(ur'tr.*?>\s+<td.*?>(?:<h5>)?(.*?)(?:</h5>)?</td>\s+<td.*?><h5>\s*<a href="/personne/fichepersonne_gen_cpersonne=(\d+).html" class="link1">(.*?)</a>\s+</h5></td>\s+</tr>')
                persos = exp.findall(fctdatas)
                print persos
                memmetier = "-"
                for metier,idp,nom in persos:
                    if not metier:
                        metier = memmetier
                    else:
                        memmetier = metier
                    print "\t%s (%s) [%s]"%(nom,metier,idp)
                    casting.append((fcttitre,metier,idp,nom))
                    
                    
                

    def get_mediaIDs(self):
        """
        Récupère les vidéos disponibles
            [ ( IDmedia , picurl, title ) , ... ]
        """
        if not self.has_videos(): raise AllocineError,"No available media Video for the movie ID#%s"%self.ID #retourne si pas de videos pour le film
        if not (self.MEDIAS):
            self.MEDIAS=[]
            #1- on récupère les datas javascripts contenant toutes les vidéos
            exp=re.compile(r"contenu = new Array\('(.+)'\)|contenu.push\('(.+)'\)")
            datas=exp.findall(self.HTML)
            #2- on récupre toutes les vidéos sous forme [(idmedia,urlimage,titre), ... ]
            exp=re.compile(r'<a href="/video/player_gen_cmedia=(\d+)&cfilm=\d+\.html"><img src="(http://[\.\w/-_]+)" width="100" height="80" border="0" alt="(.*?)"></a>')
            for datamedia in datas:
                match = exp.search("".join(datamedia))
                if match:self.MEDIAS.append((match.group(1),match.group(2),unescape(match.group(3).decode(ALLOCINE_ENCODING))))
                else: Log("No match for these media datas","W")
        return self.MEDIAS


    def BAurl(self):
        """
        Return the first mediaID video url found for the current movie
        """
        if self.has_videos():
            if not self.MEDIAS:
                self.get_mediaIDs()
                IDmedia,title=self.get_mediaIDs()[0]
                
            else:
                IDmedia,title=self.MEDIAS[0]
            return get_video_url(IDmedia)
        else:
            raise AllocineError,"No available media Video for the movie ID#%s"%self.ID

    def XML(self,filename=None):
        # non prioritaire !!
        """
        Génère un XML des données du film
            Si filename est fourni, correspond au chemin vers le fichier dans lequel le XML sera écrit
            Sinon, retourne un xml sous forme de chaine
        """
        xmldatas = """<xml>blabla</xml>"""
        if filename:
            try:
                open(filename,"w").write(xmldatas)
            except IOError, err:
                raise " Exception from allocine.py : %s"%err
                
        else:
            return xmldatas
        
    def __repr__(self):
        return "< Allocine movie object ID#%s >"%self.ID

class SearchOLD:
    def __init__(self):#,keyword,searchtype="0"):
        #/recherche/?motcle=""&rub=
        #   0 - tout allocine
        #   1 - les films
        #   2 - les stars
        #   3 - les salles
        #   4 - les localités
        #   5 - les articles
        #   6 - les séries TV
        #   8 - les sociétés
        #   10- les tags
        #   13- les blogs

##        #basic checkings
##        from types import StringType
##        if not (type(searchtype) is StringType): raise AllocineError, "Type for <searchtype> argument MUST be string. (searchtype argument is now %s)"%type(searchtype)
##        if not (type(keyword) is StringType): raise AllocineError, "Type for <keyword> argument MUST be string. (keyword argument is now %s)"%type(keyword)

        self.HAS_NEXT = False #booleen pour savoir si la recherche contient une page de résultat suivante
        self.KW = ""#keyword
        self.TYPE = "0"#searchtype
        self.RESULTS_PER_PAGE = [] #the results on only one page
        self.RESULTS_ALL = [] #all differents results found for this search
        self.REGEXP = { "1" : r'<a href="/film/fichefilm_gen_cfilm=(\d+)\.html"><img src="(http:[a-z0-9/\.-]+?)"[^/]*?/>.*?</a></td><td valign="top"><h4><a href="/film/fichefilm_gen_cfilm=\1\.html" class="link1">(.*?)</a></h4>',
                        "2" : r'<a href="/personne/fichepersonne_gen_cpersonne=(\d+)\.html"><img src="(http:[a-z0-9/\.-]+?)"[^/]*?/>.*?</a></td><td valign="top"><h4><a href="/personne/fichepersonne_gen_cpersonne=\1\.html" class="link1">(.*?)</a>', #REGEXP est utilisé également pour connaitre les recherches supportées
                        "3" : r'<a href="/seance/salle_gen_csalle=([A-Za-z0-9]+)\.html" class="link1">(.*?)<hr />',
                        'etc':'etc'
                        }
        #getting allocine search themes
        self.SEARCH_THEMES = self.get_Themes()
        print "\n".join(["%s : %s"%(tid,self.SEARCH_THEMES[tid]) for tid in self.SEARCH_THEMES.keys()])
        ##advanced checkings
        #if not searchtype in self.SEARCH_THEMES.keys(): raise AllocineError,"If given, <searchtype> argument MUST be one of the followings : "+self.SEARCH_THEMES.keys()

        #if not searchtype in self.REGEXP.keys(): raise AllocineError,"Sorry, '%s' search is currently not supported. Supported search(s) is(are) %s."%(self.SEARCH_THEMES[searchtype],
        #                                                                                                                                          ",".join(self.SEARCH_THEMES.values())
        #                                                                                                                                          )
        #routage
        #if searchtype in self.REGEXP.keys():
        #    self.search(keyword,searchtype)
            
    def supported(self):
        """
        retourne un dictionnaire des recherches disponibles sur le site et supportées par la librairie
        """
        return dict( [ (thid,self.SEARCH_THEMES[thid]) for thid in set(self.REGEXP.keys()).intersection(self.SEARCH_THEMES.keys())])    
        
    def get_type(self):
        """
        Return the associated name of the type of search
        """
        return self.SEARCH_THEMES[self.TYPE]
            
    def get_Themes(self):
        """
        Return a dictionnary with themesID as int and themes name as string
        """
        html=get_page(ALLOCINE_DOMAIN + SEARCH_URL)
        exp=re.compile(r'<option value="(\d+)" (?:selected="selected" )?/>([^<\t]*)')
        types = exp.findall(html)
        return dict([(tid,unescape(tname.decode(ALLOCINE_ENCODING))) for tid,tname in types])

                        
    def search(self,keyword="",Type="0",next=None):
        """
        Search in <Type> for <keyword> results
        Return a list with (id,text,title)
            -id for the id of the searched item
            -text for something interesting (i.e: picture url)
            -title for the label to give to the found items
        """
        keyword=keyword.encode(ALLOCINE_ENCODING)
        if next and self.HAS_NEXT: page="&page="+next
        else: page =""
        #on va remplir une liste de résultats
        html = get_page(ALLOCINE_DOMAIN + SEARCH_URL + "?motcle=%s&rub=%s"%(keyword,Type) + page)
        #parser html selon le theme
        exp=re.compile(self.REGEXP[Type]) #ATTENTION, le parser doit retourner l'ID de l'élément considéré ainsi que son libellé
        results = exp.findall(html)
        results = [ (id,text,infos_text(title).replace("\n","")) for id,text,title in results ]
        #rechercher
        if results: # en cas de résultats ...
            self.HTML = html #... on mémorise le code HTML
            self.KW = keyword #... on mémorie le mot clé
            self.TYPE = Type #... on mémorise le type de recherche
            self.HAS_NEXT = self.has_next() #... on cherche si éventuellement la page contient d'autres résultats et on mémorise
            self.RESULTS_ALL= self.RESULTS_ALL + results #... on ajoute les résultats à tous les autres résultats précédents
            self.RESULTS_PAGE = results#... on mémorise les derniers résultats trouvés
            return results
        else:
            raise AllocineError, "Search in '%s' (%s) for '%s' did not match anything."%(self.SEARCH_THEMES[Type],Type,keyword)
        
    def has_next(self):
        """
        Return wether or not, the search results contain a 'next page' link
        Return False if no other page or page number if next page
        """
        match=re.search(ur'<a href="/recherche/default\.html\?motcle=.*?&rub=\d*?&page=(\d*)" class="link1">.*?</a>',self.HTML)
        if match: self.HAS_NEXT = match.group(1)
        else: self.HAS_NEXT = None
        return self.HAS_NEXT
        #A FAIRE
        
        
    def next_results(self):
        """
        Récupère la prochaine page de résultats
        """
        if self.has_next(): return self.search(self.KW,self.TYPE,self.HAS_NEXT)

    def __repr__(self):
        return "< Allocine Search instance [keyword=%s , Theme_searched=%s]>"%(self.KW,self.TYPE)


class Search:
    def __init__(self,keyword="",searchtype="0"):
##        #basic checkings
##        from types import StringType
##        if not (type(searchtype) is StringType): raise AllocineError, "Type for <searchtype> argument MUST be string. (searchtype argument is now %s)"%type(searchtype)
##        if not (type(keyword) is StringType): raise AllocineError, "Type for <keyword> argument MUST be string. (keyword argument is now %s)"%type(keyword)

        self.KW = keyword.encode(ALLOCINE_ENCODING)
        self.TYPE = searchtype
        self.HAS_NEXT = False #booleen pour savoir si la recherche contient une page de résultat suivante
        self.RESULTS_PER_PAGE = [] #the results on only one page
        self.RESULTS_ALL = [] #all differents results found for this search
        self.HTML = ""
        self.SEARCH_THEMES = self.get_Themes()
        
        if not self.TYPE in self.SEARCH_THEMES.keys():
            raise AllocineError,"The search ID you asked for is not available for this website. Available web site searchs are %s"%", ".join(self.SEARCH_THEMES.keys())
        AvailableRegexp = { "1" : r'<a href="/film/fichefilm_gen_cfilm=(\d+)\.html"><img src="(http:[a-z0-9/\.-]+?)"[^/]*?/>.*?</a></td><td valign="top"><h4><a href="/film/fichefilm_gen_cfilm=\1\.html" class="link1">(.*?)</a></h4>',
                            "2" : r'<a href="/personne/fichepersonne_gen_cpersonne=(\d+)\.html"><img src="(http:[a-z0-9/\.-]+?)"[^/]*?/>.*?</a></td><td valign="top"><h4><a href="/personne/fichepersonne_gen_cpersonne=\1\.html" class="link1">(.*?)</a>', #REGEXP est utilisé également pour connaitre les recherches supportées
                            "3" : r'<a href="/seance/salle_gen_csalle=([A-Za-z0-9]+)\.html" class="link1"([^>]*)>(.*?)<hr />'
                            }
        try:
            self.REGEXP = AvailableRegexp[self.TYPE]
        except:
            raise AllocineError,u"Type of search #%s is not supported. Should be in %s"%(self.TYPE,AvailableRegexp.keys())
        #getting allocine search themes
        #self.SEARCH_THEMES = self.get_Themes()

    def start(self,nextpage=None):
        "Commence la recherche première page de résultats"
        if nextpage: page="&page="+nextpage
        else: page =""
        html = get_page(ALLOCINE_DOMAIN + SEARCH_URL + "?motcle=%s&rub=%s"%(self.KW,self.TYPE) + page )
##        html = get_page(ALLOCINE_DOMAIN + SEARCH_URL,
##                        params={"motcle":self.KW,
##                                "rub":self.TYPE,
##                                "page":page})
        #parser html selon le theme
        exp=re.compile(self.REGEXP)
        results = exp.findall(html)
        results = [ (id,text,infos_text(title).replace("\n","")) for id,text,title in results ]
        if results: # en cas de résultats ...
            self.HTML = html
            self.HAS_NEXT = self.has_next() #... on cherche si éventuellement la page contient d'autres résultats et on mémorise le numéro de page
            self.RESULTS_ALL= self.RESULTS_ALL + results #... on ajoute les résultats à tous les autres résultats précédents
            self.RESULTS_PAGE = results#... on mémorise les derniers résultats trouvés
            return results
        else:
            raise AllocineError, "Search in '%s' (%s) for '%s' did not match anything."%(self.SEARCH_THEMES[Type],Type,keyword)        

    def get_Themes(self):
        """
        Return a dictionnary with themesID as int and themes name as string
        These are those available for search on website
        """
        html=get_page(ALLOCINE_DOMAIN + SEARCH_URL)
        exp=re.compile(r'<option value="(\d+)" (?:selected="selected" )?/>([^<\t]*)')
        types = exp.findall(html)
        return dict([(tid,unescape(tname.decode(ALLOCINE_ENCODING))) for tid,tname in types])
    
    def next(self):
        "Continue la recherche sur la page suivante"
        if self.HAS_NEXT: return self.start(self.HAS_NEXT)
        else: raise AllocineError, u"Search do not have more page results"

    def previous(self):
        "Recupère la page précédente de résultats"
        #A FAIRE
        pass
    
    def has_next(self):
        """
        Return wether or not, the search results contain a 'next page' link
        Return False if no other page or page number if next page
        """
        match=re.search(ur'<a href="/recherche/default\.html\?motcle=.*?&rub=\d*?&page=(\d*)" class="link1">.*?</a>',self.HTML)
        if match: return match.group(1)
        else: return False

class Movie_search(Search):#inutilisé, pour tests et conservé pour mémoire
    def __init__(self,kw):
        Search.__init__(self,kw,"1")
        self.REGEXP = r'<a href="/film/fichefilm_gen_cfilm=(\d+)\.html"><img src="(http:[a-z0-9/\.-]+?)"[^/]*?/>.*?</a></td><td valign="top"><h4><a href="/film/fichefilm_gen_cfilm=\1\.html" class="link1">(.*?)</a></h4>'

        
class Personality:
    """
    gère les informations d'une personnalité selon son ID
    """
    def __init__(self,IDperso):
        self.ID = IDperso
        self.HTML = get_page(ALLOCINE_DOMAIN + PERSO_URL%self.ID)
        self.NAME = ""
        self.JOBS = ""
        self.BIRTH =""
        self.PICurl = ""
        self.BIO = ""
        self.HAS_PHOTO = None
        self.PHOTOS = []
        self.HAS_VIDEOS = None
        self.MEDIAS = None
        self.parser()

    def name(self):
        """
        retourne le nom de la personnalité
        """
        if not self.NAME:
            match=re.search(r'<title>(.*?)</title>',self.HTML)
            if match: self.NAME=match.group(1)
            else: self.NAME="Not found"
        return self.NAME

    def jobs(self):
        """return cinema functions (jobs)"""
        if not self.JOBS:
            match=re.search(r'<div><h4><b>(.*?)</b></h4></div>',self.HTML)
            if match: self.JOBS = match.group(1)
            else: self.JOBS = "Not found !"
        return self.JOBS

    def birth(self):
        """return birth infos"""
        if not self.BIRTH:
            match = re.search(r'<h4><div[^>]+>(.*?)</h4></div>',self.HTML)
            if match: self.BIRTH = match.group(1)
            else: self.BIRTH = "Not found !"
        return self.BIRTH

    def Biography(self,force=False):
        """
        Return biography - Right now only FR, EN and ES country (not DE)
        Set <force> to True to force parsing datas if needed"""
        if not (self.BIO) or force:
            match=re.search(ur'<h3><b>(?:Biographie|Biography|Biografie|Biografía)</b></h3>(.*?)</table>',self.HTML)
            #  match for countries :       FR           EN       DE         ES
            if match: datas = match.group(1)
            else: return ["No Biography available",[],[]]
            bio = infos_text(datas)
            exp=re.compile(r'<a class="link1" href="/personne/fichepersonne_gen_cpersonne=(\d+)\.html">(.*?)</a>')
            persos = exp.findall(datas)
            exp=re.compile(r'<a class="link1" href="/film/fichefilm_gen_cfilm=(\d+)\.html"><b>(.*?)</b></a>')
            movies = exp.findall(datas)
            self.BIO = [bio,movies,persos]
        return self.BIO

    def Filmography(self,force=False):
        """
        return filmography
        """
        ## NON FONCTIONNEL... A refaire plus complet ultérieurement
        #il faut télécharger la page de filmographie
        if not(self.FILMO) or force:
            match=re.search(r'<table cellpadding="0" cellspacing="0" border="0" width="100%">.*?</table>\r',self.HTML)
            if match:#il faut parser le resultat
                exp=re.compile(r'<h4><a href="/film/fichefilm_gen_cfilm=(?P<idfilm>\d+)\.html" class="link1"><b>(?P<title>[^<]+?)</b></a>(?: \((?P<year>[\w ]+)\))*(?:, [.\w]+ <a class="link1" href="/personne/fichepersonne_gen_cpersonne=(?P<idperson>\d+).html">(.*?)</a>)*</h4>')
                self.FILMO=exp.findall(match.group())
                return self.FILMO
            else:
                pass
                        
    def has_photos(self):
        """
        """
        if self.HTML.count(PHOTOS_PERSON_URL%self.ID): self.HAS_PHOTOS=True
        else: self.HAS_PHOTOS=False
        return self.HAS_PHOTOS
    
    def get_photos(self,force=False):
        """return photos related to the personnality
        return [ ( picpath , title ) , ... ]"""
        if not self.has_photos(): raise AllocineError,"No photos for the personnality ID#%s"%self.ID
        if not (self.PHOTOS) or force:
            html=get_page(ALLOCINE_DOMAIN + PHOTOS_PERSON_URL%self.ID)
            exp = re.compile(r'{"\w+?":\d+,"\w+":"([a-z0-9\d/]+\.jpg)","\w+":"(.*?)"}')
            # VIDEO_STREAM_URL + picpath
            self.PHOTOS = [(PHOTOS_MEDIA_URL+picpath,unescape(title.decode(ALLOCINE_ENCODING))) for picpath,title in exp.findall(html)]
        return self.PHOTOS

    def has_videos(self):
        """
        """
        
        match = re.search(r'<a href="(/video/player_gen_cmedia=\d+&cpersonne=\d+\.html)" class="link5">',self.HTML)
        if match:self.HAS_VIDEOS=match.group(1)
        else: self.HAS_VIDEOS=False
        return self.HAS_VIDEOS
    
    def get_mediaIDs(self,force=False):
        """
        Récupère les vidéos disponibles
            [ ( IDmedia , urlimage, title ) , ... ]
        """
        if not self.has_videos(): raise AllocineError,"No available media Video for the personnality ID#%s"%self.ID #retourne si pas de videos pour le film
        if not (self.MEDIAS) or force:
            self.MEDIAS=[]
            #1- on récupère les datas javascripts contenant toutes les vidéos
            exp=re.compile(r"contenu = new Array\('(.+)'\)|contenu.push\('(.+)'\)")
            datas=exp.findall(self.HTML)
            #2- on récupre toutes les vidéos sous forme [(idmedia,urlimage,titre), ... ]
            exp=re.compile(r'<a href="/video/player_gen_cmedia=(\d+)&cpersonne=\d+\.html"><img src="(http://[\.\w/-_]+)" width="100" height="80" border="0" alt="(.*?)"></a>')
            for datamedia in datas:
                match = exp.search("".join(datamedia))
                if match:self.MEDIAS.append((match.group(1),match.group(2),unescape(match.group(3).decode(ALLOCINE_ENCODING))))
                else: Log("No match for these media datas","W")
        return self.MEDIAS

    
    def pictureURL(self):
        """
        retourne l'image associée à la personnalité
        """
        if not self.PICurl:
            match=re.search(r'<img src="(http://[\w\./_-]+)" width="\d+" height="\d+" border="0"><br />',self.HTML)
            if match: self.PICurl = match.group(1)
            else: self.PICurl = None
        return self.PICurl

    def parser(self):
        """
        parse la page html de la personnalité et alimente les informations
        """
        self.nom = ""
        self.PICurl = ""

    def __repr__(self):
        return "< Allocine character object ID#%s >"%self.ID


#initialisation des domaines pour l'internationalisation
set_country("FR")

if __name__ == "__main__":
    print "This script is intended to be used as a library."
    print len(get_page("http://a69.g.akamai.net/n/69/10688/v1/img5.allocine.fr/acmedia/rsz/434/x/x/x/medias/nmedia/18/67/67/24/18992446.jpg"))
    
    


             
