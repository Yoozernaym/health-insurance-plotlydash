import requests as req
import sqlite3 as sql
import pandas as pd

#Get State Codes
statecodes = req.get('https://api.census.gov/data/timeseries/healthins/sahie?get=NAME&for=state:*&time=2019')
cols = ['Name','year','Statecode']
statecodesdf = pd.DataFrame(statecodes.json()[1:], columns=cols)
statecodesdf = statecodesdf[['Name','Statecode']]

#Create statecodes Table
sql_cols = []
for col in statecodesdf.columns:
    sql_cols.append(f'{col} text')
sql_cols_str = ','.join(sql_cols)
create_table_str = f'CREATE TABLE IF NOT EXISTS statecodes ({sql_cols_str})'
con = sql.connect('censusdata.db')
cur = con.cursor()
cur.execute('DROP TABLE IF EXISTS statecodes')
cur.execute(create_table_str)
statecodesdf.to_sql('statecodes', con, if_exists = 'replace', index = False)


#Get State Data
cols = ['Race', 'Sex', 'IPR', 'Percent Uninsured', 'Year', 'State']
statedata = req.get('https://api.census.gov/data/timeseries/healthins/sahie?get=RACECAT,SEXCAT,IPRCAT,PCTUI_PT,YEAR&for=state:*')
statedatadf = pd.DataFrame(statedata.json()[1:], columns=cols)

#Replace Codes with descriptions
racecodes = {'0': 'All Races', '1': 'White', '2': 'Black', '3': 'Hispanic'}
sexcodes = {'0': 'Both', '1': 'Male', '2': 'Female'}
iprcodes = {'0': 'All Incomes', '1': 'At or Below 200% of Poverty', '2': 'At or Below 250% of Poverty', '3': 'At or Below 138% of Poverty', '4': 'At or Below 400% of Poverty', '5': 'Between 138% - 400% of Poverty'}
democodes = [['Race', racecodes], ['Sex', sexcodes], ['IPR', iprcodes]]
for code in democodes:
            for k, v in code[1].items():
                statedatadf.loc[statedatadf[code[0]] == k, code[0]] = v
#Create statedata Table
sql_cols = []
for col in statedatadf.columns:
    if col == 'Year':
        sql_cols.append(f'{col} integer')
    elif col == 'Percent Uninsured':
        sql_cols.append(f'{col} real')
    else:
        sql_cols.append(f'{col} text')
sql_cols_str = ','.join(sql_cols)
create_table_str = f'CREATE TABLE IF NOT EXISTS statedata ({sql_cols_str})'
cur.execute('DROP TABLE IF EXISTS statedata')
cur.execute(create_table_str)
statedatadf.to_sql('statedata', con, if_exists = 'replace', index = False)


#Get County Data
cols = ["Percent Uninsured","County","Year","statecode","countycode"]
countydata = req.get('https://api.census.gov/data/timeseries/healthins/sahie?get=PCTUI_PT,NAME,YEAR&for=county:*&in=state:*')
countydatadf = pd.DataFrame(countydata.json()[1:], columns=cols)

#Create countydata Table
sql_cols = []
for col in countydatadf.columns:
    if col == 'Percent Uninsured':
        sql_cols.append(f'{col} real')
    elif col == 'Year':
        sql_cols.append(f'{col} integer')
    else:
        sql_cols.append(f'{col} text')
create_table_str = f'CREATE TABLE IF NOT EXISTS countydata ({sql_cols_str})'
cur.execute('DROP TABLE IF EXISTS countydata')
cur.execute(create_table_str)
countydatadf.to_sql('countydata', con, if_exists = 'replace', index = False)


#Get Time Data
cols = ["Percent Uninsured","State","Year","Statecode"]
timedata = req.get('https://api.census.gov/data/timeseries/healthins/sahie?get=PCTUI_PT,NAME,YEAR&for=state:*')
timedatadf = pd.DataFrame(timedata.json()[1:], columns=cols)

#Create timedata Table
sql_cols = []
for col in timedatadf.columns:
    if col == 'Percent Uninsured':
        sql_cols.append(f'{col} real')
    elif col == 'Year':
        sql_cols.append(f'{col} integer')
    else:
        sql_cols.append(f'{col} text')
create_table_str = f'CREATE TABLE IF NOT EXISTS timedata ({sql_cols_str})'
cur.execute('DROP TABLE IF EXISTS timedata')
cur.execute(create_table_str)
timedatadf.to_sql('timedata', con, if_exists = 'replace', index = False)


con.close()
