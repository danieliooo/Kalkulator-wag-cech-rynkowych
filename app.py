import streamlit as st
import pandas as pd
import io

# Konfiguracja strony (to, co widać na karcie w przeglądarce)
st.set_page_config(page_title="Kalkulator Wag Cech Rynkowych", layout="wide")

# Nagłówek główny programu
st.title("📊 Kalkulator wag cech rynkowych – wycena nieruchomości")

# Sprawdzenie czy plik został wgrany - potrzebne do automatycznego zwijania instrukcji
plik_wgrany = st.session_state.get("file_uploaded", False)

# Jeśli plik jest wgrany, instrukcja domyślnie się zwija (expanded=False)
with st.expander("📖 Instrukcja obsługi kalkulatora i zasada działania", expanded=not plik_wgrany):
    st.markdown("""
    Narzędzie jest niezwykle pomocne przy stosowaniu **podejścia porównawczego w wycenie nieruchomości**. 
    Umożliwia ono obiektywne i matematyczne określenie wag cech rynkowych w oparciu o algorytm analizy statystycznej par spełniających kryterium **ceteris paribus** (przy pozostałych warunkach niezmiennych).

    ### 💡 Czym jest zasada ceteris paribus w tym programie?
    Algorytm przeszukuje Twoją bazę danych i automatycznie **wskazuje pary nieruchomości, które różnią się między sobą oceną tylko jednej, konkretnej cechy**, podczas gdy wszystkie pozostałe parametry są identyczne. 

    > **Przykład:** Jeśli program znajdzie dwa mieszkania, które mają taki sam standard, są na tym samym piętrze i mają tę samą powierzchnię, ale jedno leży w lepszej lokalizacji niż drugie – oznacza to, że różnica w ich cenie wynika wyłącznie z czynnika lokalizacji. Na tej podstawie system oblicza wagę dla cechy 'lokalizacja'.

    ---

    ### 🛠️ Krok 1: Przygotowanie danych w pliku Excel / CSV
    Przed uruchomieniem analizy należy odpowiednio przygotować bazę danych rynkowych w arkuszu kalkulacyjnym.

    ⚠️ **WAŻNE (Parametryzacja rynku i skala ocen):**
    System **nie przypisuje automatycznie ocen** na podstawie opisów słownych (np. *"stan dobry"*, *"lokalizacja korzystna"*) ani surowych wartości fizycznych (np. powierzchni w $m^2$ czy konkretnego roku budowy). 

    Rzeczoznawca majątkowy/użytkownik musi samodzielnie przeprowadzić analizę jakościową rynku i wprowadzić oceny cech w postaci **ręcznie przygotowanej skali liczbowej** (np. `-1`, `0`, `1`, `2`). Kolumny przeznaczone do wyliczenia wag muszą zawierać wyłącznie cyfry.

    **Wymagana struktura tabeli:**
    Plik może posiadać dowolne nazwy nagłówków, ale musi zawierać kolumnę z identyfikatorem (np. *Lp.* lub *ID*), kolumnę z ceną jednostkową (np. *Cena za m2*) oraz kolumny z cyfrowymi ocenami cech.

    ---

    ### 💻 Krok 2: Wczytanie i konfiguracja w aplikacji WWW
    1. **Wgranie bazy:** W panelu bocznym (po lewej stronie) kliknij przycisk **"Browse files"** i wskaż przygotowany plik Excel (`.xlsx`) lub CSV.
    2. **Mapowanie ceny i ID:** Z list rozwijanych wybierz, która kolumna w Twoim pliku odpowiada za **ID/Lp.**, a która zawiera **CENĘ**.
    3. **Wybór cech rynkowych:** W polu wielokrotnego wyboru (*multiselect*) zaznacz wyłącznie te kolumny, które **zawierają już liczbową ocenę cech (nie słowną)**. Na ich podstawie system rozpocznie szukanie par.

    ---

    ### 🎯 Krok 3: Odczyt wyników i pobranie raportu
    * **Automatyczna filtracja:** Algorytm sparuje nieruchomości, wyliczy wagi wstępne dla każdej cechy, a następnie dokona matematycznego przeskalowania wyników do poziomu **100%**.
    * **Prezentacja wyników:** Wyniki końcowe są generowane w czasie rzeczywistym i prezentowane za pomocą tabeli wynikowej oraz wykresu słupkowego.
    * **Generowanie dokumentacji:** Przycisk **"Pobierz raport tekstowy"** w panelu bocznym umożliwia pobranie gotowego pliku `.txt` ze szczegółowym wykazem wszystkich odnalezionych par.
    """)

# Panel boczny do wczytywania danych
st.sidebar.header("📁 1. Wczytywanie Danych")
uploaded_file = st.sidebar.file_uploader("Wgraj dowolny plik Excel (.xlsx) lub CSV", type=["xlsx", "xls", "csv"])

if uploaded_file is not None:
    # Zgłaszamy systemowi, że plik jest wgrany, aby schować instrukcję przy następnym przeładowaniu
    if not plik_wgrany:
        st.session_state["file_uploaded"] = True
        st.rerun()
        
    try:
        # --- INTELIGENTNE WCZYTYWANIE PLIKU ---
        if uploaded_file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file, sep=None, engine='python')
        
        # Czyszczenie całkowicie pustych wierszy i kolumn
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # --- BEZPIECZNE SZUKANIE NAGŁÓWKA ---
        index_naglowka = None
        for idx in range(min(5, len(df))):  # sprawdzamy pierwsze 5 wierszy
            wiersz_str = df.iloc[idx].astype(str).str.lower().values
            if any('lp' in x or 'id' in x or 'cena' in x for x in wiersz_str):
                index_naglowka = idx
                break
                
        if index_naglowka is not None:
            # POPRAWIONE: Bezpieczna konwersja na tekst i czyszczenie nazw kolumn
            nowe_kolumny = df.iloc[index_naglowka].fillna("Unnamed").astype(str).tolist()
            df.columns = [str(c).strip() for c in nowe_kolumny]
            df = df.iloc[index_naglowka + 1:]
            
        df = df.reset_index(drop=True)
        # -----------------------------------------------------
        
        # --- AUTOMATYCZNE CZYSZCZENIE DANYCH Z TEKSTU ---
        for col in df.columns:
            if str(col).lower() != 'nazwa':
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # --- DYNAMICZNE MAPOWANIE KOLUMN (W PANELU BOCZNYM) ---
        st.sidebar.header("⚙️ 2. Konfiguracja Kolumn")
        
        kolumna_lp = st.sidebar.selectbox("Wskaż kolumnę z ID/Lp.:", options=df.columns)
        kolumna_cena = st.sidebar.selectbox("Wskaż kolumnę z CENĄ (za m² lub całkowitą):", options=df.columns)
        
        df = df.dropna(subset=[kolumna_cena])
        
        dostasowane_kolumny = [c for c in df.columns if c != kolumna_lp and c != kolumna_cena and str(c).lower() != 'nazwa']
        wybrane_cechy = st.sidebar.multiselect(
            "Wybierz kolumny stanowiące CECHY RYNKOWE (tylko kolumny z ocenami liczbowymi):",
            options=dostasowane_kolumny,
            default=[]  
        )
        
        # Podgląd bazy danych w sekcji rozwijanej (zwinięty jeśli wybrano cechy)
        cechy_wybrane = len(wybrane_cechy) > 0
        with st.expander("👀 Podgląd wczytanej bazy danych", expanded=not cechy_wybrane):
            st.dataframe(df, use_container_width=True)
        
        if not wybrane_cechy:
            st.warning("⚠️ Wybierz przynajmniej jedną cechę rynkową z ocenami liczbowymi w panelu bocznym (Krok 2), aby rozpocząć obliczenia.")
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
                    if pelny_zakres_ocen == 0 or pd.isna(pelny_zakres_ocen):
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
    # Resetujemy stan jeśli plik został usunięty
    if plik_wgrany:
        st.session_state["file_uploaded"] = False
        st.rerun()
    st.info("ℹ️ Wgraj dowolny plik z danymi w panelu bocznym, aby rozpocząć konfigurację analizy.")
