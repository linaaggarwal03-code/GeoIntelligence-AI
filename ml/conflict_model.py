import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib

file_list = [
    'data/currency_impact.csv',
    'data/Middle-East_aggregated_data_up_to_week_of-2026-09-19.xlsx',
    'data/number_of_political_violence_events_by_country-year_as-of-25Sep2026.xlsx',
    'data/sector_impact_index.csv',
    'data/pros_cons_analysis.csv',
    'data/price_trend_monthly.csv',
    'data/sector_impact.csv',
    'data/shipping_logistics_disruption.csv',
    'data/tariff_news_headlines.csv',
    'data/tariff_rates_by_country_2026.csv',
    'data/tariff_rates.csv',
    'data/tariff_timeline_events_2025_26.csv',
    'data/tariff_timeline.csv',
    'data/trade_balance.csv',
    'data/trade_disruption_score_index.csv',
    'data/trade_volume_annual.csv',
    'data/war_economic_impact_dataset.csv',
    'data/war_history_economics_1948_2026.csv',
    'data/convertcsv.csv',
    'data/iran_political_violence_events_and_fatalities_by_month-year_as-of-25feb2026.xlsx',
    'data/war_timeline.csv'
]

all_data = []

for file in file_list:
    clean_path = file.strip()
    try:
        if clean_path.endswith('.csv'):
            temp_df = pd.read_csv(clean_path)
        elif clean_path.endswith('.xlsx'):
            temp_df = pd.read_excel(clean_path)
        else:
            continue
            
        temp_df.columns = temp_df.columns.str.lower()
        
        all_data.append(temp_df)
    except:
        continue

df = pd.concat(all_data, ignore_index=True)

if 'country' in df.columns and 'fatalities' in df.columns:
    df['fatalities'] = pd.to_numeric(df['fatalities'], errors='coerce').fillna(0)
    df = df.dropna(subset=['country'])
    
    conflict_features = df.groupby('country').agg(
        recent_events=('country', 'count'),
        conflict_intensity=('fatalities', 'sum')
    ).reset_index()

    conflict_features['escalation_warning'] = conflict_features['conflict_intensity'].apply(
        lambda x: 1 if x > 50 else 0
    )

    X = conflict_features[['recent_events', 'conflict_intensity']]
    y = conflict_features['escalation_warning']

    if len(X) > 1:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        model = RandomForestClassifier(random_state=42)
        model.fit(X_train, y_train)

        predictions = model.predict(X_test)
        print(f"Model Accuracy: {accuracy_score(y_test, predictions) * 100:.2f}%")

        joblib.dump(model, 'ml/conflict_model.pkl')
        print("Model saved successfully!")
    else:
        print("Not enough data to train the model.")
else:
    print("Error: 'country' ya 'fatalities' column merge hone ke baad bhi nahi mila.")