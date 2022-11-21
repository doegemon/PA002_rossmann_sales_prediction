import math
import pickle
import datetime
import inflection
import numpy  as np
import pandas as pd

class Rossmann(object):
    
    def __init__(self):
        self.home_path = ''
        self.competition_distance_rescaler   = pickle.load(open(self.home_path + 'parameters/competition_distance_rescaler.pkl', 'rb'))
        self.competition_time_month_rescaler = pickle.load(open(self.home_path + 'parameters/competition_time_month_rescaler.pkl', 'rb'))
        self.promo_since_week_rescaler       = pickle.load(open(self.home_path + 'parameters/promo_since_week_rescaler.pkl', 'rb'))
        self.year_rescaler                   = pickle.load(open(self.home_path + 'parameters/year_rescaler.pkl', 'rb'))
        self.store_type_encoder              = pickle.load(open(self.home_path + 'parameters/store_type_encoder.pkl', 'rb'))
      
        
    def data_cleaning(self, df1):

        # Renomeando Colunas
        old_cols = ['Store', 'DayOfWeek', 'Date', 'Open', 'Promo',
                   'StateHoliday', 'SchoolHoliday', 'StoreType', 'Assortment',
                   'CompetitionDistance', 'CompetitionOpenSinceMonth',
                   'CompetitionOpenSinceYear', 'Promo2', 'Promo2SinceWeek',
                   'Promo2SinceYear', 'PromoInterval']

        to_snakecase = lambda x: inflection.underscore(x)

        new_cols = list(map(to_snakecase, old_cols))

        df1.columns = new_cols
        
        # Alterando Tipos de Dados
        df1['date'] = pd.to_datetime(df1['date'], format='%Y-%m-%d')

        # Preenchendo Valores Nulos
        df1['competition_distance'] = df1['competition_distance'].apply(lambda x: 200000.0 if math.isnan(x) else x)

        df1['competition_open_since_month'] = df1.apply(lambda x: x['date'].month if math.isnan(x['competition_open_since_month']) else x['competition_open_since_month'], axis = 1)

        df1['competition_open_since_year'] = df1.apply(lambda x: x['date'].year if math.isnan(x['competition_open_since_year']) else x['competition_open_since_year'], axis = 1)

        df1['promo2_since_week'] = df1.apply(lambda x: x['date'].week if math.isnan(x['promo2_since_week']) else x['promo2_since_week'], axis = 1)

        df1['promo2_since_year'] = df1.apply(lambda x: x['date'].year if math.isnan(x['promo2_since_year']) else x['promo2_since_year'], axis = 1)

        months = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6:'Jun', 7: 'Jul', 8:'Aug', 9:'Sept', 10:'Oct', 11:'Nov', 12:'Dec'}

        df1['promo_interval'] = df1['promo_interval'].fillna(0)

        df1['month'] = df1['date'].dt.month.map(months)

        df1['is_promo'] = df1[['promo_interval', 'month']].apply(lambda x: 0 if x['promo_interval'] == 0 else 1 if x['month'] in x['promo_interval'].split(',') else 0, axis = 1)
        
        # Alterando Tipos de Dados após Preenchimento de Valores Nulos
        
        df1['competition_open_since_month'] = df1['competition_open_since_month'].astype('int64')
        
        df1['competition_open_since_year']  = df1['competition_open_since_year'].astype('int64')
        
        df1['promo2_since_week']            = df1['promo2_since_week'].astype('int64')
        
        df1['promo2_since_year']            = df1['promo2_since_year'].astype('int64')
        
        return df1
    
    
    def feature_engineering(self, df2):
        
        df2['year'] = df2['date'].dt.year

        df2['month'] = df2['date'].dt.month

        df2['day'] = df2['date'].dt.day

        df2['week_of_year'] = df2['date'].dt.weekofyear

        df2['year_week'] = df2['date'].dt.strftime('%Y-%W')

        df2['competition_open_since'] = df2.apply(lambda x: datetime.datetime(year=x['competition_open_since_year'], month=x['competition_open_since_month'], day=1), axis=1)

        df2['competition_open_time_month'] = ((df2['date'] - df2['competition_open_since']) / 30).apply(lambda x: x.days).astype(int)

        df2['promo_since'] = df2['promo2_since_year'].astype(str) + '-' + df2['promo2_since_week'].astype(str)

        df2['promo_since'] = df2['promo_since'].apply(lambda x: datetime.datetime.strptime(x + '-1', '%Y-%W-%w') - datetime.timedelta(days=7))

        df2['promo_since_week'] = ((df2['date'] - df2['promo_since']) / 7).apply(lambda x: x.days).astype(int)

        df2['assortment'] = df2['assortment'].apply(lambda x: 'basic' if x == 'a' else 'extra' if x == 'b' else 'extended')

        df2['state_holiday'] = df2['state_holiday'].apply(lambda x: 'public_holiday' if x == 'a' else 'easter_holiday' if x == 'b' else 'christmas' if x == 'c' else 'regular_day')
        
        return df2
    
    
    def data_filter(self, df3):
        
        df3 = df3[df3['open'] != 0]
        
        cols_to_drop = ['open', 'promo_interval']
        df3 = df3.drop(cols_to_drop, axis = 1)
        
        return df3
    
    
    def data_preparation(self, df5):
        
        # Rescaling
        df5['competition_distance'] = self.competition_distance_rescaler.transform(df5[['competition_distance']].values)
        df5['competition_open_time_month'] = self.competition_time_month_rescaler.transform(df5[['competition_open_time_month']].values)
        df5['promo_since_week'] = self.promo_since_week_rescaler.transform(df5[['promo_since_week']].values)
        df5['year'] = self.year_rescaler.transform(df5[['year']].values)
        
        # Encoding
        df5 = pd.get_dummies(df5, prefix=['state_holiday'], columns=['state_holiday'])
        df5['store_type'] = self.store_type_encoder.fit_transform(df5['store_type'])
        assortment_dict = {'basic': 1, 'extra': 2, 'extended': 3}
        df5['assortment'] = df5['assortment'].map(assortment_dict)

        # Transformação de Natureza  
        # day_of_week
        df5['day_of_week_sin'] = df5['day_of_week'].apply(lambda x: np.sin(x * (2. * np.pi/7)))
        df5['day_of_week_cos'] = df5['day_of_week'].apply(lambda x: np.cos(x * (2. * np.pi/7)))

        # day
        df5['day_sin'] = df5['day'].apply(lambda x: np.sin(x * (2. * np.pi/30)))
        df5['day_cos'] = df5['day'].apply(lambda x: np.cos(x * (2. * np.pi/30)))

        # week_of_year
        df5['week_of_year_sin'] = df5['week_of_year'].apply(lambda x: np.sin(x * (2. * np.pi/52)))
        df5['week_of_year_cos'] = df5['week_of_year'].apply(lambda x: np.cos(x * (2. * np.pi/52)))

        # month
        df5['month_sin'] = df5['month'].apply(lambda x: np.sin(x * (2. * np.pi/12)))
        df5['month_cos'] = df5['month'].apply(lambda x: np.cos(x * (2. * np.pi/12)))
        
        # Seleção de Variáveis
        cols_selected = [ 'store', 'promo', 'store_type', 'assortment', 'competition_distance', 'competition_open_since_month',
                          'competition_open_since_year', 'promo2', 'promo2_since_week',  'promo2_since_year', 'competition_open_time_month',
                          'promo_since_week', 'day_of_week_sin', 'day_of_week_cos', 'day_sin', 'day_cos', 'week_of_year_sin', 'week_of_year_cos',
                          'month_sin', 'month_cos']
        
        return df5[cols_selected]
    
    def get_prediction(self, model, original_data, test_data):
        
        # Previsões
        pred = model.predict(test_data)
        
        # Juntar as previsões no conjunto de dados
        original_data['prediction'] = np.expm1(pred)
        
        return original_data.to_json(orient='records', date_format='iso')