#!pip install vaderSentiment
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import sys

q = str(sys.argv[-1])

data = pd.read_csv(f'{q}.csv', lineterminator='\n')

##### vader lexicon
import nltk
nltk.download('vader_lexicon')


sid = SentimentIntensityAnalyzer()

listy = []

for index, row in data.iterrows():
  ss = sid.polarity_scores(row.values[11])   ## Set it
  sa = ss['compound']
  listy.append(sa)

se = pd.Series(listy)
data['polarity'] = se.values

#setting index as date
data['date'] = pd.to_datetime(data['date'],format='%Y-%m-%d %H:%M:%S')
data.index = data['date']

### Calculation of Nature
neg = 0
pos = 0
neu = 0
sum1 = 0.0
sum2 = 0
sum3 = 0
for index, row in data.iterrows():
    sum3+= row['polarity']
    if row['polarity']>0 :
     pos+=1
    elif row['polarity']<0 :
     neg+=1
    else :
     neu+=1

sum1 = (pos - neg)/ (pos + neg)
sum2 = pos - neg

print("\nCompany: ",q)
print("Positive : ",pos)
print("Negative : ", neg)
print("Neutral : ", neu)
print("(Pos-Neg)/(Pos+Neg)",sum1)
print("Pos-Neg",sum2)
print("Polarity_Sum : ",sum3)


if sum1 < 0 :
 print('bear')
else :
 print('bull')
print("\n")