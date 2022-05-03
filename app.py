#HAP 618 Project

from dash import Dash, html, dcc, dash_table
from dash.dependencies import Output, Input
from dash.exceptions import PreventUpdate
import plotly.express as px
import pandas as pd
import sqlite3 as sql

app = Dash(__name__)
server = app.server

con = sql.connect('censusdata.db')
cur = con.cursor()
statecodesql = cur.execute('SELECT * FROM statecodes')
cols = [col[0] for col in statecodesql.description]
statecodes = pd.DataFrame(statecodesql, columns=cols)
con.close()

racecodes = {'0': 'All Races', '1': 'White', '2': 'Black', '3': 'Hispanic'}
sexcodes = {'0': 'Both', '1': 'Male', '2': 'Female'}
iprcodes = {'0': 'All Incomes', '1': 'At or Below 200% of Poverty', '2': 'At or Below 250% of Poverty', '3': 'At or Below 138% of Poverty', '4': 'At or Below 400% of Poverty', '5': 'Between 138% - 400% of Poverty'}
democodes = [['Race', racecodes], ['Sex', sexcodes], ['IPR', iprcodes]]

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='store',data='main page'),
    dcc.Store(id='statestore'),
    dcc.Store(id='countystore'),
    dcc.Store(id='timestore'),
    html.H1('Small Area Health Insurance Estimates (SAHIE) from U.S. Census Bureau'),
    html.Div([
        html.Label([
            html.P('Select Year: '), 
            dcc.Dropdown(
            options=[i for i in range(2006, 2020)],
            id='yeardropdown'
            )
        ]),
        html.Label([
            html.P('Select State: '), 
            dcc.Dropdown(
            options=[{'label': statecodes.iloc[i,0],'value': statecodes.iloc[i,1]} for i in range(len(statecodes))],
            id='statedropdown'
            )
        ]),
        html.Button(dcc.Link('Submit', href='', id='submit'))
    ], id='dropdowndiv'),
    html.Br(),
    html.Main([
        dcc.Tabs([
            dcc.Tab(label='County', value='countytab', id='countytab'),
            dcc.Tab(label='Race and IPR', value='demotab', id='demotab'),
            dcc.Tab(label='Over Time', value='timetab', id='timetab'),
        ], id='statetabs', value='countytab'),
        dcc.Loading(id='graph'),
        html.Br(),
        html.H3('State Data Table'),
        html.Div([
            html.Div([    
                dcc.Dropdown(
                    options=[{'label': racecodes[v], 'value': racecodes[v]} for v in racecodes],
                    id='racedropdown', placeholder='Race', multi=True
                ),
                dcc.Dropdown(
                    options=[{'label': sexcodes[v], 'value': sexcodes[v]} for v in sexcodes],
                    id='sexdropdown', placeholder='Sex', multi=True
                ),
                dcc.Dropdown(
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
    html.Br(),
    html.Footer([
        'Made by Willem Gardner with  ', 
        html.A(html.Img(id='logo', src='/assets/logo-plotly.svg', alt='Plotly'), href='https://dash.plotly.com/'), 
        'Dash using data from ',
        html.A(html.Img(src='/assets/census-logo.svg'),id='censuslogo',style={'width':64,'height':24}, href='https://www.census.gov/data/developers/data-sets/Health-Insurance-Statistics.html')

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
  
        rsel, rselec, ssel, sselec, isel, iselec = None, None, None, None, None, None
    
        if race is not None:
            rsel = [(df['Race'] == race[i]) for i in range(0,len(race))]
            if len(rsel) == 1:
                rselec = rsel[0]
            elif len(rsel) == 2:
                rselec = (rsel[0] | rsel[1])
            elif len(rsel) == 3:
                rselec = (rsel[0] | rsel[1] | rsel[2])
            else:
                rselec = (rsel[0] | rsel[1] | rsel[2] | rsel[3])

        if sex is not None:
            ssel = [(df['Sex'] == sex[i]) for i in range(0,len(sex))]
            if len(ssel) == 1:
                sselec = ssel[0]
            elif len(ssel) == 2:
                sselec = (ssel[0] | ssel[1])
            else:
                sselec = (ssel[0] | ssel[1] | ssel[2])
        
        if ipr is not None:
            isel = [(df['IPR'] == ipr[i]) for i in range(0,len(ipr))]
            if len(isel) == 1:
                iselec = isel[0]
            elif len(isel) == 2:
                iselec = (isel[0] | isel[1])
            elif len(isel) == 3:
                iselec = (isel[0] | isel[1] | isel[2])
            elif len(isel) == 4:
                iselec = (isel[0] | isel[1] | isel[2] | isel[3])
            elif len(isel) == 5:
                iselec = (isel[0] | isel[1] | isel[2] | isel[3] | isel[4])
            else:
                iselec = (isel[0] | isel[1] | isel[2] | isel[3] | isel[4] | isel[5])
        if race is not None and sex is not None and ipr is not None:
            updatedf = df.loc[rselec & sselec & iselec]
        elif race is not None and sex is not None and ipr is None:
            updatedf = df.loc[rselec & sselec]
        elif race is not None and sex is None and ipr is not None:
            updatedf = df.loc[rselec & iselec]
        elif race is not None and sex is None and ipr is None:
            updatedf = df.loc[rselec]
        elif race is None and sex is not None and ipr is not None:
            updatedf = df.loc[sselec & iselec]
        elif race is None and sex is not None and ipr is None:
            updatedf = df.loc[sselec]
        else:
            updatedf = df.loc[iselec]

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
            html.H2('Select Year and State to see percentage of people without health insurance.'),
            html.H2('Select tab to visualize data by County, Race and IPR, or Over time.'),
            html.P('Data is retrieved from Small Area Health Insurance Estimates (SAHIE) U.S. Census Bureau API.'),
        ]
    elif value == 'countytab':
        countydf = pd.DataFrame(county)
        countyfig = px.bar(countydf, x='County', y='Percent Uninsured', title=f'{store["statename"]} {store["year"]}')
        countyfig.update_yaxes(type='linear')
        countyfig.update_layout(xaxis={'categoryorder':'total descending'}, title={'x': 0.5})
        return dcc.Graph(figure=countyfig)

    elif value == 'demotab':
        demodf = pd.DataFrame(state)
        demodf = demodf[demodf['Sex'] == 'Both']
        demofig = px.bar(demodf, x='IPR', y='Percent Uninsured', barmode='group',color='Race',
            title=f'{store["statename"]} {store["year"]}')
        demofig.update_xaxes(type='category')
        demofig.update_yaxes(type='linear')
        demofig.update_layout(title={'x': 0.5})
        return dcc.Graph(figure=demofig)
    else:
        timedf = pd.DataFrame(time)
        timefig = px.line(timedf, x='Year', y='Percent Uninsured',
            title=f'{store["statename"]} 2006 - 2019')
        timefig.update_yaxes(type='linear')
        timefig.update_layout(title={'x': 0.5})
        return dcc.Graph(figure=timefig)
if __name__ == '__main__':
    app.run_server(debug=True)
