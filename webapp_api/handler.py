import os
import pickle
import pandas as pd
from flask             import Flask, request, Response
from rossmann.Rossmann import Rossmann

# Carregando o modelo de ML
model = pickle.load(open('model/model_rossmann.pkl', 'rb'))

# Inicializando a API
app = Flask(__name__)

@app.route('/rossmann/predict', methods=['POST'])
def rossmann_predict():
    test_json = request.get_json()
    
    if test_json: # Caso existam dados
        
        if isinstance(test_json, dict): # Um registro
            test_raw = pd.DataFrame(test_json, index=[0])
            
        else: # Múltiplos registros
            test_raw = pd.DataFrame(test_json, columns = test_json[0].keys())
        
        # Instanciando a classe Rossmann
        pipeline = Rossmann()
        
        # Limpeza e Preparação dos dados
        df1 = pipeline.data_cleaning(test_raw)
        df2 = pipeline.feature_engineering(df1)
        df3 = pipeline.data_filter(df2)
        df4 = pipeline.data_preparation(df3)
        
        # Previsão
        df_response = pipeline.get_prediction(model, test_raw, df4)
        
        return df_response        
        
    else: # Caso não existam dados
        return Response('{}', status=200, mimetype='application/json')

        
if __name__ == '__main__':
    find_port = os.environ.get('PORT', 5000)
    app.run(host='0.0.0.0', port=find_port)