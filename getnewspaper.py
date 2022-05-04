import re # Регулярные выражения.
import requests # Загрузка новостей с сайта.
from bs4 import BeautifulSoup # Превращалка html в текст.
import pymorphy2 # Морфологический анализатор.
import datetime # Новости будем перебирать по дате.
from collections import Counter # Не считать же частоты самим.
import math # Корень квадратный.

class getNewsPaper:
        
    # Конструктор - вызывается при создании объекта и инициализирует его.
    def __init__(self):
        self.articles=[]     # Загруженные статьи.
        self.titles=[]       # Заголовки статей.
        self.dictionaries=[] # Словари для каждой из статей.
        # Создаем и загружаем морфологический словарь.
        self.morph=pymorphy2.MorphAnalyzer()

    # Загрузка статьи по URL.
    def getLentaArticle(self, url):
        """ getLentaArticle gets the body of an article from Lenta.ru"""
        # Получает текст страницы.
        resp=requests.get(url)
        # Загружаем текст в объект типа BeautifulSoup.
        bs=BeautifulSoup(resp.text, "html5lib") 
        # Получаем заголовок статьи.
        self.titles.append(bs.h1.text.replace("\xa0", " "))
        # Получаем текст статьи.
        self.articles.append(BeautifulSoup(" ".join([p.text for p in bs.find_all("p")]), "html5lib").get_text().replace("\xa0", " "))

    # Загрузка всех статей за один день.
    def getLentaDay(self, url):
        """ Gets all URLs for a given day and gets all texts. """
        try:
            # Грузим страницу со списком всех статей.
            day = requests.get(url) 
            # Получаем фрагменты с нужными нам адресами статей.
            h3s=BeautifulSoup(day.text, "html5lib").find_all("h3")
            # Получаем все адреса на статьи за день.
            links=["http://lenta.ru"+l.find_all("a")[0]["href"] for l in h3s]
            # Загружаем статьи.
            for l in links:
                self.getLentaArticle(l)
        except:
            pass

    # Загрузка всех статей за несколько дней.
    def getLentaPeriod(self, start, finish):
        curdate=start
        while curdate<=finish:
            print(curdate.strftime('%Y/%m/%d')) # Just in case.
            # Список статей грузится с вот такого адреса.
            self.getLentaDay('https://lenta.ru/news/'+curdate.strftime('%Y/%m/%d'))
            curdate+=datetime.timedelta(days=1)

    # Построение вектора для статьи.
    posConv={'ADJF':'_ADJ','NOUN':'_NOUN','VERB':'_VERB'}
    def getArticleDictionary(self, text, needPos=None):
        words=[a[0] for a in re.findall("([А-ЯЁа-яё]+(-[А-ЯЁа-яё]+)*)", text)]
        reswords=[]
    
        for w in words:
            wordform=self.morph.parse(w)[0]
            try:
                if wordform.tag.POS in ['ADJF', 'NOUN', 'VERB']:
                    if needPos!=None:
                        reswords.append(wordform.normal_form+self.posConv[wordform.tag.POS])
                    else:
                        reswords.append(wordform.normal_form)
            except:
                pass
            
        stat=Counter(reswords)
        # Берем только слова с частотой больше 1.
        stat={a: stat[a] for a in stat.keys() if stat[a]>1}
        return stat

    # Посчитаем вектора для всех статей.
    def calcArticleDictionaries(self, needPos=None):
        self.dictionaries=[]
        for a in self.articles:
            self.dictionaries.append(self.getArticleDictionary(a, needPos))
            
    # Сохраняем статьи в файл.
    def saveArticles(self, filename):
        """ Saves all articles to a file with a filename. """
        newsfile=open(filename, "w")
        for art, titl in zip(self.articles, self.titles):
            newsfile.write('\n=====\n'+titl)
            newsfile.write('\n-----\n'+art)
        newsfile.close()

    # Читаем статьи из файла.
    def loadArticles(self, filename):
        """ Loads and replaces all articles from a file with a filename. """
        newsfile=open(filename, encoding="utf-8")
        text=newsfile.read()
        self.articles=text.split('\n=====\n')[1:]
        for i, a in enumerate(self.articles):
            b, self.articles[i] = a.split('\n-----\n')
            self.titles.append(b)
        newsfile.close()

    # Для удобства - поиск статьи по ее заголовку.
    def findNewsByTitle(self, title):
        if title in self.titles:
            return self.titles.index(title)
        else:
            return -1

def cosineSimilarity(a, b):
    if len(a.keys())==0 or len(b.keys())==0:
        return 0
    sumab=sum([a[na]*b[na] for na in a.keys() if na in b.keys()])
    suma2=sum([a[na]*a[na] for na in a.keys()])
    sumb2=sum([b[nb]*b[nb] for nb in b.keys()])
    return sumab/math.sqrt(suma2*sumb2)

