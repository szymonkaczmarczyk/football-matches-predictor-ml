
const API_BASE_URL = 'http://localhost:8000';

const COUNTRY_CODES = {
    "Afghanistan": "af", "Albania": "al", "Algeria": "dz", "American Samoa": "as", "Andorra": "ad", "Angola": "ao", "Anguilla": "ai", "Antigua and Barbuda": "ag", "Argentina": "ar", "Armenia": "am", "Aruba": "aw", "Australia": "au", "Austria": "at", "Azerbaijan": "az",
    "Bahamas": "bs", "Bahrain": "bh", "Bangladesh": "bd", "Barbados": "bb", "Belarus": "by", "Belgium": "be", "Belize": "bz", "Benin": "bj", "Bermuda": "bm", "Bhutan": "bt", "Bolivia": "bo", "Bosnia and Herzegovina": "ba", "Botswana": "bw", "Brazil": "br", "British Virgin Islands": "vg", "Brunei": "bn", "Bulgaria": "bg", "Burkina Faso": "bf", "Burundi": "bi",
    "Cambodia": "kh", "Cameroon": "cm", "Canada": "ca", "Cape Verde": "cv", "Cayman Islands": "ky", "Central African Republic": "cf", "Chad": "td", "Chile": "cl", "China PR": "cn", "China": "cn", "Chinese Taipei": "tw", "Colombia": "co", "Comoros": "km", "Congo DR": "cd", "Congo": "cg", "Cook Islands": "ck", "Costa Rica": "cr", "Croatia": "hr", "Cuba": "cu", "Curaçao": "cw", "Curacao": "cw", "Cyprus": "cy", "Czech Republic": "cz", "Czechia": "cz",
    "Denmark": "dk", "Djibouti": "dj", "Dominica": "dm", "Dominican Republic": "do",
    "Ecuador": "ec", "Egypt": "eg", "El Salvador": "sv", "England": "gb-eng", "Equatorial Guinea": "gq", "Eritrea": "er", "Estonia": "ee", "Eswatini": "sz", "Ethiopia": "et",
    "Faroe Islands": "fo", "Fiji": "fj", "Finland": "fi", "France": "fr",
    "Gabon": "ga", "Gambia": "gm", "Georgia": "ge", "Germany": "de", "Ghana": "gh", "Gibraltar": "gi", "Greece": "gr", "Grenada": "gd", "Guam": "gu", "Guatemala": "gt", "Guinea": "gn", "Guinea-Bissau": "gw", "Guyana": "gy",
    "Haiti": "ht", "Honduras": "hn", "Hong Kong": "hk", "Hungary": "hu",
    "Iceland": "is", "India": "in", "Indonesia": "id", "Iran": "ir", "Iraq": "iq", "Israel": "il", "Italy": "it", "Ivory Coast": "ci",
    "Jamaica": "jm", "Japan": "jp", "Jordan": "jo",
    "Kazakhstan": "kz", "Kenya": "ke", "Kosovo": "xk", "Kuwait": "kw", "Kyrgyz Republic": "kg", "Kyrgyzstan": "kg",
    "Laos": "la", "Latvia": "lv", "Lebanon": "lb", "Lesotho": "ls", "Liberia": "lr", "Libya": "ly", "Liechtenstein": "li", "Lithuania": "lt", "Luxembourg": "lu",
    "Macau": "mo", "Madagascar": "mg", "Malawi": "mw", "Malaysia": "my", "Maldives": "mv", "Mali": "ml", "Malta": "mt", "Mauritania": "mr", "Mauritius": "mu", "Mexico": "mx", "Moldova": "md", "Mongolia": "mn", "Montenegro": "me", "Montserrat": "ms", "Morocco": "ma", "Mozambique": "mz", "Myanmar": "mm",
    "Namibia": "na", "Nepal": "np", "Netherlands": "nl", "New Caledonia": "nc", "New Zealand": "nz", "Nicaragua": "ni", "Niger": "ne", "Nigeria": "ng", "North Macedonia": "mk", "Northern Ireland": "gb-nir", "Norway": "no",
    "Oman": "om",
    "Pakistan": "pk", "Palestine": "ps", "Panama": "pa", "Papua New Guinea": "pg", "Paraguay": "py", "Peru": "pe", "Philippines": "ph", "Poland": "pl", "Portugal": "pt", "Puerto Rico": "pr",
    "Qatar": "qa",
    "Republic of Ireland": "ie", "Ireland": "ie", "Romania": "ro", "Russia": "ru", "Rwanda": "rw",
    "Saint Kitts and Nevis": "kn", "St. Kitts and Nevis": "kn", "Saint Lucia": "lc", "St. Lucia": "lc", "Saint Vincent and the Grenadines": "vc", "St. Vincent and the Grenadines": "vc", "Samoa": "ws", "San Marino": "sm", "São Tomé and Príncipe": "st", "Saudi Arabia": "sa", "Scotland": "gb-sct", "Senegal": "sn", "Serbia": "rs", "Seychelles": "sc", "Sierra Leone": "sl", "Singapore": "sg", "Slovakia": "sk", "Slovenia": "si", "Solomon Islands": "sb", "Somalia": "so", "South Africa": "za", "South Sudan": "ss", "Spain": "es", "Sri Lanka": "lk", "Sudan": "sd", "Suriname": "sr", "Sweden": "se", "Switzerland": "ch", "Syria": "sy",
    "Tahiti": "pf", "Tajikistan": "tj", "Tanzania": "tz", "Thailand": "th", "East Timor": "tl", "Togo": "tg", "Tonga": "to", "Trinidad and Tobago": "tt", "Tunisia": "tn", "Turkey": "tr", "Türkiye": "tr", "Turkmenistan": "tm", "Turks and Caicos Islands": "tc",
    "Uganda": "ug", "Ukraine": "ua", "United Arab Emirates": "ae", "United States": "us", "USA": "us", "Uruguay": "uy", "Uzbekistan": "uz",
    "Vanuatu": "vu", "Venezuela": "ve", "Vietnam": "vn",
    "Wales": "gb-wls",
    "Yemen": "ye",
    "Zambia": "zm", "Zimbabwe": "zw"
};

function getFlagUrl(country) {
    if (!country) return 'https://flagcdn.com/w40/un.png';
    const code = COUNTRY_CODES[country];
    if (code) {
        return `https://flagcdn.com/w40/${code}.png`;
    }

    return 'https://flagcdn.com/w40/un.png';
}

document.addEventListener('DOMContentLoaded', () => {

    const homeSelect = document.getElementById('home-team-select');
    const awaySelect = document.getElementById('away-team-select');

    const homeFlag = document.getElementById('home-flag');
    const awayFlag = document.getElementById('away-flag');

    const homeScoreBox = document.getElementById('home-score-box');
    const awayScoreBox = document.getElementById('away-score-box');

    const barTeam1 = document.getElementById('bar-team1');
    const barDraw = document.getElementById('bar-draw');
    const barTeam2 = document.getElementById('bar-team2');

    const legendTeam1Text = document.getElementById('legend-team1-text');
    const legendDrawText = document.getElementById('legend-draw-text');
    const legendTeam2Text = document.getElementById('legend-team2-text');

    const predictBtn = document.getElementById('predict-btn');
    const spinner = document.getElementById('btn-spinner');
    const notification = document.getElementById('notification');

    const neutralCheckbox = document.getElementById('neutral-ground-checkbox');
    const homeRoleLabel = document.getElementById('home-role-label');
    const awayRoleLabel = document.getElementById('away-role-label');

    async function initTeams() {
        try {
            showNotification('Ładowanie list drużyn...', 'warning');

            const response = await fetch(`${API_BASE_URL}/api/teams`);
            if (!response.ok) {
                throw new Error('Nie udało się pobrać listy zespołów z serwera.');
            }

            const teams = await response.json();

            homeSelect.innerHTML = '';
            awaySelect.innerHTML = '';

            teams.forEach(team => {
                const optHome = document.createElement('option');
                optHome.value = team;
                optHome.textContent = team;
                homeSelect.appendChild(optHome);

                const optAway = document.createElement('option');
                optAway.value = team;
                optAway.textContent = team;
                awaySelect.appendChild(optAway);
            });

            if (teams.includes('Poland')) {
                homeSelect.value = 'Poland';
            } else {
                homeSelect.selectedIndex = 0;
            }

            if (teams.includes('Argentina')) {
                awaySelect.value = 'Argentina';
            } else {
                awaySelect.selectedIndex = teams.length > 1 ? 1 : 0;
            }

            updateFlags();
            hideNotification();

        } catch (err) {
            console.error(err);
            showNotification('Błąd: Nie można połączyć się z backendem FastAPI. Upewnij się, że serwer działa na porcie 8000.', 'error');
        }
    }

    function updateFlags() {
        homeFlag.src = getFlagUrl(homeSelect.value);
        awayFlag.src = getFlagUrl(awaySelect.value);
    }

    function updateRoleLabels() {
        if (neutralCheckbox.checked) {
            homeRoleLabel.textContent = 'DRUŻYNA A';
            awayRoleLabel.textContent = 'DRUŻYNA B';
        } else {
            homeRoleLabel.textContent = 'GOSPODARZ';
            awayRoleLabel.textContent = 'GOŚĆ';
        }
    }

    homeSelect.addEventListener('change', updateFlags);
    awaySelect.addEventListener('change', updateFlags);
    neutralCheckbox.addEventListener('change', updateRoleLabels);

    async function runPrediction() {
        const team1 = homeSelect.value;
        const team2 = awaySelect.value;
        const neutral = neutralCheckbox.checked;

        if (!team1 || !team2) {
            showNotification('Wybierz obie drużyny przed rozpoczęciem symulacji.', 'warning');
            return;
        }

        if (team1 === team2) {
            showNotification('Gospodarz i gość muszą być różnymi zespołami!', 'warning');
            return;
        }

        hideNotification();
        predictBtn.disabled = true;
        spinner.classList.remove('hidden');
        predictBtn.querySelector('span').textContent = 'Obliczanie szans...';

        try {
            const res = await fetch(`${API_BASE_URL}/api/predict`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ team1, team2, neutral })
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || 'Błąd podczas przetwarzania predykcji.');
            }

            const data = await res.json();

            homeScoreBox.textContent = data.predicted_score.team1;
            awayScoreBox.textContent = data.predicted_score.team2;

            const p1 = data.probabilities.team1;
            const pd = data.probabilities.draw;
            const p2 = data.probabilities.team2;

            barTeam1.style.width = `${p1}%`;
            barDraw.style.width = `${pd}%`;
            barTeam2.style.width = `${p2}%`;

            barTeam1.textContent = p1 > 10 ? `${p1}%` : '';
            barDraw.textContent = pd > 10 ? `${pd}%` : '';
            barTeam2.textContent = p2 > 10 ? `${p2}%` : '';

            legendTeam1Text.textContent = `${team1}: ${p1}%`;
            legendDrawText.textContent = `Remis: ${pd}%`;
            legendTeam2Text.textContent = `${team2}: ${p2}%`;

        } catch (err) {
            console.error(err);
            showNotification(err.message || 'Wystąpił nieoczekiwany błąd serwera.', 'error');
        } finally {

            predictBtn.disabled = false;
            spinner.classList.add('hidden');
            predictBtn.querySelector('span').textContent = 'Oblicz prawdopodobieństwo';
        }
    }

    function showNotification(msg, type) {
        notification.textContent = msg;
        notification.className = `notification ${type}`;
    }

    function hideNotification() {
        notification.className = 'notification hidden';
    }

    predictBtn.addEventListener('click', runPrediction);

    initTeams();
});
