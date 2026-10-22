# Football Match Predictor

**Polski** · [English](README.en.md)

> Kto wygra, ile bramek i jak bardzo jesteśmy tego pewni.

Aplikacja webowa i API do przewidywania wyników meczów reprezentacji narodowych. Wybierasz dwie drużyny, a model
podaje prawdopodobieństwo zwycięstwa każdej z nich i remisu oraz najbardziej prawdopodobny wynik. Model uczy się
na ponad 48 tysiącach meczów międzynarodowych od 1872 roku i na historii rankingu FIFA.

Pod spodem są dwa modele: kalibrowany Gradient Boosting do wyniku 1X2 i dwie regresje Poissona do liczby bramek
gospodarza i gościa. Backend to FastAPI, frontend to czysty HTML, CSS i JavaScript bez frameworka.

![Predykcja meczu Polska - Niemcy z wynikiem 1:2 i paskiem prawdopodobieństwa](docs/screenshots/predykcja.png)

## Dla kogo

- **Dla kibiców**, którzy chcą sprawdzić, jak historia i forma oceniają szanse ich drużyny, np. przed
  mundialem 2026.
- **Dla osób uczących się machine learningu** - kompletny przykład od surowego CSV, przez inżynierię cech
  i chronologiczny podział danych, po model serwowany przez API.

Czym projekt **nie jest**: nie jest narzędziem do zakładów bukmacherskich. Trafność ok. 59% na meczach z 2025
roku to dobry wynik dla piłki nożnej, ale piłka nożna pozostaje bardzo losowa.

## Jak to działa

```
results.csv + fifa_ranking.csv (Kaggle)
   │
   ▼
verify_data.py   sprawdza i czyści dane
   │
   ▼
data_prep.py     dokleja ranking FIFA, liczy formę i bilans bezpośrednich meczów
   │
   ▼
train.py         trenuje modele na meczach sprzed 2025, testuje na meczach z 2025-2026
   │
   ▼
main.py          FastAPI: /api/teams, /api/predict i strona w przeglądarce
```

**Cechy meczu** (9 na każdy mecz):

| Cecha | Co mierzy |
|---|---|
| ważona forma gospodarza i gościa | punkty z ostatnich 100 meczów, nowsze mecze ważą więcej (zanik wykładniczy) |
| ranking FIFA obu drużyn i różnica | pozycja w rankingu z dnia przed meczem |
| bilans bezpośrednich meczów | odsetek zwycięstw gospodarza i średnia różnica bramek w meczach tych drużyn |
| bramki w ostatnich 5 meczach | średnia strzelonych bramek obu drużyn |

Wszystkie cechy są liczone tylko z meczów rozegranych wcześniej, żeby model nie widział przyszłości.

**Teren neutralny** - przy zaznaczonej opcji model liczy mecz z obu perspektyw (A u siebie i B u siebie)
i uśrednia wyniki, żeby usunąć przewagę własnego boiska.

## Wyniki

Test na 1 408 meczach od 1 stycznia 2025, trening na 46 783 wcześniejszych meczach:

| Model | Miara | Wynik |
|---|---|---|
| Gradient Boosting (1X2) | trafność | 59,2% |
| Gradient Boosting (1X2) | log-loss | 0,902 |
| Poisson - bramki gospodarza | MAE | 1,12 |
| Poisson - bramki gościa | MAE | 0,92 |

Najważniejsze cechy według modelu: średnia różnica bramek w bezpośrednich meczach i ważona forma obu drużyn.

## Zrzuty ekranu

| Teren neutralny | Telefon |
|---|---|
| ![Mecz Francja - Holandia na terenie neutralnym, drużyny oznaczone jako A i B](docs/screenshots/neutralny-teren.png) | ![Widok na telefonie z meczem Polska - Holandia](docs/screenshots/telefon.png) |

## Uruchomienie

Wymagany Python 3.10 lub nowszy.

1. Zainstaluj zależności:
   ```bash
   pip install -r requirements.txt
   ```
2. Pobierz z Kaggle pliki `results.csv` (wyniki meczów międzynarodowych) i `fifa_ranking.csv` (historia
   rankingu FIFA) i umieść je w folderze `data/`.
3. Przygotuj dane i wytrenuj modele:
   ```bash
   python src/verify_data.py
   python src/data_prep.py
   python src/train.py
   ```
4. Uruchom serwer:
   ```bash
   python main.py
   ```
   Aplikacja działa pod adresem [http://localhost:8000](http://localhost:8000).

## API

| Metoda | Adres | Co robi |
|---|---|---|
| `GET` | `/api/teams` | Lista drużyn z danych historycznych |
| `POST` | `/api/predict` | Predykcja meczu |

Przykład:

```bash
curl -X POST http://localhost:8000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"team1": "Poland", "team2": "Germany", "neutral": false}'
```

```json
{
  "status": "success",
  "matchup": { "home_team": "Poland", "away_team": "Germany", "neutral": false },
  "probabilities": { "team1": 23, "draw": 28, "team2": 49 },
  "predicted_score": { "team1": 1, "team2": 2 }
}
```

Nazwy drużyn są po angielsku, tak jak w danych źródłowych. Interaktywna dokumentacja FastAPI jest pod
`/docs`.

## Struktura

```
src/
  verify_data.py   sprawdzenie i czyszczenie danych
  data_prep.py     ranking FIFA, forma, bilans bezpośrednich meczów
  train.py         trening i ocena modeli
static/            frontend (HTML, CSS, JavaScript)
main.py            serwer FastAPI
data/              pliki CSV (poza gitem)
models/            wytrenowane modele .joblib (poza gitem)
docs/screenshots/  zrzuty ekranu do README
```

## Licencja

[MIT](LICENSE) © 2026 Szymon Kaczmarczyk

Dane z Kaggle mają własne licencje, sprawdź je na stronach zbiorów. Flagi w interfejsie pochodzą z
[flagcdn.com](https://flagcdn.com).
