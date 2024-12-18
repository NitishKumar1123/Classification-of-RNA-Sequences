# -*- coding: utf-8 -*-
"""BDMH_Ass1_Group_1

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1tLCDJcM0MzLuleiEqw4JVG6TA7M8SO2y
"""

import argparse
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.metrics import accuracy_score, roc_auc_score
from tensorflow.keras.preprocessing.sequence import pad_sequences
from sklearn.preprocessing import StandardScaler

def encode_sequences(sequences, max_length):
    encoding = {'A': [1, 0, 0, 0], 'C': [0, 1, 0, 0], 'G': [0, 0, 1, 0], 'U': [0, 0, 0, 1]}
    encoded_seqs = []
    for seq in sequences:
        encoded_seq = [encoding.get(base, [0, 0, 0, 0]) for base in seq]
        padded_seq = pad_sequences([encoded_seq], maxlen=max_length, padding='post', dtype='float32')[0]
        encoded_seqs.append(padded_seq)
    return np.array(encoded_seqs)

def main(train_file, test_file, output_file):
    # Step 1: Data Loading
    train_df = pd.read_csv(train_file)
    test_df = pd.read_csv(test_file)

    # Step 2: Data Preprocessing
    # Concatenate training and test data to find the maximum sequence length
    all_sequences = train_df['Sequence'].tolist() + test_df['Sequence'].tolist()
    max_length = max(len(seq) for seq in all_sequences)

    # Encode and pad sequences
    X_train_encoded = encode_sequences(train_df['Sequence'], max_length)
    X_test_encoded = encode_sequences(test_df['Sequence'], max_length)

    # Add additional feature: sequence length
    X_train_len = np.array([len(seq) for seq in train_df['Sequence']]).reshape(-1, 1)
    X_test_len = np.array([len(seq) for seq in test_df['Sequence']]).reshape(-1, 1)

    # Reshape X_train_encoded and X_test_encoded to have the same number of dimensions as X_train_len
    X_train_encoded = X_train_encoded.reshape(X_train_encoded.shape[0], -1)
    X_test_encoded = X_test_encoded.reshape(X_test_encoded.shape[0], -1)

    # Concatenate encoded sequences and additional features
    X_train_features = np.concatenate([X_train_encoded, X_train_len], axis=1)
    X_test_features = np.concatenate([X_test_encoded, X_test_len], axis=1)

    # Step 3: Hyperparameter Tuning
    # Initialize model (Random Forest)
    rf_model = RandomForestClassifier()

    # Define parameter grid for GridSearchCV
    param_grid = {
        'n_estimators': [25, 50, 75],
        'max_depth': [None, 5, 10],
        'min_samples_split': [2, 5, 10]
    }

    # Perform grid search with stratified k-fold cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    grid_search = GridSearchCV(rf_model, param_grid, cv=cv, scoring='roc_auc')
    grid_search.fit(X_train_features, train_df['Label'])
    best_rf_model = grid_search.best_estimator_

    # Step 5: Ensemble Methods
    # Initialize ensemble method (AdaBoost)
    ada_model = AdaBoostClassifier(base_estimator=best_rf_model, n_estimators=50)

    # Step 10: Regularization
    # Apply regularization techniques to prevent overfitting
    # Here, we can apply standardization as a form of regularization
    scaler = StandardScaler()
    X_train_features = scaler.fit_transform(X_train_features)
    X_test_features = scaler.transform(X_test_features)

    # Step 12: Model Training
    # Train the AdaBoost model on the full training data
    ada_model.fit(X_train_features, train_df['Label'])

    # Step 13: Model Evaluation
    y_pred_train = ada_model.predict_proba(X_train_features)[:, 1]
    auc_train = roc_auc_score(train_df['Label'], y_pred_train)
    print("AUC on training set:", auc_train)

    # Calculate accuracy on training set
    y_pred_train_labels = ada_model.predict(X_train_features)
    accuracy_train = accuracy_score(train_df['Label'], y_pred_train_labels)
    print("Accuracy on training set:", accuracy_train)

    # Step 14: Prediction
    predictions = ada_model.predict_proba(X_test_features)[:, 1]

    # Step 15: Submission
    submission_df = pd.DataFrame({'ID': test_df['ID'], 'Label': predictions})
    submission_df.to_csv(output_file, index=False)

    #command line option
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="classify positive and negative oligonucleotide sequences (RNA Sequences) using AdaBoost")
    parser.add_argument("--train_file", type=str, required=True, help="Path to the training data file")
    parser.add_argument("--test_file", type=str, required=True, help="Path to the test data file")
    parser.add_argument("--output_file", type=str, required=True, help="Path to save the submission file")
    args = parser.parse_args()
    main(args.train_file, args.test_file, args.output_file)

