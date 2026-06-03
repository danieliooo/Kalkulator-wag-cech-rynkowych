import streamlit as st
import pandas as pd
import io

# Konfiguracja strony (to, co widać na karcie w przeglądarce)
st.set_page_config(page_title="Kalkulator Wag Cech Rynkowych", layout="wide")

# Nagłówek główny programu
st.title("📊 Kalkulator wag cech rynkowych – wycena nieruchomości")

# --- PEŁNA INSTRUKCJA UŻYTKOWNIKA NA EKRANIE GŁÓWNYM ---
st.markdown("""
Aplikacja jest profesjonalnym narzędziem wspomagającym proces wyceny nieruchomości w podejściu porównawczym. Służy do automatycznego określania wag cech rynkowych w oparciu o algorytm analizy statystycznej par spełniających rygorystyczne kryterium **ceteris paribus** (przy pozostałych warunkach niezmiennych).

---

### 🛠️ Krok 1: Przygotowanie danych w pliku Excel / CSV

Przed uruchomieniem analizy należy odpowiednio przygotować bazę danych rynkowych w arkuszu kalkulacyjnym.

⚠️ **WAŻNE (Parametryzacja rynku i skala ocen):**
System **nie przypisuje automatycznie ocen** na podstawie opisów słownych (np. *"stan dobry"*, *"lokalizacja korzystna"*) ani surowych wartości fizycznych (np. powierzchni w $m^2$ czy konkretnego roku budowy). 

Rzeczoznawca majątkowy/użytkownik musi samodzielnie przeprowadzić analizę jakościową rynku i wprowadzić oceny cech w postaci **ręcznie przygotowanej skali liczbowej** (np. `-1`, `0`, `1`, `2`). Kolumny przeznaczone do wyliczenia wag muszą zawierać wyłącznie cyfry.

**Wymagana struktura tabeli:**
Plik może posiadać dowolne nazwy nagłówków i dowolną liczbę kolumn, ale algorytm wymaga wskazania trzech kluczowych elementów:
1. **Kolumny z identyfikatorem** (np. *Lp.* lub *ID*).
2. **Kolumny z ceną jednostkową** (np. *Cena za m2* lub *Cena*).
3. **Kolumn z cyfrowymi ocenami cech** (np. *lokalizacja, stan_techniczny, pietro, powierzchnia_kodowana*).

---

### 💻 Krok 2: Wczytanie i konfiguracja w aplikacji WWW

Interfejs programu został zaprojektowany tak, aby obsługiwać pliki o niestandardowej strukturze.

1. **Wgranie bazy:** W panelu bocznym (po lewej stronie) kliknij przycisk **"Browse files"** i wskaż przygotowany plik Excel (`.xlsx`) lub CSV. *(Do celów demonstracyjnych można użyć dołączonego osobno pliku testowego).*
2. **Mapowanie ceny i ID:** Z list rozwijanych wybierz, która kolumna w Twoim pliku odpowiada za **ID/Lp.**, a która zawiera **CENĘ**.
3. **Wybór cech rynkowych:** W polu wielokrotnego wyboru (*multiselect*) zaznacz wyłącznie te kolumny, które stanowią **CECHY RYNKOWE** podlegające analizie. 

---

### 🎯 Krok 3: Odczyt wyników i pobranie raportu

Po poprawnym skonfigurowaniu kolumn, program natychmiastowo wykonuje pełną procedurę obliczeniową:

* **Automatyczna filtracja:** Algorytm przeszukuje całą bazę danych, paruje nieruchomości spełniające warunek *ceteris paribus*, wyliczy wagi wstępne dla każdej cechy, a następnie dokonuje matematycznego przeskalowania wyników do poziomu **100%**.
* **Prezentacja wyników:** Wyniki końcowe są generowane w czasie rzeczywistym i prezentowane za pomocą **czytelnej tabeli wynikowej** oraz **interaktywnego wykresu słupkowego**.
* **Generowanie dokumentacji:** W lewym dolnym rogu aplikacji znajduje się przycisk **"Pobierz raport tekstowy"**. Umożliwia on pobranie gotowego pliku `.txt` zawierającego szczegółowy wykaz wszystkich odnalezionych par wraz z kompletnym tokiem obliczeniowym.

---
""")

# Panel boczny do wczytywania danych
st.sidebar.header("📁 1. Wczytywanie Danych")
uploaded_file = st.sidebar.file_uploader("Wgraj dowolny plik Excel (.xlsx) lub CSV", type=["xlsx", "xls", "csv"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file, sep=';')
        
        # --- AUTOMATYCZNE CZYSZCZENIE DANYCH Z TEKSTU ---
        for col in df.columns:
            if col != 'nazwa' and col != 'Nazwa':
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        st.subheader("👀 Podgląd wczytanej bazy danych")
        st.dataframe(df, use_container_width=True)
        
        # --- DYNAMICZNE MAPOWANIE KOLUMN ---
        st.sidebar.header("⚙️ 2. Konfiguracja Kolumn")
        
        kolumna_lp = st.sidebar.selectbox("Wskaż kolumnę z ID/Lp.:", options=df.columns)
        kolumna_cena = st.sidebar.selectbox("Wskaż kolumnę z CENĄ (za m² lub całkowitą):", options=df.columns)
        
        df = df.dropna(subset=[kolumna_cena])
        
        dostasowane_kolumny = [c for c in df.columns if c not in [kolumna_lp, kolumna_cena]]
        wybrane_cechy = st.sidebar.multiselect(
            "Wybierz kolumny stanowiące CECHY RYNKOWE:",
            options=dostasowane_kolumny,
            default=[]  
        )
        
        if not wybrane_cechy:
            st.warning("⚠️ Wybierz przynajmniej jedną cechę rynkową w panelu bocznym (Krok 2), aby rozpocząć obliczenia.")
        else:
            delta_c = df[kolumna_cena].max() - df[kolumna_cena].min()
            sredmie_wagi = {}
            
            st.subheader("🔍 Analiza par rynkowych (Ceteris Paribus)")
            
            log_output = io.StringIO()
            log_output.write("RAPORT Z DYNAMICZNEJ ANALIZY PAR RYNKOWYCH\n====================================\n")
            
            for kolumna_glowna in wybrane_cechy:
                pozostale_cechy = [c for c in wybrane_cechy if c != kolumna_glowna]
                wagi_par = []
                pelny_zakres_ocen = df[kolumna_glowna].max() - df[kolumna_glowna].min()
                
                nazwa_wyswietlana = str(kolumna_glowna).upper()
                with st.expander(f"Cecha: {nazwa_wyswietlana} (Pełen zakres ocen = {pelny_zakres_ocen})"):
                    if pelny_zakres_ocen == 0:
                        st.warning("Brak zróżnicowania ocen dla tej cechy w bazie danych.")
                        sredmie_wagi[kolumna_glowna] = 0.0
                        continue
                    
                    tabela_par = []
                    for i in range(len(df)):
                        for j in range(i + 1, len(df)):
                            m1 = df.iloc[i]
                            m2 = df.iloc[j]
                            
                            if all(pd.notna(m1[c]) and pd.notna(m2[c]) and m1[c] == m2[c] for c in pozostale_cechy) and m1[kolumna_glowna] != m2[kolumna_glowna]:
                                if m1[kolumna_glowna] > m2[kolumna_glowna]:
                                    pmax, pmin = m1, m2
                                else:
                                    pmax, pmin = m2, m1
                                
                                cena_pmax = pmax[kolumna_cena]
                                cena_pmin = pmin[kolumna_cena]
                                
                                if pd.notna(cena_pmax) and pd.notna(cena_pmin) and cena_pmax >= cena_pmin:
                                    roznica_ocen = pmax[kolumna_glowna] - pmin[kolumna_glowna]
                                    waga_bazowa = (cena_pmax - cena_pmin) / delta_c
                                    mnoznik = pelny_zakres_ocen / roznica_ocen
                                    waga_ostateczna = waga_bazowa * mnoznik * 100
                                    
                                    wagi_par.append(waga_ostateczna)
                                    
                                    tabela_par.append({
                                        "Para": f"ID {int(pmax[kolumna_lp])} vs ID {int(pmin[kolumna_lp])}",
                                        "Cena wyższa": f"{cena_pmax:.2f} zł",
                                        "Cena niższa": f"{cena_pmin:.2f} zł",
                                        "Różnica ocen": roznica_ocen,
                                        "Waga pary (Wi)": f"{waga_ostateczna:.2f}%"
                                    })
                    
                    if tabela_par:
                        st.table(pd.DataFrame(tabela_par))
                        srednia_cechy = sum(wagi_par) / len(wagi_par)
                        sredmie_wagi[kolumna_glowna] = srednia_cechy
                        st.info(f"**Średnia waga wstępna dla cechy '{kolumna_glowna}': {srednia_cechy:.2f}%**")
                        log_output.write(f"\nCecha: {kolumna_glowna} -> Wykryto par: {len(wagi_par)}, Waga wstępna: {srednia_cechy:.2f}%\n")
                    else:
                        st.write("Nie znaleziono par spełniających kryteria rynkowe dla tej cechy.")
                        sredmie_wagi[kolumna_glowna] = 0.0
            
            # --- WYNIKI KOŃCOWE ---
            st.subheader("🎯 Wynik Końcowy - Wagi Cech Rynkowych")
            suma_srednich = sum(sredmie_wagi.values())
            
            if suma_srednich > 0:
                wyniki_tabela = []
                for cecha, sw in sredmie_wagi.items():
                    waga_przeskalowana = (sw / suma_srednich) * 100
                    wyniki_tabela.append({
                        "Cecha rynkowa": str(cecha).capitalize(),
                        "Waga wstępna": f"{sw:.2f}%",
                        "Waga ostateczna (Skorygowana do 100%)": f"{waga_przeskalowana:.2f}%"
                    })
                
                df_wyniki = pd.DataFrame(wyniki_tabela)
                st.dataframe(df_wyniki, use_container_width=True)
                
                df_wykres = pd.DataFrame({
                    'Cecha': [str(c).capitalize() for c in sredmie_wagi.keys()],
                    'Waga (%)': [(sw / suma_srednich) * 100 for sw in sredmie_wagi.values()]
                })
                st.bar_chart(data=df_wykres, x='Cecha', y='Waga (%)')
                
                log_output.write("\n====================================\nZESTAWIENIE KOŃCOWE (DO 100%):\n")
                for cecha, sw in sredmie_wagi.items():
                    log_output.write(f"-> {cecha}: {(sw / suma_srednich) * 100:.2f}%\n")
                
                st.sidebar.download_button(
                    label="📥 Pobierz raport tekstowy",
                    data=log_output.getvalue(),
                    file_name="dynamiczny_raport_wagi_cech.txt",
                    mime="text/plain"
                )
            else:
                st.error("Błąd: Algorytm nie wygenerował żadnych par rynkowych. Spróbuj zmienić zestaw wybranych cech.")
                
    except Exception as e:
        st.error(f"Wystąpił błąd podczas przetwarzania pliku: {e}")
else:
    st.info("ℹ️ Wgraj dowolny plik z danymi w panelu bocznym, aby rozpocząć konfigurację analizy.")
