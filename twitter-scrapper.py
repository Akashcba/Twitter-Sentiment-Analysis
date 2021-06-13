## Twitter scrapper using taspinar/TwitterScraper

import twint
import nest_asyncio
nest_asyncio.apply()

import datetime as dt
import pandas as pd
import os
import sys

#q = str(os.environ.get("COMPANY"))
#q = "JP Morgan"#input("> Enter the name of the company : ")

q = str(sys.argv[-1])
df = pd.DataFrame(columns=['id','conversation_id','created_at','date','time','timezone','user_id','username','name','place','tweet','language','mentions','urls','photos','replies_count','retweets_count','likes_count','hashtags','cashtags','link','retweet','quote_url','video','thumbnail','near','geo','source','user_rt_id','user_rt','retweet_id','reply_to','retweet_date','translate','trans_src','trans_dest'])

current_date = dt.date(2020, 5,13) ## yyyy, mm, dd
current_end_date = current_date + dt.timedelta(days=1)
end_date = dt.date(2020, 6, 11)
while (current_date != end_date):
    c = twint.Config()
    c.Search = q
    c.Limit = 100
    c.Lang = 'en'
    c.Store_csv = True
    c.Output = f'{q}.csv'
    c.Since = current_date.strftime("%Y-%m-%d")
    c.Until = current_end_date.strftime("%Y-%m-%d")
    twint.run.Search(c)
    current_date = current_end_date
    current_end_date += dt.timedelta(days=1)
    #print(current_date != end_date)
    temp = pd.read_csv(f'{q}.csv')
    print("################")
    print(temp.shape)
    #print(temp.columns)
    df = df.append(temp, ignore_index = True)
    print("###############################")
    print(df.shape)

### Storing to csv
df.to_csv(f"{q}.csv")
print("Finished ...")
