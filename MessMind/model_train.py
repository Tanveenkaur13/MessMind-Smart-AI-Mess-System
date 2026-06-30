import pandas as pd
import pickle
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder

df = pd.read_csv('mess_detailed_dataset.csv')

# Encoding categorical strings to numbers
le_meal = LabelEncoder()
df['Meal_Encoded'] = le_meal.fit_transform(df['Meal_Type'])

# We use Day_of_Week (0-6), Meal_Encoded (0-2), Holiday, Exam, and Popularity
X = df[['Day_of_Week', 'Meal_Encoded', 'Is_Holiday', 'Is_Exam', 'Menu_Popularity']]
y = df['Quantity_Consumed']

model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)

# Save EVERYTHING into one pickle file
with open('mess_model.pkl', 'wb') as f:
    pickle.dump({'model': model, 'le_meal': le_meal}, f)

print("Detailed model trained successfully!")