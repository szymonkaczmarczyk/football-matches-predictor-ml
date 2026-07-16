# Football Match Predictor | ML

Aplikacja webowa i API do przewidywania wyników meczów piłkarskich na podstawie historii rozgrywek oraz rankingu FIFA przy użyciu modeli Machine Learning.

## Jak uruchomić projekt

1. **Zainstaluj wymagane biblioteki:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Przygotuj dane:**
   Umieść pliki danych z Kaggle (`results.csv` oraz `fifa_ranking.csv`) w folderze `data/`.

3. **Przetwórz dane i wytrenuj modele:**
   ```bash
   # Weryfikacja poprawności plików danych
   python src/verify_data.py
   
   # Przygotowanie danych i inżynieria cech
   python src/data_prep.py
   
   # Wytrenowanie modeli uczenia maszynowego
   python src/train.py
   ```

4. **Uruchom serwer API i stronę WWW:**
   ```bash
   python main.py
   ```
   Aplikacja będzie dostępna pod adresem: [http://localhost:8000](http://localhost:8000)

## Struktura projektu

* `data/` – dane wejściowe (surowe) oraz przetworzone pliki CSV.
* `models/` – pliki wytrenowanych modeli ML (`.joblib`).
* `src/` – skrypty Pythona do weryfikacji, obróbki danych i treningu modeli.
* `static/` – frontend aplikacji (HTML, CSS, JavaScript).
* `main.py` – serwer FastAPI i obsługa zapytań API.
