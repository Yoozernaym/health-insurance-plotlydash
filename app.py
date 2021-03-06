#HAP 618 Project

from dash import Dash, dash_table
from dash.html import H1,H2,H3,Div,P,Label,Button,Br,Main,Footer,A,Img 
from dash.dcc import Location,Store,Dropdown,Tabs,Tab,Loading,Link,Graph
from dash.dependencies import Output, Input
from dash.exceptions import PreventUpdate
import plotly.express as px
import pandas as pd
import sqlite3 as sql

app = Dash(__name__,meta_tags=[
    {
        'charset':'UTF-8'
    },
    {
        'name':'description',
        'content':'U.S. Census health insurance statistics visualization using Plotly Dash'
    },
    {
        'name': 'viewport',
        'content': 'width=device-width, initial-scale=1.0'
    }],
    index_string = '''
        <!DOCTYPE html>
        <html lang="en">
            <head>
                {%metas%}
                <title>{%title%}</title>
                {%favicon%}
                {%css%}
            </head>
            <body>
                {%app_entry%}
                <footer>
                    {%config%}
                    {%scripts%}
                    {%renderer%}
                </footer>
            </body>
        </html>
'''
    )


server = app.server

con = sql.connect('censusdata.db')
cur = con.cursor()
statecodesql = cur.execute('SELECT * FROM statecodes')
cols = [col[0] for col in statecodesql.description]
statecodes = pd.DataFrame(statecodesql, columns=cols)
con.close()

racecodes = {'0': 'All Races', '1': 'White', '2': 'Black', '3': 'Hispanic'}
sexcodes = {'0': 'Both', '1': 'Male', '2': 'Female'}
iprcodes = {'0': 'All Incomes', '1': '<= 200% of Poverty', '2': '<= 250% of Poverty', '3': '<= 138% of Poverty', '4': '<= 400% of Poverty', '5': '138% - 400% of Poverty'}
democodes = [['Race', racecodes], ['Sex', sexcodes], ['IPR', iprcodes]]

app.layout = Div([
    Location(id='url', refresh=False),
    Store(id='store',data='main page'),
    Store(id='statestore'),
    Store(id='countystore'),
    Store(id='timestore'),
    H1('Small Area Health Insurance Estimates from U.S. Census Bureau'),
    Div([
        Label([
            P('Select Year: '), 
            Dropdown(
            options=[i for i in range(2006, 2020)],
            id='yeardropdown'
            )
        ]),
        Label([
            P('Select State: '), 
            Dropdown(
            options=[{'label': statecodes.iloc[i,0],'value': statecodes.iloc[i,1]} for i in range(len(statecodes))],
            id='statedropdown'
            )
        ]),
        Button(Link('Submit', href='', id='submit'))
    ], id='dropdowndiv'),
    Br(),
    Main([
        Tabs([
            Tab(label='County', value='countytab', id='countytab'),
            Tab(label='Race and IPR', value='demotab', id='demotab'),
            Tab(label='Over Time', value='timetab', id='timetab'),
        ], id='statetabs', value='countytab'),
        Loading(id='graph'),
        Br(),
        H3('State Data Table'),
        Div([
            Div([    
                Dropdown(
                    options=[{'label': racecodes[v], 'value': racecodes[v]} for v in racecodes],
                    id='racedropdown', placeholder='Race', multi=True
                ),
                Dropdown(
                    options=[{'label': sexcodes[v], 'value': sexcodes[v]} for v in sexcodes],
                    id='sexdropdown', placeholder='Sex', multi=True
                ),
                Dropdown(
                    options=[{'label': iprcodes[v], 'value': iprcodes[v]} for v in iprcodes],
                    id='iprdropdown', placeholder='IPR', multi=True
                ),
            ],id='tabledropdowncontainer'),
            dash_table.DataTable(columns=[{'name': i, 'id': i} for i in ['Race', 'Sex', 'IPR', 'Percent Uninsured', 'Comparison to State']], 
                id='datatable',sort_action='native',style_header={'background-color': '#cce0ff'},
                style_data_conditional=[{'if': {'row_index': 'odd'},'backgroundColor': '#e6f0ff',},
                {'if': {'filter_query': '{Comparison to State} > 0 && {Comparison to State} < 10', 'column_id': 'Comparison to State'}, 'backgroundColor': '#ffe6e6'},
                {'if': {'filter_query': '{Comparison to State} >= 10', 'column_id': 'Comparison to State'}, 'backgroundColor': '#ffb3b3'},
                {'if': {'filter_query': '{Comparison to State} < 0 && {Comparison to State} > -10', 'column_id': 'Comparison to State'}, 'backgroundColor': '#e6ffe6'},
                {'if': {'filter_query': '{Comparison to State} <= -10', 'column_id': 'Comparison to State'}, 'backgroundColor': '#b3ffb3'},
                ]
            )
        ],id='tablediv'),
    ]),
    Br(),
    Footer([
        'Made by Willem Gardner with  ', 
        A(Img(id='logo', src='/assets/logo-plotly.svg', alt='Plotly'), href='https://dash.plotly.com/'), 
        'Dash using data from ',
        A(Img(src='/assets/census-logo.svg', alt='U.S. Census Bureau Logo'),id='censuslogo', href='https://www.census.gov/data/developers/data-sets/Health-Insurance-Statistics.html')

    ])
])

@app.callback(
    Output('submit', 'href'),
    Input('statedropdown', 'value'),
    Input('yeardropdown', 'value')
)
def submitPath(state, year):
    if state is None or year is None:
        raise PreventUpdate
    else:
        statename = statecodes.loc[statecodes['Statecode'] == state, 'Name'].iloc[0]
        return f'/{statename}/{state}/{year}'

@app.callback(
    Output('store', 'data'),
    Input('url', 'pathname')
)
def loadpage(path):
    if path == '/':
        return 'main page'
    else:
        statename, statecode, year = path.lstrip('/').split('/')
        statename = statename.replace('%20', ' ')
        return {'statename': statename, 'statecode': statecode, 'year': year}
@app.callback(
    Output('statestore', 'data'),
    Input('store', 'data')
)
def storestatedata(data):
    if data == None or type(data) == str:
        raise PreventUpdate
    else:
        con = sql.connect('censusdata.db')
        cur = con.cursor()
        statedata = cur.execute("SELECT Race, Sex, IPR, \"Percent Uninsured\" FROM statedata WHERE State=:statecode AND Year=:year",{'statecode':data['statecode'],'year':data['year']})
        cols = [col[0] for col in statedata.description]
        statedf = pd.DataFrame(statedata, columns=cols)
        con.close()
        stateavg = statedf.loc[(statedf['Race'] == 'All Races') & (statedf['Sex'] == 'Both') & (statedf['IPR'] == 'All Incomes'), ['Percent Uninsured']].loc[0,'Percent Uninsured']
        statedf['Comparison to State'] = [round(float(p) - float(stateavg),2) for p in statedf['Percent Uninsured']]
        return statedf.to_dict('records')
@app.callback(
    Output('countystore', 'data'),
    Input('store', 'data')
)
def storecountydata(data):
    if data == None or type(data) == str:
        raise PreventUpdate
    else:
        con = sql.connect('censusdata.db')
        cur = con.cursor()
        countydata = cur.execute("SELECT \"Percent Uninsured\", County FROM countydata WHERE statecode=:statecode AND Year=:year",{'statecode':data['statecode'],'year':data['year']})
        cols = [col[0] for col in countydata.description]
        countydf = pd.DataFrame(countydata, columns=cols)
        con.close()
        return countydf.to_dict('records')

@app.callback(
    Output('timestore', 'data'),
    Input('store', 'data')
)
def storetimedata(data):
    if data == None or type(data) == str:
        raise PreventUpdate
    else:
        con = sql.connect('censusdata.db')
        cur = con.cursor()
        timedata = cur.execute("SELECT \"Percent Uninsured\", Year FROM timedata WHERE Statecode=:statecode",{'statecode':data['statecode']})
        cols = [col[0] for col in timedata.description]
        timedf = pd.DataFrame(timedata, columns=cols)
        con.close()
        return timedf.to_dict('records')

@app.callback(
    Output('datatable', 'data'),
    Input('racedropdown', 'value'),
    Input('sexdropdown', 'value'),
    Input('iprdropdown', 'value'),
    Input('statestore','data'),
    Input('store','data')
)
def updatetable(race, sex, ipr,data,store):
    if race == []:
        race = None
    if sex == []:
        sex = None
    if ipr == []:
        ipr = None

    if store == 'main page':
        df = pd.DataFrame({'Race': ['No State Selected'], 'Sex': ['No State Selected'], 'IPR': ['No State Selected'], 'Percent Uninsured': ['No State Selected'], 'Comparison to State': ['No State Selected']})
        return df.to_dict('records')
    elif race is None and sex is None and ipr is None:
        return data
    else:
        df = pd.DataFrame(data)
        updatedf = df.copy(deep=True)
  
        rselected, rselection, sselected, sselection, iselected, iselection = None, None, None, None, None, None
    
        if race is not None:
            rselected = [(df['Race'] == race[i]) for i in range(0,len(race))]
            if len(rselected) == 1:
                rselection = rselected[0]
            elif len(rselected) == 2:
                rselection = (rselected[0] | rselected[1])
            elif len(rselected) == 3:
                rselection = (rselected[0] | rselected[1] | rselected[2])
            else:
                rselection = (rselected[0] | rselected[1] | rselected[2] | rselected[3])

        if sex is not None:
            sselected = [(df['Sex'] == sex[i]) for i in range(0,len(sex))]
            if len(sselected) == 1:
                sselection = sselected[0]
            elif len(sselected) == 2:
                sselection = (sselected[0] | sselected[1])
            else:
                sselection = (sselected[0] | sselected[1] | sselected[2])
        
        if ipr is not None:
            iselected = [(df['IPR'] == ipr[i]) for i in range(0,len(ipr))]
            if len(iselected) == 1:
                iselection = iselected[0]
            elif len(iselected) == 2:
                iselection = (iselected[0] | iselected[1])
            elif len(iselected) == 3:
                iselection = (iselected[0] | iselected[1] | iselected[2])
            elif len(iselected) == 4:
                iselection = (iselected[0] | iselected[1] | iselected[2] | iselected[3])
            elif len(iselected) == 5:
                iselection = (iselected[0] | iselected[1] | iselected[2] | iselected[3] | iselected[4])
            else:
                iselection = (iselected[0] | iselected[1] | iselected[2] | iselected[3] | iselected[4] | iselected[5])
        if race is not None and sex is not None and ipr is not None:
            updatedf = df.loc[rselection & sselection & iselection]
        elif race is not None and sex is not None and ipr is None:
            updatedf = df.loc[rselection & sselection]
        elif race is not None and sex is None and ipr is not None:
            updatedf = df.loc[rselection & iselection]
        elif race is not None and sex is None and ipr is None:
            updatedf = df.loc[rselection]
        elif race is None and sex is not None and ipr is not None:
            updatedf = df.loc[sselection & iselection]
        elif race is None and sex is not None and ipr is None:
            updatedf = df.loc[sselection]
        else:
            updatedf = df.loc[iselection]

        return updatedf.to_dict('records')

@app.callback(
    Output('graph', 'children'),
    Input('statetabs', 'value'),
    Input('store', 'data'),
    Input('countystore', 'data'),
    Input('statestore', 'data'),
    Input('timestore', 'data')
)
def showgraph(value,store,county,state,time):
    if store == 'main page':
        return [
            H2('Select Year and State to see percentage of people without health insurance.'),
            H2('Select tab to visualize data by County, Race and IPR, or Over time.'),
            P('Data is retrieved from the Small Area Health Insurance Estimates U.S. Census Bureau API.'),
        ]
    elif value == 'countytab':
        countydf = pd.DataFrame(county)
        countyfig = px.bar(countydf, x='County', y='Percent Uninsured', title=f'{store["statename"]} {store["year"]}')
        countyfig.update_yaxes(type='linear')
        countyfig.update_layout(xaxis={'categoryorder':'total descending'}, title={'x': 0.5})
        return Graph(figure=countyfig)

    elif value == 'demotab':
        demodf = pd.DataFrame(state)
        demodf = demodf[demodf['Sex'] == 'Both']
        demofig = px.bar(demodf, x='IPR', y='Percent Uninsured', barmode='group',color='Race',
            title=f'{store["statename"]} {store["year"]}')
        demofig.update_xaxes(type='category')
        demofig.update_yaxes(type='linear')
        demofig.update_layout(title={'x': 0.5})
        return Graph(figure=demofig)
    else:
        timedf = pd.DataFrame(time)
        timefig = px.line(timedf, x='Year', y='Percent Uninsured',
            title=f'{store["statename"]} 2006 - 2019')
        timefig.update_yaxes(type='linear')
        timefig.update_layout(title={'x': 0.5})
        return Graph(figure=timefig)
if __name__ == '__main__':
    app.run_server()
