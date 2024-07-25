# train.py

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
import joblib
import pickle

# Load data from JSON file
data = pd.read_json('./output.json')

# Define input features
input_features = [
    "acidity", "indigestion", "headache", "blurred_and_distorted_vision",
    "excessive_hunger", "muscle_weakness", "stiff_neck", "swelling_joints",
    "movement_stiffness", "depression", "irritability", "visual_disturbances",
    "painful_walking", "abdominal_pain", "nausea", "vomiting", "blood_in_mucus",
    "Fatigue", "Fever", "Dehydration", "loss_of_appetite", "cramping",
    "blood_in_stool", "gnawing", "upper_abdomain_pain", "fullness_feeling",
    "hiccups", "abdominal_bloating", "heartburn", "belching", "burning_ache",
    "age", "gender", "severity"
]

# Convert gender to numerical values
data['gender'] = data['gender'].map({'male': 0, 'female': 1})

# Encode severity column
le = LabelEncoder()
data['severity'] = le.fit_transform(data['severity'])

# Split data into features (X) and target (y)
X = data[input_features]
y = data['prognosis']

# Split data into train and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Create and train the random forest model
rf_model = RandomForestClassifier()
rf_model.fit(X_train, y_train)

# Make predictions on the test set
y_pred = rf_model.predict(X_test)



def predict_prognosis_and_recommend_drug(input_data: dict) -> tuple:
    """Predict prognosis and recommend drug based on input data"""
    print("Input Data:", input_data)  # Print input data for debugging
    
    required_features = input_features[:-3]  # Excluding 'age', 'gender', and 'severity'
    
    # Initialize all symptoms to 0
    input_data_full = {symptom: 0 for symptom in input_features[:-3]}
    
    # Update input_data with provided symptoms
    input_data_full.update(input_data)
    
    # Check if all required features are present
    if not all(feature in input_data_full for feature in required_features):
        raise ValueError("Insufficient information provided.")

    # Convert input data to a DataFrame
    input_df = pd.DataFrame([input_data_full], columns=input_features)

    # Encode gender in input data
    input_df['gender'] = input_df['gender'].map({'male': 0, 'female': 1})
    
    # Fill NaN values in the 'severity' column with 'NORMAL'
    input_df['severity'] = input_df['severity'].fillna('NORMAL')
    
    # Encode severity in input data
    input_df['severity'] = le.transform(input_df['severity'])

    # Check if input data matches a row in the dataset
    conditions = (data[required_features] == input_df[required_features].values[0]).all(axis=1)
    if not conditions.any():
        raise ValueError("No matching row found in the dataset.")
    
    # Make prediction
    prognosis = rf_model.predict(input_df)[0]

    # Recommend drug based on prognosis, age, severity, and gender
    conditions = (
        (data['prognosis'] == prognosis) &
        (data['age'] == input_data['age']) &
        (data['severity'] == input_df['severity'].values[0]) &
        (data['gender'] == input_df['gender'].values[0])
    )
    drug_recommendation = data.loc[conditions, 'drug'].values
    if len(drug_recommendation) == 0:
        raise ValueError("No drug recommendation available for the provided data.")
    else:
        return prognosis, drug_recommendation[0]

# Example usage
#input_data = {}
 #   "acidity": 0,
  #  "indigestion": 0,
   # "headache": 0,
   # "blurred_and_distorted_vision": 0,
   # "excessive_hunger": 0,
    #"muscle_weakness": 1,
    #"stiff_neck": 1,
    #"swelling_joints": 1,
    #"movement_stiffness": 1,
    #"depression": 0,
    #"irritability": 1,
    #"visual_disturbances": 0,
    #"painful_walking": 1,
    #"abdominal_pain": 0,
    #"nausea": 0,
    #"vomiting": 0,
    #"blood_in_mucus": 0,
    #"Fatigue": 0,
    #"Fever": 0,
    #"Dehydration": 0,
    #"loss_of_appetite": 0,
    #"cramping": 0,
    #"blood_in_stool": 0,
    #"gnawing": 0,
    #"upper_abdomain_pain": 0,
    #"fullness_feeling": 0,
    #"hiccups": 0,
    #"abdominal_bloating": 0,
    #"heartburn": 0,
    #"belching": 0,
    #"burning_ache": 0,
    #"age": 29,
    #"gender": "female",
    #"severity": "NORMAL"
#}

#prognosis, drug_recommendation = predict_prognosis_and_recommend_drug(input_data)
#if prognosis is not None:
 #   print(f"Predicted Prognosis: {prognosis}")
  #  print(f"Recommended Drug(s): {drug_recommendation}")

# Save the trained model to a file
#joblib.dump(rf_model, 'rf_model.joblib')

# Save the trained model to a file
#with open('rf_model.pkl', 'wb') as file:
 #   pickle.dump(rf_model, file)
