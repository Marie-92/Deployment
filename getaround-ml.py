import pandas as pd
import time
import mlflow
from mlflow.models.signature import infer_signature
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import  OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
import joblib
import os

mlflow.set_tracking_uri("https://mlflow-marie.herokuapp.com/")

if __name__ == "__main__":
    EXPERIMENT_NAME="price_estimator"
    mlflow.set_experiment(EXPERIMENT_NAME)
    experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
    client = mlflow.tracking.MlflowClient()
    run = client.create_run(experiment.experiment_id) 
    mlflow.sklearn.autolog()

    df = pd.read_csv("get_around_pricing_project.csv")
    df.drop('Unnamed: 0', axis=1, inplace=True)
    target_variable = "rental_price_per_day"
    X = df.drop(target_variable, axis=1)
    Y = df[target_variable]
    numeric_features = []
    categorical_features = []
    for i,t in X.dtypes.iteritems():
        if ('float' in str(t)) or ('int' in str(t)) :
            numeric_features.append(i)
        else :
            categorical_features.append(i)
    X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size = 0.2)
    numeric_transformer = StandardScaler()
    categorical_transformer = OneHotEncoder(drop='first', handle_unknown='infrequent_if_exist')
    preprocessor = ColumnTransformer(
    transformers=[
        ('num', numeric_transformer, numeric_features),
        ('cat', categorical_transformer, categorical_features)
    ])
    model = Pipeline(steps=[("Preprocessing", preprocessor),
                            ("Regressor", LinearRegression())
                            ])
    with mlflow.start_run() as run:
        model.fit(X_train, y_train)
        predictions = model.predict(X_train)
        mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="price_estimator",
            registered_model_name="price_estimator_lr",
            signature=infer_signature(X_train, predictions)
        )

    