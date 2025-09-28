import pandas as pd
import os
from dotenv import load_dotenv
from database_setup import DBSetup
from sentence_transformers import SentenceTransformer

load_dotenv()

class DataPreprocessor:
    def __init__(self):
        self.model_name = os.getenv('MODEL_NAME', 'all-MiniLM-L6-v2')
        self.model = SentenceTransformer(self.model_name)
        self.db_setup = DBSetup()

    def load_data(self, data_path):
        try:
            data = pd.read_csv(data_path)
            print(f"Data loaded successfully from {data_path}")
            return data
        except Exception as e:
            print(f"Error loading data: {e}")
            return None

    def clean_data(self, data):
        self.name_col = 'name' if 'name' in data.columns else 'strDrink'
        self.alcoholic_col = 'alcoholic' if 'alcoholic' in data.columns else 'strAlcoholic'
        self.category_col = 'category' if 'category' in data.columns else 'strCategory'
        self.glass_col = 'glassType' if 'glassType' in data.columns else 'strGlass'
        self.instructions_col = 'instructions' if 'instructions' in data.columns else 'strInstructions'
        print(f'Detected columns: {data.columns.tolist()}')

        # Drop duplicated drink
        if self.name_col in data.columns:
            data = data.drop_duplicates(subset=[self.name_col])

        data = data.fillna('')
        
        data['combined_text'] = ''
        if self.name_col in data.columns:
            data['combined_text'] += data[self.name_col].astype(str) + ' '
        if self.category_col in data.columns:
            data['combined_text'] += data[self.category_col].astype(str) + ' '
        if self.alcoholic_col in data.columns:
            data['combined_text'] += data[self.alcoholic_col].astype(str) + ' '
        if self.glass_col in data.columns:
            data['combined_text'] += data[self.glass_col].astype(str) + ' '

        if 'ingredients' in data.columns:
            data['combined_text'] += data['ingredients'].astype(str) + ' '
        else:
            ingredient_cols = [c for c in data.columns if c.startswith('strIngredient')]
            for col in ingredient_cols:
                data['combined_text'] += data[col].astype(str) + ' '

        if self.instructions_col in data.columns:
            data['combined_text'] += data[self.instructions_col].astype(str) + ' '

        data['combined_text'] = data['combined_text'].str.replace(r'\s+', ' ', regex=True).str.strip()
        print(f'Data cleaned. Sample combined text: {data["combined_text"].iloc[0][:100]}...')
        return data

    def generate_embeddings(self, texts):
        embeddings = self.model.encode(texts, show_progress_bar=True)
        print(f'Generated {len(embeddings)} embeddings.')
        return embeddings

    def create_recipe(self, row):
        recipe = f'Drink: {row.get(self.name_col, "")}\n'
        recipe += f'Category: {row.get(self.category_col, "")}\n'
        recipe += f'Type: {row.get(self.alcoholic_col, "")}\n'
        recipe += f'Glass: {row.get(self.glass_col, "")}\n'

        if row.get(self.instructions_col):
            recipe += f'Instructions: {row[self.instructions_col]}\n'
        
        recipe += 'Ingredients:\n'
        if 'ingredients' in row and row['ingredients']:
            try:
                import ast
                ingredients_str = row['ingredients']

                if ingredients_str.startswith('[') and ingredients_str.endswith(']'):
                    ingredients = ast.literal_eval(ingredients_str)
                else:
                    ingredients = [ingredients_str]

                measures = []
                if 'ingredientMeasures' in row and row['ingredientMeasures']:
                    measures_str = row['ingredientMeasures']
                    if measures_str.startswith('[') and measures_str.endswith(']'):
                        measures = ast.literal_eval(measures_str)
                    else:
                        measures = [measures_str]

                for i, ingredient in enumerate(ingredients):
                    if ingredient and str(ingredient).strip() and str(ingredient).strip().lower() != 'none':
                        if i < len(measures) and measures[i] and str(measures[i]).strip() and str(measures[i]).strip().lower() != 'none':
                            recipe += f' - {measures[i]} {ingredient}\n'
                        else:
                            recipe += f' - {ingredient}\n'
            except Exception as e:
                recipe += f"- {row['ingredients']}\n"

        else:
            for i in range(1, 16):
                ingredient = row.get(f'strIngredient{i}')
                measure = row.get(f'strMeasure{i}')
                if ingredient and str(ingredient).strip() and str(ingredient).strip().lower() != 'none':
                    if measure and str(measure).strip() and str(measure).strip().lower() != 'none':
                        recipe += f' - {measure} {ingredient}\n'
                    else:
                        recipe += f' - {ingredient}\n'
        return recipe
    
    def get_ingredients_list(self, row):
        ingredients = []
        
        if 'ingredients' in row and row['ingredients']:
            try:
                import ast
                ingredients_str = row['ingredients']
                
                if ingredients_str.startswith('[') and ingredients_str.endswith(']'):
                    ingredients_list = ast.literal_eval(ingredients_str)
                    for ingredient in ingredients_list:
                        if ingredient and str(ingredient).strip() and str(ingredient).strip().lower() != 'none':
                            ingredients.append(str(ingredient).strip())
                else:
                    if ingredients_str.strip():
                        ingredients.append(ingredients_str.strip())
            except Exception as e:
                if row['ingredients'].strip():
                    ingredients.append(row['ingredients'].strip())
        else:
            for i in range(1, 16):
                ingredient = row.get(f'strIngredient{i}')
                if ingredient and str(ingredient).strip() and str(ingredient).strip() != 'nan':
                    ingredients.append(str(ingredient).strip())
        
        return ', '.join(ingredients)

    def store_cocktails(self, data):
        try:
            conn = self.db_setup.get_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM cocktails")

            print(f'Generating and storing embeddings for {len(data)} cocktails...')
            embeddings = self.generate_embeddings(data['combined_text'].tolist())

            for idx, (_, row) in enumerate(data.iterrows()):
                emb = embeddings[idx]

                name = row.get(self.name_col, '')
                ingredients = self.get_ingredients_list(row)
                recipe = self.create_recipe(row)
                alcoholic = row.get(self.alcoholic_col, '')
                category = row.get(self.category_col, '')
                glass = row.get(self.glass_col, '')
                iba = row.get('strIBA', '') 

                cursor.execute("""
                   INSERT INTO cocktails (name, ingredients, recipe, glass, category, iba, alcoholic, embedding)            
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (name, ingredients, recipe, glass, category, iba, alcoholic, emb.tolist()))

                if (idx + 1) % 100 == 0:
                    print(f'Inserted {idx + 1} records...')
            
            conn.commit()
            cursor.close()
            conn.close()
            print('✅ All cocktails stored successfully.')
        except Exception as e:
            print(f'❌ Error storing cocktails: {e}')
            # Rollback in case of error
            if 'conn' in locals():
                conn.rollback()
                conn.close()

    def run(self, data_path):
        data = self.load_data(data_path)
        if data is None:
            return
        cleaned_data = self.clean_data(data)
        self.store_cocktails(cleaned_data)


if __name__ == "__main__":
    cocktail_processor = DataPreprocessor()
    data_path = 'data/final_cocktails.csv'
    if os.path.exists(data_path):
        cocktail_processor.run(data_path)
    else:
        print(f'Please download the dataset and place it in the data directory.')
        print("Dataset URL: https://www.kaggle.com/datasets/aadyasingh55/cocktails/data")







