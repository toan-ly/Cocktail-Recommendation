import os
from dotenv import load_dotenv
from database_setup import DBSetup
from sentence_transformers import SentenceTransformer

load_dotenv()

class CocktailRecommender:
    def __init__(self):
        self.model_name = os.getenv('MODEL_NAME', 'all-MiniLM-L6-v2')
        self.model = SentenceTransformer(self.model_name)
        self.db_setup = DBSetup()

    def get_user_preferences_embedding(self, preferences):
        pref_text = ' '.join(preferences)
        return self.model.encode([pref_text])[0]

    @staticmethod
    def _to_vector(obj) -> list:
        if hasattr(obj, 'tolist'):
            return obj.tolist()
        return list(obj)

    def search_similar_cocktails(
        self,
        query_embedding,
        limit: int = 10,
        threshold: float = 0.3,
    ):
        try:
            with self.db_setup.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""SELECT COUNT(*) FROM cocktails""")
                    total_cocktails = cursor.fetchone()[0]
                    print(f"Total cocktails in database: {total_cocktails}")
                    if total_cocktails == 0:
                        print("❌ No cocktails found in the database.")
                        return []
                    
                    vec = self._to_vector(query_embedding)
                    cursor.execute("""
                        SELECT id, name, ingredients, recipe, glass, category, iba, alcoholic,
                            1 - (embedding <=> %s::vector) as similarity
                        FROM cocktails
                        WHERE 1 - (embedding <=> %s::vector) > %s
                        ORDER BY similarity DESC
                        LIMIT %s
                    """, (vec, vec, threshold, limit))

                    return cursor.fetchall()
        except Exception as e:
            print(f"Error searching for cocktails: {e}")
            import traceback
            traceback.print_exc()
            return []

    # Recommendation helpers
    def recommend_by_ingredients(self, ingredients, limit=10):
        """
        Recommend by preferred ingredients
        """
        text = f"cocktail with {' and '.join(ingredients)}"
        emb = self.get_user_preferences_embedding([text])
        return self.search_similar_cocktails(emb, limit=limit)
    
    def recommend_by_style(self, style, limit=10):
        """
        Recommend by preferred style (e.g., sweet, strong, fruity)
        """
        text = f"cocktail that is {' and '.join(style)}"
        emb = self.get_user_preferences_embedding([text])
        return self.search_similar_cocktails(emb, limit=limit)

    def recommend_by_occasion(self, occasion, limit=10):
        """
        Recommend by occasion (e.g., party, relaxing, summer)
        """
        text = f"cocktail for {occasion}"
        emb = self.get_user_preferences_embedding([text])
        return self.search_similar_cocktails(emb, limit=limit)

    def recommend_by_mixed_preferences(
        self,
        ingredients=None,
        style=None,
        occasion=None,
        alcoholic=None,
        limit=10
    ):
        """
        Recommend by mixed preferences
        """
        parts = []
        if ingredients:
            parts.append(f"contains {' and '.join(ingredients)}")
        if style:
            parts.append(f"is {' and '.join(style)}")
        if occasion:
            parts.append(f"perfect for {occasion}")
        if alcoholic:
            parts.append(f"is {alcoholic}")
        if not parts:
            return []

        emb = self.get_user_preferences_embedding(parts)
        return self.search_similar_cocktails(emb, limit=limit)

    # Lookups
    def get_cocktail_by_name(self, name):
        try:
            with self.db_setup.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT id, name, ingredients, recipe, glass, category, iba, alcoholic
                        FROM cocktails
                        WHERE LOWER(name) LIKE LOWER(%s)
                        LIMIT 5
                    """, (f"%{name}%",))
                    return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching cocktail by name: {e}")
            return []

    def get_random_cocktails(self, limit=5):
        try:
            with self.db_setup.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM cocktails")
                    count = cur.fetchone()[0]
                    print(f"Database contains {count} cocktails")
                    if count == 0:
                        print("Warning: No cocktails found. Have you run data_processor.py?")
                        return []

                    cur.execute(
                        """
                        SELECT id, name, ingredients, recipe, glass, category, iba, alcoholic
                        FROM cocktails
                        ORDER BY RANDOM()
                        LIMIT %s
                        """,
                        (limit,),
                    )
                    return cur.fetchall()
        except Exception as e:
            print(f"Error getting random cocktails: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_cocktail_by_category(self, category, limit=10):
        try:
            with self.db_setup.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, name, ingredients, recipe, glass, category, iba, alcoholic
                        FROM cocktails
                        WHERE LOWER(category) LIKE LOWER(%s)
                        ORDER BY name
                        LIMIT %s
                        """,
                        (f"%{category}%", limit),
                    )
                    return cur.fetchall()
        except Exception as e:
            print(f"Error getting cocktails by category: {e}")
            return []

    def format_result(self, result):
        if len(result) == 9: # with similarity
            id_, name, ingredients, recipe, glass, category, iba, alcoholic, similarity = result
            return {
                'id': id_,
                'name': name,
                'ingredients': ingredients,
                'recipe': recipe,
                'glass': glass,
                'category': category,
                'iba': iba,
                'alcoholic': alcoholic,
                'similarity': round(similarity * 100, 1) 
            }
        else: # without similarity
            id_, name, ingredients, recipe, glass, category, iba, alcoholic = result
            return {
                'id': id_,
                'name': name,
                'ingredients': ingredients,
                'recipe': recipe,
                'glass': glass,
                'category': category,
                'iba': iba,
                'alcoholic': alcoholic
            }

if __name__ == "__main__":
    recommender = CocktailRecommender()

    print('Testing...')
    results = recommender.recommend_by_ingredients(['vodka', 'lime'], limit=3)
    print(f'\nRecommendations for vodka and lime:')
    for res in results:
        cocktail = recommender.format_result(res)
        print(f" - {cocktail['name']} (Similarity: {cocktail.get('similarity', 'N/A')}%)")
    
    results = recommender.get_random_cocktails(limit=3)
    print(f'\nRandom cocktails:')
    for res in results:
        cocktail = recommender.format_result(res)
        print(f" - {cocktail['name']}")