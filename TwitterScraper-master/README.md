# TwitterScraper
This Python script will extract tweets, and data about them, by web scraping pages of Twitter search results. This is a fork, with some stuff edited and added, of the Python version of Tom Dickinson's original Java implementation https://github.com/tomkdickinson/TwitterSearchAPI.

Running TwitterScraper:
- Download TwitterScraper.py and open Terminal in its directory
- ```$ python TwitterScraper.py```
- Follow the on-screen instructions

Required Libraries:
* bs4
* lxml

## TwitterSucker
Running ```$ python TwitterSucker.py``` will do the same thing as TwitterScraper, but will divide the search procedure into date-by-date queries.

## TwitterSlicer
Running ```$ python TwitterSlicer.py``` will divide the search procedure into date-by-date queries and return a dataset consisting of slices (a set number
of tweets per day in your search interval).

