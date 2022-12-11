import json
from pprint import pprint

import pandas as pd

pd.set_option('display.max_columns', None)


def save_json(dict_params:dict):
    with open('settings.json', 'w',  encoding='utf8') as f:
        json.dump(dict_params, f, indent=6)


def transform_param(df: pd.Series) ->dict:
    '''
     'EBS': {'position': True, 'settings': []},
    '''
    param = dict()
    for i in range(len(df)):
        param[df.iloc[i][0]] = {'position': False, 'settings': [str(df.iloc[i][1]), str(df.iloc[i][2]), str(df.iloc[i][3])]}
    print(param)

    return param


def main():
    df = pd.read_csv('stats.csv')
    df.Start = pd.to_datetime(df.Start)

    # Поиск макс Return [%]
    df_max_return = df.loc[df.groupby(by=df.ticker)['Return [%]'].idxmax()]
    res = df_max_return[['ticker', 'Start', 'ten', 'kij', 'sen', "Return [%]", 'Buy & Hold Return [%]']]

    # save file
    res.to_csv('filter_stat.csv', index=False)

    df_max_return.index = df_max_return.ticker
    param = df_max_return[['ticker', 'ten', 'kij', 'sen']]
    # print(param.to_dict('index'))

    dict_params = transform_param(param)
    save_json(dict_params)

if __name__ == '__main__':
    main()
