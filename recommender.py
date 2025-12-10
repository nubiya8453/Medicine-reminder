# recommender.py — Fully fixed version for disease_medicine_schedule.xlsx

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from difflib import get_close_matches


class Recommender:
    def __init__(self, dataset_path="disease_medicine_schedule.xlsx"):
        # Load and clean dataset
        self.df = pd.read_excel(dataset_path)
        self.df.columns = [c.strip().lower().replace(" ", "_") for c in self.df.columns]

        print(f"🧾 Loaded Excel Columns: {list(self.df.columns)}")

        # Column detection
        self.disease_col = "disease"
        self.medicine_col = "medicine"
        self.dosage_col = "dosage"
        self.time_col = "time_to_take"

        # Clean text
        for col in [self.disease_col, self.medicine_col, self.dosage_col, self.time_col]:
            self.df[col] = (
                self.df[col]
                .astype(str)
                .fillna("")
                .str.lower()
                .str.strip()
            )

        # Train model
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.vectors = self.vectorizer.fit_transform(self.df[self.disease_col])
        print("✅ Recommender initialized successfully!")

    def recommend(self, disease_query):
        """Intelligent partial + fuzzy + semantic matching"""
        query = disease_query.lower().strip()
        if not query:
            return self._fallback("No disease entered")

        # Step 1️⃣: Partial match
        for _, row in self.df.iterrows():
            if query in row[self.disease_col]:
                return self._format_output(row)

        # Step 2️⃣: TF-IDF similarity
        query_vec = self.vectorizer.transform([query])
        similarity = cosine_similarity(query_vec, self.vectors)
        idx = similarity.argmax()
        score = similarity[0, idx]
        print(f"🔍 Search: '{query}' | Match: '{self.df.iloc[idx][self.disease_col]}' | Score: {score:.2f}")

        if score >= 0.1:
            return self._format_output(self.df.iloc[idx])

        # Step 3️⃣: Fuzzy matching
        close_matches = get_close_matches(query, self.df[self.disease_col], n=1, cutoff=0.3)
        if close_matches:
            row = self.df[self.df[self.disease_col] == close_matches[0]].iloc[0]
            return self._format_output(row)

        # Step 4️⃣: No match found
        return self._fallback(query)

    def _format_output(self, row):
        """Format and clean output"""
        return {
            "disease": str(row[self.disease_col]).capitalize(),
            "medicine": str(row[self.medicine_col]).capitalize(),
            "dosage": str(row[self.dosage_col]),
            "time_to_take": str(row[self.time_col]),
        }

    def _fallback(self, disease_query):
        """Default fallback"""
        return {
            "disease": disease_query.capitalize(),
            "medicine": "Consult Doctor for Proper Medicine",
            "dosage": "N/A",
            "time_to_take": "N/A",
        }
